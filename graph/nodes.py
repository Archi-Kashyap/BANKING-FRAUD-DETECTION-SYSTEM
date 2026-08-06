import numpy as np

# ==================================================================
# Shared helpers
# ==================================================================


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def clamp(value, low=0.0, high=100.0):
    try:
        value = float(value)
    except (ValueError, TypeError):
        value = 0.0
    return max(low, min(high, value))


def normalize_score(value):
    """0-1 scores become 0-100."""
    try:
        value = float(value)
    except (ValueError, TypeError):
        return 0.0
    if 0 <= value <= 1:
        value *= 100.0
    return clamp(value)


def get_indicators(data):
    indicators = data.get("risk_indicators", []) or []
    if isinstance(indicators, list):
        return [str(x).strip() for x in indicators if str(x).strip()]
    text = str(indicators).strip()
    return [text] if text else []


# ==================================================================
# AGENT 1 - BEHAVIOR ANALYZER
# ==================================================================


def _amount_deviation(current_amount, historical_amount):
    if historical_amount <= 0:
        return 0.0
    ratio = current_amount / historical_amount
    if ratio >= 3:
        return 1.0
    if ratio >= 2:
        return 0.8
    if ratio >= 1.5:
        return 0.5
    if ratio >= 1.2:
        return 0.3
    return 0.0


def _hour_deviation(current_hour, history):
    if history.empty:
        return 0.3

    hours = history["transaction_hour"].dropna().tolist()
    if not hours:
        return 0.3

    gaps = []
    for hour in hours:
        gap = abs(int(current_hour) - int(hour))
        gaps.append(min(gap, 24 - gap))

    smallest = min(gaps)
    if smallest <= 1:
        return 0.0
    if smallest <= 3:
        return 0.3
    if smallest <= 6:
        return 0.6
    return 1.0


def behavior_node(state, ctx):
    tx = state["transaction"]
    history = ctx.user_history(tx["user_id"], state.get("row_index"))

    if history.empty:
        behavior_score = 0.30
        indicators = ["No historical transactions available"]
        reasoning = (
            "This is the user's first available transaction in the dataset, "
            "so there is not enough historical behavior to establish a "
            "reliable behavioral baseline."
        )
    else:
        amount_score = _amount_deviation(
            safe_float(tx["transaction_amount"]),
            safe_float(history["transaction_amount"].mean()),
        )

        seen = lambda col: set(history[col].dropna().astype(str))

        location_score = 0.0 if str(tx["device_location"]) in seen("device_location") else 1.0
        type_score = 0.0 if str(tx["transaction_type"]) in seen("transaction_type") else 0.8
        payment_score = 0.0 if str(tx["payment_mode"]) in seen("payment_mode") else 0.7
        device_score = 0.0 if str(tx["device_type"]) in seen("device_type") else 0.5
        hour_score = _hour_deviation(int(safe_float(tx["transaction_hour"])), history)

        behavior_score = (
            amount_score * 0.30
            + location_score * 0.20
            + type_score * 0.15
            + payment_score * 0.10
            + device_score * 0.10
            + hour_score * 0.15
        )
        behavior_score = round(max(0.0, min(1.0, behavior_score)), 2)

        checks = [
            (amount_score >= 0.5,
             "High transaction amount deviation",
             "The transaction amount differs significantly from the user's "
             "historical transaction behavior."),
            (location_score > 0,
             "Different transaction location",
             "The transaction is occurring in a location not previously "
             "observed for this user."),
            (type_score > 0,
             "Different transaction type",
             "The transaction type differs from the user's previous "
             "transaction types."),
            (payment_score > 0,
             "Different payment mode",
             "The payment mode differs from the user's previous payment modes."),
            (device_score > 0,
             "Different device",
             "The device type differs from the user's previous device usage."),
            (hour_score >= 0.6,
             "Unusual transaction hour",
             "The transaction occurs at an unusual time compared with the "
             "user's history."),
        ]

        indicators = [name for hit, name, _ in checks if hit]
        reasons = [text for hit, _, text in checks if hit]

        if not indicators:
            indicators = ["No major behavioral deviation detected"]
            reasons = ["The transaction is generally consistent with the "
                       "user's historical behavior."]

        reasoning = " ".join(reasons)

    return {
        "behavior": {
            "behavior_score": behavior_score,
            "risk_indicators": indicators,
            "reasoning": reasoning,
            "transaction_id": str(tx["transaction_id"]),
            "user_id": str(tx["user_id"]),
            "agent": "behavior_analyzer",
            "historical_transaction_count": int(len(history)),
        }
    }


