import json
import os
from collections import Counter


# ============================================================
# AGENT 4 - DECISION SYNTHESIZER
# Stable Multi-Agent Fraud Decision Engine
# ============================================================

AGENT1_FILE = "agent1_results.json"
AGENT2_FILE = "agent2_results.json"
AGENT3_FILE = "agent3_results.json"

OUTPUT_FILE = "agent4_results.json"


# ============================================================
# CONFIGURATION
# ============================================================

# Score thresholds
HIGH_SCORE = 70.0
MEDIUM_SCORE = 50.0

# Final decision thresholds
# Note: check_agent4.py validator expects score>=70 -> FRAUD, score>=40 -> SUSPICIOUS
FRAUD_SCORE_THRESHOLD = 70.0
SUSPICIOUS_SCORE_THRESHOLD = 40.0

# Strong evidence requirements
MIN_FRAUD_AGENTS = 2
MIN_FRAUD_INDICATORS = 2

# Consensus bonus
CONSENSUS_BONUS_2 = 2.0
CONSENSUS_BONUS_3 = 4.0

MAX_SCORE = 100.0


# ============================================================
# HELPERS
# ============================================================

def load_json(filename):

    if not os.path.exists(filename):
        raise FileNotFoundError(
            f"Missing file: {filename}"
        )

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(
            f"{filename} must contain a JSON list."
        )

    return data


def clamp(
    value,
    low=0.0,
    high=100.0
):

    try:
        value = float(value)
    except (
        ValueError,
        TypeError
    ):
        value = 0.0

    return max(
        low,
        min(high, value)
    )


def get_score(
    data,
    possible_keys
):

    for key in possible_keys:

        value = data.get(key)

        if value is None:
            continue

        try:
            return float(value)

        except (
            ValueError,
            TypeError
        ):
            continue

    return 0.0


def normalize_score(value):

    try:
        value = float(value)
    except (
        ValueError,
        TypeError
    ):
        return 0.0

    # Convert 0-1 scores to 0-100
    if 0 <= value <= 1:
        value *= 100.0

    return clamp(value)


def get_indicators(data):

    indicators = data.get(
        "risk_indicators",
        []
    )

    if indicators is None:
        return []

    if isinstance(
        indicators,
        list
    ):

        return [
            str(x).strip()
            for x in indicators
            if str(x).strip()
        ]

    text = str(indicators).strip()

    if text:
        return [text]

    return []


def safe_text(value):

    if value is None:
        return ""

    return str(value)


def numeric_transaction_key(transaction_id):

    transaction_id = str(
        transaction_id
    )

    if (
        transaction_id.startswith("T")
        and transaction_id[1:].isdigit()
    ):
        return int(
            transaction_id[1:]
        )

    return transaction_id


# ============================================================
# START
# ============================================================

print("=" * 70)
print("          AGENT 4 - DECISION SYNTHESIZER")
print("=" * 70)


# ============================================================
# LOAD RESULTS
# ============================================================

agent1 = load_json(
    AGENT1_FILE
)

agent2 = load_json(
    AGENT2_FILE
)

agent3 = load_json(
    AGENT3_FILE
)


print(
    f"\nAgent 1 results: {len(agent1)}"
)

print(
    f"Agent 2 results: {len(agent2)}"
)

print(
    f"Agent 3 results: {len(agent3)}"
)


# ============================================================
# LOOKUP TABLES
# ============================================================

a1_map = {}

for item in agent1:

    transaction_id = item.get(
        "transaction_id"
    )

    if transaction_id is not None:

        a1_map[
            str(transaction_id)
        ] = item


a2_map = {}

for item in agent2:

    transaction_id = item.get(
        "transaction_id"
    )

    if transaction_id is not None:

        a2_map[
            str(transaction_id)
        ] = item


a3_map = {}

for item in agent3:

    transaction_id = item.get(
        "transaction_id"
    )

    if transaction_id is not None:

        a3_map[
            str(transaction_id)
        ] = item


# ============================================================
# COMMON TRANSACTIONS
# ============================================================

common_ids = sorted(

    set(a1_map.keys())
    &
    set(a2_map.keys())
    &
    set(a3_map.keys()),

    key=numeric_transaction_key
)


print(
    f"\nCommon transactions: "
    f"{len(common_ids)}"
)

print(
    f"Transactions to process: "
    f"{len(common_ids)}"
)


if not common_ids:

    raise RuntimeError(
        "No common transactions found "
        "between Agent 1, Agent 2 and Agent 3."
    )


# ============================================================
# SYNTHESIS
# ============================================================

results = []

decision_counter = Counter()


