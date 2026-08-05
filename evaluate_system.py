# import pandas as pd
# import json
# from sklearn.metrics import (
#     accuracy_score,
#     precision_score,
#     recall_score,
#     f1_score,
#     confusion_matrix,
#     classification_report
# )

# # ============================================================
# # 1. LOAD DATASET
# # ============================================================

# DATASET_PATH = "Data/Digital_Payment_Fraud_Detection_Dataset.csv"

# df = pd.read_csv(DATASET_PATH)

# print("=" * 70)
# print("          MULTI-AGENT SYSTEM EVALUATION")
# print("=" * 70)

# print("\nDataset shape:", df.shape)


# # ============================================================
# # 2. LOAD AGENT 4 RESULTS
# # ============================================================

# with open(
#     "agent4_results.json",
#     "r",
#     encoding="utf-8"
# ) as f:

#     results = json.load(f)

# print(
#     "Agent 4 results:",
#     len(results)
# )


# # ============================================================
# # 3. CREATE PREDICTION TABLE
# # ============================================================

# predictions = []

# for result in results:

#     transaction_id = result["transaction_id"]

#     decision = result["decision"]

#     fraud_score = result["fraud_score"]

#     # Convert Agent 4 decision to binary label
#     if decision in ["FRAUD", "SUSPICIOUS"]:
#         predicted_label = 1
#     else:
#         predicted_label = 0

#     predictions.append({
#         "transaction_id": transaction_id,
#         "fraud_score": fraud_score,
#         "decision": decision,
#         "predicted_label": predicted_label
#     })


# pred_df = pd.DataFrame(predictions)


# # ============================================================
# # 4. MERGE WITH REAL DATASET
# # ============================================================

# evaluation_df = pred_df.merge(
#     df[
#         [
#             "transaction_id",
#             "fraud_label"
#         ]
#     ],
#     on="transaction_id",
#     how="inner"
# )


# print(
#     "\nTransactions successfully matched:",
#     len(evaluation_df)
# )


# if len(evaluation_df) == 0:

#     raise ValueError(
#         "No transaction IDs matched the dataset."
#     )


# # ============================================================
# # 5. ACTUAL VS PREDICTED
# # ============================================================

# y_true = evaluation_df[
#     "fraud_label"
# ].astype(int)

# y_pred = evaluation_df[
#     "predicted_label"
# ].astype(int)


# # ============================================================
# # 6. METRICS
# # ============================================================

# accuracy = accuracy_score(
#     y_true,
#     y_pred
# )

# precision = precision_score(
#     y_true,
#     y_pred,
#     zero_division=0
# )

# recall = recall_score(
#     y_true,
#     y_pred,
#     zero_division=0
# )

# f1 = f1_score(
#     y_true,
#     y_pred,
#     zero_division=0
# )


# # ============================================================
# # 7. DISPLAY METRICS
# # ============================================================

# print("\n")
# print("=" * 70)
# print("                 PERFORMANCE")
# print("=" * 70)

# print(
#     f"\nAccuracy :  {accuracy:.4f}"
# )

# print(
#     f"Precision:  {precision:.4f}"
# )

# print(
#     f"Recall   :  {recall:.4f}"
# )

# print(
#     f"F1 Score :  {f1:.4f}"
# )


# # ============================================================
# # 8. CONFUSION MATRIX
# # ============================================================

# cm = confusion_matrix(
#     y_true,
#     y_pred
# )

# print("\n----- CONFUSION MATRIX -----")

# print(cm)


# # ============================================================
# # 9. CLASSIFICATION REPORT
# # ============================================================

# print("\n----- CLASSIFICATION REPORT -----")

# print(
#     classification_report(
#         y_true,
#         y_pred,
#         target_names=[
#             "Legitimate",
#             "Fraud"
#         ],
#         zero_division=0
#     )
# )


# # ============================================================
# # 10. DECISION DISTRIBUTION
# # ============================================================

# print(
#     "\n----- AGENT 4 DECISIONS -----"
# )

# print(
#     evaluation_df[
#         "decision"
#     ].value_counts()
# )


# # ============================================================
# # 11. SAVE EVALUATION
# # ============================================================

# evaluation_df.to_csv(
#     "system_evaluation.csv",
#     index=False
# )

# print(
#     "\nSaved: system_evaluation.csv"
# )

# print("=" * 70)


# import pandas as pd
# import json
# from sklearn.metrics import (
#     accuracy_score,
#     precision_score,
#     recall_score,
#     f1_score,
#     confusion_matrix,
#     classification_report
# )

# # ============================================================
# # CONFIG
# # ============================================================

# DATASET_PATH = "Data/Digital_Payment_Fraud_Detection_Dataset.csv"
# AGENT4_FILE = "agent4_results.json"


# # ============================================================
# # LOAD DATASET
# # ============================================================

# print("=" * 70)
# print("             FINAL SYSTEM EVALUATION")
# print("=" * 70)

# df = pd.read_csv(DATASET_PATH)

# print("\nDataset shape:", df.shape)

# if "fraud_label" not in df.columns:
#     raise ValueError(
#         "fraud_label column not found in dataset."
#     )


# # ============================================================
# # LOAD AGENT 4
# # ============================================================

# with open(
#     AGENT4_FILE,
#     "r",
#     encoding="utf-8"
# ) as f:

#     agent4_results = json.load(f)


