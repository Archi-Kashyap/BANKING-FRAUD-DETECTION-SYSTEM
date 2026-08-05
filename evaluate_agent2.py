"""
evaluate_agent2.py — Agent 2 Full-Dataset Risk Score Evaluation
================================================================
This script provides a more statistically meaningful evaluation
of the Agent 2 risk_score across all 7,500 transactions and their
ground-truth fraud_label.

IMPORTANT:
- This does NOT change any production output.
- agent2_results.json is read-only here.
- fraud_label is used only for evaluation, never in risk scoring.
- risk_score is an OPERATIONAL signal, not a calibrated probability.
- Results are clearly labeled as Agent 2 only, separate from Agent 4.
"""

import json
import os
import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)


# ============================================================
# CONFIG
# ============================================================

DATASET_FILE = os.path.join(
    "Data",
    "Digital_Payment_Fraud_Detection_Dataset.csv"
)
AGENT2_FILE = "agent2_results.json"
OUTPUT_FILE = "agent2_evaluation.csv"


# ============================================================
# LOAD
# ============================================================

print("=" * 70)
print("     AGENT 2 FULL-DATASET RISK SCORE EVALUATION")
print("     (Separate from Agent 4 end-to-end evaluation)")
print("=" * 70)

if not os.path.exists(DATASET_FILE):
    raise FileNotFoundError(f"Dataset not found: {DATASET_FILE}")

if not os.path.exists(AGENT2_FILE):
    raise FileNotFoundError(
        f"{AGENT2_FILE} not found. Run agent2_risk_v4.py first."
    )

df = pd.read_csv(DATASET_FILE)
df["transaction_id"] = df["transaction_id"].astype(str)

print(f"\nDataset: {df.shape[0]} rows")
print(f"Fraud prevalence: {df['fraud_label'].mean():.4f}")

with open(AGENT2_FILE, "r", encoding="utf-8") as fh:
    a2_data = json.load(fh)

print(f"Agent 2 records loaded: {len(a2_data)}")


# ============================================================
# BUILD EVALUATION DATAFRAME
# ============================================================

a2_df = pd.DataFrame([
    {
        "transaction_id": str(r["transaction_id"]),
        "risk_score": float(r["risk_score"]),
        "risk_level": r["risk_level"],
    }
    for r in a2_data
])

merged = df[["transaction_id", "fraud_label"]].merge(
    a2_df,
    on="transaction_id",
    how="inner"
)

print(f"Matched: {len(merged)} transactions")

if len(merged) == 0:
    raise RuntimeError("No matching transaction IDs found.")

y_true = merged["fraud_label"].astype(int).values
y_score = merged["risk_score"].values
fraud_prev = y_true.mean()


# ============================================================
# ROC-AUC & PR-AUC
# ============================================================

roc_auc = roc_auc_score(y_true, y_score)
pr_auc = average_precision_score(y_true, y_score)

print("\n" + "=" * 70)
print("  AGENT 2 RISK SCORE vs FRAUD LABEL — FULL DATASET (7,500 rows)")
print("=" * 70)

print(f"\nFraud prevalence (baseline PR-AUC):  {fraud_prev:.4f}")
print(f"Agent 2 ROC-AUC:                     {roc_auc:.4f}  (random = 0.5000)")
print(f"Agent 2 PR-AUC:                      {pr_auc:.4f}  (baseline = {fraud_prev:.4f})")

if roc_auc < 0.55 or pr_auc < (fraud_prev + 0.02):
    print("\nCONCLUSION: Weak predictive signal.")
    print(
        "Univariate and cross-validated model evaluation found little evidence\n"
        "of useful predictive signal in the available features against fraud_label.\n"
        "This confirms Agent 2's design choice: ML probability is used as a\n"
        "supporting signal (20% weight) rather than the primary decision driver."
    )
else:
    print("\nCONCLUSION: Some predictive signal detected in risk_score.")


# ============================================================
# THRESHOLD SWEEP (for reporting only — no production change)
# ============================================================

print("\n----- THRESHOLD SWEEP (reporting only) -----")
print(f"{'Threshold':>10} {'Prec':>8} {'Rec':>8} {'F1':>8} {'TP':>6} {'FP':>6} {'FN':>6} {'TN':>6}")

thresholds = [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]

best_f1 = 0.0
best_thresh = 0.50

for t in thresholds:
    y_pred_t = (y_score >= t).astype(int)
    prec = precision_score(y_true, y_pred_t, zero_division=0)
    rec = recall_score(y_true, y_pred_t, zero_division=0)
    f1 = f1_score(y_true, y_pred_t, zero_division=0)
    cm = confusion_matrix(y_true, y_pred_t, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    print(f"{t:>10.2f} {prec:>8.4f} {rec:>8.4f} {f1:>8.4f} {tp:>6d} {fp:>6d} {fn:>6d} {tn:>6d}")
    if f1 > best_f1:
        best_f1 = f1
        best_thresh = t


# ============================================================
# BEST THRESHOLD DETAIL
# ============================================================

print(f"\nBest reporting threshold: {best_thresh:.2f} (F1 = {best_f1:.4f})")
y_pred_best = (y_score >= best_thresh).astype(int)

print("\n----- CLASSIFICATION REPORT (best threshold) -----")
print(classification_report(
    y_true, y_pred_best,
    target_names=["Legitimate", "Fraud"],
    zero_division=0
))

cm_best = confusion_matrix(y_true, y_pred_best, labels=[0, 1])
tn, fp, fn, tp = cm_best.ravel()

print("----- CONFUSION MATRIX (best threshold) -----")
print("                 Predicted")
print("                 Legit   Fraud")
print(f"Actual Legit     {tn:5d}   {fp:5d}")
print(f"Actual Fraud     {fn:5d}   {tp:5d}")


# ============================================================
# RISK LEVEL DISTRIBUTION vs FRAUD LABEL
# ============================================================

print("\n----- RISK LEVEL vs FRAUD LABEL -----")
pivot = merged.groupby(["risk_level", "fraud_label"]).size().unstack(fill_value=0)
pivot.columns = ["Legitimate", "Fraud"]
pivot["Total"] = pivot.sum(axis=1)
pivot["Fraud%"] = (pivot["Fraud"] / pivot["Total"] * 100).round(2)
print(pivot.sort_index())


# ============================================================
# IMPORTANT DISCLAIMER
# ============================================================

print("\n" + "=" * 70)
print("  IMPORTANT DISCLAIMER")
print("=" * 70)
print(
    "\nThe risk_score produced by Agent 2 is an OPERATIONAL RISK SIGNAL,\n"
    "not a calibrated fraud probability. It should not be interpreted\n"
    "as 'P(fraud | features)'.\n"
    "\nThe threshold sweep above is for analysis/reporting purposes only.\n"
    "It does NOT modify any production risk score or agent output.\n"
    "\nThis evaluation is SEPARATE from the Agent 4 end-to-end evaluation\n"
    "which covers 100 transactions (see system_evaluation.csv)."
)


# ============================================================
# SAVE
# ============================================================

merged.to_csv(OUTPUT_FILE, index=False)
print(f"\nSaved: {OUTPUT_FILE}")
print("\n" + "=" * 70)
print("  AGENT 2 EVALUATION COMPLETE")
print("=" * 70)
