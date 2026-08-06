import os

import numpy as np
import pandas as pd
from dotenv import load_dotenv

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DATASET_PATH = "Data/Digital_Payment_Fraud_Detection_Dataset.csv"
RANDOM_STATE = 42
LLM_MODEL = "llama-3.1-8b-instant"

# Model already selected by agent2_risk_v4.py (best PR-AUC of 5 candidates)
ML_MODEL_NAME = "Random Forest (none)"

CATEGORICAL_FEATURES = [
    "transaction_type",
    "payment_mode",
    "device_type",
    "device_location",
]

NUMERIC_FEATURES = [
    "transaction_amount",
    "account_age_days",
    "transaction_hour",
    "previous_failed_attempts",
    "avg_transaction_amount",
    "is_international",
    "ip_risk_score",
    "login_attempts_last_24h",
]

THRESHOLD_GRID = [0.065, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]


def _build_pipeline():
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    preprocessor = ColumnTransformer([
        ("num", numeric, NUMERIC_FEATURES),
        ("cat", categorical, CATEGORICAL_FEATURES),
    ])

    model = RandomForestClassifier(
        n_estimators=100,
        class_weight=None,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    return Pipeline([("prep", preprocessor), ("clf", model)])


class FraudContext:
    """Dataset, trained model and LLM client. Built once, reused by every node."""

    def __init__(self, dataset_path=DATASET_PATH, use_llm=False, verbose=True):
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")

        np.random.seed(RANDOM_STATE)

        self.df = pd.read_csv(dataset_path)
        self.index_by_id = {
            str(tx): i for i, tx in enumerate(self.df["transaction_id"])
        }
        self.verbose = verbose

        self._train_model()
        self.llm = self._make_llm() if use_llm else None

    # --------------------------------------------------------------
    # ML model (same recipe as agent2_risk_v4.py)
    # --------------------------------------------------------------

    def _train_model(self):
        X = self.df[CATEGORICAL_FEATURES + NUMERIC_FEATURES].copy()
        y = self.df["fraud_label"].astype(int).values

        pipeline = _build_pipeline()
        folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

        oof = np.zeros(len(self.df))
        for train_idx, val_idx in folds.split(X, y):
            pipeline.fit(X.iloc[train_idx], y[train_idx])
            oof[val_idx] = pipeline.predict_proba(X.iloc[val_idx])[:, 1]

        self.prevalence = float(y.mean())
        self.roc_auc = float(roc_auc_score(y, oof))
        self.pr_auc = float(average_precision_score(y, oof))
        self.weak_signal = (
            self.roc_auc < 0.55 or self.pr_auc < (self.prevalence + 0.02)
        )

        best_f1, self.ml_threshold = 0.0, 0.50
        for t in THRESHOLD_GRID:
            score = f1_score(y, (oof >= t).astype(int), zero_division=0)
            if score > best_f1:
                best_f1, self.ml_threshold = score, t

        pipeline.fit(X, y)
        self.model = pipeline
        self.ml_probabilities = pipeline.predict_proba(X)[:, 1]
        self.model_name = ML_MODEL_NAME

        if self.verbose:
            print(f"ML model: {self.model_name}")
            print(f"ROC-AUC: {self.roc_auc:.4f} | PR-AUC: {self.pr_auc:.4f}")
            print(f"Weak signal: {'YES' if self.weak_signal else 'NO'}")

    def _make_llm(self):
        load_dotenv()
        key = os.getenv("GROQ_API_KEY")
        if not key:
            return None
        try:
            from groq import Groq
            return Groq(api_key=key)
        except Exception:
            return None

    # --------------------------------------------------------------
    # Lookups used by the nodes
    # --------------------------------------------------------------

    def ml_probability(self, row_index=None, transaction=None):
        if row_index is not None:
            return float(self.ml_probabilities[row_index])

        frame = pd.DataFrame([transaction])[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
        return float(self.model.predict_proba(frame)[:, 1][0])

    def user_history(self, user_id, row_index=None):
        """Past transactions of this user only (rows before the current one)."""
        same_user = self.df["user_id"] == user_id
        if row_index is None:
            return self.df[same_user].copy()
        return self.df[same_user & (self.df.index < row_index)].copy()

    def get_transaction(self, transaction_id):
        key = str(transaction_id)
        if key not in self.index_by_id:
            raise KeyError(f"Transaction not found: {key}")
        row_index = self.index_by_id[key]
        return row_index, self.df.iloc[row_index].to_dict()

    def explain(self, prompt):
        if self.llm is None:
            return None
        try:
            response = self.llm.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return None


_CONTEXT = None


def get_context(dataset_path=DATASET_PATH, use_llm=False, verbose=True):
    """Returns a single shared context so the model is trained only once."""
    global _CONTEXT
    if _CONTEXT is None:
        _CONTEXT = FraudContext(dataset_path, use_llm=use_llm, verbose=verbose)
    return _CONTEXT