# print(
#     "Agent 4 results:",
#     len(agent4_results)
# )


# # ============================================================
# # CREATE PREDICTIONS
# # ============================================================

# predictions = []

# for result in agent4_results:

#     transaction_id = result[
#         "transaction_id"
#     ]

#     fraud_score = float(
#         result["fraud_score"]
#     )

#     decision = result[
#         "decision"
#     ]


#     # Binary prediction
#     #
#     # FRAUD and SUSPICIOUS
#     # are treated as positive/fraud
#     #
#     if decision in [
#         "FRAUD",
#         "SUSPICIOUS"
#     ]:

#         predicted_label = 1

#     else:

#         predicted_label = 0


#     predictions.append({

#         "transaction_id":
#             transaction_id,

#         "fraud_score":
#             fraud_score,

#         "decision":
#             decision,

#         "predicted_label":
#             predicted_label

#     })


# prediction_df = pd.DataFrame(
#     predictions
# )


# # ============================================================
# # MERGE WITH ACTUAL LABEL
# # ============================================================

# evaluation_df = prediction_df.merge(

#     df[
#         [
#             "transaction_id",
#             "fraud_label"
#         ]
#     ],

#     on="transaction_id",

#     how="inner"
# )


# print(
#     "\nMatched transactions:",
#     len(evaluation_df)
# )


# if len(evaluation_df) == 0:

#     raise ValueError(
#         "No transaction IDs matched."
#     )


# # ============================================================
# # TRUE / PREDICTED
# # ============================================================

# y_true = evaluation_df[
#     "fraud_label"
# ].astype(int)

# y_pred = evaluation_df[
#     "predicted_label"
# ].astype(int)


# # ============================================================
# # METRICS
# # ============================================================

# accuracy = accuracy_score(
#     y_true,
#     y_pred
# )

# precision = precision_score(
#     y_true,
#     y_pred,
#     zero_division=0
# )

# recall = recall_score(
#     y_true,
#     y_pred,
#     zero_division=0
# )

# f1 = f1_score(
#     y_true,
#     y_pred,
#     zero_division=0
# )


# # ============================================================
# # PRINT METRICS
# # ============================================================

# print("\n")
# print("=" * 70)
# print("                 PERFORMANCE")
# print("=" * 70)

# print(
#     f"\nAccuracy  : {accuracy:.4f}"
# )

# print(
#     f"Precision : {precision:.4f}"
# )

# print(
#     f"Recall    : {recall:.4f}"
# )

# print(
#     f"F1 Score  : {f1:.4f}"
# )


# # ============================================================
# # CONFUSION MATRIX
# # ============================================================

# cm = confusion_matrix(
#     y_true,
#     y_pred
# )


# print("\n")
# print("----- CONFUSION MATRIX -----")

# print(
#     "                 Predicted"
# )

# print(
#     "                 Legit  Fraud"
# )

# print(
#     f"Actual Legit    {cm[0][0]:5d}  {cm[0][1]:5d}"
# )

# print(
#     f"Actual Fraud    {cm[1][0]:5d}  {cm[1][1]:5d}"
# )


# # ============================================================
# # CLASSIFICATION REPORT
# # ============================================================

# print("\n")
# print("----- CLASSIFICATION REPORT -----")

# print(
#     classification_report(

#         y_true,

#         y_pred,

#         target_names=[
#             "Legitimate",
#             "Fraud"
#         ],

#         zero_division=0
#     )
# )


# # ============================================================
# # DECISION DISTRIBUTION
# # ============================================================

# print(
#     "----- AGENT 4 DECISION DISTRIBUTION -----"
# )

# print(
#     evaluation_df[
#         "decision"
#     ].value_counts()
# )


# # ============================================================
# # ACTUAL DISTRIBUTION
# # ============================================================

# print(
#     "\n----- ACTUAL DATASET DISTRIBUTION -----"
# )

# print(
#     evaluation_df[
#         "fraud_label"
#     ].value_counts()
# )


# # ============================================================
# # SAVE RESULTS
# # ============================================================

# evaluation_df.to_csv(
#     "system_evaluation.csv",
#     index=False
# )


# print(
#     "\nSaved: system_evaluation.csv"
# )


# # ============================================================
# # FINAL
# # ============================================================

# print("\n")
# print("=" * 70)
# print("             EVALUATION COMPLETE")
# print("=" * 70)


import json
import os

import pandas as pd

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

DATASET_FILE =  os.path.join(
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

    raise FileNotFoundError(
        f"Missing dataset file: {DATASET_FILE}"
    )


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

    raise ValueError(
        "Dataset must contain 'fraud_label' column."
    )


# ============================================================
# LOAD AGENT 4
# ============================================================

if not os.path.exists(AGENT4_FILE):

    raise FileNotFoundError(
        f"Missing file: {AGENT4_FILE}\n"
        f"Run agent4_synthesizer.py first."
    )


with open(
    AGENT4_FILE,
    "r",
    encoding="utf-8"
) as f:

    agent4_results = json.load(f)


if not isinstance(
    agent4_results,
    list
):

    raise ValueError(
        "agent4_results.json must contain a JSON list."
    )


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

    raise ValueError(
        "Agent 4 results must contain transaction_id."
    )


if "decision" not in agent4_df.columns:

    raise ValueError(
        "Agent 4 results must contain decision."
    )


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

    raise RuntimeError(
        "No matching transaction IDs found."
    )


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