for index, transaction_id in enumerate(
    common_ids,
    start=1
):

    print(
        f"\nProcessing "
        f"{index}/{len(common_ids)}: "
        f"{transaction_id}"
    )


    r1 = a1_map[
        transaction_id
    ]

    r2 = a2_map[
        transaction_id
    ]

    r3 = a3_map[
        transaction_id
    ]


    # ========================================================
    # AGENT 1 - CUSTOMER BEHAVIOR
    # ========================================================

    behavior_score = normalize_score(

        get_score(
            r1,
            [
                "behavior_score",
                "risk_score",
                "fraud_score",
                "score"
            ]
        )
    )


    # ========================================================
    # AGENT 2 - TRANSACTION RISK
    # ========================================================

    transaction_score = normalize_score(

        get_score(
            r2,
            [
                "transaction_score",
                "risk_score",
                "fraud_score",
                "score"
            ]
        )
    )


    # ========================================================
    # AGENT 3 - ANOMALY
    # ========================================================

    anomaly_score = normalize_score(

        get_score(
            r3,
            [
                "anomaly_score",
                "anomaly_risk",
                "risk_score",
                "fraud_score",
                "score"
            ]
        )
    )


    # ========================================================
    # AGENT 3 - VELOCITY
    # ========================================================

    velocity_raw = get_score(

        r3,
        [
            "velocity_score",
            "velocity_risk",
            "transaction_velocity_score"
        ]
    )


    if velocity_raw != 0:

        velocity_score = normalize_score(
            velocity_raw
        )

    else:

        # Missing velocity should NOT create
        # additional fraud evidence.
        velocity_score = 0.0


    # ========================================================
    # INDICATORS
    # ========================================================

    indicators_1 = get_indicators(
        r1
    )

    indicators_2 = get_indicators(
        r2
    )

    indicators_3 = get_indicators(
        r3
    )


    all_indicators = (

        indicators_1
        +
        indicators_2
        +
        indicators_3

    )


    unique_indicators = list(
        dict.fromkeys(
            all_indicators
        )
    )


    indicator_count = len(
        unique_indicators
    )


    # ========================================================
    # AGENT EVIDENCE
    # ========================================================
    #
    # An agent counts as evidence only if it has:
    #
    # 1. A reasonably high score
    # OR
    # 2. Explicit risk indicators
    #
    # Weak scores such as 0.3 / 0.4 should not
    # independently create fraud evidence.
    # ========================================================

    agent1_evidence = (

        behavior_score >= MEDIUM_SCORE
        or
        len(indicators_1) >= 2

    )


    agent2_evidence = (

        transaction_score >= MEDIUM_SCORE
        or
        len(indicators_2) >= 2

    )


    agent3_evidence = (

        anomaly_score >= MEDIUM_SCORE
        or
        velocity_score >= MEDIUM_SCORE
        or
        len(indicators_3) >= 2

    )


    agent_evidence = sum([

        int(agent1_evidence),
        int(agent2_evidence),
        int(agent3_evidence)

    ])


    # ========================================================
    # HIGH-RISK AGENT CONSENSUS
    # ========================================================

    high_agent_consensus = 0


    if behavior_score >= HIGH_SCORE:

        high_agent_consensus += 1


    if transaction_score >= HIGH_SCORE:

        high_agent_consensus += 1


    # Agent 3 is ONE agent.
    # Anomaly and velocity must NOT count as two agents.

    agent3_high = (

        anomaly_score >= HIGH_SCORE
        or
        velocity_score >= HIGH_SCORE

    )


    if agent3_high:

        high_agent_consensus += 1


    # ========================================================
    # BASE WEIGHTED SCORE
    # ========================================================
    #
    # Agent 1 = 30%
    # Agent 2 = 30%
    # Agent 3 anomaly = 25%
    # Agent 3 velocity = 15%
    #
    # Velocity remains part of Agent 3.
    # ========================================================

    base_score = (

        0.30 * behavior_score
        +
        0.30 * transaction_score
        +
        0.25 * anomaly_score
        +
        0.15 * velocity_score

    )


    # ========================================================
    # CONSENSUS BONUS
    # ========================================================

    consensus_bonus = 0.0


    if high_agent_consensus >= 3:

        consensus_bonus = (
            CONSENSUS_BONUS_3
        )

    elif high_agent_consensus == 2:

        consensus_bonus = (
            CONSENSUS_BONUS_2
        )


    weighted_score = (

        base_score
        +
        consensus_bonus

    )


    # ========================================================
    # INDICATOR BONUS
    # ========================================================
    #
    # Indicators are supporting evidence only.
    # They should never create fraud by themselves.
    # ========================================================

    if indicator_count >= 5:

        weighted_score += 1.5

    elif indicator_count >= 3:

        weighted_score += 0.75


    weighted_score = clamp(
        weighted_score
    )


    # ========================================================
    # FRAUD DECISION
    # ========================================================
    #
    # FRAUD requires BOTH:
    #
    # - high combined score
    # - at least two independent agents agreeing
    #
    # This prevents one noisy agent from producing FRAUD.
    # ========================================================

    # FRAUD: score >= 70 (aligned with check_agent4.py validator contract)
    if weighted_score >= FRAUD_SCORE_THRESHOLD:

        decision = "FRAUD"


    # ========================================================
    # SUSPICIOUS DECISION
    # ========================================================
    # SUSPICIOUS: score >= 40 (aligned with check_agent4.py validator contract)

    elif weighted_score >= SUSPICIOUS_SCORE_THRESHOLD:

        decision = "SUSPICIOUS"


    # ========================================================
    # LEGIT DECISION
    # ========================================================

    else:

        decision = "LEGIT"


    # ========================================================
    # CONFIDENCE
    # ========================================================

    score_strength = abs(
        weighted_score - 50
    )


    if decision == "FRAUD":

        confidence = (

            70
            +
            score_strength * 0.35
            +
            high_agent_consensus * 4
            +
            agent_evidence * 2

        )


    elif decision == "SUSPICIOUS":

        confidence = (

            55
            +
            score_strength * 0.30
            +
            high_agent_consensus * 3
            +
            agent_evidence * 2

        )


    else:

        confidence = (

            55
            +
            (50 - min(
                weighted_score,
                50
            )) * 0.5

        )


    confidence = round(

        clamp(
            confidence,
            50,
            99
        ),

        2

    )


    # ========================================================
    # REASONING
    # ========================================================

    reasoning_parts = []


    reasoning_parts.append(
        f"Behavior score={behavior_score:.2f}"
    )


    reasoning_parts.append(
        f"Transaction score={transaction_score:.2f}"
    )


    reasoning_parts.append(
        f"Anomaly score={anomaly_score:.2f}"
    )


    reasoning_parts.append(
        f"Velocity score={velocity_score:.2f}"
    )


    reasoning_parts.append(
        f"Combined risk score={weighted_score:.2f}"
    )


    reasoning_parts.append(
        f"High-risk agent consensus="
        f"{high_agent_consensus}/3"
    )


    reasoning_parts.append(
        f"Independent agent evidence="
        f"{agent_evidence}/3"
    )


    reasoning_parts.append(
        f"Risk indicators={indicator_count}"
    )


    if decision == "FRAUD":

        reasoning_parts.append(
            "Multiple independent agents show "
            "strong fraud-related evidence."
        )


    elif decision == "SUSPICIOUS":

        reasoning_parts.append(
            "Elevated risk detected, but "
            "fraud-level multi-agent agreement "
            "was not sufficient."
        )


    else:

        reasoning_parts.append(
            "Available risk evidence is not "
            "strong enough for suspicious or "
            "fraud classification."
        )


    reasoning = "; ".join(
        reasoning_parts
    )


    # ========================================================
    # RESULT
    # ========================================================

    result = {

        "transaction_id":
            transaction_id,

        "user_id":
            r1.get("user_id", r2.get("user_id", r3.get("user_id", ""))),

        "decision":
            decision,

        "fraud_score":
            round(
                weighted_score,
                2
            ),

        "confidence":
            confidence,

        "behavior_score":
            round(
                behavior_score,
                2
            ),

        "transaction_score":
            round(
                transaction_score,
                2
            ),

        "anomaly_score":
            round(
                anomaly_score,
                2
            ),

        "velocity_score":
            round(
                velocity_score,
                2
            ),

        "agent_scores": {
            "behavior_score": round(min(1.0, max(0.0, behavior_score / 100.0)), 4),
            "risk_score": round(min(1.0, max(0.0, transaction_score / 100.0)), 4),
            "anomaly_score": round(min(1.0, max(0.0, anomaly_score / 100.0)), 4),
            "velocity_score": round(min(1.0, max(0.0, velocity_score / 100.0)), 4),
        },

        "high_score_agent_count":
            high_agent_consensus,

        "agent_evidence_count":
            agent_evidence,

        "risk_indicator_count":
            indicator_count,

        "risk_indicators":
            unique_indicators,

        "agent_findings": {
            "agent1_high": behavior_score >= HIGH_SCORE,
            "agent2_high": transaction_score >= HIGH_SCORE,
            "agent3_high": agent3_high,
            "consensus": high_agent_consensus,
            "evidence_count": agent_evidence,
        },

        "reasoning":
            reasoning,

        "agent1_reasoning":
            safe_text(
                r1.get(
                    "reasoning"
                )
            ),

        "agent2_reasoning":
            safe_text(
                r2.get(
                    "reasoning"
                )
            ),

        "agent3_reasoning":
            safe_text(
                r3.get(
                    "reasoning"
                )
            ),

        "agent":
            "decision_synthesizer"

    }


    results.append(
        result
    )

    decision_counter[
        decision
    ] += 1


# ============================================================
# SAVE
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        indent=4,
        ensure_ascii=False
    )


# ============================================================
# SUMMARY
# ============================================================

print("\n")

print("=" * 70)

print(
    "             AGENT 4 COMPLETE"
)

print("=" * 70)


print(
    f"Successfully processed: "
    f"{len(results)}"
)


print(
    f"LEGIT:       "
    f"{decision_counter.get('LEGIT', 0)}"
)


print(
    f"SUSPICIOUS:  "
    f"{decision_counter.get('SUSPICIOUS', 0)}"
)


print(
    f"FRAUD:       "
    f"{decision_counter.get('FRAUD', 0)}"
)


print(
    f"\nSaved: {OUTPUT_FILE}"
)


print("=" * 70)


if len(results) == len(common_ids):

    print(
        "SUCCESS: All common transactions "
        "were processed."
    )

else:

    print(
        "WARNING: Some transactions "
        "were not processed."
    )