import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from batch_loader import load_agent_results

FILE_NAME = "agent3_results.json"

if os.path.exists(FILE_NAME):
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            results = json.load(f)
        print(f"[INFO] Loaded {len(results)} results from '{FILE_NAME}'.")
    except Exception as exc:
        print(f"[WARNING] Error reading '{FILE_NAME}': {exc}")
        results = load_agent_results(
            agent_id=3,
            target_file=FILE_NAME,
            fallback_file="graph_results.json",
            run_limit=25
        )
else:
    results = load_agent_results(
        agent_id=3,
        target_file=FILE_NAME,
        fallback_file="graph_results.json",
        run_limit=25
    )

if not isinstance(results, list) or len(results) == 0:
    print(f"File {FILE_NAME} not found. Run python run_graph.py --limit 100 --output agent4_results.json to generate pipeline results.")
    sys.exit(1)


print("=" * 70)
print("              AGENT 3 VALIDATION")
print("=" * 70)


# ============================================================
# BASIC CHECK
# ============================================================

print("\nTotal results:", len(results))





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