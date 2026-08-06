import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

COLORS = {"FRAUD": "#d62728", "SUSPICIOUS": "#ff9800", "LEGIT": "#2ca02c"}

TRANSACTION_TYPES = ["Payment", "Transfer", "Withdrawal"]
PAYMENT_MODES = ["Card", "NetBanking", "UPI", "Wallet"]
DEVICE_TYPES = ["Android", "Web", "iOS"]
LOCATIONS = ["Bangalore", "Chennai", "Delhi", "Hyderabad", "Mumbai"]

st.set_page_config(page_title="Fraud Detection", layout="wide")
st.title("Multi-Agent Fraud Detection")


def call_api(method, path, payload=None):
    try:
        if method == "GET":
            response = requests.get(f"{API_URL}{path}", timeout=60)
        else:
            response = requests.post(f"{API_URL}{path}", json=payload, timeout=60)
        if response.status_code != 200:
            st.error(f"API error {response.status_code}: {response.text[:200]}")
            return None
        return response.json()
    except requests.exceptions.RequestException:
        st.error("Cannot reach the API. Is uvicorn running?")
        return None


def show_decision(result):
    color = COLORS.get(result["decision"], "#666")

    st.markdown(
        f"<h2 style='color:{color}'>{result['decision']}</h2>",
        unsafe_allow_html=True,
    )

    a, b, c = st.columns(3)
    a.metric("Fraud Score", f"{result['fraud_score']:.2f} / 100")
    b.metric("Confidence", f"{result['confidence']:.2f}%")
    c.metric("Agent Consensus", f"{result['high_score_agent_count']}/3")

    st.progress(min(result["fraud_score"] / 100, 1.0))

    st.subheader("Agent Scores")
    w, x, y, z = st.columns(4)
    w.metric("Behavior", f"{result['behavior_score']:.1f}")
    x.metric("Risk", f"{result['transaction_score']:.1f}")
    y.metric("Anomaly", f"{result['anomaly_score']:.1f}")
    z.metric("Velocity", f"{result['velocity_score']:.1f}")

    st.subheader("Final Reasoning")
    st.info(result["reasoning"])


def show_agents(data):
    a1 = data["agent1_behavior"]
    a2 = data["agent2_risk"]
    a3 = data["agent3_validation"]

    with st.expander("Agent 1 - Behavior Analyzer"):
        st.write(f"Score: {a1['behavior_score']}")
        st.write(f"History used: {a1['historical_transaction_count']} transactions")
        for item in a1["risk_indicators"]:
            st.write(f"- {item}")
        st.caption(a1["reasoning"])

    with st.expander("Agent 2 - Risk Assessor"):
        st.write(f"Score: {a2['risk_score']} ({a2['risk_level']})")
        for item in a2["risk_indicators"]:
            st.write(f"- {item.replace('_', ' ')}")
        st.caption(a2.get("llm_reasoning", a2["reasoning"]))
        st.json(a2["details"], expanded=False)

    with st.expander("Agent 3 - Transaction Validator"):
        st.write(f"Anomaly: {a3['anomaly_score']} | Velocity: {a3['velocity_score']}")
        for item in a3["risk_indicators"]:
            st.write(f"- **{item['indicator']}** ({item['score']}): {item['description']}")
        st.caption(a3["reasoning"])


# ==================================================================
# SIDEBAR
# ==================================================================

with st.sidebar:
    st.header("Input")
    mode = st.radio("Mode", ["Dataset transaction", "Manual entry"])

    health = call_api("GET", "/health")
    if health:
        st.success(f"API online - {health['transactions_loaded']} rows loaded")
        st.caption(f"Model: {health['model']}")


# ==================================================================
# DATASET MODE
# ==================================================================

if mode == "Dataset transaction":
    transaction_id = st.text_input("Transaction ID", "T7")

    if st.button("Analyze", type="primary"):
        with st.spinner("Running agents..."):
            data = call_api("GET", f"/predict/{transaction_id}")
        if data:
            show_decision(data["result"])
            show_agents(data)


# ==================================================================
# MANUAL MODE
# ==================================================================

else:
    left, right = st.columns(2)

    with left:
        user_id = st.text_input("User ID", "U9999")
        amount = st.number_input("Transaction amount", value=90000.0, step=100.0)
        avg_amount = st.number_input("Average amount", value=4000.0, step=100.0)
        transaction_type = st.selectbox("Transaction type", TRANSACTION_TYPES)
        payment_mode = st.selectbox("Payment mode", PAYMENT_MODES)
        device_type = st.selectbox("Device type", DEVICE_TYPES)
        location = st.selectbox("Device location", LOCATIONS)

    with right:
        account_age = st.number_input("Account age (days)", 1, 3000, 30)
        hour = st.slider("Transaction hour", 0, 23, 2)
        failed = st.slider("Previous failed attempts", 0, 10, 5)
        logins = st.slider("Logins last 24h", 0, 15, 9)
        ip_risk = st.slider("IP risk score", 0.0, 1.0, 0.95)
        international = st.checkbox("International transaction", value=True)

    if st.button("Analyze", type="primary"):
        payload = {
            "user_id": user_id,
            "transaction_amount": amount,
            "transaction_type": transaction_type,
            "payment_mode": payment_mode,
            "device_type": device_type,
            "device_location": location,
            "account_age_days": account_age,
            "transaction_hour": hour,
            "previous_failed_attempts": failed,
            "avg_transaction_amount": avg_amount,
            "is_international": int(international),
            "ip_risk_score": ip_risk,
            "login_attempts_last_24h": logins,
            "transaction_id": "MANUAL",
        }
        with st.spinner("Running agents..."):
            data = call_api("POST", "/predict", payload)
        if data:
            show_decision(data["result"])
            show_agents(data)
