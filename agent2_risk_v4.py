import os
import json
import numpy as np
import pandas as pd
from dotenv import load_dotenv

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

# Optional LLM integration
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


# ============================================================
# CONFIGURATION & REPRODUCIBILITY
# ============================================================

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

DATASET_PATH = "Data/Digital_Payment_Fraud_Detection_Dataset.csv"
OUTPUT_FILE = "agent2_results.json"
MODEL_NAME_LLM = "llama-3.1-8b-instant"
LLM_EXPLANATIONS_COUNT = 20

EXPECTED_ROWS = 7500
EXPECTED_COLUMNS = [
    "transaction_id",
    "user_id",
    "transaction_amount",
    "transaction_type",
    "payment_mode",
    "device_type",
    "device_location",
    "account_age_days",
    "transaction_hour",
    "previous_failed_attempts",
    "avg_transaction_amount",
    "is_international",
    "ip_risk_score",
    "login_attempts_last_24h",
    "fraud_label",
]

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


# ============================================================
# DATA VALIDATION
# ============================================================

def validate_input_dataset(filepath):
    """
    Validates input dataset schema, row count, uniqueness, and data integrity.
    Fails explicitly if constraints are violated.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CRITICAL: Dataset file not found at '{filepath}'")

    df = pd.read_csv(filepath)

    # 1. Column presence check
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"CRITICAL: Missing expected dataset columns: {missing_cols}")

    # 2. Row count check
    if len(df) != EXPECTED_ROWS:
        print(f"NOTICE: Dataset row count is {len(df)} (Expected standard: {EXPECTED_ROWS})")

    # 3. Transaction ID uniqueness
    if df["transaction_id"].duplicated().any():
        dup_count = df["transaction_id"].duplicated().sum()
        raise ValueError(f"CRITICAL: Found {dup_count} duplicate transaction_ids")

    # 4. Null value check
    null_counts = df[EXPECTED_COLUMNS].isnull().sum()
    if null_counts.sum() > 0:
        cols_with_nulls = null_counts[null_counts > 0].to_dict()
        raise ValueError(f"CRITICAL: Dataset contains unexpected null values: {cols_with_nulls}")

    # 5. Infinite numeric value check
    for col in NUMERIC_FEATURES + ["fraud_label"]:
        if np.isinf(df[col]).any():
            raise ValueError(f"CRITICAL: Column '{col}' contains infinite values")

    return df


# ============================================================
# MAIN AGENT 2 PIPELINE
# ============================================================

def main():
    print("=" * 70)
    print("             AGENT 2 - RISK ASSESSOR")
    print("=" * 70)

    # Load and validate dataset
    df = validate_input_dataset(DATASET_PATH)
    print(f"\nDataset shape: {df.shape}")

    fraud_counts = df["fraud_label"].value_counts().to_dict()
    fraud_0 = fraud_counts.get(0, 0)
    fraud_1 = fraud_counts.get(1, 0)
    fraud_prevalence = df["fraud_label"].mean()

    print("\nFraud distribution:")
    print(f"0    {fraud_0}")
    print(f"1    {fraud_1}")
    print(f"\nFraud prevalence: {fraud_prevalence:.4f}")

    print("\nCreating behavioral features...")

    # Define features and target for ML pipeline
    X = df[CATEGORICAL_FEATURES + NUMERIC_FEATURES].copy()
    y = df["fraud_label"].astype(int).values

    # ============================================================
    # LEAK-FREE PREPROCESSING PIPELINE
    # ============================================================

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ]
    )

    # ============================================================
    # MODEL DEFINITIONS & 5-FOLD OOF EVALUATION
    # ============================================================

    candidate_models = {
        "Logistic Regression (balanced)": LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=RANDOM_STATE
        ),
        "Logistic Regression (none)": LogisticRegression(
            class_weight=None, max_iter=1000, random_state=RANDOM_STATE
        ),
        "Random Forest (balanced)": RandomForestClassifier(
            n_estimators=100, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1
        ),
        "Random Forest (none)": RandomForestClassifier(
            n_estimators=100, class_weight=None, random_state=RANDOM_STATE, n_jobs=-1
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            random_state=RANDOM_STATE
        ),
    }

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    print("\nTraining and comparing models with 5-fold OOF validation...")

    model_evaluations = {}

    for model_name, clf in candidate_models.items():
        oof_probs = np.zeros(len(df))

        pipeline = Pipeline([
            ("prep", preprocessor),
            ("clf", clf),
        ])

        for train_idx, val_idx in skf.split(X, y):
            X_tr, y_tr = X.iloc[train_idx], y[train_idx]
            X_va, y_va = X.iloc[val_idx], y[val_idx]

            pipeline.fit(X_tr, y_tr)
            oof_probs[val_idx] = pipeline.predict_proba(X_va)[:, 1]

        roc_auc = roc_auc_score(y, oof_probs)
        pr_auc = average_precision_score(y, oof_probs)

        # Operational decision threshold evaluation (maximizing F1 for reporting)
        best_thresh = 0.50
        best_f1 = 0.0
        best_prec = 0.0
        best_rec = 0.0
        best_cm = confusion_matrix(y, (oof_probs >= 0.50).astype(int))

        for t in [0.065, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]:
            preds_t = (oof_probs >= t).astype(int)
            f1_t = f1_score(y, preds_t, zero_division=0)
            if f1_t > best_f1:
                best_f1 = f1_t
                best_thresh = t
                best_prec = precision_score(y, preds_t, zero_division=0)
                best_rec = recall_score(y, preds_t, zero_division=0)
                best_cm = confusion_matrix(y, preds_t)

        model_evaluations[model_name] = {
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "best_threshold": best_thresh,
            "precision": best_prec,
            "recall": best_rec,
            "f1": best_f1,
            "confusion_matrix": best_cm,
            "oof_probs": oof_probs,
        }

        print(f"\nModel: {model_name}")
        print(f"  ROC-AUC:   {roc_auc:.4f}")
        print(f"  PR-AUC:    {pr_auc:.4f} (Baseline prevalence = {fraud_prevalence:.4f})")
        print(f"  Reporting Threshold: {best_thresh:.3f} | Prec: {best_prec:.4f} | Rec: {best_rec:.4f} | F1: {best_f1:.4f}")
        print(f"  Confusion Matrix:\n{best_cm}")

    # Select best model based on PR-AUC
    best_model_name = max(model_evaluations.keys(), key=lambda k: model_evaluations[k]["pr_auc"])
    best_eval = model_evaluations[best_model_name]

    # ============================================================
    # WEAK SIGNAL DETECTION
    # ============================================================

    is_weak_signal = (
        best_eval["roc_auc"] < 0.55
        or best_eval["pr_auc"] < (fraud_prevalence + 0.02)
    )

    if is_weak_signal:
        print("\n" + "!" * 70)
        print("WARNING:")
        print("The available dataset does not contain strong predictive fraud signal.")
        print("ML probability will be treated as a supporting signal rather than the sole")
        print("source of final risk assessment.")
        print("!" * 70)

    print(f"\nFraud prevalence baseline: {fraud_prevalence:.4f}")
    print(f"ML ROC-AUC: {best_eval['roc_auc']:.4f}")
    print(f"ML PR-AUC:  {best_eval['pr_auc']:.4f}")
    print(f"Weak signal: {'YES' if is_weak_signal else 'NO'}")

    print(f"\nBEST AVAILABLE ML MODEL")
    print(f"Selected: {best_model_name} (best available weak-signal model)")

    # Train selected model once on full dataset to produce final probabilities
    final_pipeline = Pipeline([
        ("prep", preprocessor),
        ("clf", candidate_models[best_model_name]),
    ])
    final_pipeline.fit(X, y)
    ml_probabilities = final_pipeline.predict_proba(X)[:, 1]

    # Optional Groq LLM setup
    load_dotenv()
    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_client = None
    if HAS_GROQ and groq_api_key:
        try:
            groq_client = Groq(api_key=groq_api_key)
        except Exception:
            groq_client = None

    print("\nGenerating final risk assessments...")

    results = []
    level_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for idx, row in df.iterrows():
        tx_id = str(row["transaction_id"])
        user_id = str(row["user_id"])
        ml_prob = float(ml_probabilities[idx])

        # ============================================================
        # TRANSPARENT BEHAVIORAL RISK COMPONENTS
        # ============================================================

        # 1. IP Risk (Direct 0-1 score)
        ip_risk = float(np.clip(row["ip_risk_score"], 0.0, 1.0))

        # 2. Failed Attempt Risk (0-4 observed range normalized to [0,1])
        failed_attempts = float(row["previous_failed_attempts"])
        failed_risk = float(np.clip(failed_attempts / 4.0, 0.0, 1.0))

        # 3. Login Attempt Risk (1-9 observed range normalized to [0,1])
        login_attempts = float(row["login_attempts_last_24h"])
        login_risk = float(np.clip(login_attempts / 9.0, 0.0, 1.0))

        # 4. Amount Anomaly Risk (Ratio normalized via log deviation)
        tx_amount = float(row["transaction_amount"])
        avg_amount = float(row["avg_transaction_amount"])
        amount_ratio = tx_amount / max(avg_amount, 1.0)
        # Log-ratio deviation: 5x deviation maps to 1.0, 1x maps to 0.0
        amt_anomaly_risk = float(np.clip(abs(np.log(max(amount_ratio, 0.001))) / np.log(5.0), 0.0, 1.0))

        # 5. International Risk (Binary flag)
        is_intl = int(row["is_international"])
        intl_risk = float(np.clip(is_intl, 0.0, 1.0))

        # Combined Domain Risk
        domain_risk = (
            0.30 * ip_risk
            + 0.25 * failed_risk
            + 0.20 * login_risk
            + 0.15 * amt_anomaly_risk
            + 0.10 * intl_risk
        )
        domain_risk = float(np.clip(domain_risk, 0.0, 1.0))

        # Hybrid Final Risk Score: 80% Domain Risk + 20% ML Probability
        final_risk = 0.80 * domain_risk + 0.20 * ml_prob
        risk_score = round(float(np.clip(final_risk, 0.0, 1.0)), 4)

        # Fixed Deterministic Risk Level Cutoffs
        if risk_score >= 0.55:
            risk_lvl = "HIGH"
        elif risk_score >= 0.35:
            risk_lvl = "MEDIUM"
        else:
            risk_lvl = "LOW"

        level_counts[risk_lvl] += 1

        # ============================================================
        # EXPLAINABLE RISK INDICATORS & REASONING
        # ============================================================

        indicators = []
        if ip_risk >= 0.70:
            indicators.append("high_ip_risk")
        if failed_attempts >= 3:
            indicators.append("repeated_failed_attempts")
        if login_attempts >= 5:
            indicators.append("high_login_attempts")
        if amount_ratio >= 2.0 or amount_ratio <= 0.20:
            indicators.append("unusual_transaction_amount")
        if is_intl == 1:
            indicators.append("international_transaction")
        if ml_prob >= 0.20:
            indicators.append("elevated_ml_probability")

        if risk_lvl == "HIGH":
            reasoning = "Elevated behavioral risk driven by IP risk, authentication activity, or transaction anomaly."
        elif risk_lvl == "MEDIUM":
            reasoning = "Moderate risk signals detected across authentication or transaction parameters."
        else:
            reasoning = "Low behavioral risk based on IP risk, authentication activity, and transaction amount."

        if is_weak_signal:
            reasoning += " ML probability was used as a supporting signal; dataset-level validation indicates weak predictive ML signal."

        llm_reasoning = reasoning

        # Optional LLM Explanation for top records if Groq is available
        if groq_client and len(results) < LLM_EXPLANATIONS_COUNT:
            try:
                prompt = (
                    f"Explain this banking risk assessment briefly.\n"
                    f"Risk Score: {risk_score:.4f}, Level: {risk_lvl}\n"
                    f"IP Risk: {ip_risk:.2f}, Failed Attempts: {int(failed_attempts)}, Logins 24h: {int(login_attempts)}\n"
                    f"Amount Ratio: {amount_ratio:.2f}, International: {is_intl}, ML Prob: {ml_prob:.4f}\n"
                    f"Provide a 2-sentence objective summary."
                )
                res = groq_client.chat.completions.create(
                    model=MODEL_NAME_LLM,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                llm_reasoning = res.choices[0].message.content.strip()
            except Exception:
                pass

        record = {
            "transaction_id": tx_id,
            "user_id": user_id,
            "agent": "risk_assessor",
            "risk_score": risk_score,
            "risk_level": risk_lvl,
            "risk_indicators": indicators,
            "details": {
                "ml_probability": round(ml_prob, 4),
                "domain_risk": round(domain_risk, 4),
                "ip_risk": round(ip_risk, 4),
                "international_risk": intl_risk,
                "failed_attempts": int(failed_attempts),
                "login_attempts": int(login_attempts),
                "transaction_amount": round(tx_amount, 2),
                "average_transaction_amount": round(avg_amount, 2),
                "amount_to_average_ratio": round(amount_ratio, 4),
                "account_age_days": int(row["account_age_days"]),
                "transaction_hour": int(row["transaction_hour"]),
                "transaction_type": str(row["transaction_type"]),
                "payment_mode": str(row["payment_mode"]),
                "device_type": str(row["device_type"]),
                "device_location": str(row["device_location"]),
            },
            "model": best_model_name,
            "ml_decision_threshold": best_eval["best_threshold"],
            "reasoning": reasoning,
            "llm_reasoning": llm_reasoning,
        }

        results.append(record)

        if (idx + 1) % 500 == 0 or (idx + 1) == len(df):
            print(f"Processed {idx + 1}/{len(df)}")

    # ============================================================
    # JSON VALIDATION BEFORE SAVING
    # ============================================================

    if len(results) != len(df):
        raise ValueError(f"CRITICAL: Output record count ({len(results)}) != input dataset count ({len(df)})")

    tx_ids = [r["transaction_id"] for r in results]
    if len(set(tx_ids)) != len(results):
        raise ValueError("CRITICAL: Duplicate transaction_ids detected in final results")

    for r in results:
        s = r["risk_score"]
        if not isinstance(s, (float, int)) or np.isnan(s) or np.isinf(s) or not (0.0 <= s <= 1.0):
            raise ValueError(f"CRITICAL: Invalid risk_score '{s}' for transaction {r['transaction_id']}")
        if r["risk_level"] not in ["HIGH", "MEDIUM", "LOW"]:
            raise ValueError(f"CRITICAL: Invalid risk_level '{r['risk_level']}' for transaction {r['transaction_id']}")

    # Save output JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("             AGENT 2 COMPLETE")
    print("=" * 70)
    print(f"Successfully processed: {len(results)}")

    scores = [r["risk_score"] for r in results]
    print("\nFinal risk score statistics:")
    print(f"Min: {min(scores):.4f}")
    print(f"Max: {max(scores):.4f}")
    print(f"Avg: {sum(scores)/len(scores):.4f}")

    print("\nRisk levels:")
    print(f"HIGH:   {level_counts['HIGH']}")
    print(f"MEDIUM: {level_counts['MEDIUM']}")
    print(f"LOW:    {level_counts['LOW']}")

    print("\nTop 10 highest-risk transactions:")
    top_10 = sorted(results, key=lambda x: x["risk_score"], reverse=True)[:10]
    for item in top_10:
        print(f"  {item['transaction_id']}: Score={item['risk_score']:.4f}, Level={item['risk_level']}, Indicators={item['risk_indicators']}")

    print("=" * 70)


if __name__ == "__main__":
    main()
