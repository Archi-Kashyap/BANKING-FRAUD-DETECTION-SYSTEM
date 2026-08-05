import pandas as pd
from groq import Groq
from dotenv import load_dotenv
import os


# ============================================================
# 1. GROQ SETUP
# ============================================================

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL_NAME = "llama-3.1-8b-instant"


# ============================================================
# 2. LOAD DATASET
# ============================================================

df = pd.read_csv(
    "Data/Digital_Payment_Fraud_Detection_Dataset.csv"
)

print("Dataset shape:", df.shape)


# ============================================================
# 3. FIND 10 TRANSACTIONS WITH PREVIOUS USER HISTORY
# ============================================================

selected_transactions = []

for i in range(1, len(df)):

    current_user = df.iloc[i]["user_id"]

    previous_data = df.iloc[:i]

    user_history = previous_data[
        previous_data["user_id"] == current_user
    ]

    if len(user_history) > 0:

        selected_transactions.append(i)

    if len(selected_transactions) == 10:
        break


print("\nSelected transaction indexes:")
print(selected_transactions)


# ============================================================
# 4. PROCESS EACH TRANSACTION
# ============================================================

for count, current_index in enumerate(selected_transactions, start=1):

    print("\n")
    print("=" * 70)
    print(f"TRANSACTION {count}/10")
    print("=" * 70)

    current_transaction = df.iloc[current_index]

    user_id = current_transaction["user_id"]

    # Only transactions BEFORE current transaction
    previous_data = df.iloc[:current_index]

    user_history = previous_data[
        previous_data["user_id"] == user_id
    ]

    # --------------------------------------------------------
    # Relevant behavior features
    # --------------------------------------------------------

    behavior_columns = [
        "transaction_id",
        "transaction_amount",
        "transaction_type",
        "payment_mode",
        "device_location",
        "transaction_hour"
    ]

    history_text = user_history[
        behavior_columns
    ].to_string(index=False)

    current_text = current_transaction[
        behavior_columns
    ].to_string()


    # ========================================================
    # 5. CREATE AGENT 1 PROMPT
    # ========================================================

    prompt = f"""
You are Agent 1: Behavior Analyzer.

Your task is ONLY to analyze behavioral deviation
of the current UPI transaction compared with
the user's previous transactions.

Do NOT make the final fraud decision.

Previous transactions:

{history_text}


Current transaction:

{current_text}


Analyze:

1. Transaction amount
2. Transaction timing
3. Transaction location
4. Transaction type
5. Payment mode
6. Overall behavioral deviation

Important:

- Use only the provided data.
- Do not invent information.
- Compare the current transaction with historical behavior.
- Unusual behavior does NOT automatically mean fraud.
- Behavior score represents behavioral deviation only.

Return:

Behavior Score: <0 to 1>

Risk Indicators:
- ...
- ...
- ...

Reasoning:
...

Final Note:
Behavior analysis only. Not a final fraud decision.
"""


    # ========================================================
    # 6. CALL GROQ
    # ========================================================

    response = client.chat.completions.create(

        model=MODEL_NAME,

        messages=[
            {
                "role": "system",
                "content": "You are a careful Behavior Analyzer Agent."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0
    )


    # ========================================================
    # 7. DISPLAY RESULT
    # ========================================================

    result = response.choices[0].message.content

    print("\nCurrent Transaction:")
    print(current_transaction[behavior_columns])

    print("\nPrevious History:")
    print(user_history[behavior_columns])

    print("\n----- AGENT 1 RESULT -----")
    print(result)