# ==================================================================
# AGENT 2 - RISK ASSESSOR
# ==================================================================


def risk_node(state, ctx):
    tx = state["transaction"]
    ml_prob = ctx.ml_probability(state.get("row_index"), tx)

    ip_risk = float(np.clip(tx["ip_risk_score"], 0.0, 1.0))

    failed_attempts = float(tx["previous_failed_attempts"])
    failed_risk = float(np.clip(failed_attempts / 4.0, 0.0, 1.0))

    login_attempts = float(tx["login_attempts_last_24h"])
    login_risk = float(np.clip(login_attempts / 9.0, 0.0, 1.0))

    amount = float(tx["transaction_amount"])
    avg_amount = float(tx["avg_transaction_amount"])
    amount_ratio = amount / max(avg_amount, 1.0)
    amount_risk = float(
        np.clip(abs(np.log(max(amount_ratio, 0.001))) / np.log(5.0), 0.0, 1.0)
    )

    is_intl = int(tx["is_international"])
    intl_risk = float(np.clip(is_intl, 0.0, 1.0))

    domain_risk = float(np.clip(
        0.30 * ip_risk
        + 0.25 * failed_risk
        + 0.20 * login_risk
        + 0.15 * amount_risk
        + 0.10 * intl_risk,
        0.0, 1.0,
    ))

    risk_score = round(float(np.clip(0.80 * domain_risk + 0.20 * ml_prob, 0.0, 1.0)), 4)

    if risk_score >= 0.55:
        risk_level = "HIGH"
    elif risk_score >= 0.35:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    indicators = []
    if ip_risk >= 0.70:
        indicators.append("high_ip_risk")
    if failed_attempts >= 3:
        indicators.append("repeated_failed_attempts")
    if login_attempts >= 5:
        indicators.append("high_login_attempts")
    if amount_ratio >= 2.0 or amount_ratio <= 0.20:
        indicators.append("unusual_transaction_amount")
    if is_intl == 1:
        indicators.append("international_transaction")
    if ml_prob >= 0.20:
        indicators.append("elevated_ml_probability")

    if risk_level == "HIGH":
        reasoning = ("Elevated behavioral risk driven by IP risk, "
                     "authentication activity, or transaction anomaly.")
    elif risk_level == "MEDIUM":
        reasoning = ("Moderate risk signals detected across authentication "
                     "or transaction parameters.")
    else:
        reasoning = ("Low behavioral risk based on IP risk, authentication "
                     "activity, and transaction amount.")

    if ctx.weak_signal:
        reasoning += (" ML probability was used as a supporting signal; "
                      "dataset-level validation indicates weak predictive ML signal.")

    risk = {
        "transaction_id": str(tx["transaction_id"]),
        "user_id": str(tx["user_id"]),
        "agent": "risk_assessor",
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_indicators": indicators,
        "details": {
            "ml_probability": round(ml_prob, 4),
            "domain_risk": round(domain_risk, 4),
            "ip_risk": round(ip_risk, 4),
            "international_risk": intl_risk,
            "failed_attempts": int(failed_attempts),
            "login_attempts": int(login_attempts),
            "transaction_amount": round(amount, 2),
            "average_transaction_amount": round(avg_amount, 2),
            "amount_to_average_ratio": round(amount_ratio, 4),
            "account_age_days": int(tx["account_age_days"]),
            "transaction_hour": int(tx["transaction_hour"]),
            "transaction_type": str(tx["transaction_type"]),
            "payment_mode": str(tx["payment_mode"]),
            "device_type": str(tx["device_type"]),
            "device_location": str(tx["device_location"]),
        },
        "model": ctx.model_name,
        "ml_decision_threshold": ctx.ml_threshold,
        "reasoning": reasoning,
    }

    explanation = ctx.explain(
        "Explain this banking risk assessment briefly.\n"
        f"Risk Score: {risk_score:.4f}, Level: {risk_level}\n"
        f"IP Risk: {ip_risk:.2f}, Failed Attempts: {int(failed_attempts)}, "
        f"Logins 24h: {int(login_attempts)}\n"
        f"Amount Ratio: {amount_ratio:.2f}, International: {is_intl}, "
        f"ML Prob: {ml_prob:.4f}\n"
        "Provide a 2-sentence objective summary."
    )
    risk["llm_reasoning"] = explanation or reasoning

    return {"risk": risk}


# ==================================================================
# AGENT 3 - TRANSACTION VALIDATOR
# ==================================================================


