"""Checks each agent against values worked out by hand from the design rules."""

from graph.context import get_context
from graph.nodes import behavior_node, risk_node, synthesizer_node, validator_node

ctx = get_context(verbose=False)

pass_count, fail_count = 0, 0


def check(name, got, expected):
    global pass_count, fail_count
    ok = abs(got - expected) < 0.005 if isinstance(expected, float) else got == expected
    if ok:
        pass_count += 1
        print(f"  PASS  {name:<45} {got}")
    else:
        fail_count += 1
        print(f"  FAIL  {name:<45} got {got}, expected {expected}")


def make(**overrides):
    tx = {
        "transaction_id": "TEST",
        "user_id": "UTEST",
        "transaction_amount": 1000.0,
        "avg_transaction_amount": 1000.0,
        "transaction_type": "Payment",
        "payment_mode": "UPI",
        "device_type": "Android",
        "device_location": "Delhi",
        "account_age_days": 500,
        "transaction_hour": 12,
        "previous_failed_attempts": 0,
        "login_attempts_last_24h": 0,
        "is_international": 0,
        "ip_risk_score": 0.0,
    }
    tx.update(overrides)
    return tx


def run(tx, row_index=None):
    state = {"transaction": tx, "row_index": row_index}
    state.update(behavior_node(state, ctx))
    state.update(risk_node(state, ctx))
    state.update(validator_node(state, ctx))
    state.update(synthesizer_node(state, ctx))
    return state


# ==================================================================
print("\nAGENT 3 - amount anomaly thresholds")
print("  rule: 5x=1.0, 3x=0.8, 2x=0.5, 1.5x=0.3, below=0.0")
print("  anomaly = 0.70 * amount + 0.30 * international\n")

for ratio, expected in [(5.0, 0.70), (3.0, 0.56), (2.0, 0.35), (1.5, 0.21), (1.0, 0.0)]:
    tx = make(transaction_amount=1000.0 * ratio)
    check(f"ratio {ratio}x", run(tx)["validation"]["anomaly_score"], expected)

tx = make(transaction_amount=5000.0, is_international=1)
check("5x + international", run(tx)["validation"]["anomaly_score"], 1.0)

# ==================================================================
print("\nAGENT 3 - velocity")
print("  failed: 5+=1.0, 3+=0.7, 1+=0.3    logins: 8+=1.0, 5+=0.7, 2+=0.3")
print("  velocity = 0.55 * failed + 0.45 * logins\n")

for failed, logins, expected in [
    (0, 0, 0.0),
    (1, 0, 0.165),
    (3, 0, 0.385),
    (5, 0, 0.55),
    (0, 8, 0.45),
    (4, 9, 0.835),
    (5, 8, 1.0),
]:
    tx = make(previous_failed_attempts=failed, login_attempts_last_24h=logins)
    check(f"failed={failed}, logins={logins}", run(tx)["validation"]["velocity_score"], expected)

# ==================================================================
print("\nAGENT 2 - domain risk")
print("  0.30*ip + 0.25*(failed/4) + 0.20*(logins/9) + 0.15*amount + 0.10*intl\n")

tx = make(ip_risk_score=0.9, previous_failed_attempts=4, login_attempts_last_24h=9,
          transaction_amount=90000.0, avg_transaction_amount=4000.0, is_international=1)
check("all signals high", run(tx)["risk"]["details"]["domain_risk"], 0.97)

tx = make(ip_risk_score=1.0)
check("ip risk only", run(tx)["risk"]["details"]["domain_risk"], 0.30)

check("clean transaction", run(make())["risk"]["details"]["domain_risk"], 0.0)

# ==================================================================
print("\nAGENT 1 - behaviour vs history")
print("  0.30*amount + 0.20*location + 0.15*type + 0.10*payment")
print("  + 0.10*device + 0.15*hour\n")

index, tx = ctx.get_transaction("T145")
result = run(tx, index)
check("T145 first transaction of user", result["behavior"]["behavior_score"], 0.30)
check("T145 history rows", result["behavior"]["historical_transaction_count"], 0)

# T804: amount 2.13x (0.8), new location (1.0), new type (0.8),
# new payment (0.7), same device (0), hour gap 1 (0)
index, tx = ctx.get_transaction("T804")
result = run(tx, index)
check("T804 behaviour score", result["behavior"]["behavior_score"], 0.63)
check("T804 history rows", result["behavior"]["historical_transaction_count"], 1)
check("T804 indicators found", len(result["behavior"]["risk_indicators"]), 4)

# ==================================================================
print("\nAGENT 4 - combining the three agents")
print("  0.30*behaviour + 0.30*risk + 0.25*anomaly + 0.15*velocity")
print("  + consensus bonus + indicator bonus\n")

index, tx = ctx.get_transaction("T7")
result = run(tx, index)["result"]
check("T7 fraud score", result["fraud_score"], 40.79)
check("T7 decision", result["decision"], "SUSPICIOUS")
check("T7 consensus", result["high_score_agent_count"], 1)

tx = make(transaction_amount=90000.0, avg_transaction_amount=4000.0, ip_risk_score=0.95,
          previous_failed_attempts=5, login_attempts_last_24h=9, is_international=1,
          transaction_hour=2, account_age_days=30)
result = run(tx)["result"]
check("high risk decision", result["decision"], "FRAUD")

check("clean transaction decision", run(make())["result"]["decision"], "LEGIT")

# ==================================================================
print("\n" + "=" * 60)
print(f"PASSED: {pass_count}   FAILED: {fail_count}")
print("=" * 60)
