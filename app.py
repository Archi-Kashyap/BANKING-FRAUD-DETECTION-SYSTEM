import ast
import html
import json
import os
import sys
import math
import random
import time
from datetime import datetime
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as _st_components
import importlib
import components.agent_network_svg
importlib.reload(components.agent_network_svg)
from components.agent_network_svg import render_agent_network as _render_agent_network
import components.blurhash_placeholder
importlib.reload(components.blurhash_placeholder)
from components.blurhash_placeholder import (
    render_blurhash_dashboard_placeholder as _render_blurhash_placeholder,
    PRESET_BLURHASHES,
    decode_blurhash_to_data_url,
)
import components.starting_scene
importlib.reload(components.starting_scene)
from components.starting_scene import (
    get_starting_scene_css,
    render_starting_scene_hero,
)
import components.threat_inspector
importlib.reload(components.threat_inspector)
from components.threat_inspector import get_threat_inspector_html
import threading




# ==================================================================
# CONFIGURATION & CONSTANTS
# ==================================================================

API_URL = os.getenv("API_URL", "http://127.0.0.1:8001").rstrip("/")
DATASET_PATH = "Data/Digital_Payment_Fraud_Detection_Dataset.csv"

if not hasattr(sys, "_fraudguard_api_online"):
    sys._fraudguard_api_online = None

if "_API_ONLINE_STATUS" not in globals():
    _API_ONLINE_STATUS = getattr(sys, "_fraudguard_api_online", None)

TRANSACTION_TYPES = ["Payment", "Transfer", "Withdrawal"]
PAYMENT_MODES = ["Card", "Net banking", "UPI", "Wallet"]
DEVICE_TYPES = ["Android", "Web", "iOS"]
LOCATIONS = ["Bangalore", "Chennai", "Delhi", "Hyderabad", "Mumbai"]