def validator_node(state, ctx):
    tx = state["transaction"]

    amount = float(tx["transaction_amount"])
    avg_amount = float(tx.get("avg_transaction_amount", 0))
    amount_ratio = amount / avg_amount if avg_amount > 0 else 1.0
    amount_difference = amount - avg_amount

    if amount_ratio >= 5:
        amount_anomaly = 1.0
    elif amount_ratio >= 3:
        amount_anomaly = 0.8
    elif amount_ratio >= 2:
        amount_anomaly = 0.5
    elif amount_ratio >= 1.5:
        amount_anomaly = 0.3
    else:
        amount_anomaly = 0.0

    failed = float(tx.get("previous_failed_attempts", 0))
    if failed >= 5:
        failed_risk = 1.0
    elif failed >= 3:
        failed_risk = 0.7
    elif failed >= 1:
        failed_risk = 0.3
    else:
        failed_risk = 0.0

    login = float(tx.get("login_attempts_last_24h", 0))
    if login >= 8:
        login_risk = 1.0
    elif login >= 5:
        login_risk = 0.7
    elif login >= 2:
        login_risk = 0.3
    else:
        login_risk = 0.0

    international = int(tx.get("is_international", 0))
    intl_risk = 1.0 if international else 0.0

    anomaly_score = round(min(1.0, 0.70 * amount_anomaly + 0.30 * intl_risk), 3)
    velocity_score = round(min(1.0, 0.55 * failed_risk + 0.45 * login_risk), 3)

    indicators = []
    if amount_anomaly > 0:
        indicators.append({
            "indicator": "Transaction amount anomaly",
            "score": amount_anomaly,
            "description": f"Amount is {amount_ratio:.2f} times the average.",
        })
    if failed_risk > 0:
        indicators.append({
            "indicator": "Failed transaction attempts",
            "score": failed_risk,
            "description": f"{int(failed)} failed attempts.",
        })
    if login_risk > 0:
        indicators.append({
            "indicator": "Login attempts",
            "score": login_risk,
            "description": f"{int(login)} login attempts.",
        })
    if international:
        indicators.append({
            "indicator": "International transaction",
            "score": intl_risk,
            "description": "Transaction is international.",
        })

    validation = {
        "transaction_id": str(tx["transaction_id"]),
        "user_id": str(tx["user_id"]),
        "agent": "transaction_validator",
        "anomaly_score": anomaly_score,
        "velocity_score": velocity_score,
        "amount_ratio": round(amount_ratio, 3),
        "amount_difference": round(amount_difference, 2),
        "risk_indicators": indicators,
        "reasoning": ("Transaction anomaly and velocity scores calculated "
                      "using deterministic rules."),
    }

    explanation = ctx.explain(
        "You are the Transaction Validator in a fraud detection system.\n"
        "Explain these findings briefly.\n"
        f"Amount ratio: {amount_ratio:.2f}\n"
        f"Amount anomaly: {amount_anomaly}\n"
        f"Failed attempt risk: {failed_risk}\n"
        f"Login risk: {login_risk}\n"
        f"International: {international}\n"
        f"Anomaly score: {anomaly_score}\n"
        f"Velocity score: {velocity_score}\n"
        "Do not change the scores. Do not make a final fraud decision.\n"
        "Return a short explanation."
    )
    if explanation:
        validation["llm_reasoning"] = explanation

    return {"validation": validation}


# ==================================================================
# AGENT 4 - DECISION SYNTHESIZER
# ==================================================================

HIGH_SCORE = 70.0
MEDIUM_SCORE = 50.0
FRAUD_THRESHOLD = 70.0
SUSPICIOUS_THRESHOLD = 40.0
CONSENSUS_BONUS_2 = 2.0
CONSENSUS_BONUS_3 = 4.0


