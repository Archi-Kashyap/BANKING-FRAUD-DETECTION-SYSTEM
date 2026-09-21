# # import pandas as pd
# # from groq import Groq
# # from dotenv import load_dotenv
# # import os
# # import json
# # import time


# # # ============================================================
# # # GROQ SETUP
# # # ============================================================

# # load_dotenv()

# # api_key = os.getenv("GROQ_API_KEY")

# # if not api_key:
# #     raise ValueError("GROQ_API_KEY not found in .env")

# # client = Groq(api_key=api_key)

# # MODEL_NAME = "qwen/qwen3.8-27b"


# # # ============================================================
# # # LOAD DATASET
# # # ============================================================

# # DATASET_PATH = "Data/Digital_Payment_Fraud_Detection_Dataset.csv"

# # df = pd.read_csv(DATASET_PATH)

# # print("=" * 70)
# # print("          AGENT 3 - TRANSACTION VALIDATOR")
# # print("=" * 70)

# # print("\nDataset shape:", df.shape)


# # # ============================================================
# # # CHECK REQUIRED COLUMNS
# # # ============================================================

# # required_columns = [
# #     "transaction_id",
# #     "user_id",
# #     "transaction_amount",
# #     "avg_transaction_amount",
# #     "amount_ratio",
# #     "amount_difference",
# #     "previous_failed_attempts",
# #     "login_attempts_last_24h",
# #     "is_international"
# # ]

# # missing = [
# #     col for col in required_columns
# #     if col not in df.columns
# # ]

# # if missing:
# #     raise ValueError(
# #         f"Missing columns: {missing}"
# #     )


# # # ============================================================
# # # AGENT 3 PYTHON ANALYSIS
# # # ============================================================

# # def calculate_validator_scores(transaction):

# #     # --------------------------------------------------------
# #     # 1. AMOUNT ANOMALY
# #     # --------------------------------------------------------

# #     current_amount = float(
# #         transaction["transaction_amount"]
# #     )

# #     average_amount = float(
# #         transaction["avg_transaction_amount"]
# #     )

# #     if average_amount > 0:
# #         amount_ratio = (
# #             current_amount / average_amount
# #         )
# #     else:
# #         amount_ratio = 1.0


# #     # Amount anomaly score
# #     if amount_ratio >= 3:
# #         amount_anomaly = 1.0

# #     elif amount_ratio >= 2:
# #         amount_anomaly = 0.8

# #     elif amount_ratio >= 1.5:
# #         amount_anomaly = 0.5

# #     elif amount_ratio <= 0.3:
# #         amount_anomaly = 0.7

# #     elif amount_ratio <= 0.5:
# #         amount_anomaly = 0.4

# #     else:
# #         amount_anomaly = 0.0


# #     # --------------------------------------------------------
# #     # 2. FAILED ATTEMPTS
# #     # --------------------------------------------------------

# #     failed_attempts = float(
# #         transaction["previous_failed_attempts"]
# #     )

# #     if failed_attempts >= 5:
# #         failed_risk = 1.0

# #     elif failed_attempts >= 3:
# #         failed_risk = 0.7

# #     elif failed_attempts >= 1:
# #         failed_risk = 0.3

# #     else:
# #         failed_risk = 0.0


# #     # --------------------------------------------------------
# #     # 3. LOGIN ATTEMPTS
# #     # --------------------------------------------------------

# #     login_attempts = float(
# #         transaction["login_attempts_last_24h"]
# #     )

# #     if login_attempts >= 5:
# #         login_risk = 1.0

# #     elif login_attempts >= 3:
# #         login_risk = 0.7

# #     elif login_attempts >= 1:
# #         login_risk = 0.3

# #     else:
# #         login_risk = 0.0


# #     # --------------------------------------------------------
# #     # 4. INTERNATIONAL
# #     # --------------------------------------------------------

# #     international = int(
# #         transaction["is_international"]
# #     )

