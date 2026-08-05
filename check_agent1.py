import json
import pandas as pd


with open(
    "agent1_results.json",
    "r",
    encoding="utf-8"
) as f:

    results = json.load(f)


print("=" * 60)
print("        AGENT 1 QUALITY CHECK")
print("=" * 60)


# Number of results

print("\n1. Number of results")

print(
    "Total:",
    len(results)
)

print(
    "PASS" if len(results) == 100
    else "WARNING"
)


# Duplicate transactions

print("\n2. Duplicate transaction check")

transaction_ids = [
    r["transaction_id"]
    for r in results
]

duplicates = (
    pd.Series(transaction_ids)
    .duplicated()
    .sum()
)

print(
    "Duplicates:",
    duplicates
)

print(
    "PASS" if duplicates == 0
    else "WARNING"
)


# Behavior scores

print("\n3. Behavior score check")

scores = [
    r["behavior_score"]
    for r in results
]

invalid = [
    s
    for s in scores
    if s < 0 or s > 1
]

print(
    "Min:",
    min(scores)
)

print(
    "Max:",
    max(scores)
)

print(
    "PASS" if len(invalid) == 0
    else "WARNING"
)


# Required fields

print("\n4. Required fields")

required = [
    "transaction_id",
    "user_id",
    "behavior_score",
    "risk_indicators",
    "reasoning",
    "agent"
]

errors = 0

for result in results:

    missing = [
        x
        for x in required
        if x not in result
    ]

    if missing:

        errors += 1

        print(
            "Missing:",
            missing
        )


print(
    "PASS" if errors == 0
    else "WARNING"
)


# Agent name

print("\n5. Agent name")

wrong = [
    r
    for r in results
    if r["agent"]
    != "behavior_analyzer"
]

print(
    "PASS" if len(wrong) == 0
    else "WARNING"
)


# Distribution

print("\n6. Score distribution")

print(
    pd.Series(scores).describe()
)


print("\n")
print("=" * 60)
print("AGENT 1 QUALITY CHECK COMPLETE")
print("=" * 60)