def synthesizer_node(state, ctx=None):
    r1 = state["behavior"]
    r2 = state["risk"]
    r3 = state["validation"]

    behavior_score = normalize_score(r1.get("behavior_score", 0.0))
    transaction_score = normalize_score(r2.get("risk_score", 0.0))
    anomaly_score = normalize_score(r3.get("anomaly_score", 0.0))

    velocity_raw = safe_float(r3.get("velocity_score", 0.0))
    velocity_score = normalize_score(velocity_raw) if velocity_raw != 0 else 0.0

    indicators_1 = get_indicators(r1)
    indicators_2 = get_indicators(r2)
    indicators_3 = get_indicators(r3)

    unique_indicators = list(
        dict.fromkeys(indicators_1 + indicators_2 + indicators_3)
    )
    indicator_count = len(unique_indicators)

    # An agent counts as evidence only with a solid score or 2+ indicators
    agent1_evidence = behavior_score >= MEDIUM_SCORE or len(indicators_1) >= 2
    agent2_evidence = transaction_score >= MEDIUM_SCORE or len(indicators_2) >= 2
    agent3_evidence = (
        anomaly_score >= MEDIUM_SCORE
        or velocity_score >= MEDIUM_SCORE
        or len(indicators_3) >= 2
    )
    agent_evidence = sum([int(agent1_evidence), int(agent2_evidence), int(agent3_evidence)])

    # Agent 3 counts as one agent, not two
    agent3_high = anomaly_score >= HIGH_SCORE or velocity_score >= HIGH_SCORE
    consensus = sum([
        int(behavior_score >= HIGH_SCORE),
        int(transaction_score >= HIGH_SCORE),
        int(agent3_high),
    ])

    weighted_score = (
        0.30 * behavior_score
        + 0.30 * transaction_score
        + 0.25 * anomaly_score
        + 0.15 * velocity_score
    )

    if consensus >= 3:
        weighted_score += CONSENSUS_BONUS_3
    elif consensus == 2:
        weighted_score += CONSENSUS_BONUS_2

    if indicator_count >= 5:
        weighted_score += 1.5
    elif indicator_count >= 3:
        weighted_score += 0.75

    weighted_score = clamp(weighted_score)

    if weighted_score >= FRAUD_THRESHOLD:
        decision = "FRAUD"
    elif weighted_score >= SUSPICIOUS_THRESHOLD:
        decision = "SUSPICIOUS"
    else:
        decision = "LEGIT"

    strength = abs(weighted_score - 50)
    if decision == "FRAUD":
        confidence = 70 + strength * 0.35 + consensus * 4 + agent_evidence * 2
    elif decision == "SUSPICIOUS":
        confidence = 55 + strength * 0.30 + consensus * 3 + agent_evidence * 2
    else:
        confidence = 55 + (50 - min(weighted_score, 50)) * 0.5
    confidence = round(clamp(confidence, 50, 99), 2)

    reasoning_parts = [
        f"Behavior score={behavior_score:.2f}",
        f"Transaction score={transaction_score:.2f}",
        f"Anomaly score={anomaly_score:.2f}",
        f"Velocity score={velocity_score:.2f}",
        f"Combined risk score={weighted_score:.2f}",
        f"High-risk agent consensus={consensus}/3",
        f"Independent agent evidence={agent_evidence}/3",
        f"Risk indicators={indicator_count}",
    ]

    if decision == "FRAUD":
        reasoning_parts.append("Multiple independent agents show strong "
                               "fraud-related evidence.")
    elif decision == "SUSPICIOUS":
        reasoning_parts.append("Elevated risk detected, but fraud-level "
                               "multi-agent agreement was not sufficient.")
    else:
        reasoning_parts.append("Available risk evidence is not strong enough "
                               "for suspicious or fraud classification.")

    result = {
        "transaction_id": str(state["transaction"]["transaction_id"]),
        "user_id": r1.get("user_id", r2.get("user_id", r3.get("user_id", ""))),
        "decision": decision,
        "fraud_score": round(weighted_score, 2),
        "confidence": confidence,
        "behavior_score": round(behavior_score, 2),
        "transaction_score": round(transaction_score, 2),
        "anomaly_score": round(anomaly_score, 2),
        "velocity_score": round(velocity_score, 2),
        "agent_scores": {
            "behavior_score": round(min(1.0, max(0.0, behavior_score / 100.0)), 4),
            "risk_score": round(min(1.0, max(0.0, transaction_score / 100.0)), 4),
            "anomaly_score": round(min(1.0, max(0.0, anomaly_score / 100.0)), 4),
            "velocity_score": round(min(1.0, max(0.0, velocity_score / 100.0)), 4),
        },
        "high_score_agent_count": consensus,
        "agent_evidence_count": agent_evidence,
        "risk_indicator_count": indicator_count,
        "risk_indicators": unique_indicators,
        "agent_findings": {
            "agent1_high": behavior_score >= HIGH_SCORE,
            "agent2_high": transaction_score >= HIGH_SCORE,
            "agent3_high": agent3_high,
            "consensus": consensus,
            "evidence_count": agent_evidence,
        },
        "reasoning": "; ".join(reasoning_parts),
        "agent1_reasoning": str(r1.get("reasoning") or ""),
        "agent2_reasoning": str(r2.get("reasoning") or ""),
        "agent3_reasoning": str(r3.get("reasoning") or ""),
        "agent": "decision_synthesizer",
    }

    return {"result": result}