st.set_page_config(
    page_title="FraudGuard Threat Analysis Console",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================================================================
# CACHED DATA & LOCAL MODEL FALLBACK
# ==================================================================

@st.cache_data
def get_dataset():
    if os.path.exists(DATASET_PATH):
        return pd.read_csv(DATASET_PATH)
    return pd.DataFrame()

@st.cache_resource(show_spinner=False)
def get_local_engine():
    try:
        from graph.context import get_context
        from graph.workflow import build_workflow
        ctx = get_context(verbose=False)
        graph = build_workflow(ctx)
        return ctx, graph
    except Exception:
        return None, None

df_dataset = get_dataset()

def _prewarm_local_engine():
    try:
        get_local_engine()
    except Exception:
        pass

try:
    from streamlit.runtime import exists as runtime_exists
    if runtime_exists():
        threading.Thread(target=_prewarm_local_engine, daemon=True).start()
except Exception:
    pass

# ==================================================================
# SESSION STATE INITIALIZATION
# ==================================================================

if "api_online" not in st.session_state:
    st.session_state["api_online"] = None

if "history" not in st.session_state:
    st.session_state["history"] = []

if "current_analysis" not in st.session_state:
    st.session_state["current_analysis"] = None

if "tx_id_input" not in st.session_state:
    st.session_state["tx_id_input"] = "T3768"

if "manual_user_id" not in st.session_state:
    st.session_state["manual_user_id"] = "U9999"

if "manual_amount" not in st.session_state:
    st.session_state["manual_amount"] = 90000

if "manual_avg_amount" not in st.session_state:
    st.session_state["manual_avg_amount"] = 4000

if "manual_type" not in st.session_state:
    st.session_state["manual_type"] = "Payment"

if "manual_mode" not in st.session_state:
    st.session_state["manual_mode"] = "Card"

if "manual_intl" not in st.session_state:
    st.session_state["manual_intl"] = True

if "manual_age" not in st.session_state:
    st.session_state["manual_age"] = 30

if "manual_hour" not in st.session_state:
    st.session_state["manual_hour"] = 2

if "manual_failed" not in st.session_state:
    st.session_state["manual_failed"] = 5

if "manual_logins" not in st.session_state:
    st.session_state["manual_logins"] = 9

if "manual_device" not in st.session_state:
    st.session_state["manual_device"] = "Android"

if "manual_location" not in st.session_state:
    st.session_state["manual_location"] = "Bangalore"

if "manual_ip_risk" not in st.session_state:
    st.session_state["manual_ip_risk"] = 0.95

# ==================================================================
# API & ENGINE CALLERS
# ==================================================================

def check_health(force=False):
    global _API_ONLINE_STATUS
    has_runtime = False
    try:
        from streamlit.runtime import exists as runtime_exists
        has_runtime = runtime_exists()
    except Exception:
        pass

    if has_runtime and not force:
        if "health_data" in st.session_state and st.session_state.get("api_online") is not None:
            return st.session_state["health_data"]
        if getattr(sys, "_fraudguard_api_online", None) is False or _API_ONLINE_STATUS is False:
            fallback = {
                "online": False,
                "status": "local",
                "transactions_loaded": len(df_dataset) if (df_dataset is not None and not df_dataset.empty) else 7500,
                "model": "Random Forest (Local Engine)",
            }
            try:
                st.session_state["api_online"] = False
                st.session_state["health_data"] = fallback
            except Exception:
                pass
            return fallback

    try:
        r = requests.get(f"{API_URL}/health", timeout=1.0)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                data["online"] = True
                if "transactions_loaded" not in data or data["transactions_loaded"] is None:
                    data["transactions_loaded"] = len(df_dataset) if (df_dataset is not None and not df_dataset.empty) else 7500
                elif not isinstance(data["transactions_loaded"], int):
                    try:
                        data["transactions_loaded"] = int(data["transactions_loaded"])
                    except (ValueError, TypeError):
                        data["transactions_loaded"] = len(df_dataset) if (df_dataset is not None and not df_dataset.empty) else 7500
                if "model" not in data or not data["model"]:
                    data["model"] = "Random Forest"
                if has_runtime:
                    _API_ONLINE_STATUS = True
                    sys._fraudguard_api_online = True
                    try:
                        st.session_state["api_online"] = True
                        st.session_state["health_data"] = data
                    except Exception:
                        pass
                return data
    except Exception:
        pass

    if has_runtime:
        _API_ONLINE_STATUS = False
        sys._fraudguard_api_online = False
    fallback_data = {
        "online": False,
        "status": "local",
        "transactions_loaded": len(df_dataset) if (df_dataset is not None and not df_dataset.empty) else 7500,
        "model": "Random Forest (Local Engine)",
    }
    if has_runtime:
        try:
            st.session_state["api_online"] = False
            st.session_state["health_data"] = fallback_data
        except Exception:
            pass
    return fallback_data

def call_api(method, path, payload=None):
    global _API_ONLINE_STATUS
    has_runtime = False
    try:
        from streamlit.runtime import exists as runtime_exists
        has_runtime = runtime_exists()
    except Exception:
        pass

    if has_runtime:
        if getattr(sys, "_fraudguard_api_online", None) is False or _API_ONLINE_STATUS is False or st.session_state.get("api_online") is False:
            return None

    try:
        if method == "GET":
            response = requests.get(f"{API_URL}{path}", timeout=1.0)
        else:
            response = requests.post(f"{API_URL}{path}", json=payload, timeout=1.0)
        if response.status_code == 200:
            if has_runtime:
                _API_ONLINE_STATUS = True
                sys._fraudguard_api_online = True
                try:
                    st.session_state["api_online"] = True
                except Exception:
                    pass
            return response.json()
    except Exception:
        if has_runtime:
            _API_ONLINE_STATUS = False
            sys._fraudguard_api_online = False
            try:
                st.session_state["api_online"] = False
                st.session_state["health_data"] = {
                    "online": False,
                    "status": "local",
                    "transactions_loaded": len(df_dataset) if (df_dataset is not None and not df_dataset.empty) else 7500,
                    "model": "Random Forest (Local Engine)",
                }
            except Exception:
                pass
    return None

def analyze_dataset_tx(tx_id: str):
    clean_id = tx_id.strip()

    # API call
    api_res = None
    is_online = True
    try:
        from streamlit.runtime import exists as runtime_exists
        if runtime_exists():
            if getattr(sys, "_fraudguard_api_online", None) is False or _API_ONLINE_STATUS is False or st.session_state.get("api_online") is False:
                is_online = False
    except Exception:
        if getattr(sys, "_fraudguard_api_online", None) is False or _API_ONLINE_STATUS is False:
            is_online = False

    if is_online:
        api_res = call_api("GET", f"/predict/{clean_id}")

    if not api_res:
        ctx, graph = get_local_engine()
        if graph and ctx:
            from graph.workflow import analyze_by_id
            try:
                api_res = analyze_by_id(graph, ctx, clean_id)
            except Exception:
                return None
        else:
            return None

    res = api_res["result"]
    a1 = api_res.get("agent1_behavior") or api_res.get("behavior", {})
    a2 = api_res.get("agent2_risk") or api_res.get("risk", {})
    a3 = api_res.get("agent3_validation") or api_res.get("validation", {})

    decision = res.get("decision", "LEGIT")
    verdict = "SAFE" if decision == "LEGIT" else decision
    score = float(res.get("fraud_score", 0.0))
    confidence = float(res.get("confidence", 80.0))
    consensus = int(res.get("high_score_agent_count", 0))

    # Lookup row from dataset for metadata title
    row_match = df_dataset[df_dataset["transaction_id"] == clean_id]
    if not row_match.empty:
        r = row_match.iloc[0]
        u_id = str(r["user_id"])
        amt = f"₹{int(r['transaction_amount']):,}"
    else:
        u_id = res.get("user_id", "Unknown")
        amt = "₹-"

    tx_title = f"Transaction {clean_id} for {amt} by {u_id}"

    # Indicators
    graph_indicators = res.get("risk_indicators", [])
    if graph_indicators:
        if isinstance(graph_indicators, list):
            indicators = list(graph_indicators)
        elif isinstance(graph_indicators, str):
            s = graph_indicators.strip()
            if s.startswith("[") and s.endswith("]"):
                try:
                    indicators = json.loads(s)
                except Exception:
                    try:
                        indicators = ast.literal_eval(s)
                    except Exception:
                        indicators = [s]
            else:
                indicators = [s]
        else:
            try:
                indicators = list(graph_indicators)
            except Exception:
                indicators = [str(graph_indicators)]
    else:
        indicators = []
        if not row_match.empty:
            r = row_match.iloc[0]
            cur_amt = float(r["transaction_amount"])
            avg_amt = max(float(r["avg_transaction_amount"]), 1.0)
            ratio = cur_amt / avg_amt
            if ratio >= 2.0:
                indicators.append(f"Amount is {ratio:.1f} times this user's average")
            hour = int(r["transaction_hour"])
            if hour in [0, 1, 2, 3, 4, 5, 23]:
                indicators.append(f"Made at {hour:02d}:00, outside normal hours")
            failed = int(r["previous_failed_attempts"])
            if failed >= 2:
                indicators.append(f"{failed} failed attempts before this one")
            logins = int(r["login_attempts_last_24h"])
            if logins >= 5:
                indicators.append(f"{logins} logins in the last 24 hours")
            ip = float(r["ip_risk_score"])
            if ip >= 0.7:
                indicators.append(f"High-risk IP address ({ip:.2f})")
            if int(r["is_international"]) == 1:
                indicators.append("International transaction")

    return {
        "verdict": verdict,
        "fraud_score": score,
        "confidence": confidence,
        "consensus": consensus,
        "behavior_score": float(res.get("behavior_score", 0.0)),
        "transaction_score": float(res.get("transaction_score", 0.0)),
        "anomaly_score": float(res.get("anomaly_score", 0.0)),
        "velocity_score": float(res.get("velocity_score", 0.0)),
        "tx_title": tx_title,
        "amount_str": amt,
        "tx_id": clean_id,
        "user_id": u_id,
        "indicators": indicators,
        "agent1_summary": f"Behavior score {float(res.get('behavior_score', 0.0)):.1f} and velocity score {float(res.get('velocity_score', 0.0)):.1f}. Looks at failed attempts, login frequency, account age and device familiarity.",
        "agent2_summary": f"Risk score {float(res.get('transaction_score', 0.0)):.1f}. Weighs how far the amount is above the user's average, plus IP reputation and whether the payment is international.",
        "agent3_summary": f"Anomaly score {float(res.get('anomaly_score', 0.0)):.1f}. Flags outliers in amount and timing compared to normal activity for this user.",
        "agent1_reasoning": a1.get("reasoning", ""),
        "agent1_history_count": a1.get("historical_transaction_count", 0),
        "agent2_reasoning": a2.get("reasoning", ""),
        "agent2_ml_prob": a2.get("details", {}).get("ml_probability", 0.0),
        "agent3_reasoning": a3.get("reasoning", ""),
        "agent3_amount_ratio": a3.get("amount_ratio", 1.0),
    }

def analyze_manual_tx(payload: dict):
    # API call
    api_res = None
    is_online = True
    try:
        from streamlit.runtime import exists as runtime_exists
        if runtime_exists():
            if getattr(sys, "_fraudguard_api_online", None) is False or _API_ONLINE_STATUS is False or st.session_state.get("api_online") is False:
                is_online = False
    except Exception:
        if getattr(sys, "_fraudguard_api_online", None) is False or _API_ONLINE_STATUS is False:
            is_online = False

    if is_online:
        api_res = call_api("POST", "/predict", payload)

    if not api_res:
        ctx, graph = get_local_engine()
        if graph and ctx:
            from graph.workflow import analyze_transaction
            try:
                api_res = analyze_transaction(graph, payload)
            except Exception:
                return None
        else:
            return None

    res = api_res["result"]
    a1 = api_res.get("agent1_behavior") or api_res.get("behavior", {})
    a2 = api_res.get("agent2_risk") or api_res.get("risk", {})
    a3 = api_res.get("agent3_validation") or api_res.get("validation", {})

    decision = res.get("decision", "LEGIT")
    verdict = "SAFE" if decision == "LEGIT" else decision
    score = float(res.get("fraud_score", 0.0))
    confidence = float(res.get("confidence", 80.0))
    consensus = int(res.get("high_score_agent_count", 0))

    cur_amt = float(payload.get("transaction_amount", 0.0))
    avg_amt = max(float(payload.get("avg_transaction_amount", 1.0)), 1.0)
    ratio = cur_amt / avg_amt
    amt_str = f"₹{int(cur_amt):,}"
    u_id = payload.get("user_id", "Manual")
    tx_title = f"Transaction (manual) for {amt_str} by {u_id}"

    # Build indicators
    graph_indicators = res.get("risk_indicators", [])
    if graph_indicators:
        if isinstance(graph_indicators, list):
            indicators = list(graph_indicators)
        elif isinstance(graph_indicators, str):
            s = graph_indicators.strip()
            if s.startswith("[") and s.endswith("]"):
                try:
                    indicators = json.loads(s)
                except Exception:
                    try:
                        indicators = ast.literal_eval(s)
                    except Exception:
                        indicators = [s]
            else:
                indicators = [s]
        else:
            try:
                indicators = list(graph_indicators)
            except Exception:
                indicators = [str(graph_indicators)]
    else:
        indicators = []
        if ratio >= 1.5:
            indicators.append(f"Amount is {ratio:.1f} times this user's average")
        hour = int(payload.get("transaction_hour", 12))
        if hour in [0, 1, 2, 3, 4, 5, 23]:
            indicators.append(f"Made at {hour:02d}:00, outside normal hours")
        failed = int(payload.get("previous_failed_attempts", 0))
        if failed >= 1:
            indicators.append(f"{failed} failed attempts before this one")
        logins = int(payload.get("login_attempts_last_24h", 0))
        if logins >= 3:
            indicators.append(f"{logins} logins in the last 24 hours")
        ip = float(payload.get("ip_risk_score", 0.0))
        if ip >= 0.5:
            indicators.append(f"High-risk IP address ({ip:.2f})")
        if int(payload.get("is_international", 0)) == 1:
            indicators.append("International transaction")

    return {
        "verdict": verdict,
        "fraud_score": score,
        "confidence": confidence,
        "consensus": consensus,
        "behavior_score": float(res.get("behavior_score", 0.0)),
        "transaction_score": float(res.get("transaction_score", 0.0)),
        "anomaly_score": float(res.get("anomaly_score", 0.0)),
        "velocity_score": float(res.get("velocity_score", 0.0)),
        "tx_title": tx_title,
        "amount_str": amt_str,
        "tx_id": f"{u_id} (manual)",
        "user_id": u_id,
        "indicators": indicators,
        "agent1_summary": f"Behavior score {float(res.get('behavior_score', 0.0)):.1f} and velocity score {float(res.get('velocity_score', 0.0)):.1f}. Looks at failed attempts, login frequency, account age and device familiarity.",
        "agent2_summary": f"Risk score {float(res.get('transaction_score', 0.0)):.1f}. Weighs how far the amount is above the user's average, plus IP reputation and whether the payment is international.",
        "agent3_summary": f"Anomaly score {float(res.get('anomaly_score', 0.0)):.1f}. Flags outliers in amount and timing compared to normal activity for this user.",
        "agent1_reasoning": a1.get("reasoning", ""),
        "agent1_history_count": a1.get("historical_transaction_count", 0),
        "agent2_reasoning": a2.get("reasoning", ""),
        "agent2_ml_prob": a2.get("details", {}).get("ml_probability", 0.0),
        "agent3_reasoning": a3.get("reasoning", ""),
        "agent3_amount_ratio": a3.get("amount_ratio", ratio),
    }

def format_risk_indicator(item) -> str:
    if not item:
        return ""
    if isinstance(item, dict):
        text = str(item.get("description") or item.get("indicator") or "").strip()
    else:
        text = str(item).strip()

    if not text:
        return ""

    if text.startswith("{") and text.endswith("}"):
        parsed = None
        try:
            parsed = json.loads(text)
        except Exception:
            try:
                parsed = ast.literal_eval(text)
            except Exception:
                pass
        if isinstance(parsed, dict):
            text = str(parsed.get("description") or parsed.get("indicator") or text).strip()

    # Filter non-risk indicators stating absence of deviations
    if text.strip().lower() in [
        "no major behavioral deviation detected",
        "no behavioral deviation detected",
        "no deviation detected",
    ]:
        return ""

    label_map = {
        "high_ip_risk": "High IP risk",
        "repeated_failed_attempts": "Repeated failed attempts",
        "high_login_attempts": "High login attempts",
        "unusual_transaction_amount": "Unusual transaction amount",
        "international_transaction": "International transaction",
        "elevated_ml_probability": "Elevated ML probability",
    }
    normalized_key = text.lower().strip()
    if normalized_key in label_map:
        return label_map[normalized_key]

    if ("_" in text or "-" in text) and text.replace("_", "").replace("-", "").isalnum():
        return text.replace("_", " ").replace("-", " ").strip().capitalize()

    return text

# ==================================================================
# SVG GAUGE GENERATOR
# ==================================================================

def render_gauge_svg(score: float, verdict_color: str = None) -> str:
    score_clamped = max(0.0, min(100.0, float(score)))

    if score_clamped < 35:
        c_glow = "#00e676"
        c_start = "#00e676"
        c_end = "#00e676"
        tier_label = "LOW RISK"
        track_color = "rgba(0, 230, 118, 0.16)"
    elif score_clamped < 70:
        c_glow = "#ffab00"
        c_start = "#ffea00"
        c_end = "#ff9100"
        tier_label = "MODERATE"
        track_color = "rgba(255, 171, 0, 0.16)"
    else:
        c_glow = "#ff1744"
        c_start = "#ff9100"
        c_end = "#ff1744"
        tier_label = "HIGH RISK"
        track_color = "rgba(255, 23, 68, 0.18)"

    cx, cy, r = 120, 96, 70
    start_deg = 215
    end_deg = -35
    total_deg = start_deg - end_deg  # 250 degrees

    def pt(deg, radius):
        rad = math.radians(deg)
        return cx + radius * math.cos(rad), cy - radius * math.sin(rad)

    p_start = pt(start_deg, r)
    p_end = pt(end_deg, r)

    eff_score = max(0.8, score_clamped)
    curr_deg = start_deg - (eff_score / 100.0) * total_deg
    p_curr = pt(curr_deg, r)

    swept = (eff_score / 100.0) * total_deg
    large_arc = 1 if swept > 180 else 0

    ticks = []
    for i in range(25):
        t_deg = start_deg - (i / 24.0) * total_deg
        t_score = (i / 24.0) * 100.0
        p1 = pt(t_deg, r + 12)
        p2 = pt(t_deg, r + 17 if i % 6 == 0 else r + 15)
        if t_score <= score_clamped:
            t_col = c_glow if i % 6 == 0 else "rgba(255,255,255,0.7)"
        else:
            t_col = "rgba(255,255,255,0.12)"
        ticks.append(
            f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" stroke="{t_col}" stroke-width="{1.5 if i % 6 == 0 else 1}" />'
        )
    ticks_html = "".join(ticks)

    gid = f"grad-gauge-{int(score_clamped * 10)}"
    fid = f"gauge-bloom-{int(score_clamped * 10)}"
    bid = f"beacon-glow-{int(score_clamped * 10)}"

    # Single-line SVG string with no indentation so Markdown cannot mangle internal tags
    return (
        f'<svg viewBox="0 0 240 185" class="gauge-svg" xmlns="http://www.w3.org/2000/svg" style="display:block;width:100%;height:auto;">'
        f'<defs>'
        f'<linearGradient id="{gid}" x1="0%" y1="100%" x2="100%" y2="0%">'
        f'<stop offset="0%" stop-color="{c_start}" />'
        f'<stop offset="100%" stop-color="{c_end}" />'
        f'</linearGradient>'
        f'<filter id="{fid}" x="-50%" y="-50%" width="200%" height="200%" filterUnits="userSpaceOnUse">'
        f'<feDropShadow dx="0" dy="0" stdDeviation="4.5" flood-color="{c_glow}" flood-opacity="0.85"/>'
        f'</filter>'
        f'<filter id="{bid}" x="-50%" y="-50%" width="200%" height="200%" filterUnits="userSpaceOnUse">'
        f'<feDropShadow dx="0" dy="0" stdDeviation="3.5" flood-color="{c_glow}" flood-opacity="1"/>'
        f'</filter>'
        f'</defs>'
        f'{ticks_html}'
        f'<path d="M {p_start[0]:.2f} {p_start[1]:.2f} A {r} {r} 0 1 1 {p_end[0]:.2f} {p_end[1]:.2f}" fill="none" stroke="{track_color}" stroke-width="7" stroke-linecap="round" />'
        f'<path d="M {p_start[0]:.2f} {p_start[1]:.2f} A {r} {r} 0 {large_arc} 1 {p_curr[0]:.2f} {p_curr[1]:.2f}" fill="none" stroke="url(#{gid})" stroke-width="7" stroke-linecap="round" filter="url(#{fid})" />'
        f'<circle cx="{p_curr[0]:.2f}" cy="{p_curr[1]:.2f}" r="6" fill="#ffffff" filter="url(#{bid})" />'
        f'<circle cx="{p_curr[0]:.2f}" cy="{p_curr[1]:.2f}" r="3.2" fill="{c_glow}" />'
        f'<text x="{cx}" y="{cy - 8}" text-anchor="middle" font-family="\'JetBrains Mono\', Consolas, monospace" font-size="34" font-weight="800" fill="#ffffff" letter-spacing="-1">{score_clamped:.1f}</text>'
        f'<text x="{cx}" y="{cy + 13}" text-anchor="middle" font-family="\'JetBrains Mono\', Consolas, monospace" font-size="11" font-weight="700" fill="{c_glow}" letter-spacing="1.5">{tier_label}</text>'
        f'<text x="{cx}" y="{cy + 28}" text-anchor="middle" font-family="\'JetBrains Mono\', Consolas, monospace" font-size="9" font-weight="600" fill="#627d98" letter-spacing="1.2">FRAUD SCORE</text>'
        f'<text x="{p_start[0] - 2:.1f}" y="{p_start[1] + 16:.1f}" font-family="\'JetBrains Mono\', monospace" font-size="9.5" font-weight="600" fill="#58728a">0</text>'
        f'<text x="{p_end[0] - 12:.1f}" y="{p_end[1] + 16:.1f}" font-family="\'JetBrains Mono\', monospace" font-size="9.5" font-weight="600" fill="#58728a">100</text>'
        f'</svg>'
    )

# ==================================================================
# CUSTOM CSS INJECTION
# ==================================================================

custom_css = """
<style>
/* Root CSS Variables for Safe Area Insets */
:root {
    --sat: env(safe-area-inset-top, 0px);
    --sar: env(safe-area-inset-right, 0px);
    --sab: env(safe-area-inset-bottom, 0px);
    --sal: env(safe-area-inset-left, 0px);
}

/* Global App Background, Safe Area Insets & Clean Enterprise Dark Theme */
html, body, .stApp, .stAppViewContainer, section.main {
    background-color: #090e17 !important;
    background-image: none !important;
    color: #f1f5f9 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif !important;
    padding-top: env(safe-area-inset-top, 0px) !important;
    padding-bottom: env(safe-area-inset-bottom, 0px) !important;
    padding-left: env(safe-area-inset-left, 0px) !important;
    padding-right: env(safe-area-inset-right, 0px) !important;
    overscroll-behavior-x: auto !important;
    overscroll-behavior-y: contain !important;
    touch-action: pan-y pinch-zoom;
}

/* Page Layout Margins with Safe Area Compliance */
section.main,
[data-testid="stMain"] {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    width: 100% !important;
}

.stMainBlockContainer {
    padding-top: max(1.8rem, calc(1.8rem + env(safe-area-inset-top, 0px))) !important;
    padding-bottom: max(3rem, calc(3rem + env(safe-area-inset-bottom, 0px))) !important;
    padding-left: max(2.5rem, calc(2.5rem + env(safe-area-inset-left, 0px))) !important;
    padding-right: max(2.5rem, calc(2.5rem + env(safe-area-inset-right, 0px))) !important;
    max-width: 100% !important;
    transition: max-width 240ms cubic-bezier(0.4, 0, 0.2, 1), margin 240ms cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* When sidebar is closed: center main content in the middle with balanced symmetrical margins */
html[data-sidebar-closed="true"] .stMainBlockContainer,
body.sidebar-is-closed .stMainBlockContainer,
html[data-sidebar-closed="true"] [data-testid="stMainBlockContainer"],
body.sidebar-is-closed [data-testid="stMainBlockContainer"],
.stApp:has([data-testid="stSidebar"][data-collapsed="true"]) .stMainBlockContainer,
.stApp:has([data-testid="stSidebar"][aria-expanded="false"]) .stMainBlockContainer,
.stApp:has(button[data-testid="stExpandSidebarButton"]) .stMainBlockContainer,
.stApp:has([data-testid="stSidebarCollapsedControl"]) .stMainBlockContainer,
[data-testid="stSidebar"][data-collapsed="true"] ~ [data-testid="stMain"] .stMainBlockContainer,
[data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] .stMainBlockContainer,
[data-testid="stSidebar"][data-collapsed="true"] ~ section.main .stMainBlockContainer,
[data-testid="stSidebar"][aria-expanded="false"] ~ section.main .stMainBlockContainer {
    max-width: 1200px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    width: 100% !important;
}

/* Hide standard top header & toolbar with safe area offset */
header[data-testid="stHeader"] {
    background: transparent !important;
    height: calc(1.5rem + env(safe-area-inset-top, 0px)) !important;
    top: env(safe-area-inset-top, 0px) !important;
    padding-left: env(safe-area-inset-left, 0px) !important;
    padding-right: env(safe-area-inset-right, 0px) !important;
    z-index: 100 !important;
    overflow: visible !important;
}
div[data-testid="stToolbar"] {
    visibility: hidden !important;
}
footer {
    display: none !important;
}

/* Sidebar Customization with Safe Area Insets */
section[data-testid="stSidebar"],
[data-testid="stSidebar"] {
    background-color: #0b1320 !important;
    border-right: 1px solid #1e293b !important;
    min-width: 332px !important;
    max-width: 332px !important;
    width: 332px !important;
    padding-top: env(safe-area-inset-top, 0px) !important;
    padding-bottom: env(safe-area-inset-bottom, 0px) !important;
    padding-left: env(safe-area-inset-left, 0px) !important;
    transition: min-width 240ms cubic-bezier(0.4, 0, 0.2, 1), max-width 240ms cubic-bezier(0.4, 0, 0.2, 1), width 240ms cubic-bezier(0.4, 0, 0.2, 1), transform 240ms cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Sidebar open state explicitly defined */
section[data-testid="stSidebar"][data-collapsed="false"],
section[data-testid="stSidebar"][aria-expanded="true"],
aside[data-testid="stSidebar"][data-collapsed="false"],
aside[data-testid="stSidebar"][aria-expanded="true"],
[data-testid="stSidebar"][data-collapsed="false"],
[data-testid="stSidebar"][aria-expanded="true"] {
    min-width: 332px !important;
    max-width: 332px !important;
    width: 332px !important;
    visibility: visible !important;
    pointer-events: auto !important;
}

/* Sidebar collapsed state: fully collapses width so main content aligns to the middle */
section[data-testid="stSidebar"][data-collapsed="true"],
section[data-testid="stSidebar"][aria-expanded="false"],
aside[data-testid="stSidebar"][data-collapsed="true"],
aside[data-testid="stSidebar"][aria-expanded="false"],
[data-testid="stSidebar"][data-collapsed="true"],
[data-testid="stSidebar"][aria-expanded="false"],
html[data-sidebar-closed="true"] [data-testid="stSidebar"],
body.sidebar-is-closed [data-testid="stSidebar"],
.stApp:has([data-testid="stSidebar"][data-collapsed="true"]) [data-testid="stSidebar"],
.stApp:has([data-testid="stSidebar"][aria-expanded="false"]) [data-testid="stSidebar"],
.stApp:has(button[data-testid="stExpandSidebarButton"]) [data-testid="stSidebar"],
.stApp:has([data-testid="stSidebarCollapsedControl"]) [data-testid="stSidebar"] {
    min-width: 0px !important;
    max-width: 0px !important;
    width: 0px !important;
    padding: 0px !important;
    margin: 0px !important;
    border-right: none !important;
    overflow: hidden !important;
    visibility: hidden !important;
    pointer-events: none !important;
    flex-shrink: 0 !important;
}

/* Sidebar expand (open) button */
button[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapsedControl"] button {
    visibility: visible !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: #0f172a !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    color: #94a3b8 !important;
    width: 34px !important;
    height: 34px !important;
    cursor: pointer !important;
    pointer-events: auto !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
}
button[data-testid="stExpandSidebarButton"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"] button:hover {
    background: #1e293b !important;
    color: #38bdf8 !important;
    border-color: #38bdf8 !important;
}
button[data-testid="stExpandSidebarButton"] span,
[data-testid="stSidebarCollapsedControl"] span {
    color: inherit !important;
}

/* Sidebar header & collapse button: absolute position with safe area */
div[data-testid="stSidebarHeader"] {
    position: absolute !important;
    top: calc(8px + env(safe-area-inset-top, 0px)) !important;
    right: calc(8px + env(safe-area-inset-right, 0px)) !important;
    background: transparent !important;
    padding: 0 !important;
    z-index: 10 !important;
}
div[data-testid="stSidebarHeader"] button {
    color: #64748b !important;
    opacity: 0 !important;
    transition: opacity 0.2s ease, color 0.15s ease !important;
}
section[data-testid="stSidebar"]:hover div[data-testid="stSidebarHeader"] button {
    opacity: 0.8 !important;
}
section[data-testid="stSidebar"]:hover div[data-testid="stSidebarHeader"] button:hover {
    opacity: 1 !important;
    color: #38bdf8 !important;
}

/* Sidebar content padding & scrollbar hiding */
section[data-testid="stSidebar"] > div:first-child,
div[data-testid="stSidebarContent"] {
    background-color: #0b1320 !important;
    padding: calc(29px + env(safe-area-inset-top, 0px)) 24px calc(24px + env(safe-area-inset-bottom, 0px)) calc(24px + env(safe-area-inset-left, 0px)) !important;
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
    box-sizing: border-box !important;
}
div[data-testid="stSidebarContent"]::-webkit-scrollbar {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
}

div[data-testid="stSidebarUserContent"] {
    padding: 0 !important;
    margin: 0 !important;
    width: 284px !important;
    max-width: 284px !important;
}

section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
    gap: 0px !important;
    width: 284px !important;
    max-width: 284px !important;
}

section[data-testid="stSidebar"] .stElementContainer {
    width: 284px !important;
    max-width: 284px !important;
}

/* Brand styling */
.brand-container {
    display: flex !important;
    align-items: center !important;
    gap: 14px !important;
    margin-bottom: 38px !important;
    width: 284px !important;
    box-sizing: border-box !important;
}
.brand-icon-box {
    width: 42px !important;
    height: 42px !important;
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 9px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
    flex-shrink: 0 !important;
}
.brand-text {
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    letter-spacing: -0.2px !important;
    line-height: 1 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

/* Sidebar Radio Button Styling */
div.st-key-app_input_mode,
div[data-testid="stRadio"] {
    width: 284px !important;
    max-width: 284px !important;
}
div[data-testid="stRadio"] > label,
div[data-testid="stRadio"] label[data-testid="stWidgetLabel"] p {
    color: #64748b !important;
    font-family: 'JetBrains Mono', Consolas, 'SF Mono', monospace !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    margin-bottom: 14px !important;
    display: block !important;
}
div[data-testid="stRadio"] div[role="radiogroup"],
div[data-testid="stRadioGroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 9px !important;
    width: 284px !important;
}
div[data-testid="stRadioGroup"] > div {
    width: 284px !important;
}
div[data-testid="stRadio"] [data-testid="stRadioOption"],
div[data-testid="stRadio"] div[role="radiogroup"] > label,
div[data-testid="stRadioGroup"] > div > label {
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    border-radius: 6px !important;
    height: 51px !important;
    min-height: 51px !important;
    max-height: 51px !important;
    padding: 0 16px !important;
    color: #ffffff !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    display: flex !important;
    align-items: center !important;
    margin: 0 !important;
    width: 284px !important;
    box-sizing: border-box !important;
}
div[data-testid="stRadio"] [data-testid="stRadioOption"]:hover,
div[data-testid="stRadio"] div[role="radiogroup"] > label:hover,
div[data-testid="stRadioGroup"] > div > label:hover {
    border-color: #334155 !important;
}
div[data-testid="stRadio"] [data-testid="stRadioOption"][data-selected="true"],
div[data-testid="stRadio"] div[data-selected="true"] [data-testid="stRadioOption"],
div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked),
div[data-testid="stRadioGroup"] > div[data-selected="true"] > label {
    background: #0f1f38 !important;
    border: 1.5px solid #2563eb !important;
    color: #ffffff !important;
    box-shadow: none !important;
}

/* Radio Indicator Dots */
div[data-testid="stRadio"] [data-testid="stRadioOption"] > div:first-of-type {
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
}
div[data-testid="stRadio"] [data-testid="stRadioOption"] > div > div:first-child,
div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child,
div[data-testid="stRadio"] [data-testid="stRadioGroupIndicator"],
div[data-testid="stRadioGroup"] > div:not([data-selected="true"]) > label > div > div:first-child,
div[data-testid="stRadio"] label:not(:has(input:checked)) > div:first-child,
div[data-testid="stRadio"] label:not(:has(input:checked)) [data-testid="stRadioGroupIndicator"] {
    border: 2px solid #1c3550 !important;
    background-color: transparent !important;
    width: 18px !important;
    height: 18px !important;
    min-width: 18px !important;
    min-height: 18px !important;
    border-radius: 50% !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin-right: 14px !important;
    box-shadow: none !important;
    flex-shrink: 0 !important;
}
div[data-testid="stRadio"] div[data-selected="true"] [data-testid="stRadioOption"] > div > div:first-child,
div[data-testid="stRadio"] [data-selected="true"][data-testid="stRadioOption"] > div > div:first-child,
div[data-testid="stRadio"] label:has(input:checked) > div:first-child,
div[data-testid="stRadio"] label:has(input:checked) [data-testid="stRadioGroupIndicator"],
div[data-testid="stRadioGroup"] > div[data-selected="true"] > label > div > div:first-child {
    border: none !important;
    background-color: #2563eb !important;
    width: 18px !important;
    height: 18px !important;
    min-width: 18px !important;
    min-height: 18px !important;
    border-radius: 50% !important;
    margin-right: 14px !important;
    box-shadow: none !important;
    flex-shrink: 0 !important;
}
div[data-testid="stRadio"] div:not([data-selected="true"]) [data-testid="stRadioOption"] > div > div:first-child > div,
div[data-testid="stRadio"] label:not(:has(input:checked)) > div:first-child > div,
div[data-testid="stRadio"] label:not(:has(input:checked)) [data-testid="stRadioGroupIndicator"] *,
div[data-testid="stRadioGroup"] > div:not([data-selected="true"]) > label > div > div:first-child > div {
    display: none !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] input[type="radio"] {
    appearance: none !important;
    -webkit-appearance: none !important;
    width: 18px !important;
    height: 18px !important;
    border-radius: 50% !important;
    border: 2px solid #1c3550 !important;
    background: transparent !important;
    margin: 0 14px 0 0 !important;
    outline: none !important;
    cursor: pointer !important;
    flex-shrink: 0 !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] input[type="radio"]:checked {
    border: none !important;
    background-color: #2563eb !important;
    box-shadow: none !important;
}

/* Radio Option Text */
div[data-testid="stRadio"] [data-testid="stRadioOption"] p,
div[data-testid="stRadio"] div[role="radiogroup"] label p,
div[data-testid="stRadioGroup"] label p {
    font-family: 'JetBrains Mono', Consolas, 'SF Mono', monospace !important;
    font-size: 14.5px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    letter-spacing: 0.2px !important;
    margin: 0 !important;
    line-height: 1 !important;
}

/* Status Box */
.status-box {
    background: #051b12 !important;
    border: 1px solid #134e2b !important;
    border-radius: 6px !important;
    height: 80px !important;
    min-height: 80px !important;
    max-height: 80px !important;
    padding: 0 16px !important;
    display: flex !important;
    align-items: center !important;
    gap: 14px !important;
    margin-top: 26px !important;
    margin-bottom: 32px !important;
    width: 284px !important;
    box-sizing: border-box !important;
}
.status-box.local {
    background: #071726 !important;
    border: 1px solid #1b3a57 !important;
    color: #38bdf8 !important;
}
.status-indicator {
    width: 20px !important;
    height: 20px !important;
    min-width: 20px !important;
    border-radius: 50% !important;
    background: rgba(16, 185, 129, 0.2) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
}
.status-indicator.local {
    background: rgba(56, 189, 248, 0.2) !important;
}
.status-inner-dot {
    width: 8px !important;
    height: 8px !important;
    border-radius: 50% !important;
    background: #10b981 !important;
    box-shadow: none !important;
}
.status-inner-dot.local {
    background: #38bdf8 !important;
    box-shadow: none !important;
}
.status-text {
    color: #10b981 !important;
    font-family: 'JetBrains Mono', Consolas, monospace !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    line-height: 1.35 !important;
    letter-spacing: 0.2px !important;
}
.status-text.local {
    color: #38bdf8 !important;
}

/* Sidebar Telemetry */
.sidebar-telemetry {
    font-family: 'JetBrains Mono', Consolas, monospace !important;
    font-size: 14.5px !important;
    line-height: 1.2 !important;
    margin: 24px 0 30px 0 !important;
    width: 284px !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 14px !important;
}
.sidebar-telemetry > div {
    line-height: 1.2 !important;
    margin: 0 !important;
    padding: 0 !important;
}
.telemetry-label {
    color: #3ea0dc !important;
    font-weight: 500 !important;
}
.telemetry-val {
    color: #ffffff !important;
    font-weight: 700 !important;
}
.telemetry-subnote {
    font-size: 11.5px !important;
    line-height: 1.35 !important;
    margin-top: -6px !important;
}
.telemetry-sublabel {
    color: #6a8298 !important;
    font-weight: 500 !important;
}
.telemetry-subval {
    color: #ffab00 !important;
    font-weight: 600 !important;
}

/* Sidebar Expander Customization */
section[data-testid="stSidebar"] div[data-testid="stExpander"] {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    margin: 0px !important;
    width: 284px !important;
    max-width: 284px !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] details {
    border: 1px solid #15263b !important;
    border-radius: 4px !important;
    background: #07121e !important;
    overflow: hidden !important;
    width: 284px !important;
    box-sizing: border-box !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] details:hover {
    border-color: #1e3a58 !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary {
    height: 51px !important;
    min-height: 51px !important;
    box-sizing: border-box !important;
    padding: 0 16px !important;
    background: #07121e !important;
    color: #ffffff !important;
    border: none !important;
    outline: none !important;
    cursor: pointer !important;
    list-style: none !important;
    display: flex !important;
    align-items: center !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary::-webkit-details-marker {
    display: none !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary [data-testid="stIconMaterial"],
section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary span.material-symbols-rounded,
section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary svg {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    font-size: 0 !important;
    overflow: hidden !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary p,
section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary span {
    font-family: 'JetBrains Mono', Consolas, monospace !important;
    font-size: 14.5px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    margin: 0 !important;
    letter-spacing: 0.2px !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] details div[data-testid="stExpanderDetails"] {
    padding: 16px !important;
    background: #050d18 !important;
    border-top: 1px solid #15263b !important;
    color: #8da4be !important;
    font-size: 13px !important;
    line-height: 1.6 !important;
}

/* Main Console Header */
.console-header {
    margin-bottom: 24px;
    padding-top: 4px;
}
.console-title {
    font-size: 32px;
    font-weight: 800;
    color: #ffffff;
    margin: 0 0 6px 0;
    letter-spacing: -0.5px;
}
.console-subtitle {
    font-size: 15px;
    color: #7993aa;
    margin: 0;
}

/* Tabs Styling */
div[data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #14273d !important;
    gap: 32px !important;
    margin-bottom: 28px !important;
}
div[data-baseweb="tab"] {
    background: transparent !important;
    color: #657e93 !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    padding: 8px 4px 14px 4px !important;
    border: none !important;
}
div[data-baseweb="tab"]:hover {
    color: #a0c2dc !important;
}
div[data-baseweb="tab"][aria-selected="true"] {
    color: #ffffff !important;
    border: none !important;
}
div[data-baseweb="tab-highlight"] {
    background-color: #3b82f6 !important;
    box-shadow: none !important;
    height: 3px !important;
}
div[data-baseweb="tab-border"] {
    display: none !important;
}

/* Robust Container Border across Streamlit versions */
div.st-key-card_pick_tx,
div.st-key-card_manual_tx,
div.st-key-card_manual_ab,
div.st-key-card_manual_dn,
div.st-key-card_history,
div[data-testid="stVerticalBlock"]:has(> div > div > .card-title),
div[data-testid="stVerticalBlock"]:has(> div > .card-title) {
    position: relative !important;
    background: #0d1524 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    padding: 22px 24px !important;
    margin-bottom: 24px !important;
}

/* Sci-fi HUD corner brackets removed for clean professional fintech surface */
div.st-key-card_pick_tx::before,
div.st-key-card_manual_tx::before,
div.st-key-card_manual_ab::before,
div.st-key-card_manual_dn::before,
div.st-key-card_history::before,
div[data-testid="stVerticalBlock"]:has(> div > div > .card-title)::before,
div[data-testid="stVerticalBlock"]:has(> div > .card-title)::before,
div.st-key-card_pick_tx::after,
div.st-key-card_manual_tx::after,
div.st-key-card_manual_ab::after,
div.st-key-card_manual_dn::after,
div.st-key-card_history::after,
div[data-testid="stVerticalBlock"]:has(> div > div > .card-title)::after,
div[data-testid="stVerticalBlock"]:has(> div > .card-title)::after,
.hud-box::before,
.hud-box::after,
.hero-card::before,
.hero-card::after,
.hero-corner-tr,
.hero-corner-bl {
    display: none !important;
}

/* Standalone HUD Box */
.hud-box {
    position: relative;
    background: #0d1524;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 22px 24px;
    margin-bottom: 24px;
}

/* Card Title */
.card-title {
    font-size: 16px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 16px;
}

/* Input & Select Customization */
div[data-baseweb="input"], div[data-baseweb="base-input"] {
    background-color: #0b1320 !important;
    border: 1px solid #1e293b !important;
    border-radius: 6px !important;
    min-height: 44px !important;
}
div[data-baseweb="input"]:focus-within, div[data-baseweb="base-input"]:focus-within {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 1px #3b82f6 !important;
}
div[data-baseweb="input"] input, div[data-baseweb="base-input"] input {
    color: #ffffff !important;
    font-family: 'JetBrains Mono', Consolas, monospace !important;
    font-size: 14px !important;
}
div[data-baseweb="select"] > div {
    background-color: #0b1320 !important;
    border: 1px solid #1e293b !important;
    border-radius: 6px !important;
    color: #ffffff !important;
    min-height: 44px !important;
    font-family: 'JetBrains Mono', Consolas, monospace !important;
}
label[data-testid="stWidgetLabel"] p {
    color: #94a3b8 !important;
    font-size: 13px !important;
    margin-bottom: 4px !important;
}

/* Checkbox */
div[data-testid="stCheckbox"] label p {
    color: #e2e8f0 !important;
    font-size: 13px !important;
}

/* Sliders */
div[data-testid="stSlider"] [role="slider"] {
    background-color: #2563eb !important;
    border-color: #2563eb !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
}
div[data-testid="stSlider"] [data-testid="stSliderThumbValue"] {
    color: #ffffff !important;
    font-family: 'JetBrains Mono', Consolas, monospace !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}
div[data-testid="stSlider"] [data-testid="stSliderTickBar"] {
    display: none !important;
}

/* Buttons */
button[kind="primary"], button[data-testid="baseButton-primary"] {
    background-color: #2563eb !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 6px !important;
    min-height: 44px !important;
    padding: 9px 20px !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15) !important;
    cursor: pointer !important;
    transition: background-color 0.15s ease !important;
}
button[kind="primary"]:hover, button[data-testid="baseButton-primary"]:hover {
    background-color: #1d4ed8 !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
}
button[kind="secondary"], button[data-testid="baseButton-secondary"] {
    background-color: #0f172a !important;
    color: #e2e8f0 !important;
    border: 1px solid #1e293b !important;
    border-radius: 6px !important;
    min-height: 44px !important;
    padding: 9px 18px !important;
    cursor: pointer !important;
    transition: border-color 0.15s ease, color 0.15s ease !important;
}
button[kind="secondary"]:hover, button[data-testid="baseButton-secondary"]:hover {
    border-color: #3b82f6 !important;
    color: #ffffff !important;
}

/* Preview Strip (6 Chips) */
.preview-strip {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
    margin-top: 18px;
}
.preview-chip {
    background: #050d18;
    border: 1px solid #102135;
    border-radius: 4px;
    padding: 10px 14px;
}
.chip-label {
    color: #637c93;
    font-size: 11px;
    margin-bottom: 4px;
}
.chip-value {
    color: #e2ecf5;
    font-size: 14px;
    font-weight: 600;
    font-family: 'JetBrains Mono', Consolas, monospace;
}

/* Dashed Empty State Box */
.empty-state-box {
    border: 1px dashed #14324f;
    border-radius: 6px;
    padding: 55px 20px;
    text-align: center;
    color: #557796;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 13px;
    margin-top: 24px;
    background: rgba(7, 16, 28, 0.4);
}

/* Hero Verdict Card */
.hero-card {
    position: relative;
    border-radius: 8px;
    padding: 22px 28px;
    background: #081322;
    overflow: hidden;
    box-sizing: border-box;
    width: 100%;
    margin-bottom: 24px;
}

/* Symmetrical Tech Corner Accents (All 4 Corners) */
.hero-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 16px;
    height: 16px;
    border-top: 2px solid currentColor;
    border-left: 2px solid currentColor;
    pointer-events: none;
}
.hero-card::after {
    content: "";
    position: absolute;
    bottom: 0;
    right: 0;
    width: 16px;
    height: 16px;
    border-bottom: 2px solid currentColor;
    border-right: 2px solid currentColor;
    pointer-events: none;
}
.hero-corner-tr {
    position: absolute;
    top: 0;
    right: 0;
    width: 16px;
    height: 16px;
    border-top: 2px solid currentColor;
    border-right: 2px solid currentColor;
    pointer-events: none;
}
.hero-corner-bl {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 16px;
    height: 16px;
    border-bottom: 2px solid currentColor;
    border-left: 2px solid currentColor;
    pointer-events: none;
}

/* Card State Variants */
.hero-safe {
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.35);
    background: #091712;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}
.hero-fraud {
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.4);
    background: #1c0a0e;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}
.hero-suspicious {
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.4);
    background: #191206;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

/* Inner Layout & Structure */
.hero-inner {
    display: flex;
    align-items: center;
    gap: 32px;
}
.hero-gauge-col {
    flex: 0 0 240px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}
.hero-gauge-col svg {
    width: 240px;
    height: auto;
    overflow: visible;
}
.hero-divider {
    width: 1px;
    height: 125px;
    background: #1e293b;
}
.hero-info-col {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 13px;
}

/* Header Area */
.hero-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
}
.verdict-title-wrap {
    display: flex;
    align-items: baseline;
    gap: 14px;
}
.verdict-title {
    font-size: 34px;
    font-weight: 800;
    letter-spacing: 0.05em;
    line-height: 1;
    margin: 0;
    text-shadow: none;
}

/* Status Pill Badge */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 11px;
    border-radius: 20px;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.badge-fraud {
    background: rgba(255, 23, 68, 0.15);
    border: 1px solid rgba(255, 23, 68, 0.4);
    color: #ff4060;
}
.badge-safe {
    background: rgba(0, 230, 118, 0.15);
    border: 1px solid rgba(0, 230, 118, 0.4);
    color: #00e676;
}
.badge-suspicious {
    background: rgba(255, 171, 0, 0.15);
    border: 1px solid rgba(255, 171, 0, 0.4);
    color: #ffab00;
}

/* Transaction Metadata Row */
.tx-meta-row {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}
.tx-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 4px;
    padding: 3px 9px;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 12px;
    color: #9cb3c9;
}
.tx-chip-key {
    color: #627d98;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.tx-chip-val {
    color: #ffffff;
    font-weight: 600;
}
.tx-chip-val.amount {
    color: #00f0ff;
    font-weight: 700;
}

/* Stats Grid - 3 Balanced Cards */
.verdict-stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-top: 2px;
}
.stat-card {
    background: rgba(255, 255, 255, 0.025);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 6px;
    padding: 10px 14px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.stat-label {
    color: #728ca3;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.stat-value-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    white-space: nowrap;
}
.stat-value {
    color: #ffffff;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 19px;
    font-weight: 700;
    line-height: 1.2;
    white-space: nowrap;
}
.stat-subtext {
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.04em;
}

/* Agent Agreement Dots */
.agent-dots-wrap {
    display: inline-flex;
    align-items: center;
    gap: 5px;
}
.agent-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}
.agent-dot.inactive {
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.22);
}

@media (max-width: 800px) {
    .hero-inner {
        flex-direction: column;
        gap: 20px;
    }
    .hero-divider {
        display: none;
    }
    .verdict-stats-grid {
        grid-template-columns: 1fr;
    }
}

/* 4 Metric Cards */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}
.metric-card {
    background: #081322;
    border: 1px solid #142840;
    border-radius: 4px;
    padding: 16px 20px;
}
.metric-label {
    color: #6f889e;
    font-size: 13px;
    margin-bottom: 6px;
}
.metric-val {
    color: #ffffff;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 28px;
    font-weight: 700;
    line-height: 1.1;
    margin-bottom: 12px;
}
.metric-bar-track {
    width: 100%;
    height: 4px;
    background: #112236;
    border-radius: 2px;
    margin-bottom: 12px;
    overflow: hidden;
}
.metric-bar-fill {
    height: 100%;
    border-radius: 2px;
}
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 11px;
    font-weight: 600;
}
.badge-normal {
    background: rgba(0, 230, 118, 0.12);
    color: #00e676;
    border: 1px solid rgba(0, 230, 118, 0.3);
}
.badge-elevated {
    background: rgba(255, 171, 0, 0.12);
    color: #ffab00;
    border: 1px solid rgba(255, 171, 0, 0.3);
}
.badge-high {
    background: rgba(255, 23, 68, 0.12);
    color: #ff1744;
    border: 1px solid rgba(255, 23, 68, 0.3);
}

/* Why this verdict */
.safe-summary-box {
    background: #050d17;
    border: 1px solid #0f2237;
    border-radius: 4px;
    padding: 14px 18px;
    color: #8da6bd;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 13px;
}
.risk-lines-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.risk-line {
    color: #d8e6f4;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 13px;
    line-height: 1.5;
}
.risk-tag {
    color: #ff2b4e;
    font-weight: 700;
    margin-right: 6px;
}

/* Expander accordions */
div[data-testid="stExpander"] {
    background: #081322 !important;
    border: 1px solid #142840 !important;
    border-radius: 4px !important;
    margin-bottom: 12px !important;
}
div[data-testid="stExpander"] summary {
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 12px 18px !important;
}
div[data-testid="stExpander"] summary svg,
div[data-testid="stExpander"] [data-testid="stExpanderStepChevron"] {
    display: none !important;
}
div[data-testid="stExpander"] div[role="region"],
div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    padding: 0 18px 16px 18px !important;
}
.agent-summary-text {
    color: #8da6bd;
    font-size: 13px;
    line-height: 1.5;
    margin-top: 4px;
}

/* History Table */
.hist-table {
    margin-top: 14px;
}
.hist-header {
    display: grid;
    grid-template-columns: 1.5fr 2.5fr 2fr 1.5fr 1.5fr;
    padding: 10px 14px;
    border-bottom: 1px solid #142840;
    color: #6a8298;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 12px;
}
.hist-row {
    display: grid;
    grid-template-columns: 1.5fr 2.5fr 2fr 1.5fr 1.5fr;
    padding: 14px;
    border-bottom: 1px solid #0f2034;
    align-items: center;
    color: #d0e2f2;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 13px;
}
.hist-badge {
    display: inline-block;
    padding: 3px 14px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    text-align: center;
}
.hist-safe {
    background: #082d1c;
    color: #00e676;
    border: 1px solid rgba(0, 230, 118, 0.4);
}
.hist-fraud {
    background: #360a14;
    color: #ff1744;
    border: 1px solid rgba(255, 23, 68, 0.4);
}
.hist-suspicious {
    background: #362208;
    color: #ffab00;
    border: 1px solid rgba(255, 171, 0, 0.4);
}
.empty-history-text {
    color: #6a8298;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 13px;
    padding: 20px 0;
}

/* ==================================================================
   VIEW TRANSITIONS API & PREDICTIVE BACK
   ================================================================== */

@view-transition {
    navigation: auto;
}

::view-transition-old(root) {
    animation: 240ms cubic-bezier(0.4, 0, 0.2, 1) both vt-fade-out;
}
::view-transition-new(root) {
    animation: 240ms cubic-bezier(0.4, 0, 0.2, 1) both vt-fade-in;
}

@keyframes vt-fade-out {
    from { opacity: 1; transform: scale(1); }
    to { opacity: 0; transform: scale(0.985); }
}
@keyframes vt-fade-in {
    from { opacity: 0; transform: scale(1.015); }
    to { opacity: 1; transform: scale(1); }
}

/* Semantic view-transition-names for spatial continuity */
section[data-testid="stSidebar"] {
    view-transition-name: app-sidebar;
}
.brand-container {
    view-transition-name: app-brand;
}
.hero-card {
    view-transition-name: app-hero-card;
}
.hud-box {
    view-transition-name: app-hud-box;
}
.metric-row {
    view-transition-name: app-metric-row;
}
.hist-table {
    view-transition-name: app-hist-table;
}
div[data-testid="stTabs"] {
    view-transition-name: app-tabs;
}

/* Predictive Back gesture transition animations */
@keyframes pb-slide-in-left {
    from { transform: translateX(-24px); opacity: 0.85; }
    to { transform: translateX(0); opacity: 1; }
}
@keyframes pb-slide-out-right {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(24px); opacity: 0.85; }
}

.predictive-back-enter {
    animation: pb-slide-in-left 220ms cubic-bezier(0.4, 0, 0.2, 1) both;
}
.predictive-back-exit {
    animation: pb-slide-out-right 220ms cubic-bezier(0.4, 0, 0.2, 1) both;
}

/* Motion accessibility: respect user's motion preferences */
@media (prefers-reduced-motion: reduce) {
    ::view-transition-group(*),
    ::view-transition-old(*),
    ::view-transition-new(*) {
        animation: none !important;
    }
    .predictive-back-enter,
    .predictive-back-exit {
        animation: none !important;
    }
}

/* ==================================================================
   1. HIT SLOP (EXPANDED INTERACTION HIT TARGETS)
   ================================================================== */
.hit-slop,
[data-hit-slop],
div[data-testid="stSidebarHeader"] button,
button[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapsedControl"] button,
div[data-baseweb="tab"],
section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary,
div[data-testid="stRadio"] [data-testid="stRadioOption"],
.stButton > button,
.flyout-nav-item {
    position: relative !important;
}

.hit-slop::after,
[data-hit-slop]::after,
div[data-testid="stSidebarHeader"] button::after,
button[data-testid="stExpandSidebarButton"]::after,
[data-testid="stSidebarCollapsedControl"]::after,
[data-testid="stSidebarCollapsedControl"] button::after,
div[data-baseweb="tab"]::after,
section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary::after,
div[data-testid="stRadio"] [data-testid="stRadioOption"]::after,
.stButton > button::after,
.flyout-nav-item::after {
    content: '' !important;
    position: absolute !important;
    top: -8px !important;
    bottom: -8px !important;
    left: -8px !important;
    right: -8px !important;
    pointer-events: auto !important;
    z-index: 1 !important;
}

.hit-slop-sm::after {
    top: -4px !important; bottom: -4px !important; left: -4px !important; right: -4px !important;
}
.hit-slop-md::after {
    top: -8px !important; bottom: -8px !important; left: -8px !important; right: -8px !important;
}
.hit-slop-lg::after {
    top: -14px !important; bottom: -14px !important; left: -14px !important; right: -14px !important;
}

/* ==================================================================
   2. TABULAR NUMBERS (EQUAL ADVANCE NUMERICAL FIGURES)
   ================================================================== */
:root {
    --font-numeric-tabular: tabular-nums;
}

.tabular-nums,
[data-tabular-nums],
[data-tabular-nums="true"],
.stat-value,
.metric-val,
.chip-value,
.telemetry-val,
.telemetry-subval,
.status-text,
.hist-cell,
.gauge-score,
.tx-chip-val,
.verdict-title,
.agent-score,
.risk-score,
.hud-metric,
.amount,
.flyout-metric-value,
.threat-flyout-badge,
table, td, th,
[data-testid="stTable"],
[data-testid="stMetricValue"],
[data-testid="stDataFrame"],
.stDataFrame,
code, pre,
.mono {
    font-variant-numeric: tabular-nums !important;
    font-feature-settings: "tnum" 1 !important;
}

/* ==================================================================
   3. BALANCED HEADLINES (LINE BALANCING & ORPHAN PREVENTION)
   ================================================================== */
h1, h2, h3, h4, h5, h6,
.brand-text,
.console-title,
.console-subtitle,
.card-title,
.verdict-title,
.balanced-headline,
[data-balanced-headline],
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4,
[data-testid="stHeading"],
[data-testid="stSubheader"],
.threat-flyout-header,
.flyout-panel-title {
    text-wrap: pretty;
    text-wrap: balance !important;
}

/* ==================================================================
   4. CONTINUOUS CORNERS (SUPER-ELLIPSE / APPLE-STYLE SMOOTH CURVATURE)
   ================================================================== */
.continuous-corner,
[data-continuous-corners],
.hero-card,
.stat-card,
.metric-card,
.hud-box,
.preview-strip,
div.st-key-card_pick_tx,
div.st-key-card_manual_tx,
div.st-key-card_manual_ab,
div.st-key-card_manual_dn,
div.st-key-card_history,
.stButton > button,
section[data-testid="stSidebar"] div[data-testid="stExpander"] details,
div[data-testid="stRadio"] [data-testid="stRadioOption"],
.flyout-nav-list,
.flyout-nav-item,
.flyout-panel-container {
    -webkit-corner-smoothing: 60% !important;
    corner-smoothing: 60% !important;
    border-radius: 12px !important;
}

.continuous-corner-sm,
.preview-chip,
.tx-chip,
.badge,
.flyout-metric-cell {
    -webkit-corner-smoothing: 60% !important;
    corner-smoothing: 60% !important;
    border-radius: 6px !important;
}

.continuous-corner-md {
    -webkit-corner-smoothing: 60% !important;
    corner-smoothing: 60% !important;
    border-radius: 12px !important;
}

.continuous-corner-lg {
    -webkit-corner-smoothing: 60% !important;
    corner-smoothing: 60% !important;
    border-radius: 18px !important;
}

.continuous-corner-xl {
    -webkit-corner-smoothing: 60% !important;
    corner-smoothing: 60% !important;
    border-radius: 24px !important;
}

.brand-icon-box {
    -webkit-corner-smoothing: 60% !important;
    corner-smoothing: 60% !important;
    border-radius: 10px !important;
}

.status-box {
    -webkit-corner-smoothing: 60% !important;
    corner-smoothing: 60% !important;
    border-radius: 10px !important;
}

div[data-testid="stRadio"] [data-testid="stRadioOption"] {
    -webkit-corner-smoothing: 60% !important;
    corner-smoothing: 60% !important;
    border-radius: 8px !important;
}

/* ==================================================================
   5. AMAZON SAFE TRIANGLE & THREAT FLYOUT MENU STYLING
   ================================================================== */
.threat-flyout-container {
    width: 100% !important;
    max-width: 284px !important;
    margin: 18px 0 !important;
    position: relative !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

.threat-flyout-header {
    margin-bottom: 8px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    padding: 0 2px !important;
}

.threat-flyout-title-group {
    display: flex !important;
    align-items: center !important;
    gap: 7px !important;
}

.threat-live-beacon {
    width: 6px !important;
    height: 6px !important;
    border-radius: 50% !important;
    background: #38bdf8 !important;
    display: inline-block !important;
    flex-shrink: 0 !important;
}

.threat-flyout-title {
    font-family: 'JetBrains Mono', Consolas, monospace !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    color: #cbd5e1 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

.threat-flyout-badge {
    background: rgba(56, 189, 248, 0.08) !important;
    border: 1px solid rgba(56, 189, 248, 0.25) !important;
    color: #38bdf8 !important;
    font-size: 9.5px !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 2.5px 8px !important;
    border-radius: 9999px !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 4px !important;
    font-variant-numeric: tabular-nums !important;
    transition: all 0.2s ease !important;
    cursor: default !important;
}

.threat-flyout-badge:hover {
    background: rgba(56, 189, 248, 0.16) !important;
    border-color: rgba(56, 189, 248, 0.5) !important;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.2) !important;
}

.threat-badge-icon {
    width: 10px !important;
    height: 10px !important;
    opacity: 0.9 !important;
}

.flyout-nav-list {
    background: linear-gradient(180deg, #090e18 0%, #060a12 100%) !important;
    border: 1px solid rgba(56, 189, 248, 0.14) !important;
    border-radius: 10px !important;
    -webkit-corner-smoothing: 60% !important;
    corner-smoothing: 60% !important;
    padding: 6px !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 4px !important;
    width: 100% !important;
    max-width: 284px !important;
    box-sizing: border-box !important;
    position: relative !important;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

.flyout-nav-item {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    padding: 7px 10px !important;
    min-height: 48px !important;
    background: rgba(15, 23, 42, 0.55) !important;
    border: 1px solid rgba(255, 255, 255, 0.04) !important;
    border-radius: 8px !important;
    -webkit-corner-smoothing: 60% !important;
    corner-smoothing: 60% !important;
    cursor: pointer !important;
    transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
    position: relative !important;
    box-sizing: border-box !important;
}

.flyout-nav-item:hover,
.flyout-nav-item.active,
.flyout-nav-item:focus-visible {
    background: linear-gradient(90deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.9) 100%) !important;
    border-color: rgba(56, 189, 248, 0.4) !important;
    box-shadow: 0 4px 14px -2px rgba(0, 0, 0, 0.45) !important;
    transform: translateX(2px) !important;
    outline: none !important;
}

.flyout-nav-item:focus-visible {
    outline: 2px solid #38bdf8 !important;
    outline-offset: 1px !important;
}

.flyout-nav-left {
    display: flex !important;
    align-items: center !important;
    gap: 9px !important;
    min-width: 0 !important;
}

.flyout-nav-icon {
    width: 24px !important;
    height: 24px !important;
    border-radius: 5px !important;
    font-family: 'JetBrains Mono', Consolas, monospace !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex-shrink: 0 !important;
    box-sizing: border-box !important;
}

/* Cohesive Palette: Cool Slate, Cyan & Indigo */
.agent-1-icon {
    color: #38bdf8 !important;
    background: rgba(56, 189, 248, 0.12) !important;
    border: 1px solid rgba(56, 189, 248, 0.28) !important;
}
.agent-2-icon {
    color: #818cf8 !important;
    background: rgba(129, 140, 248, 0.12) !important;
    border: 1px solid rgba(129, 140, 248, 0.28) !important;
}
.agent-3-icon {
    color: #38bdf8 !important;
    background: rgba(56, 189, 248, 0.12) !important;
    border: 1px solid rgba(56, 189, 248, 0.28) !important;
}
.agent-4-icon {
    color: #2dd4bf !important;
    background: rgba(45, 212, 191, 0.12) !important;
    border: 1px solid rgba(45, 212, 191, 0.28) !important;
}
.agent-5-icon {
    color: #94a3b8 !important;
    background: rgba(148, 163, 184, 0.12) !important;
    border: 1px solid rgba(148, 163, 184, 0.24) !important;
}

.flyout-nav-text-col {
    display: flex !important;
    flex-direction: column !important;
    min-width: 0 !important;
}

.flyout-nav-name {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #e2e8f0 !important;
    line-height: 1.25 !important;
    letter-spacing: -0.01em !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

.flyout-nav-item:hover .flyout-nav-name,
.flyout-nav-item.active .flyout-nav-name,
.flyout-nav-item:focus-visible .flyout-nav-name {
    color: #ffffff !important;
}

.flyout-nav-sub {
    font-size: 10px !important;
    color: #64748b !important;
    line-height: 1.2 !important;
    margin-top: 2px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

.flyout-nav-item:hover .flyout-nav-sub,
.flyout-nav-item.active .flyout-nav-sub,
.flyout-nav-item:focus-visible .flyout-nav-sub {
    color: #94a3b8 !important;
}

.flyout-nav-right {
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    flex-shrink: 0 !important;
}

.flyout-nav-tag {
    font-family: 'JetBrains Mono', Consolas, monospace !important;
    font-size: 8.5px !important;
    font-weight: 700 !important;
    padding: 1.5px 5px !important;
    border-radius: 3px !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}

.agent-1-tag { color: #38bdf8 !important; background: rgba(56, 189, 248, 0.08) !important; border: 1px solid rgba(56, 189, 248, 0.2) !important; }
.agent-2-tag { color: #818cf8 !important; background: rgba(129, 140, 248, 0.08) !important; border: 1px solid rgba(129, 140, 248, 0.2) !important; }
.agent-3-tag { color: #38bdf8 !important; background: rgba(56, 189, 248, 0.08) !important; border: 1px solid rgba(56, 189, 248, 0.2) !important; }
.agent-4-tag { color: #2dd4bf !important; background: rgba(45, 212, 191, 0.08) !important; border: 1px solid rgba(45, 212, 191, 0.2) !important; }
.agent-5-tag { color: #94a3b8 !important; background: rgba(148, 163, 184, 0.08) !important; border: 1px solid rgba(148, 163, 184, 0.2) !important; }

.flyout-nav-chevron {
    color: #64748b !important;
    flex-shrink: 0 !important;
    transition: transform 0.15s ease, color 0.15s ease, stroke 0.15s ease !important;
}

.flyout-nav-item:hover .flyout-nav-chevron,
.flyout-nav-item.active .flyout-nav-chevron,
.flyout-nav-item:focus-visible .flyout-nav-chevron {
    color: #38bdf8 !important;
    stroke: #38bdf8 !important;
    transform: translateX(2px) !important;
}

/* Subtle Divider */
.flyout-nav-divider {
    display: flex !important;
    align-items: center !important;
    margin: 4px 2px !important;
    gap: 8px !important;
}

.flyout-nav-divider::before,
.flyout-nav-divider::after {
    content: '' !important;
    flex: 1 !important;
    height: 1px !important;
    background: rgba(255, 255, 255, 0.06) !important;
}

.flyout-divider-text {
    font-family: 'JetBrains Mono', Consolas, monospace !important;
    font-size: 8.5px !important;
    font-weight: 700 !important;
    color: #475569 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
}

/* Redesigned Flyout Popover Panel */
.flyout-panel-container {
    position: fixed !important;
    width: 340px !important;
    max-width: calc(100vw - 320px) !important;
    max-height: calc(100vh - 32px) !important;
    overflow-y: auto !important;
    scrollbar-width: thin !important;
    background: rgba(11, 17, 30, 0.98) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(56, 189, 248, 0.22) !important;
    border-radius: 12px !important;
    -webkit-corner-smoothing: 60% !important;
    corner-smoothing: 60% !important;
    padding: 16px 18px !important;
    box-shadow: 0 16px 36px -8px rgba(0, 0, 0, 0.75), 0 0 1px 1px rgba(56, 189, 248, 0.2) !important;
    z-index: 999999 !important;
    display: none !important;
    pointer-events: auto !important;
    box-sizing: border-box !important;
}

.flyout-panel-container.open {
    display: block !important;
    animation: flyout-appear 180ms cubic-bezier(0.16, 1, 0.3, 1) both !important;
}

@keyframes flyout-appear {
    from { opacity: 0; transform: translateX(-6px) scale(0.98); }
    to { opacity: 1; transform: translateX(0) scale(1); }
}

.flyout-panel-header {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    margin-bottom: 8px !important;
    gap: 8px !important;
}

.flyout-panel-badge-group {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}

.flyout-panel-icon {
    width: 22px !important;
    height: 22px !important;
    border-radius: 4px !important;
    font-family: 'JetBrains Mono', Consolas, monospace !important;
    font-size: 9.5px !important;
    font-weight: 700 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.flyout-panel-title {
    font-size: 13.5px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    letter-spacing: -0.01em !important;
    text-wrap: balance !important;
}

.flyout-panel-status {
    font-family: 'JetBrains Mono', Consolas, monospace !important;
    font-size: 9px !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 2px 7px !important;
    border-radius: 9999px !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 4px !important;
}

.agent-1-status { color: #38bdf8 !important; background: rgba(56, 189, 248, 0.1) !important; border: 1px solid rgba(56, 189, 248, 0.25) !important; }
.agent-2-status { color: #818cf8 !important; background: rgba(129, 140, 248, 0.1) !important; border: 1px solid rgba(129, 140, 248, 0.25) !important; }
.agent-3-status { color: #38bdf8 !important; background: rgba(56, 189, 248, 0.1) !important; border: 1px solid rgba(56, 189, 248, 0.25) !important; }
.agent-4-status { color: #2dd4bf !important; background: rgba(45, 212, 191, 0.1) !important; border: 1px solid rgba(45, 212, 191, 0.25) !important; }
.agent-5-status { color: #94a3b8 !important; background: rgba(148, 163, 184, 0.1) !important; border: 1px solid rgba(148, 163, 184, 0.25) !important; }

.flyout-panel-pulse {
    width: 5px !important;
    height: 5px !important;
    border-radius: 50% !important;
    background: currentColor !important;
    display: inline-block !important;
    flex-shrink: 0 !important;
}

.flyout-panel-desc {
    font-size: 11.5px !important;
    line-height: 1.55 !important;
    color: #94a3b8 !important;
    margin-bottom: 12px !important;
    text-wrap: pretty !important;
}

.flyout-metrics-grid {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 8px !important;
    margin-top: 10px !important;
}

.flyout-metric-cell {
    background: rgba(15, 23, 42, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 7px !important;
    -webkit-corner-smoothing: 60% !important;
    corner-smoothing: 60% !important;
    padding: 8px 10px !important;
    transition: background 0.15s ease, border-color 0.15s ease !important;
}

.flyout-metric-cell:hover {
    background: rgba(30, 41, 59, 0.7) !important;
    border-color: rgba(56, 189, 248, 0.3) !important;
}

.flyout-metric-key {
    font-size: 9.5px !important;
    font-weight: 600 !important;
    color: #64748b !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    margin-bottom: 3px !important;
}

.flyout-metric-value {
    font-size: 12.5px !important;
    font-weight: 700 !important;
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', Consolas, monospace !important;
    font-variant-numeric: tabular-nums !important;
}

.flyout-panel-footer {
    margin-top: 12px !important;
    padding-top: 8px !important;
    border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    font-family: 'JetBrains Mono', Consolas, monospace !important;
    font-size: 9px !important;
    color: #64748b !important;
    letter-spacing: 0.04em !important;
}

.flyout-footer-icon {
    color: #38bdf8 !important;
    flex-shrink: 0 !important;
}

.nav-target-highlight {
    outline: 2px solid rgba(56, 189, 248, 0.7) !important;
    outline-offset: 4px !important;
    transition: outline 0.3s ease !important;
}

/* Mobile responsive layout enhancements (antislop-layoutmobile) */
@media (max-width: 768px) {
    .stMainBlockContainer {
        padding-left: max(1rem, calc(1rem + env(safe-area-inset-left, 0px))) !important;
        padding-right: max(1rem, calc(1rem + env(safe-area-inset-right, 0px))) !important;
    }
    .preview-strip {
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 8px !important;
    }
    .metrics-grid {
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 8px !important;
    }
    .hero-inner {
        flex-direction: column !important;
        gap: 18px !important;
    }
}
</style>
"""

st.html(custom_css + f"<style>{get_starting_scene_css()}</style>")

# ==================================================================
# RUNTIME CONTROLLER: SAFE AREA, VIEW TRANSITIONS, HIT SLOP,
# TABULAR NUMS, BALANCED HEADLINES, CONTINUOUS CORNERS, AMAZON SAFE TRIANGLE
# ==================================================================

_st_components.html(
    """
    <script>
    (function() {
        try {
            const pDoc = window.parent.document;
            const pWin = window.parent;
            if (!pDoc || !pWin) return;

            // 1. SAFE AREA INSETS: Ensure viewport-fit=cover in top document head
            let vp = pDoc.querySelector('meta[name="viewport"]');
            if (vp) {
                let content = vp.getAttribute('content') || '';
                if (!content.includes('viewport-fit=cover')) {
                    vp.setAttribute('content', (content ? content + ', ' : '') + 'viewport-fit=cover');
                }
            } else {
                vp = pDoc.createElement('meta');
                vp.name = 'viewport';
                vp.content = 'width=device-width, initial-scale=1, shrink-to-fit=no, viewport-fit=cover';
                pDoc.head.appendChild(vp);
            }
            pDoc.documentElement.setAttribute('data-safe-area-enabled', 'true');

            // 2. VIEW TRANSITIONS & PREDICTIVE BACK
            pDoc.documentElement.setAttribute('data-view-transitions', 'true');
            pDoc.documentElement.setAttribute('data-predictive-back', 'true');

            // 3. HIT SLOP RUNTIME CONTROLLER
            pDoc.documentElement.setAttribute('data-hit-slop-enabled', 'true');
            if (!pWin._fraudguard_hit_slop_bound) {
                pWin._fraudguard_hit_slop_bound = true;
                const HIT_SLOP_PX = 10;
                pDoc.addEventListener('click', (e) => {
                    // Check if click already directly hit an interactive element
                    if (e.target.closest('button, [role="button"], [role="tab"], [role="radio"], summary, input, select, textarea, a, .flyout-nav-item, [data-hit-slop-target]')) {
                        return;
                    }
                    const x = e.clientX, y = e.clientY;
                    const candidates = pDoc.querySelectorAll('button, [role="button"], [role="tab"], [role="radio"], summary, a, .flyout-nav-item, [data-hit-slop-target]');
                    let nearest = null;
                    let minDistance = Infinity;
                    for (const el of candidates) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) continue;
                        const dx = Math.max(rect.left - x, 0, x - rect.right);
                        const dy = Math.max(rect.top - y, 0, y - rect.bottom);
                        const dist = Math.sqrt(dx * dx + dy * dy);
                        if (dist <= HIT_SLOP_PX && dist < minDistance) {
                            minDistance = dist;
                            nearest = el;
                        }
                    }
                    if (nearest) {
                        nearest.click();
                    }
                }, { capture: true });
            }

            // 4. TABULAR NUMBERS RUNTIME CONTROLLER
            pDoc.documentElement.setAttribute('data-tabular-nums', 'true');

            // 5. BALANCED HEADLINES RUNTIME ORPHAN PREVENTER
            pDoc.documentElement.setAttribute('data-balanced-headlines', 'true');
            function balanceHeadlinesRuntime() {
                const headings = pDoc.querySelectorAll('h1, h2, h3, h4, h5, h6, .brand-text, .console-title, .console-subtitle, .card-title, .verdict-title, .balanced-headline, [data-balanced-headline]');
                headings.forEach(h => {
                    if (h.getAttribute('data-balanced-done')) return;
                    h.setAttribute('data-balanced-done', 'true');
                    // Safely find the last text node within the heading without corrupting inner HTML
                    const walker = pDoc.createTreeWalker(h, NodeFilter.SHOW_TEXT, null, false);
                    let lastText = null;
                    while (walker.nextNode()) {
                        if (walker.currentNode.nodeValue.trim().length > 0) {
                            lastText = walker.currentNode;
                        }
                    }
                    if (lastText) {
                        const val = lastText.nodeValue;
                        const trimmed = val.trim();
                        if (trimmed !== 'Pick a transaction' && trimmed !== 'Why this verdict' && !trimmed.startsWith('Agent 1: Behavior')) {
                            const lastSpace = val.lastIndexOf(' ');
                            if (lastSpace > 0 && lastSpace < val.length - 1) {
                                lastText.nodeValue = val.substring(0, lastSpace) + '\u00A0' + val.substring(lastSpace + 1);
                            }
                        }
                    }
                });
            }
            balanceHeadlinesRuntime();

            // 6. CONTINUOUS CORNERS RUNTIME CONTROLLER
            pDoc.documentElement.setAttribute('data-continuous-corners', 'true');

            // 7. AMAZON SAFE TRIANGLE ALGORITHM & INTERACTION ENGINE
            pDoc.documentElement.setAttribute('data-amazon-safe-triangle', 'true');

            function vectorCross(p1, p2, p3) {
                return (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y);
            }
            function isPointInTriangle(p, a, b, c) {
                const d1 = vectorCross(p, a, b);
                const d2 = vectorCross(p, b, c);
                const d3 = vectorCross(p, c, a);
                const hasNeg = (d1 < 0) || (d2 < 0) || (d3 < 0);
                const hasPos = (d1 > 0) || (d2 > 0) || (d3 > 0);
                return !(hasNeg && hasPos);
            }

            // Mouse tracking buffer
            if (!pWin._fraudguard_mouse_locs) {
                pWin._fraudguard_mouse_locs = [];
                pDoc.addEventListener('mousemove', (e) => {
                    pWin._fraudguard_mouse_locs.push({ x: e.clientX, y: e.clientY });
                    if (pWin._fraudguard_mouse_locs.length > 8) {
                        pWin._fraudguard_mouse_locs.shift();
                    }
                });
            }

            // Expose verification API for automated testing
            pWin._amazonSafeTriangleTest = {
                isPointInTriangle: isPointInTriangle,
                checkInTriangle: function(px, py, ax, ay, bx, by, cx, cy) {
                    return isPointInTriangle({x: px, y: py}, {x: ax, y: ay}, {x: bx, y: by}, {x: cx, y: cy});
                }
            };

            // Flyout Menu Interaction with Amazon Safe Triangle
            function initFlyoutMenus() {
                const containers = pDoc.querySelectorAll('.threat-flyout-container');
                containers.forEach(container => {
                    if (container._flyout_init) return;
                    container._flyout_init = true;

                    const navItems = container.querySelectorAll('.flyout-nav-item');
                    let panel = container.querySelector('.flyout-panel-container');
                    if (!navItems.length || !panel) return;

                    // Portal panel to document.body so that sidebar overflow-x: hidden never clips it!
                    if (panel.parentElement !== pDoc.body) {
                        pDoc.body.appendChild(panel);
                    }

                    let activeIndex = -1;
                    let switchTimeout = null;
                    let lastActivePos = null;

                    const panelData = [
                        {
                            title: 'Agent 1: Behavior Analyzer',
                            badge: '01',
                            iconClass: 'agent-1-icon',
                            status: 'AI Engine',
                            statusClass: 'agent-1-status',
                            desc: 'Constructs per-user baseline from historical data. Evaluates deviations in amount, transaction hour, location, payment mode, and device familiarity.',
                            m1k: 'Amount Deviation', m1v: 'Baseline z-score',
                            m2k: 'Location Check', m2v: 'Historical match',
                            m3k: 'Payment Mode', m3v: 'Frequency profile',
                            m4k: 'Hour Norm', m4v: 'Activity window'
                        },
                        {
                            title: 'Agent 2: Risk Assessor',
                            badge: '02',
                            iconClass: 'agent-2-icon',
                            status: 'ML + Rules',
                            statusClass: 'agent-2-status',
                            desc: 'Integrates expert domain behavioral rules with Random Forest classification, IP reputation scoring, and authentication failure rate tracking.',
                            m1k: 'Primary Signal', m1v: 'Domain rules',
                            m2k: 'Secondary Signal', m2v: 'Random Forest',
                            m3k: 'IP Risk Range', m3v: '0.0 to 1.0',
                            m4k: 'Failed Logins', m4v: 'Threshold check'
                        },
                        {
                            title: 'Agent 3: Transaction Validator',
                            badge: '03',
                            iconClass: 'agent-3-icon',
                            status: 'Deterministic',
                            statusClass: 'agent-3-status',
                            desc: 'Evaluates rapid spending ratio spikes, 10-minute velocity bursts, and deterministic threshold violations.',
                            m1k: 'Anomaly Ratio', m1v: 'Deterministic spike',
                            m2k: 'Velocity Window', m2v: '10-min window',
                            m3k: 'Rule Engine', m3v: 'Threshold bounds',
                            m4k: 'Engine Status', m4v: 'ACTIVE'
                        },
                        {
                            title: 'Agent 4: Decision Synthesizer',
                            badge: '04',
                            iconClass: 'agent-4-icon',
                            status: 'Consensus',
                            statusClass: 'agent-4-status',
                            desc: 'Applies calibrated consensus weighting across all 3 agent signals and computes final calibrated confidence metrics.',
                            m1k: 'Consensus Quorum', m1v: '3-agent agreement',
                            m2k: 'Calibrated Scale', m2v: '0 to 100',
                            m3k: 'High Risk Cutoff', m3v: 'Score >= 70.0',
                            m4k: 'Output', m4v: 'Consensus verdict'
                        },
                        {
                            title: 'Threat Presets',
                            badge: 'PT',
                            iconClass: 'agent-5-icon',
                            status: 'Test Vectors',
                            statusClass: 'agent-5-status',
                            desc: 'Representative evaluation scenarios across all risk tiers for live demonstration and automated test verification.',
                            m1k: 'Sample T3768', m1v: 'Known Fraud',
                            m2k: 'Sample T7', m2v: 'Suspicious Burst',
                            m3k: 'Manual U9999', m3v: 'High Risk Attack',
                            m4k: 'Manual U1757', m4v: 'Clean Baseline'
                        }
                    ];

                    function renderPanel(idx) {
                        const data = panelData[idx];
                        if (!data) return;
                        const item = navItems[idx];
                        panel.innerHTML = `
                            <div class="flyout-panel-header">
                                <div class="flyout-panel-badge-group">
                                    <span class="flyout-panel-icon ${data.iconClass}">${data.badge}</span>
                                    <div class="flyout-panel-title balanced-headline">${data.title}</div>
                                </div>
                                <span class="flyout-panel-status ${data.statusClass}">
                                    <span class="flyout-panel-pulse"></span>
                                    ${data.status}
                                </span>
                            </div>
                            <div class="flyout-panel-desc balanced-headline">${data.desc}</div>
                            <div class="flyout-metrics-grid">
                                <div class="flyout-metric-cell continuous-corner continuous-corner-sm">
                                    <div class="flyout-metric-key">${data.m1k}</div>
                                    <div class="flyout-metric-value tabular-nums">${data.m1v}</div>
                                </div>
                                <div class="flyout-metric-cell continuous-corner continuous-corner-sm">
                                    <div class="flyout-metric-key">${data.m2k}</div>
                                    <div class="flyout-metric-value tabular-nums">${data.m2v}</div>
                                </div>
                                <div class="flyout-metric-cell continuous-corner continuous-corner-sm">
                                    <div class="flyout-metric-key">${data.m3k}</div>
                                    <div class="flyout-metric-value tabular-nums">${data.m3v}</div>
                                </div>
                                <div class="flyout-metric-cell continuous-corner continuous-corner-sm">
                                    <div class="flyout-metric-key">${data.m4k}</div>
                                    <div class="flyout-metric-value tabular-nums">${data.m4v}</div>
                                </div>
                            </div>
                            <div class="flyout-panel-footer">
                                <svg class="flyout-footer-icon" viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="8" cy="8" r="6"/>
                                    <path d="M8 5v3l2 2"/>
                                </svg>
                                <span class="flyout-footer-text">Multi-Agent Pipeline • Inspection Dossier</span>
                            </div>
                        `;
                        panel.classList.add('open');

                        if (item) {
                            const itemRect = item.getBoundingClientRect();
                            const currentHeight = panel.offsetHeight || 290;
                            const maxTop = Math.max(16, pWin.innerHeight - currentHeight - 16);
                            const panelTop = Math.max(16, Math.min(maxTop, itemRect.top - 12));
                            panel.style.setProperty('left', (itemRect.right + 12) + 'px', 'important');
                            panel.style.setProperty('top', panelTop + 'px', 'important');
                            panel.style.setProperty('z-index', '999999', 'important');
                        }
                    }

                    function handleItemAction(idx) {
                        if (idx >= 0 && idx <= 2) {
                            const prefixes = ['Agent 1', 'Agent 2', 'Agent 3'];
                            const prefix = prefixes[idx];
                            const expanders = pDoc.querySelectorAll('[data-testid="stExpander"]');
                            let found = null;
                            expanders.forEach(exp => {
                                if (exp.innerText && exp.innerText.includes(prefix)) {
                                    found = exp;
                                }
                            });
                            if (found) {
                                const details = found.querySelector('details') || found;
                                if (details && !details.open) {
                                    const summary = details.querySelector('summary');
                                    if (summary) summary.click();
                                }
                                found.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                found.classList.add('nav-target-highlight');
                                setTimeout(() => found.classList.remove('nav-target-highlight'), 1600);
                            }
                        } else if (idx === 3) {
                            const hero = pDoc.querySelector('.hero-card') || pDoc.querySelector('.hud-box') || pDoc.querySelector('.console-header');
                            if (hero) {
                                hero.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                hero.classList.add('nav-target-highlight');
                                setTimeout(() => hero.classList.remove('nav-target-highlight'), 1600);
                            }
                        } else if (idx === 4) {
                            const txInput = pDoc.querySelector('input[aria-label="Transaction ID"]') || pDoc.querySelector('.preview-strip');
                            if (txInput) {
                                txInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                if (txInput.focus) txInput.focus();
                            }
                        }
                    }

                    navItems.forEach((item, idx) => {
                        item.setAttribute('role', 'button');
                        item.setAttribute('tabindex', '0');
                        item.setAttribute('aria-haspopup', 'dialog');

                        item.addEventListener('click', () => {
                            handleItemAction(idx);
                        });

                        item.addEventListener('keydown', (e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                renderPanel(idx);
                                handleItemAction(idx);
                            } else if (e.key === 'Escape') {
                                panel.classList.remove('open');
                                item.classList.remove('active');
                                activeIndex = -1;
                            }
                        });

                        item.addEventListener('mouseenter', (e) => {
                            if (switchTimeout) {
                                clearTimeout(switchTimeout);
                                switchTimeout = null;
                            }

                            if (activeIndex === -1 || !panel.classList.contains('open')) {
                                activeIndex = idx;
                                lastActivePos = { x: e.clientX, y: e.clientY };
                                navItems.forEach(n => n.classList.remove('active'));
                                item.classList.add('active');
                                renderPanel(idx);
                                return;
                            }

                            if (activeIndex === idx) return;

                            // Amazon Safe Triangle hit test
                            const panelRect = panel.getBoundingClientRect();
                            const prevLoc = (pWin._fraudguard_mouse_locs && pWin._fraudguard_mouse_locs[0]) || { x: e.clientX, y: e.clientY };
                            const apex = lastActivePos || prevLoc;
                            const pTop = { x: panelRect.left - 4, y: panelRect.top };
                            const pBottom = { x: panelRect.left - 4, y: panelRect.bottom };
                            const currentPos = { x: e.clientX, y: e.clientY };

                            const insideSafeTriangle = isPointInTriangle(currentPos, apex, pTop, pBottom);

                            if (insideSafeTriangle) {
                                panel.setAttribute('data-in-safe-triangle', 'true');
                                switchTimeout = setTimeout(() => {
                                    activeIndex = idx;
                                    lastActivePos = { x: e.clientX, y: e.clientY };
                                    navItems.forEach(n => n.classList.remove('active'));
                                    item.classList.add('active');
                                    renderPanel(idx);
                                    panel.removeAttribute('data-in-safe-triangle');
                                }, 300);
                            } else {
                                activeIndex = idx;
                                lastActivePos = { x: e.clientX, y: e.clientY };
                                navItems.forEach(n => n.classList.remove('active'));
                                item.classList.add('active');
                                renderPanel(idx);
                            }
                        });

                        item.addEventListener('mouseleave', (e) => {
                            lastActivePos = { x: e.clientX, y: e.clientY };
                        });
                    });

                    panel.addEventListener('mouseenter', () => {
                        if (switchTimeout) {
                            clearTimeout(switchTimeout);
                            switchTimeout = null;
                        }
                        panel.removeAttribute('data-in-safe-triangle');
                    });

                    panel.addEventListener('mouseleave', (e) => {
                        const toEl = e.relatedTarget;
                        if (!toEl || !container.contains(toEl)) {
                            if (switchTimeout) clearTimeout(switchTimeout);
                            switchTimeout = setTimeout(() => {
                                panel.classList.remove('open');
                                navItems.forEach(n => n.classList.remove('active'));
                                activeIndex = -1;
                                lastActivePos = null;
                            }, 250);
                        }
                    });

                    container.addEventListener('mouseleave', (e) => {
                        const toEl = e.relatedTarget;
                        if (!toEl || (toEl !== panel && !panel.contains(toEl))) {
                            if (switchTimeout) clearTimeout(switchTimeout);
                            switchTimeout = setTimeout(() => {
                                panel.classList.remove('open');
                                navItems.forEach(n => n.classList.remove('active'));
                                activeIndex = -1;
                                lastActivePos = null;
                            }, 250);
                        }
                    });
                });
            }
            initFlyoutMenus();

            // 8. VIEW TRANSITIONS & OBSERVER RUNTIME LISTENERS
            if (!pWin._fraudguard_vt_initialized) {
                pWin._fraudguard_vt_initialized = true;

                let currentActiveTab = 'analyze';
                pDoc.addEventListener('click', (e) => {
                    const tabBtn = e.target.closest('[role="tab"]');
                    if (tabBtn) {
                        const tabLabel = (tabBtn.innerText || '').toLowerCase();
                        const nextTab = tabLabel.includes('history') ? 'history' : 'analyze';
                        if (nextTab !== currentActiveTab) {
                            currentActiveTab = nextTab;
                            try {
                                pWin.history.pushState({ tab: nextTab }, '', '#' + nextTab);
                            } catch (_) {}
                        }
                    }

                    const interactive = e.target.closest('button, [role="tab"], [role="radio"], [data-testid="stRadioOption"]');
                    if (interactive && pDoc.startViewTransition) {
                        pWin._pendingViewTransition = true;
                    }
                }, { capture: true });

                pWin.addEventListener('popstate', (e) => {
                    const state = e.state;
                    const targetTabName = (state && state.tab === 'history') ? 'history' : 'analyze';
                    currentActiveTab = targetTabName;

                    const tabs = pDoc.querySelectorAll('[role="tab"]');
                    tabs.forEach((tab) => {
                        const label = (tab.innerText || '').toLowerCase();
                        if ((targetTabName === 'history' && label.includes('history')) ||
                            (targetTabName === 'analyze' && !label.includes('history'))) {
                            if (pDoc.startViewTransition) {
                                pDoc.startViewTransition(() => {
                                    tab.click();
                                });
                            } else {
                                tab.click();
                            }
                        }
                    });
                });

                if (pWin.navigation) {
                    pWin.navigation.addEventListener('navigate', (e) => {
                        if (e.canIntercept && e.navigationType === 'traverse' && pDoc.startViewTransition) {
                            e.intercept({
                                async handler() {
                                    await Promise.resolve();
                                }
                            });
                        }
                    });
                }

                // Sidebar Collapse & Middle Alignment Controller
                function updateSidebarLayout() {
                    try {
                        const sidebar = pDoc.querySelector('section[data-testid="stSidebar"], [data-testid="stSidebar"]');
                        if (!sidebar) return;
                        const collapsedAttr = sidebar.getAttribute('data-collapsed');
                        const ariaAttr = sidebar.getAttribute('aria-expanded');
                        const isClosed = (collapsedAttr === 'true' || ariaAttr === 'false');

                        pDoc.documentElement.setAttribute('data-sidebar-closed', isClosed ? 'true' : 'false');
                        if (pDoc.body) {
                            pDoc.body.classList.toggle('sidebar-is-closed', isClosed);
                        }

                        if (isClosed) {
                            sidebar.style.setProperty('width', '0px', 'important');
                            sidebar.style.setProperty('min-width', '0px', 'important');
                            sidebar.style.setProperty('max-width', '0px', 'important');
                            sidebar.style.setProperty('margin', '0px', 'important');
                            sidebar.style.setProperty('padding', '0px', 'important');
                            sidebar.style.setProperty('visibility', 'hidden', 'important');
                            sidebar.style.setProperty('pointer-events', 'none', 'important');
                        } else {
                            sidebar.style.removeProperty('width');
                            sidebar.style.removeProperty('min-width');
                            sidebar.style.removeProperty('max-width');
                            sidebar.style.removeProperty('margin');
                            sidebar.style.removeProperty('padding');
                            sidebar.style.removeProperty('visibility');
                            sidebar.style.removeProperty('pointer-events');
                        }

                        const container = pDoc.querySelector('.stMainBlockContainer');
                        if (container) {
                            if (isClosed) {
                                container.style.setProperty('max-width', '1200px', 'important');
                                container.style.setProperty('margin-left', 'auto', 'important');
                                container.style.setProperty('margin-right', 'auto', 'important');
                            } else {
                                container.style.removeProperty('max-width');
                                container.style.removeProperty('margin-left');
                                container.style.removeProperty('margin-right');
                            }
                        }
                    } catch (_) {}
                }

                pDoc.addEventListener('click', (e) => {
                    if (e.target.closest('button[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"], div[data-testid="stSidebarCollapseButton"] button, div[data-testid="stSidebarHeader"] button')) {
                        setTimeout(updateSidebarLayout, 30);
                        setTimeout(updateSidebarLayout, 150);
                        setTimeout(updateSidebarLayout, 350);
                    }
                }, { capture: true });

                pWin.addEventListener('resize', updateSidebarLayout);
                updateSidebarLayout();

                const observer = new MutationObserver((mutations) => {
                    balanceHeadlinesRuntime();
                    initFlyoutMenus();
                    updateSidebarLayout();
                    if (pWin._pendingViewTransition && pDoc.startViewTransition) {
                        pWin._pendingViewTransition = false;
                        try {
                            pDoc.startViewTransition(() => {});
                        } catch (_) {}
                    }
                });
                const targetNode = pDoc.querySelector('.stAppViewContainer') || pDoc.body;
                observer.observe(targetNode, { childList: true, subtree: true, attributes: true, attributeFilter: ['data-collapsed', 'aria-expanded', 'class', 'style'] });
            }
        } catch(err) {
            console.warn('[FraudGuard] Enhanced features runtime setup:', err);
        }
    })();
    </script>
    """,
    height=0,
    width=0
)

# ==================================================================
# SIDEBAR
# ==================================================================

with st.sidebar:
    # 1. Branding
    st.html("""
    <div class="brand-container">
      <div class="brand-icon-box continuous-corner">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#040911" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="m9 12 2 2 4-4"/>
        </svg>
      </div>
      <div class="brand-text balanced-headline">FraudGuard</div>
    </div>
    """)

    # 2. Input Mode Radio
    mode = st.radio("Input mode", ["Dataset transaction", "Manual entry"], index=0, key="app_input_mode")

    # 4. Telemetry info
    st.html(f"""
    <div class="sidebar-telemetry">
      <div title="ML Signal: Supporting (Weak Dataset Baseline)"><span class="telemetry-label">Model:</span> <span class="telemetry-val">Hybrid (Rules + RF)</span></div>
      <div class="telemetry-subnote" title="ML Signal: Supporting (Weak Dataset Baseline)"><span class="telemetry-sublabel">ML Signal:</span> <span class="telemetry-subval">Supporting (Weak Dataset Baseline)</span></div>
      <div><span class="telemetry-label">Agents:</span> <span class="telemetry-val tabular-nums">3 active</span></div>
    </div>
    """)

    # 4b. Threat Inspector (Redesigned Multi-Agent Pipeline)
    _st_components.html(get_threat_inspector_html(), height=540, scrolling=False)

# ==================================================================
# MAIN AREA: HERO & TABS
# ==================================================================

analysis = st.session_state.get("current_analysis")

if not analysis:
    # Executive Operations Starting Hero & Telemetry Counters
    num_txs = len(df_dataset) if (df_dataset is not None and not df_dataset.empty) else 7500
    st.markdown(render_starting_scene_hero(num_txs), unsafe_allow_html=True)

history_count = len(st.session_state["history"])
history_tab_title = f"History ({history_count})" if history_count > 0 else "History"
tab_analyze, tab_history = st.tabs(["Analyze", history_tab_title])

# ==================================================================
# TAB 1: ANALYZE
# ==================================================================

with tab_analyze:
    if mode == "Dataset transaction":
        # ----------------------------------------------------------
        # DATASET TRANSACTION PICKER
        # ----------------------------------------------------------
        def _pick_random_tx():
            if not df_dataset.empty:
                st.session_state["tx_id_input"] = str(df_dataset.sample(1).iloc[0]["transaction_id"])

        with st.container(border=True, key="card_pick_tx"):
            st.html('<div class="card-title balanced-headline">Pick a transaction</div>')

            tx_input = st.text_input(
                "Transaction ID",
                key="tx_id_input",
            )
            cur_id = tx_input.strip()

            b_col1, b_col2, _ = st.columns([2.5, 2.2, 5.3])
            with b_col1:
                analyze_clicked = st.button("Analyze transaction", type="primary", use_container_width=True, key="btn_ds_analyze")
            with b_col2:
                st.button("Pick a random one", use_container_width=True, key="btn_ds_random", on_click=_pick_random_tx)

            # Dynamic Preview Strip (6 Chips)
            row_match = df_dataset[df_dataset["transaction_id"] == cur_id]
            if not row_match.empty:
                r = row_match.iloc[0]
                p_user = str(r["user_id"])
                p_amt = f"₹{int(r['transaction_amount']):,}"
                p_type = str(r["transaction_type"])
                raw_mode = str(r["payment_mode"])
                p_mode = "Net banking" if raw_mode.lower() == "netbanking" else raw_mode
                p_dev = str(r["device_type"])
                p_loc = str(r["device_location"])
            else:
                p_user, p_amt, p_type, p_mode, p_dev, p_loc = "-", "-", "-", "-", "-", "-"

            st.html(f"""
            <div class="preview-strip continuous-corner-md">
              <div class="preview-chip continuous-corner-sm">
                <div class="chip-label balanced-headline">User</div>
                <div class="chip-value tabular-nums">{p_user}</div>
              </div>
              <div class="preview-chip continuous-corner-sm">
                <div class="chip-label balanced-headline">Amount</div>
                <div class="chip-value tabular-nums">{p_amt}</div>
              </div>
              <div class="preview-chip continuous-corner-sm">
                <div class="chip-label balanced-headline">Type</div>
                <div class="chip-value tabular-nums">{p_type}</div>
              </div>
              <div class="preview-chip continuous-corner-sm">
                <div class="chip-label balanced-headline">Payment mode</div>
                <div class="chip-value tabular-nums">{p_mode}</div>
              </div>
              <div class="preview-chip continuous-corner-sm">
                <div class="chip-label balanced-headline">Device</div>
                <div class="chip-value tabular-nums">{p_dev}</div>
              </div>
              <div class="preview-chip continuous-corner-sm">
                <div class="chip-label balanced-headline">Location</div>
                <div class="chip-value tabular-nums">{p_loc}</div>
              </div>
            </div>
            """)

        if analyze_clicked:
            with st.spinner("Analyzing threat telemetry..."):
                res = analyze_dataset_tx(cur_id)
            if res:
                st.session_state["current_analysis"] = res
                # Add to history if not identical to the most recent entry
                hist_entry = {
                    "time": datetime.now().strftime("%I:%M %p").lstrip("0"),
                    "transaction": res["tx_id"],
                    "amount": res["amount_str"],
                    "score": f"{res['fraud_score']:.1f}",
                    "verdict": res["verdict"],
                }
                st.session_state["history"].insert(0, hist_entry)
                st.rerun()

    else:
        # ----------------------------------------------------------
        # MANUAL ENTRY MODE
        # ----------------------------------------------------------
        def _load_fraud_example():
            st.session_state["manual_user_id"] = "U9999"
            st.session_state["manual_amount"] = 90000
            st.session_state["manual_avg_amount"] = 4000
            st.session_state["manual_type"] = "Payment"
            st.session_state["manual_mode"] = "Card"
            st.session_state["manual_intl"] = True
            st.session_state["manual_age"] = 30
            st.session_state["manual_hour"] = 2
            st.session_state["manual_failed"] = 5
            st.session_state["manual_logins"] = 9
            st.session_state["manual_device"] = "Android"
            st.session_state["manual_location"] = "Bangalore"
            st.session_state["manual_ip_risk"] = 0.95

        def _load_safe_example():
            st.session_state["manual_user_id"] = "U1757"
            st.session_state["manual_amount"] = 4200
            st.session_state["manual_avg_amount"] = 4000
            st.session_state["manual_type"] = "Payment"
            st.session_state["manual_mode"] = "Net banking"
            st.session_state["manual_intl"] = False
            st.session_state["manual_age"] = 811
            st.session_state["manual_hour"] = 14
            st.session_state["manual_failed"] = 0
            st.session_state["manual_logins"] = 1
            st.session_state["manual_device"] = "Android"
            st.session_state["manual_location"] = "Bangalore"
            st.session_state["manual_ip_risk"] = 0.05

        # 1. Transaction Card
        with st.container(border=True, key="card_manual_tx"):
            st.html('<div class="card-title balanced-headline">Transaction</div>')
            m_c1, m_c2, m_c3, m_c4, m_c5 = st.columns(5)
            with m_c1:
                st.text_input("User ID", key="manual_user_id")
            with m_c2:
                st.number_input("Amount (₹)", min_value=0, step=100, format="%d", key="manual_amount")
            with m_c3:
                st.number_input("User's average amount (₹)", min_value=0, step=100, format="%d", key="manual_avg_amount")
            with m_c4:
                st.selectbox("Transaction type", TRANSACTION_TYPES, key="manual_type")
            with m_c5:
                st.selectbox("Payment mode", PAYMENT_MODES, key="manual_mode")

            st.checkbox("International transaction", key="manual_intl")

        # 2. Account and behavior Card
        with st.container(border=True, key="card_manual_ab"):
            st.html('<div class="card-title balanced-headline">Account and behavior</div>')
            ab_c1, ab_c2, ab_c3, ab_c4 = st.columns(4)
            with ab_c1:
                st.number_input("Account age (days)", min_value=0, step=1, format="%d", key="manual_age")
            with ab_c2:
                st.slider("Hour of day", 0, 23, key="manual_hour")
            with ab_c3:
                st.slider("Previous failed attempts", 0, 10, key="manual_failed")
            with ab_c4:
                st.slider("Logins in last 24 hours", 0, 24, key="manual_logins")

        # 3. Device and network Card
        with st.container(border=True, key="card_manual_dn"):
            st.html('<div class="card-title balanced-headline">Device and network</div>')
            dn_c1, dn_c2, dn_c3 = st.columns([1.5, 1.5, 2.0])
            with dn_c1:
                st.selectbox("Device type", DEVICE_TYPES, key="manual_device")
            with dn_c2:
                st.selectbox("Device location", LOCATIONS, key="manual_location")
            with dn_c3:
                st.slider("IP risk score", 0.0, 1.0, step=0.01, key="manual_ip_risk")

            btn_c1, btn_c2, btn_c3, _ = st.columns([2.5, 2.2, 2.2, 3.1])
            with btn_c1:
                manual_analyze_clicked = st.button("Analyze transaction", type="primary", use_container_width=True, key="btn_manual_analyze")
            with btn_c2:
                st.button("Load a fraud example", use_container_width=True, key="btn_load_fraud", on_click=_load_fraud_example)
            with btn_c3:
                st.button("Load a safe example", use_container_width=True, key="btn_load_safe", on_click=_load_safe_example)

        if manual_analyze_clicked:
            raw_payment_mode = "NetBanking" if st.session_state["manual_mode"] == "Net banking" else st.session_state["manual_mode"]
            payload = {
                "user_id": st.session_state["manual_user_id"],
                "transaction_amount": float(st.session_state["manual_amount"]),
                "transaction_type": st.session_state["manual_type"],
                "payment_mode": raw_payment_mode,
                "device_type": st.session_state["manual_device"],
                "device_location": st.session_state["manual_location"],
                "account_age_days": int(st.session_state["manual_age"]),
                "transaction_hour": int(st.session_state["manual_hour"]),
                "previous_failed_attempts": int(st.session_state["manual_failed"]),
                "avg_transaction_amount": float(st.session_state["manual_avg_amount"]),
                "is_international": int(st.session_state["manual_intl"]),
                "ip_risk_score": float(st.session_state["manual_ip_risk"]),
                "login_attempts_last_24h": int(st.session_state["manual_logins"]),
                "transaction_id": "MANUAL",
            }
            with st.spinner("Analyzing threat telemetry..."):
                res = analyze_manual_tx(payload)
            if res:
                st.session_state["current_analysis"] = res
                hist_entry = {
                    "time": datetime.now().strftime("%I:%M %p").lstrip("0"),
                    "transaction": res["tx_id"],
                    "amount": res["amount_str"],
                    "score": f"{res['fraud_score']:.1f}",
                    "verdict": res["verdict"],
                }
                st.session_state["history"].insert(0, hist_entry)
                st.rerun()

    # --------------------------------------------------------------
    # ANALYSIS RESULTS SECTION
    # --------------------------------------------------------------
    analysis = st.session_state.get("current_analysis")
    if analysis:
        def _reset_to_start():
            st.session_state["current_analysis"] = None

        if mode != "Manual entry":
            top_c1, top_c2 = st.columns([2.5, 7.5])
            with top_c1:
                st.button("← Return to Starting Scene", use_container_width=True, key="btn_back_to_start", on_click=_reset_to_start)
        verdict = analysis["verdict"]
        score = analysis["fraud_score"]
        confidence = analysis["confidence"]
        consensus = analysis["consensus"]
        tx_title = analysis["tx_title"]

        if verdict == "SAFE":
            hero_cls = "hero-safe"
            verdict_color = "#00e676"
            badge_text = "VERIFIED SECURE"
            badge_cls = "badge-safe"
            badge_icon = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#00e676" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>'
        elif verdict == "FRAUD":
            hero_cls = "hero-fraud"
            verdict_color = "#ff1744"
            badge_text = "CRITICAL THREAT"
            badge_cls = "badge-fraud"
            badge_icon = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#ff1744" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
        else:
            hero_cls = "hero-suspicious"
            verdict_color = "#ffab00"
            badge_text = "ELEVATED RISK"
            badge_cls = "badge-suspicious"
            badge_icon = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#ffab00" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'

        gauge_svg = render_gauge_svg(score, verdict_color)

        # Agent consensus visual indicators
        agent_dots = []
        for i in range(1, 4):
            if i <= consensus:
                agent_dots.append(f'<span class="agent-dot active" style="background:{verdict_color};"></span>')
            else:
                agent_dots.append('<span class="agent-dot inactive"></span>')
        dots_html = "".join(agent_dots)

        # Risk tier label
        if score >= 70:
            tier_label = "HIGH RISK"
            tier_col = "#ff1744"
        elif score >= 35:
            tier_label = "MODERATE"
            tier_col = "#ffab00"
        else:
            tier_label = "NORMAL"
            tier_col = "#00e676"

        conf_label = "HIGH" if confidence >= 80 else ("MODERATE" if confidence >= 50 else "LOW")

        # Metadata chips
        tx_id = analysis.get("tx_id")
        amount_str = analysis.get("amount_str")
        user_id = analysis.get("user_id")

        if tx_id and amount_str and user_id:
            meta_html = (
                f'<div class="tx-meta-row">'
                f'<div class="tx-chip continuous-corner-sm"><span class="tx-chip-key">TX</span><span class="tx-chip-val tabular-nums">{tx_id}</span></div>'
                f'<div class="tx-chip continuous-corner-sm"><span class="tx-chip-key">AMOUNT</span><span class="tx-chip-val amount tabular-nums">{amount_str}</span></div>'
                f'<div class="tx-chip continuous-corner-sm"><span class="tx-chip-key">USER</span><span class="tx-chip-val tabular-nums">{user_id}</span></div>'
                f'</div>'
            )
        else:
            meta_html = f'<div class="verdict-subtitle balanced-headline">{html.escape(tx_title)}</div>'

        # 1. Hero Verdict Card (clean enterprise card without sci-fi corner brackets)
        card_markup = (
            f'<div class="hero-card {hero_cls} continuous-corner">'
            f'<div class="hero-inner">'
            f'<div class="hero-gauge-col">{gauge_svg}</div>'
            f'<div class="hero-divider"></div>'
            f'<div class="hero-info-col">'
            f'<div class="hero-header-row">'
            f'<div class="verdict-title-wrap"><div class="verdict-title balanced-headline" style="color: {verdict_color};">{verdict}</div></div>'
            f'<div class="status-pill {badge_cls} continuous-corner-sm">{badge_icon}<span>{badge_text}</span></div>'
            f'</div>'
            f'{meta_html}'
            f'<div class="verdict-stats-grid">'
            f'<div class="stat-card continuous-corner">'
            f'<div class="stat-label balanced-headline">Fraud score</div>'
            f'<div class="stat-value-row">'
            f'<span class="stat-value tabular-nums">{score:.1f}<span style="font-size:12px; color:#627d98; font-weight:500;"> / 100</span></span>'
            f'<span class="stat-subtext" style="color: {tier_col};">{tier_label}</span>'
            f'</div>'
            f'</div>'
            f'<div class="stat-card continuous-corner">'
            f'<div class="stat-label balanced-headline">Confidence</div>'
            f'<div class="stat-value-row">'
            f'<span class="stat-value tabular-nums">{confidence:.1f}%</span>'
            f'<span class="stat-subtext" style="color: #38bdf8;">{conf_label}</span>'
            f'</div>'
            f'</div>'
            f'<div class="stat-card continuous-corner">'
            f'<div class="stat-label balanced-headline">Agents in agreement</div>'
            f'<div class="stat-value-row">'
            f'<span class="stat-value tabular-nums">{consensus} <span style="font-size:12px; color:#627d98; font-weight:500;">of 3</span></span>'
            f'<div class="agent-dots-wrap">{dots_html}</div>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(card_markup, unsafe_allow_html=True)

        # 2. 4 Metric Cards
        b_score = analysis["behavior_score"]
        r_score = analysis["transaction_score"]
        a_score = analysis["anomaly_score"]
        v_score = analysis["velocity_score"]

        def get_metric_badge(val):
            if val < 35:
                return "Normal", "#00e676", "badge-normal"
            elif val < 70:
                return "Elevated", "#ffab00", "badge-elevated"
            else:
                return "High", "#ff1744", "badge-high"

        b_lbl, b_col, b_cls = get_metric_badge(b_score)
        r_lbl, r_col, r_cls = get_metric_badge(r_score)
        a_lbl, a_col, a_cls = get_metric_badge(a_score)
        v_lbl, v_col, v_cls = get_metric_badge(v_score)

        st.html(f"""
        <div class="metrics-grid">
          <div class="metric-card continuous-corner">
            <div class="metric-label balanced-headline">Behavior</div>
            <div class="metric-val tabular-nums">{b_score:.1f}</div>
            <div class="metric-bar-track">
              <div class="metric-bar-fill" style="width: {max(0.0, min(100.0, b_score))}%; background: {b_col};"></div>
            </div>
            <span class="badge {b_cls} continuous-corner-sm">{b_lbl}</span>
          </div>
          <div class="metric-card continuous-corner">
            <div class="metric-label balanced-headline">Risk</div>
            <div class="metric-val tabular-nums">{r_score:.1f}</div>
            <div class="metric-bar-track">
              <div class="metric-bar-fill" style="width: {max(0.0, min(100.0, r_score))}%; background: {r_col};"></div>
            </div>
            <span class="badge {r_cls} continuous-corner-sm">{r_lbl}</span>
          </div>
          <div class="metric-card continuous-corner">
            <div class="metric-label balanced-headline">Anomaly</div>
            <div class="metric-val tabular-nums">{a_score:.1f}</div>
            <div class="metric-bar-track">
              <div class="metric-bar-fill" style="width: {max(0.0, min(100.0, a_score))}%; background: {a_col};"></div>
            </div>
            <span class="badge {a_cls} continuous-corner-sm">{a_lbl}</span>
          </div>
          <div class="metric-card continuous-corner">
            <div class="metric-label balanced-headline">Velocity</div>
            <div class="metric-val tabular-nums">{v_score:.1f}</div>
            <div class="metric-bar-track">
              <div class="metric-bar-fill" style="width: {max(0.0, min(100.0, v_score))}%; background: {v_col};"></div>
            </div>
            <span class="badge {v_cls} continuous-corner-sm">{v_lbl}</span>
          </div>
        </div>
        """)

        # 3. Agent Network Diagram
        _st_components.html(
            _render_agent_network(analysis),
            height=580,
            scrolling=False,
        )

        # 4. Why this verdict HUD Card
        raw_indicators = analysis.get("indicators", []) or []
        formatted_indicators = []
        for it in raw_indicators:
            fmt = format_risk_indicator(it)
            if fmt and fmt not in formatted_indicators:
                formatted_indicators.append(fmt)

        if not formatted_indicators:
            why_body = """
            <div style="color: #00e676; font-family: 'JetBrains Mono', Consolas, monospace; font-size: 14px; margin-bottom: 14px;">
              <span style="font-weight: bold;">[ok]</span> No risk indicators found
            </div>
            <div class="safe-summary-box">
              No agent found meaningful risk. This transaction looks normal.
            </div>
            """
        else:
            items_html = "".join([
                f'<div class="risk-line"><span class="risk-tag">[!]</span> {html.escape(item)}</div>'
                for item in formatted_indicators
            ])
            why_body = f'<div class="risk-lines-container">{items_html}</div>'

        st.html(f"""
        <div class="hud-box continuous-corner">
          <div class="card-title balanced-headline">Why this verdict</div>
          {why_body}
        </div>
        """)

        # 5. Agent Accordions
        with st.expander("Agent 1: Behavior Analyzer", expanded=True):
            st.html(f"""
            <div class="agent-summary-text">{analysis.get('agent1_summary', '')}</div>
            """)

        with st.expander("Agent 2: Risk Assessor", expanded=True):
            st.html(f"""
            <div class="agent-summary-text">{analysis.get('agent2_summary', '')}</div>
            """)

        with st.expander("Agent 3: Transaction Validator", expanded=True):
            st.html(f"""
            <div class="agent-summary-text">{analysis.get('agent3_summary', '')}</div>
            """)

# ==================================================================
# TAB 2: HISTORY
# ==================================================================

with tab_history:
    with st.container(border=True, key="card_history"):
        h_col1, h_col2 = st.columns([8, 2])
        with h_col1:
            st.html('<div class="card-title balanced-headline">Analyzed this session</div>')
        with h_col2:
            if st.button("Clear history", use_container_width=True, key="btn_clear_hist"):
                st.session_state["history"] = []
                st.rerun()

        history_items = st.session_state.get("history", [])
        if not history_items:
            st.html('<div class="empty-history-text">No transactions analyzed in this session yet.</div>')
        else:
            rows_html = ""
            for item in history_items:
                v = item["verdict"]
                if v == "SAFE":
                    v_badge = '<span class="hist-badge hist-safe continuous-corner">SAFE</span>'
                elif v == "FRAUD":
                    v_badge = '<span class="hist-badge hist-fraud continuous-corner">FRAUD</span>'
                else:
                    v_badge = '<span class="hist-badge hist-suspicious continuous-corner">SUSPICIOUS</span>'

                rows_html += f"""
                <div class="hist-row continuous-corner">
                  <div class="hist-cell tabular-nums">{item['time']}</div>
                  <div class="hist-cell tabular-nums">{item['transaction']}</div>
                  <div class="hist-cell tabular-nums">{item['amount']}</div>
                  <div class="hist-cell tabular-nums">{item['score']}</div>
                  <div class="hist-cell">{v_badge}</div>
                </div>
                """

            st.html(f"""
            <div class="hist-table tabular-nums">
              <div class="hist-header balanced-headline">
                <div>Time</div>
                <div>Transaction</div>
                <div>Amount</div>
                <div>Score</div>
                <div>Verdict</div>
              </div>
              {rows_html}
            </div>
            """)