# #     international_risk = (
# #         1.0 if international == 1 else 0.0
# #     )


# #     # --------------------------------------------------------
# #     # FINAL ANOMALY SCORE
# #     # --------------------------------------------------------

# #     anomaly_score = (
# #         0.70 * amount_anomaly
# #         + 0.15 * international_risk
# #         + 0.15 * failed_risk
# #     )


# #     # --------------------------------------------------------
# #     # FINAL VELOCITY SCORE
# #     # --------------------------------------------------------

# #     velocity_score = (
# #         0.60 * failed_risk
# #         + 0.40 * login_risk
# #     )


# #     return {
# #         "amount_ratio": round(
# #             amount_ratio, 3
# #         ),

# #         "amount_anomaly": round(
# #             amount_anomaly, 3
# #         ),

# #         "failed_attempt_risk": round(
# #             failed_risk, 3
# #         ),

# #         "login_attempt_risk": round(
# #             login_risk, 3
# #         ),

# #         "international_risk": round(
# #             international_risk, 3
# #         ),

# #         "anomaly_score": round(
# #             min(1.0, anomaly_score), 3
# #         ),

# #         "velocity_score": round(
# #             min(1.0, velocity_score), 3
# #         )
# #     }


# # # ============================================================
# # # PROCESS 100 TRANSACTIONS
# # # ============================================================

# # results = []

# # total = min(
# #     100,
# #     len(df)
# # )


# # for index in range(total):

# #     transaction = df.iloc[index]

# #     transaction_id = transaction[
# #         "transaction_id"
# #     ]

# #     user_id = transaction[
# #         "user_id"
# #     ]


# #     print("\n")
# #     print("=" * 70)

# #     print(
# #         f"PROCESSING TRANSACTION "
# #         f"{index + 1}/{total}"
# #     )

# #     print(
# #         "Transaction ID:",
# #         transaction_id
# #     )

# #     print(
# #         "User ID:",
# #         user_id
# #     )


# #     # ========================================================
# #     # PYTHON ANALYSIS
# #     # ========================================================

# #     scores = calculate_validator_scores(
# #         transaction
# #     )


# #     print("\n----- PYTHON VALIDATION -----")

# #     print(
# #         json.dumps(
# #             scores,
# #             indent=4
# #         )
# #     )


# #     # ========================================================
# #     # GROQ ANALYSIS
# #     # ========================================================

# #     prompt = f"""
# # You are Agent 3: Transaction Validator
# # in a multi-agent UPI fraud detection system.

# # Your role is to analyze transaction-level anomalies
# # and suspicious activity velocity.

# # Python has already calculated the numerical scores.

# # IMPORTANT:

# # Do NOT change the scores.

# # Do NOT make the final fraud decision.

# # Do NOT invent information.

# # CURRENT TRANSACTION:

# # {transaction.to_string()}


# # PYTHON ANALYSIS:

# # {json.dumps(scores, indent=4)}


# # Explain briefly:

# # 1. Whether the transaction amount is unusual.
# # 2. Whether failed attempts indicate suspicious activity.
# # 3. Whether login attempts indicate suspicious activity.
# # 4. Whether international status contributes to risk.
# # 5. Overall transaction anomaly.
# # 6. Overall velocity risk.

# # Return ONLY valid JSON:

# # {{
# #     "anomaly_score": {scores["anomaly_score"]},
# #     "velocity_score": {scores["velocity_score"]},
# #     "risk_indicators": [],
# #     "reasoning": "short factual explanation"
# # }}

# # Do not include markdown.
# # """


# #     try:

# #         response = client.chat.completions.create(

# #             model=MODEL_NAME,

# #             messages=[
# #                 {
# #                     "role": "system",
# #                     "content": (
# #                         "You are Agent 3, "
# #                         "Transaction Validator."
# #                     )
# #                 },
# #                 {
# #                     "role": "user",
# #                     "content": prompt
# #                 }
# #             ],

