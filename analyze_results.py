import pandas as pd

# ============================================================
# LOAD EVALUATION RESULTS
# ============================================================

FILE = "system_evaluation.csv"

df = pd.read_csv(FILE)

print("=" * 70)
print("             MULTI-AGENT RESULT ANALYSIS")
print("=" * 70)

print("\nTotal transactions:", len(df))


# ============================================================
# 1. ACTUAL FRAUD DISTRIBUTION
# ============================================================

print("\n----- ACTUAL LABEL DISTRIBUTION -----")

actual = df["fraud_label"].value_counts()

print(
    "Legitimate:",
    actual.get(0, 0)
)

print(
    "Fraud:",
    actual.get(1, 0)
)


# ============================================================
# 2. PREDICTED DISTRIBUTION
# ============================================================

print("\n----- PREDICTED DISTRIBUTION -----")

predicted = df["predicted_label"].value_counts()

print(
    "Predicted Legitimate:",
    predicted.get(0, 0)
)

print(
    "Predicted Fraud:",
    predicted.get(1, 0)
)


# ============================================================
# 3. DECISION DISTRIBUTION
# ============================================================

print("\n----- AGENT 4 DECISIONS -----")

print(
    df["decision"].value_counts()
)


# ============================================================
# 4. FRAUD SCORE ANALYSIS
# ============================================================

print("\n----- FRAUD SCORE -----")

print(
    df["fraud_score"].describe()
)


# ============================================================
# 5. TRUE FRAUD SCORE
# ============================================================

true_fraud = df[
    df["fraud_label"] == 1
]

true_legit = df[
    df["fraud_label"] == 0
]


print("\n----- AVERAGE FRAUD SCORE -----")

print(
    "Actual Fraud:",
    round(
        true_fraud["fraud_score"].mean(),
        2
    )
)

print(
    "Actual Legitimate:",
    round(
        true_legit["fraud_score"].mean(),
        2
    )
)


# ============================================================
# 6. FALSE POSITIVES
# ============================================================

false_positive = df[
    (df["fraud_label"] == 0)
    &
    (df["predicted_label"] == 1)
]

print(
    "\n----- FALSE POSITIVES -----"
)

print(
    "Count:",
    len(false_positive)
)

if len(false_positive) > 0:

    print(
        "\nAverage score:",
        round(
            false_positive[
                "fraud_score"
            ].mean(),
            2
        )
    )


# ============================================================
# 7. FALSE NEGATIVES
# ============================================================

false_negative = df[
    (df["fraud_label"] == 1)
    &
    (df["predicted_label"] == 0)
]

print(
    "\n----- FALSE NEGATIVES -----"
)

print(
    "Count:",
    len(false_negative)
)

if len(false_negative) > 0:

    print(
        "\nAverage score:",
        round(
            false_negative[
                "fraud_score"
            ].mean(),
            2
        )
    )


# ============================================================
# 8. SCORE BY DECISION
# ============================================================

print(
    "\n----- SCORE BY DECISION -----"
)

print(
    df.groupby("decision")[
        "fraud_score"
    ].agg(
        [
            "count",
            "mean",
            "min",
            "max"
        ]
    )
)


# ============================================================
# 9. MOST SUSPICIOUS TRANSACTIONS
# ============================================================

print(
    "\n----- TOP 10 HIGHEST FRAUD SCORES -----"
)

print(
    df.sort_values(
        "fraud_score",
        ascending=False
    )[
        [
            "transaction_id",
            "fraud_score",
            "decision",
            "fraud_label"
        ]
    ].head(10).to_string(
        index=False
    )
)


# ============================================================
# 10. FALSE POSITIVE EXAMPLES
# ============================================================

if len(false_positive) > 0:

    print(
        "\n----- FALSE POSITIVE EXAMPLES -----"
    )

    print(
        false_positive[
            [
                "transaction_id",
                "fraud_score",
                "decision",
                "fraud_label"
            ]
        ].head(10).to_string(
            index=False
        )
    )


# ============================================================
# 11. FALSE NEGATIVE EXAMPLES
# ============================================================

if len(false_negative) > 0:

    print(
        "\n----- FALSE NEGATIVE EXAMPLES -----"
    )

    print(
        false_negative[
            [
                "transaction_id",
                "fraud_score",
                "decision",
                "fraud_label"
            ]
        ].head(10).to_string(
            index=False
        )
    )


print("\n" + "=" * 70)
print("                 ANALYSIS COMPLETE")
print("=" * 70)