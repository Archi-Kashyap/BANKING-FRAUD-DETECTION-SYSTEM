import pandas as pd
import json
import os
import time
from groq import Groq
from dotenv import load_dotenv

# ============================================================
# CONFIG
# ============================================================

DATASET_PATH = "Data/Digital_Payment_Fraud_Detection_Dataset.csv"
OUTPUT_FILE = "agent3_results.json"

MAX_TRANSACTIONS = None

LLM_EXPLANATIONS = 20

MODEL_NAME = "qwen/qwen3.8-27b"

LLM_CALL_PAUSE_SECONDS = 8


# ============================================================
# GROQ
# ============================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY not found in .env"
    )

client = Groq(
    api_key=api_key
)


# ============================================================
# LOAD
# ============================================================

df = pd.read_csv(
    DATASET_PATH
)

if MAX_TRANSACTIONS:
    df = df.head(
        MAX_TRANSACTIONS
    )


print("=" * 70)
print("          AGENT 3 - TRANSACTION VALIDATOR")
print("=" * 70)

print(
    "Dataset shape:",
    df.shape
)


# ============================================================
# RESULTS
# ============================================================

results = []


# ============================================================
# PROCESS
# ============================================================

for index, row in df.iterrows():

    transaction_id = row[
        "transaction_id"
    ]

    user_id = row[
        "user_id"
    ]


    # ========================================================
    # AMOUNT
    # ========================================================

    amount = float(
        row["transaction_amount"]
    )

    avg_amount = float(
        row.get(
            "avg_transaction_amount",
            0
        )
    )


    if avg_amount > 0:

        amount_ratio = (
            amount / avg_amount
        )

    else:

        amount_ratio = 1.0


    amount_difference = (
        amount - avg_amount
    )


    # ========================================================
    # AMOUNT ANOMALY
    # ========================================================

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


    # ========================================================
    # FAILED ATTEMPTS
    # ========================================================

    failed = float(
        row.get(
            "previous_failed_attempts",
            0
        )
    )


    if failed >= 5:

        failed_risk = 1.0

    elif failed >= 3:

        failed_risk = 0.7

    elif failed >= 1:

        failed_risk = 0.3

    else:

        failed_risk = 0.0


    # ========================================================
    # LOGIN ATTEMPTS
    # ========================================================

    login = float(
        row.get(
            "login_attempts_last_24h",
            0
        )
    )


    if login >= 8:

        login_risk = 1.0

    elif login >= 5:

        login_risk = 0.7

    elif login >= 2:

        login_risk = 0.3

    else:

        login_risk = 0.0


    # ========================================================
    # INTERNATIONAL
    # ========================================================

    international = int(
        row.get(
            "is_international",
            0
        )
    )

    international_risk = (
        1.0
        if international
        else 0.0
    )


    # ========================================================
    # ANOMALY SCORE
    # ========================================================

    anomaly_score = (

        0.70 * amount_anomaly

        +

        0.30 * international_risk
    )


    # ========================================================
    # VELOCITY SCORE
    # ========================================================

    velocity_score = (

        0.55 * failed_risk

        +

        0.45 * login_risk
    )


    anomaly_score = round(
        min(1.0, anomaly_score),
        3
    )

    velocity_score = round(
        min(1.0, velocity_score),
        3
    )


    # ========================================================
    # INDICATORS
    # ========================================================

    indicators = []


    if amount_anomaly > 0:

        indicators.append({
            "indicator":
                "Transaction amount anomaly",

            "score":
                amount_anomaly,

            "description":
                f"Amount is {amount_ratio:.2f} "
                "times the average."
        })


    if failed_risk > 0:

        indicators.append({
            "indicator":
                "Failed transaction attempts",

            "score":
                failed_risk,

            "description":
                f"{int(failed)} failed attempts."
        })


    if login_risk > 0:

        indicators.append({
            "indicator":
                "Login attempts",

            "score":
                login_risk,

            "description":
                f"{int(login)} login attempts."
        })


    if international:

        indicators.append({
            "indicator":
                "International transaction",

            "score":
                international_risk,

            "description":
                "Transaction is international."
        })


    # ========================================================
    # RESULT
    # ========================================================

    result = {

        "transaction_id":
            transaction_id,

        "user_id":
            user_id,

        "agent":
            "transaction_validator",

        "anomaly_score":
            anomaly_score,

        "velocity_score":
            velocity_score,

        "amount_ratio":
            round(
                amount_ratio,
                3
            ),

        "amount_difference":
            round(
                amount_difference,
                2
            ),

        "risk_indicators":
            indicators,

        "reasoning":
            "Transaction anomaly and velocity scores calculated using deterministic rules."
    }


    # ========================================================
    # OPTIONAL GROQ
    # ========================================================

    if len(results) < LLM_EXPLANATIONS:

        try:

            prompt = f"""
You are the Transaction Validator in a fraud detection system.

Explain these findings briefly.

Amount ratio:
{amount_ratio:.2f}

Amount anomaly:
{amount_anomaly}

Failed attempt risk:
{failed_risk}

Login risk:
{login_risk}

International:
{international}

Anomaly score:
{anomaly_score}

Velocity score:
{velocity_score}

Do not change the scores.
Do not make a final fraud decision.

Return a short explanation.
"""

            # Retry on rate-limit (429) errors, honoring Groq's
            # retry-after header, then pace the next call so the
            # tokens-per-minute limit is not exceeded.

            for attempt in range(6):

                try:

                    response = client.chat.completions.create(

                        model=MODEL_NAME,

                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],

                        temperature=0
                    )

                    result["llm_reasoning"] = (
                        response
                        .choices[0]
                        .message
                        .content
                    )

                    break

                except Exception as e:

                    if getattr(e, "status_code", None) != 429 or attempt >= 5:
                        raise

                    retry_after = 0.0

                    try:

                        retry_after = float(
                            e.response.headers.get("retry-after", 0) or 0
                        )

                    except Exception:

                        retry_after = 0.0

                    time.sleep(
                        max(retry_after, min(15 * (2 ** attempt), 60))
                    )

            time.sleep(LLM_CALL_PAUSE_SECONDS)

        except:

            result["llm_reasoning"] = (
                "LLM explanation unavailable."
            )


    results.append(
        result
    )


    if (index + 1) % 500 == 0:

        print(
            f"Processed {index + 1}/{len(df)}"
        )


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


print("\n" + "=" * 70)
print("             AGENT 3 COMPLETE")
print("=" * 70)

print(
    "Successfully processed:",
    len(results)
)

print(
    "Saved:",
    OUTPUT_FILE
)

print("=" * 70)