# #             temperature=0,

# #             response_format={
# #                 "type": "json_object"
# #             }
# #         )


# #         groq_result = json.loads(
# #             response
# #             .choices[0]
# #             .message
# #             .content
# #         )


# #         # ====================================================
# #         # PYTHON IS SOURCE OF TRUTH
# #         # ====================================================

# #         groq_result[
# #             "anomaly_score"
# #         ] = scores[
# #             "anomaly_score"
# #         ]

# #         groq_result[
# #             "velocity_score"
# #         ] = scores[
# #             "velocity_score"
# #         ]

# #         groq_result[
# #             "transaction_id"
# #         ] = transaction_id

# #         groq_result[
# #             "user_id"
# #         ] = user_id

# #         groq_result[
# #             "agent"
# #         ] = "transaction_validator"


# #         results.append(
# #             groq_result
# #         )


# #         print("\n----- AGENT 3 RESULT -----")

# #         print(
# #             json.dumps(
# #                 groq_result,
# #                 indent=4
# #             )
# #         )


# #     except Exception as e:

# #         print(
# #             "\nERROR processing:",
# #             transaction_id
# #         )

# #         print(
# #             "Error:",
# #             e
# #         )


# #     # Small delay to avoid hitting rate limits
# #     time.sleep(0.5)


# # # ============================================================
# # # SAVE RESULTS
# # # ============================================================

# # with open(
# #     "agent3_results.json",
# #     "w",
# #     encoding="utf-8"
# # ) as f:

# #     json.dump(
# #         results,
# #         f,
# #         indent=4,
# #         ensure_ascii=False
# #     )


# # print("\n")
# # print("=" * 70)
# # print("             AGENT 3 COMPLETE")
# # print("=" * 70)

# # print(
# #     "Successfully processed:",
# #     len(results)
# # )

# # print(
# #     "Saved: agent3_results.json"
# # )

# import pandas as pd
# from groq import Groq
# from dotenv import load_dotenv
# import os
# import json
# import time


# # ============================================================
# # 1. GROQ SETUP
# # ============================================================

# load_dotenv()

# api_key = os.getenv("GROQ_API_KEY")

# if not api_key:
#     raise ValueError("GROQ_API_KEY not found in .env")

# client = Groq(api_key=api_key)

# # Updated model
# MODEL_NAME = "qwen/qwen3.8-27b"


# # ============================================================
# # 2. LOAD DATASET
# # ============================================================

# DATASET_PATH = "Data/Digital_Payment_Fraud_Detection_Dataset.csv"

# df = pd.read_csv(DATASET_PATH)

# print("=" * 70)
# print("          AGENT 3 - TRANSACTION VALIDATOR")
# print("=" * 70)

# print("\nDataset shape:", df.shape)


# # ============================================================
# # 3. CHECK REQUIRED COLUMNS
# # ============================================================

# required_columns = [
#     "transaction_id",
#     "user_id",
#     "transaction_amount",
#     "avg_transaction_amount",
#     "previous_failed_attempts",
#     "login_attempts_last_24h",
#     "is_international"
# ]

# missing = [
#     col for col in required_columns
#     if col not in df.columns
# ]

# if missing:
#     raise ValueError(
#         f"Missing columns: {missing}"
#     )


# # ============================================================
# # 4. CALCULATE AGENT 3 SCORES
# # ============================================================

# def calculate_validator_scores(transaction):

#     # --------------------------------------------------------
#     # A. TRANSACTION AMOUNT
#     # --------------------------------------------------------

#     current_amount = float(
#         transaction["transaction_amount"]
#     )

#     average_amount = float(
#         transaction["avg_transaction_amount"]
#     )

#     if average_amount > 0:

#         amount_ratio = (
#             current_amount / average_amount
#         )

#     else:

#         amount_ratio = 1.0


#     # --------------------------------------------------------
#     # B. AMOUNT ANOMALY
#     # --------------------------------------------------------

