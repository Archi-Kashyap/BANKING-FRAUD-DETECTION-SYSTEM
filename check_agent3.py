import json
import os


FILE_NAME = "agent3_results.json"


# ============================================================
# CHECK FILE
# ============================================================

if not os.path.exists(FILE_NAME):
    print("ERROR: agent3_results.json not found.")
    print("Run agent3_validator.py first.")
    exit()


# ============================================================
# LOAD RESULTS
# ============================================================

with open(
    FILE_NAME,
    "r",
    encoding="utf-8"
) as f:

    results = json.load(f)


print("=" * 70)
print("              AGENT 3 VALIDATION")
print("=" * 70)


# ============================================================
# BASIC CHECK
# ============================================================

print("\nTotal results:", len(results))


if len(results) == 0:

    print("ERROR: No results found.")
    exit()


# ============================================================
# REQUIRED FIELDS
# ============================================================

required_fields = [
    "transaction_id",
    "user_id",
    "agent",
    "anomaly_score",
    "velocity_score",
    "risk_indicators",
    "reasoning"
]


errors = []


for index, result in enumerate(results):

    for field in required_fields:

        if field not in result:

            errors.append(
                f"Transaction {index + 1}: "
                f"Missing field '{field}'"
            )


# ============================================================
# SCORE VALIDATION
# ============================================================

for index, result in enumerate(results):

    anomaly = result.get(
        "anomaly_score"
    )

    velocity = result.get(
        "velocity_score"
    )


    if anomaly is not None:

        if not (
            0 <= anomaly <= 1
        ):

            errors.append(
                f"Transaction {index + 1}: "
                f"Invalid anomaly_score = {anomaly}"
            )


    if velocity is not None:

        if not (
            0 <= velocity <= 1
        ):

            errors.append(
                f"Transaction {index + 1}: "
                f"Invalid velocity_score = {velocity}"
            )


# ============================================================
# AGENT NAME CHECK
# ============================================================

for index, result in enumerate(results):

    if result.get("agent") != "transaction_validator":

        errors.append(
            f"Transaction {index + 1}: "
            "Incorrect agent name"
        )


# ============================================================
# DISPLAY FIRST 5 RESULTS
# ============================================================

print("\n----- SAMPLE RESULTS -----\n")


for result in results[:5]:

    print(
        "Transaction:",
        result.get("transaction_id")
    )

    print(
        "User:",
        result.get("user_id")
    )

    print(
        "Anomaly Score:",
        result.get("anomaly_score")
    )

    print(
        "Velocity Score:",
        result.get("velocity_score")
    )

    print(
        "Risk Indicators:",
        result.get("risk_indicators")
    )

    print(
        "Reasoning:",
        result.get("reasoning")
    )

    print("-" * 50)


# ============================================================
# FINAL VALIDATION
# ============================================================

print("\n")
print("=" * 70)


if len(errors) == 0:

    print("[PASS] AGENT 3 VALIDATION PASSED")

    print(
        "All required fields are present."
    )

    print(
        "All scores are between 0 and 1."
    )

    print(
        "Agent identification is correct."
    )

    print(
        "Agent 3 is ready to be connected."
    )

else:

    print("❌ AGENT 3 VALIDATION FAILED")

    print("\nErrors:")

    for error in errors:

        print(
            "-",
            error
        )


print("=" * 70)