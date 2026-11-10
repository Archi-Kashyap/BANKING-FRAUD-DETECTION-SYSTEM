import json
import os
import sys

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from batch_loader import load_agent_results

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_FILE = os.path.join(
    "Data",
    "Digital_Payment_Fraud_Detection_Dataset.csv"
)
AGENT4_FILE = "agent4_results.json"

OUTPUT_FILE = "system_evaluation.csv"


# ============================================================
# START
# ============================================================

print("=" * 70)
print("             FINAL SYSTEM EVALUATION")
print("=" * 70)


# ============================================================
# LOAD DATASET
# ============================================================

if not os.path.exists(DATASET_FILE):
    print(f"\n[ERROR] Missing dataset file: {DATASET_FILE}")
    sys.exit(1)


df = pd.read_csv(
    DATASET_FILE
)


print(
    f"\nDataset shape: {df.shape}"
)


# ============================================================
# CHECK FRAUD LABEL
# ============================================================

if "fraud_label" not in df.columns:
    print("\n[ERROR] Dataset must contain 'fraud_label' column.")
    sys.exit(1)


# ============================================================
# LOAD AGENT 4
# ============================================================

if os.path.exists(AGENT4_FILE):
    try:
        with open(AGENT4_FILE, "r", encoding="utf-8") as f:
            agent4_results = json.load(f)
        print(f"[INFO] Loaded {len(agent4_results)} results from '{AGENT4_FILE}'.")
    except Exception as exc:
        print(f"[WARNING] Error reading '{AGENT4_FILE}': {exc}")
        agent4_results = load_agent_results(
            agent_id=4,
            target_file=AGENT4_FILE,
            fallback_file="graph_results.json",
            run_limit=25
        )
else:
    agent4_results = load_agent_results(
        agent_id=4,
        target_file=AGENT4_FILE,
        fallback_file="graph_results.json",
        run_limit=25
    )


if not isinstance(agent4_results, list) or len(agent4_results) == 0:
    print(
        f"File {AGENT4_FILE} not found. "
        "Run python run_graph.py --limit 100 --output agent4_results.json "
        "to generate pipeline results."
    )
    sys.exit(1)


print(
    f"Agent 4 results: "
    f"{len(agent4_results)}"
)


# ============================================================
# CONVERT AGENT 4 TO DATAFRAME
# ============================================================

agent4_df = pd.DataFrame(
    agent4_results
)


if "transaction_id" not in agent4_df.columns:
    print("\n[ERROR] Agent 4 results must contain transaction_id.")
    sys.exit(1)


if "decision" not in agent4_df.columns:
    print("\n[ERROR] Agent 4 results must contain decision.")
    sys.exit(1)


# ============================================================
# NORMALIZE IDS
# ============================================================

df["transaction_id"] = (
    df["transaction_id"]
    .astype(str)
)


agent4_df["transaction_id"] = (
    agent4_df["transaction_id"]
    .astype(str)
)


# ============================================================
# MATCH DATA
# ============================================================

merged = df.merge(
    agent4_df,
    on="transaction_id",
    how="inner",
    suffixes=(
        "_dataset",
        "_agent4"
    )
)


print(
    f"\nMatched transactions: "
    f"{len(merged)}"
)


if len(merged) == 0:
    print("\n[ERROR] No matching transaction IDs found.")
    sys.exit(1)


# ============================================================
# ACTUAL LABEL
# ============================================================

y_true = (
    pd.to_numeric(
        merged["fraud_label"],
        errors="coerce"
    )
    .fillna(0)
    .astype(int)
)


# ============================================================
# PREDICTED LABEL
# ============================================================
#
# IMPORTANT:
#
# FRAUD     -> 1
# SUSPICIOUS -> 0
# LEGIT      -> 0
#
# SUSPICIOUS is NOT automatically fraud.
# ============================================================

y_pred = (

    merged["decision"]
    .astype(str)
    .str.upper()
    .eq("FRAUD")
    .astype(int)

)


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    y_true,
    y_pred
)


precision = precision_score(
    y_true,
    y_pred,
    zero_division=0
)


recall = recall_score(
    y_true,
    y_pred,
    zero_division=0
)


f1 = f1_score(
    y_true,
    y_pred,
    zero_division=0
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    y_true,
    y_pred,
    labels=[
        0,
        1
    ]
)


tn, fp, fn, tp = cm.ravel()


# ============================================================
# REPORT
# ============================================================

print("\n")
print("=" * 70)
print("                 PERFORMANCE")
print("=" * 70)


print(
    f"\nAccuracy  : {accuracy:.4f}"
)


print(
    f"Precision : {precision:.4f}"
)


print(
    f"Recall    : {recall:.4f}"
)


print(
    f"F1 Score  : {f1:.4f}"
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("\n----- CONFUSION MATRIX -----")

print(
    "                 Predicted"
)

print(
    "                 Legit  Fraud"
)

print(
    f"Actual Legit     {tn:5d}  {fp:5d}"
)

print(
    f"Actual Fraud     {fn:5d}  {tp:5d}"
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\n----- CLASSIFICATION REPORT -----")

print(
    classification_report(
        y_true,
        y_pred,
        labels=[
            0,
            1
        ],
        target_names=[
            "Legitimate",
            "Fraud"
        ],
        zero_division=0
    )
)


# ============================================================
# AGENT 4 DISTRIBUTION
# ============================================================

print(
    "----- AGENT 4 DECISION DISTRIBUTION -----"
)

print(
    merged["decision"]
    .value_counts()
)


# ============================================================
# ACTUAL DISTRIBUTION
# ============================================================

print(
    "\n----- ACTUAL DATASET DISTRIBUTION -----"
)

print(
    merged["fraud_label"]
    .value_counts()
)


# ============================================================
# SCORE DISTRIBUTION
# ============================================================

if "fraud_score" in merged.columns:

    print(
        "\n----- FRAUD SCORE -----"
    )

    print(
        merged["fraud_score"]
        .describe()
    )


# ============================================================
# SAVE EVALUATION
# ============================================================

evaluation_df = merged[
    [
        "transaction_id",
        "fraud_label",
        "decision"
    ]
].copy()


evaluation_df[
    "predicted_label"
] = y_pred


if "fraud_score" in merged.columns:

    evaluation_df[
        "fraud_score"
    ] = merged[
        "fraud_score"
    ]


if "confidence" in merged.columns:

    evaluation_df[
        "confidence"
    ] = merged[
        "confidence"
    ]


evaluation_df[
    "correct"
] = (

    evaluation_df[
        "fraud_label"
    ]
    ==
    evaluation_df[
        "predicted_label"
    ]

)


evaluation_df.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    f"\nSaved: {OUTPUT_FILE}"
)


print("\n")
print("=" * 70)
print("             EVALUATION COMPLETE")
print("=" * 70)