#     if amount_ratio >= 3:

#         amount_anomaly = 1.0

#     elif amount_ratio >= 2:

#         amount_anomaly = 0.8

#     elif amount_ratio >= 1.5:

#         amount_anomaly = 0.5

#     elif amount_ratio <= 0.3:

#         amount_anomaly = 0.7

#     elif amount_ratio <= 0.5:

#         amount_anomaly = 0.4

#     else:

#         amount_anomaly = 0.0


#     # --------------------------------------------------------
#     # C. FAILED ATTEMPTS
#     # --------------------------------------------------------

#     failed_attempts = float(
#         transaction["previous_failed_attempts"]
#     )

#     if failed_attempts >= 5:

#         failed_risk = 1.0

#     elif failed_attempts >= 3:

#         failed_risk = 0.7

#     elif failed_attempts >= 1:

#         failed_risk = 0.3

#     else:

#         failed_risk = 0.0


#     # --------------------------------------------------------
#     # D. LOGIN ATTEMPTS
#     # --------------------------------------------------------

#     login_attempts = float(
#         transaction["login_attempts_last_24h"]
#     )

#     if login_attempts >= 5:

#         login_risk = 1.0

#     elif login_attempts >= 3:

#         login_risk = 0.7

#     elif login_attempts >= 1:

#         login_risk = 0.3

#     else:

#         login_risk = 0.0


#     # --------------------------------------------------------
#     # E. INTERNATIONAL TRANSACTION
#     # --------------------------------------------------------

#     international = int(
#         transaction["is_international"]
#     )

#     if international == 1:

#         international_risk = 1.0

#     else:

#         international_risk = 0.0


#     # --------------------------------------------------------
#     # F. ANOMALY SCORE
#     # --------------------------------------------------------

#     anomaly_score = (
#         0.70 * amount_anomaly
#         + 0.15 * international_risk
#         + 0.15 * failed_risk
#     )


#     # --------------------------------------------------------
#     # G. VELOCITY SCORE
#     # --------------------------------------------------------

#     velocity_score = (
#         0.60 * failed_risk
#         + 0.40 * login_risk
#     )


#     # --------------------------------------------------------
#     # H. LIMIT SCORES TO 0-1
#     # --------------------------------------------------------

#     anomaly_score = min(
#         1.0,
#         max(0.0, anomaly_score)
#     )

#     velocity_score = min(
#         1.0,
#         max(0.0, velocity_score)
#     )


#     # --------------------------------------------------------
#     # I. RETURN RESULTS
#     # --------------------------------------------------------

#     return {

#         "amount_ratio": round(
#             amount_ratio,
#             3
#         ),

#         "amount_anomaly": round(
#             amount_anomaly,
#             3
#         ),

#         "failed_attempt_risk": round(
#             failed_risk,
#             3
#         ),

#         "login_attempt_risk": round(
#             login_risk,
#             3
#         ),

#         "international_risk": round(
#             international_risk,
#             3
#         ),

#         "anomaly_score": round(
#             anomaly_score,
#             3
#         ),

#         "velocity_score": round(
#             velocity_score,
#             3
#         )
#     }


# # ============================================================
# # 5. PROCESS TRANSACTIONS
# # ============================================================

# results = []

# # For testing, process 100 transactions first.
# # Later we will change this to the full dataset.

# total = min(
#     100,
#     len(df)
# )


# for index in range(total):

#     transaction = df.iloc[index]

#     transaction_id = transaction[
#         "transaction_id"
#     ]

#     user_id = transaction[
#         "user_id"
#     ]


#     print("\n")
#     print("=" * 70)

#     print(
#         f"PROCESSING TRANSACTION "
#         f"{index + 1}/{total}"
#     )

#     print(
#         "Transaction ID:",
#         transaction_id
#     )

#     print(
#         "User ID:",
#         user_id
#     )


#     # ========================================================
#     # PYTHON ANALYSIS
#     # ========================================================

