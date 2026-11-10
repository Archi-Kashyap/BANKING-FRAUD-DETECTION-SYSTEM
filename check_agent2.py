import json
import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from batch_loader import load_agent_results

TARGET_FILE = "agent2_results.json"

if os.path.exists(TARGET_FILE):
    try:
        with open(TARGET_FILE, "r", encoding="utf-8") as f:
            results = json.load(f)
        print(f"[INFO] Loaded {len(results)} results from '{TARGET_FILE}'.")
    except Exception as exc:
        print(f"[WARNING] Error reading '{TARGET_FILE}': {exc}")
        results = load_agent_results(
            agent_id=2,
            target_file=TARGET_FILE,
            fallback_file="graph_results.json",
            run_limit=25
        )
else:
    results = load_agent_results(
        agent_id=2,
        target_file=TARGET_FILE,
        fallback_file="graph_results.json",
        run_limit=25
    )

if not isinstance(results, list) or len(results) == 0:
    print(f"File {TARGET_FILE} not found. Run python run_graph.py --limit 100 --output agent4_results.json to generate pipeline results.")
    sys.exit(1)


print("=" * 60)
print("        AGENT 2 QUALITY CHECK")
print("=" * 60)


# ============================================================
# NUMBER OF RESULTS
# ============================================================

print("\n1. Number of results")

print(
    "Total:",
    len(results)
)

print(
    "PASS"
    if len(results) in [25, 100, 7500] or len(results) >= 25
    else "WARNING"
)


# ============================================================
# DUPLICATES
# ============================================================

print("\n2. Duplicate transaction check")

ids = [
    r["transaction_id"]
    for r in results
]

duplicates = (
    pd.Series(ids)
    .duplicated()
    .sum()
)

print(
    "Duplicates:",
    duplicates
)

print(
    "PASS"
    if duplicates == 0
    else "WARNING"
)


# ============================================================
# RISK SCORE
# ============================================================

print("\n3. Risk score check")

scores = [
    r["risk_score"]
    for r in results
]

invalid = [
    x
    for x in scores
    if x < 0 or x > 1
]

print(
    "Minimum:",
    min(scores)
)

print(
    "Maximum:",
    max(scores)
)

print(
    "PASS"
    if len(invalid) == 0
    else "WARNING"
)


# ============================================================
# REQUIRED FIELDS
# ============================================================

print("\n4. Required fields")

required = [
    "transaction_id",
    "user_id",
    "risk_score",
    "risk_indicators",
    "reasoning",
    "agent"
]

errors = 0

for result in results:

    missing = [
        field
        for field in required
        if field not in result
    ]

    if missing:

        errors += 1

        print(
            "Missing:",
            missing
        )


print(
    "PASS"
    if errors == 0
    else "WARNING"
)


# ============================================================
# AGENT NAME
# ============================================================

print("\n5. Agent name")

wrong = [
    r
    for r in results
    if r["agent"]
    != "risk_assessor"
]

print(
    "PASS"
    if len(wrong) == 0
    else "WARNING"
)


# ============================================================
# DISTRIBUTION
# ============================================================

print("\n6. Risk score distribution")

print(
    pd.Series(scores).describe()
)


print("\n")
print("=" * 60)
print("AGENT 2 QUALITY CHECK COMPLETE")
print("=" * 60)

