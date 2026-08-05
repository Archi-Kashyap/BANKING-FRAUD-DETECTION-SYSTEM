import json
import os
from collections import Counter


FILE_NAME = "agent4_results.json"


# ============================================================
# 1. CHECK FILE
# ============================================================

if not os.path.exists(FILE_NAME):
    print("ERROR: agent4_results.json not found.")
    print("Run agent4_synthesizer.py first.")
    exit()


# ============================================================
# 2. LOAD RESULTS
# ============================================================

with open(
    FILE_NAME,
    "r",
    encoding="utf-8"
) as f:
    results = json.load(f)


print("=" * 70)
print("              AGENT 4 VALIDATION")
print("=" * 70)

print("\nTotal results:", len(results))


if len(results) == 0:
    print("ERROR: No results found.")
    exit()


# ============================================================
# 3. REQUIRED FIELDS
# ============================================================

required_fields = [
    "transaction_id",
    "user_id",
    "agent",
    "fraud_score",
    "decision",
    "reasoning",
    "agent_scores",
    "agent_findings"
]

errors = []


for index, result in enumerate(results):

    for field in required_fields:

        if field not in result:

            errors.append(
                f"Transaction {index + 1}: "
                f"Missing '{field}'"
            )


# ============================================================
# 4. FRAUD SCORE VALIDATION
# ============================================================

for index, result in enumerate(results):

    score = result.get(
        "fraud_score"
    )

    try:
        score = float(score)

        if score < 0 or score > 100:

            errors.append(
                f"Transaction {index + 1}: "
                f"Invalid fraud_score = {score}"
            )

    except:

        errors.append(
            f"Transaction {index + 1}: "
            "fraud_score is not numeric"
        )


# ============================================================
# 5. DECISION VALIDATION
# ============================================================

valid_decisions = {
    "LEGIT",
    "SUSPICIOUS",
    "FRAUD"
}


for index, result in enumerate(results):

    decision = result.get(
        "decision"
    )

    if decision not in valid_decisions:

        errors.append(
            f"Transaction {index + 1}: "
            f"Invalid decision = {decision}"
        )


# ============================================================
# 6. CHECK SCORE ↔ DECISION CONSISTENCY
# ============================================================

for index, result in enumerate(results):

    try:

        score = float(
            result["fraud_score"]
        )

        decision = result["decision"]

        if score >= 70:

            expected = "FRAUD"

        elif score >= 40:

            expected = "SUSPICIOUS"

        else:

            expected = "LEGIT"


        if decision != expected:

            errors.append(
                f"Transaction {index + 1}: "
                f"Score {score} has decision "
                f"{decision}, expected {expected}"
            )

    except:
        pass


# ============================================================
# 7. CHECK AGENT SCORES
# ============================================================

agent_score_fields = [
    "behavior_score",
    "risk_score",
    "anomaly_score",
    "velocity_score"
]


for index, result in enumerate(results):

    scores = result.get(
        "agent_scores",
        {}
    )

    for field in agent_score_fields:

        if field not in scores:

            errors.append(
                f"Transaction {index + 1}: "
                f"Missing agent score '{field}'"
            )

            continue


        try:

            value = float(
                scores[field]
            )

            if value < 0 or value > 1:

                errors.append(
                    f"Transaction {index + 1}: "
                    f"{field} = {value} "
                    "outside 0-1 range"
                )

        except:

            errors.append(
                f"Transaction {index + 1}: "
                f"{field} is not numeric"
            )


# ============================================================
# 8. CHECK AGENT NAME
# ============================================================

for index, result in enumerate(results):

    if result.get("agent") != "decision_synthesizer":

        errors.append(
            f"Transaction {index + 1}: "
            "Incorrect agent name"
        )


# ============================================================
# 9. CHECK DUPLICATE TRANSACTIONS
# ============================================================

transaction_ids = [
    result.get("transaction_id")
    for result in results
]


duplicates = [
    tx_id
    for tx_id, count
    in Counter(transaction_ids).items()
    if count > 1
]


if duplicates:

    errors.append(
        f"Duplicate transaction IDs: {duplicates}"
    )


# ============================================================
# 10. DECISION DISTRIBUTION
# ============================================================

decisions = [
    result.get("decision")
    for result in results
]


decision_counts = Counter(
    decisions
)


print("\n----- DECISION DISTRIBUTION -----")

print(
    "LEGIT:",
    decision_counts.get(
        "LEGIT",
        0
    )
)

print(
    "SUSPICIOUS:",
    decision_counts.get(
        "SUSPICIOUS",
        0
    )
)

print(
    "FRAUD:",
    decision_counts.get(
        "FRAUD",
        0
    )
)


# ============================================================
# 11. SAMPLE RESULTS
# ============================================================

print("\n----- SAMPLE RESULTS -----\n")


for result in results[:5]:

    print(
        "Transaction:",
        result.get(
            "transaction_id"
        )
    )

    print(
        "User:",
        result.get(
            "user_id"
        )
    )

    print(
        "Fraud Score:",
        result.get(
            "fraud_score"
        )
    )

    print(
        "Decision:",
        result.get(
            "decision"
        )
    )

    print(
        "Agent Scores:",
        result.get(
            "agent_scores"
        )
    )

    print(
        "Reasoning:",
        result.get(
            "reasoning"
        )
    )

    print("-" * 60)


# ============================================================
# 12. FINAL RESULT
# ============================================================

print("\n")
print("=" * 70)


if len(errors) == 0:

    print("[PASS] AGENT 4 VALIDATION PASSED")

    print(
        "\nAll required fields are present."
    )

    print(
        "Fraud scores are between 0 and 100."
    )

    print(
        "Agent scores are between 0 and 1."
    )

    print(
        "Decisions match the score thresholds."
    )

    print(
        "No duplicate transaction IDs found."
    )

    print(
        "\nAgent 4 is ready."
    )

else:

    print("[FAIL] AGENT 4 VALIDATION FAILED")

    print("\nErrors:")

    for error in errors:

        print(
            "-",
            error
        )


print("=" * 70)