#     scores = calculate_validator_scores(
#         transaction
#     )


#     print(
#         "\n----- PYTHON VALIDATION -----"
#     )

#     print(
#         json.dumps(
#             scores,
#             indent=4
#         )
#     )


#     # ========================================================
#     # 6. GROQ PROMPT
#     # ========================================================

#     prompt = f"""
# You are Agent 3: Transaction Validator
# in a multi-agent UPI fraud detection system.

# Your role is to analyze transaction-level anomalies
# and suspicious activity.

# Python has already calculated the numerical scores.

# IMPORTANT RULES:

# 1. Do NOT change the numerical scores.
# 2. Do NOT make the final fraud decision.
# 3. Do NOT invent information.
# 4. Only explain the information provided.
# 5. Keep the explanation concise.

# CURRENT TRANSACTION:

# {transaction.to_string()}


# PYTHON ANALYSIS:

# {json.dumps(scores, indent=4)}


# Analyze:

# 1. Transaction amount anomaly
# 2. Failed transaction attempts
# 3. Login attempts
# 4. International transaction status
# 5. Overall anomaly
# 6. Overall velocity risk

# Return ONLY valid JSON in this format:

# {{
#     "anomaly_score": {scores["anomaly_score"]},
#     "velocity_score": {scores["velocity_score"]},
#     "risk_indicators": [],
#     "reasoning": "short factual explanation"
# }}

# Do not include markdown.
# """


#     # ========================================================
#     # 7. CALL GROQ
#     # ========================================================

#     try:

#         response = client.chat.completions.create(

#             model=MODEL_NAME,

#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are Agent 3, "
#                         "Transaction Validator "
#                         "for a UPI fraud detection system."
#                     )
#                 },
#                 {
#                     "role": "user",
#                     "content": prompt
#                 }
#             ],

#             temperature=0,

#             response_format={
#                 "type": "json_object"
#             }
#         )


#         # ====================================================
#         # 8. READ GROQ RESPONSE
#         # ====================================================

#         groq_result = json.loads(
#             response
#             .choices[0]
#             .message
#             .content
#         )


#         # ====================================================
#         # 9. PYTHON IS SOURCE OF TRUTH
#         # ====================================================

#         groq_result[
#             "anomaly_score"
#         ] = scores[
#             "anomaly_score"
#         ]

#         groq_result[
#             "velocity_score"
#         ] = scores[
#             "velocity_score"
#         ]

#         groq_result[
#             "transaction_id"
#         ] = transaction_id

#         groq_result[
#             "user_id"
#         ] = user_id

#         groq_result[
#             "agent"
#         ] = "transaction_validator"


#         # Add raw Python values too
#         groq_result[
#             "python_analysis"
#         ] = scores


#         results.append(
#             groq_result
#         )


#         # ====================================================
#         # 10. DISPLAY RESULT
#         # ====================================================

#         print(
#             "\n----- AGENT 3 RESULT -----"
#         )

#         print(
#             json.dumps(
#                 groq_result,
#                 indent=4
#             )
#         )


#     except Exception as e:

#         print(
#             "\nERROR processing:",
#             transaction_id
#         )

#         print(
#             "Error:",
#             e
#         )


#     # Small delay
#     time.sleep(0.5)


# # ============================================================
# # 11. SAVE RESULTS
# # ============================================================

# with open(
#     "agent3_results.json",
#     "w",
#     encoding="utf-8"
# ) as f:

#     json.dump(
#         results,
#         f,
#         indent=4,
#         ensure_ascii=False
#     )


# # ============================================================
# # 12. FINAL MESSAGE
# # ============================================================

# print("\n")
# print("=" * 70)
# print("             AGENT 3 COMPLETE")
# print("=" * 70)

# print(
#     "Successfully processed:",
#     len(results)
# )

# print(
#     "Saved: agent3_results.json"
# )

# print("=" * 70)


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

