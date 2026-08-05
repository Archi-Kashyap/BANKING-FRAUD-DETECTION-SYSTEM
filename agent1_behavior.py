import json
import os
import pandas as pd
from groq import Groq
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_FILE =  "Data/Digital_Payment_Fraud_Detection_Dataset.csv"
OUTPUT_FILE = "agent1_results.json"

# Agent 2 and Agent 3 are currently processing T1-T100.
# Agent 1 MUST process the same transactions.
NUMBER_OF_TRANSACTIONS = 100

MODEL_NAME = "llama-3.1-8b-instant"


# ============================================================
# GROQ SETUP
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found. "
        "Make sure it is present in your .env file."
    )

client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# LOAD DATASET
# ============================================================

print("=" * 70)
print("             AGENT 1 - BEHAVIOR ANALYZER")
print("=" * 70)

if not os.path.exists(DATASET_FILE):
    raise FileNotFoundError(
        f"Dataset not found: {DATASET_FILE}"
    )

df = pd.read_csv(DATASET_FILE)

print("\nDataset shape:", df.shape)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "transaction_id",
    "user_id",
    "transaction_amount",
    "transaction_type",
    "payment_mode",
    "device_type",
    "device_location",
    "account_age_days",
    "transaction_hour",
    "previous_failed_attempts",
    "avg_transaction_amount",
    "is_international",
    "ip_risk_score",
    "login_attempts_last_24h",
    "fraud_label"
]

missing_columns = [
    col
    for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns: {missing_columns}"
    )


# ============================================================
# IMPORTANT:
# USE SAME TRANSACTIONS AS AGENT 2 AND AGENT 3
# ============================================================

# Agent 2 and Agent 3 currently process T1-T100.
#
# Therefore Agent 1 also processes the first 100 rows.
#
# DO NOT use df.sample() here.

test_transactions = df.head(
    NUMBER_OF_TRANSACTIONS
).copy()

print(
    "\nTransactions selected:",
    len(test_transactions)
)

print(
    "First transaction:",
    test_transactions.iloc[0]["transaction_id"]
)

print(
    "Last transaction:",
    test_transactions.iloc[-1]["transaction_id"]
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_float(value, default=0.0):

    try:
        return float(value)
    except:
        return default


def calculate_amount_deviation(
    current_amount,
    historical_amount
):

    if historical_amount <= 0:
        return 0.0

    ratio = current_amount / historical_amount

    if ratio >= 3:
        return 1.0

    elif ratio >= 2:
        return 0.8

    elif ratio >= 1.5:
        return 0.5

    elif ratio >= 1.2:
        return 0.3

    else:
        return 0.0


def calculate_hour_deviation(
    current_hour,
    history
):

    if history.empty:
        return 0.3

    hours = history[
        "transaction_hour"
    ].dropna().tolist()

    if not hours:
        return 0.3

    # Find closest historical hour.
    differences = []

    for hour in hours:

        difference = abs(
            int(current_hour) - int(hour)
        )

        # Handle circular 24-hour clock
        difference = min(
            difference,
            24 - difference
        )

        differences.append(
            difference
        )

    minimum_difference = min(
        differences
    )

    if minimum_difference <= 1:
        return 0.0

    elif minimum_difference <= 3:
        return 0.3

    elif minimum_difference <= 6:
        return 0.6

    else:
        return 1.0


# ============================================================
# PROCESS TRANSACTIONS
# ============================================================

results = []

total = len(
    test_transactions
)


for position, (
    original_index,
    current
) in enumerate(
    test_transactions.iterrows(),
    start=1
):

    transaction_id = str(
        current["transaction_id"]
    )

    user_id = str(
        current["user_id"]
    )

    print(
        "\n" + "=" * 70
    )

    print(
        f"PROCESSING {position}/{total}"
    )

    print(
        "Transaction ID:",
        transaction_id
    )

    print(
        "User ID:",
        user_id
    )


    # ========================================================
    # USER HISTORY
    # ========================================================

    # IMPORTANT:
    # Only transactions belonging to this user.
    #
    # Also only transactions that occurred before
    # the current row in the dataset.
    #
    # This prevents future transactions from being used
    # as historical behavior.

    history = df[
        (df["user_id"] == current["user_id"])
        &
        (df.index < original_index)
    ].copy()


    print(
        "Historical transactions:",
        len(history)
    )


    # ========================================================
    # CURRENT VALUES
    # ========================================================

    current_amount = safe_float(
        current["transaction_amount"]
    )

    current_hour = int(
        safe_float(
            current["transaction_hour"]
        )
    )

    current_location = str(
        current["device_location"]
    )

    current_type = str(
        current["transaction_type"]
    )

    current_payment_mode = str(
        current["payment_mode"]
    )

    current_device = str(
        current["device_type"]
    )


    # ========================================================
    # NO HISTORY CASE
    # ========================================================

    if history.empty:

        behavior_score = 0.30

        risk_indicators = [
            "No historical transactions available"
        ]

        reasoning = (
            "This is the user's first available "
            "transaction in the dataset, so there is "
            "not enough historical behavior to establish "
            "a reliable behavioral baseline."
        )


    else:

        # ====================================================
        # HISTORICAL AVERAGE
        # ====================================================

        historical_average = safe_float(
            history[
                "transaction_amount"
            ].mean()
        )


        # ====================================================
        # AMOUNT DEVIATION
        # ====================================================

        amount_score = calculate_amount_deviation(
            current_amount,
            historical_average
        )


        # ====================================================
        # LOCATION DEVIATION
        # ====================================================

        historical_locations = set(
            history[
                "device_location"
            ]
            .dropna()
            .astype(str)
        )

        location_score = 0.0

        if current_location not in historical_locations:

            location_score = 1.0


        # ====================================================
        # TRANSACTION TYPE
        # ====================================================

        historical_types = set(
            history[
                "transaction_type"
            ]
            .dropna()
            .astype(str)
        )

        type_score = 0.0

        if current_type not in historical_types:

            type_score = 0.8


        # ====================================================
        # PAYMENT MODE
        # ====================================================

        historical_payment_modes = set(
            history[
                "payment_mode"
            ]
            .dropna()
            .astype(str)
        )

        payment_mode_score = 0.0

        if (
            current_payment_mode
            not in historical_payment_modes
        ):

            payment_mode_score = 0.7


        # ====================================================
        # DEVICE
        # ====================================================

        historical_devices = set(
            history[
                "device_type"
            ]
            .dropna()
            .astype(str)
        )

        device_score = 0.0

        if current_device not in historical_devices:

            device_score = 0.5


        # ====================================================
        # TRANSACTION HOUR
        # ====================================================

        hour_score = calculate_hour_deviation(
            current_hour,
            history
        )


        # ====================================================
        # COMBINED BEHAVIOR SCORE
        # ====================================================

        behavior_score = (

            amount_score * 0.30

            +

            location_score * 0.20

            +

            type_score * 0.15

            +

            payment_mode_score * 0.10

            +

            device_score * 0.10

            +

            hour_score * 0.15

        )


        behavior_score = round(
            max(
                0.0,
                min(
                    1.0,
                    behavior_score
                )
            ),
            2
        )


        # ====================================================
        # RISK INDICATORS
        # ====================================================

        risk_indicators = []


        if amount_score >= 0.5:

            risk_indicators.append(
                "High transaction amount deviation"
            )


        if location_score > 0:

            risk_indicators.append(
                "Different transaction location"
            )


        if type_score > 0:

            risk_indicators.append(
                "Different transaction type"
            )


        if payment_mode_score > 0:

            risk_indicators.append(
                "Different payment mode"
            )


        if device_score > 0:

            risk_indicators.append(
                "Different device"
            )


        if hour_score >= 0.6:

            risk_indicators.append(
                "Unusual transaction hour"
            )


        if not risk_indicators:

            risk_indicators.append(
                "No major behavioral deviation detected"
            )


        # ====================================================
        # REASONING
        # ====================================================

        reasoning_parts = []


        if amount_score >= 0.5:

            reasoning_parts.append(
                "The transaction amount differs "
                "significantly from the user's historical "
                "transaction behavior."
            )


        if location_score > 0:

            reasoning_parts.append(
                "The transaction is occurring in a "
                "location not previously observed for "
                "this user."
            )


        if type_score > 0:

            reasoning_parts.append(
                "The transaction type differs from "
                "the user's previous transaction types."
            )


        if payment_mode_score > 0:

            reasoning_parts.append(
                "The payment mode differs from the "
                "user's previous payment modes."
            )


        if device_score > 0:

            reasoning_parts.append(
                "The device type differs from the "
                "user's previous device usage."
            )


        if hour_score >= 0.6:

            reasoning_parts.append(
                "The transaction occurs at an unusual "
                "time compared with the user's history."
            )


        if not reasoning_parts:

            reasoning_parts.append(
                "The transaction is generally consistent "
                "with the user's historical behavior."
            )


        reasoning = " ".join(
            reasoning_parts
        )


    # ========================================================
    # RESULT
    # ========================================================

    result = {

        "behavior_score":
            behavior_score,

        "risk_indicators":
            risk_indicators,

        "reasoning":
            reasoning,

        "transaction_id":
            transaction_id,

        "user_id":
            user_id,

        "agent":
            "behavior_analyzer",

        "historical_transaction_count":
            int(len(history))

    }


    results.append(
        result
    )


# ============================================================
# SAVE RESULTS
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
# FINAL SUMMARY
# ============================================================

print(
    "\n" + "=" * 70
)

print(
    "             AGENT 1 COMPLETE"
)

print(
    "=" * 70
)

print(
    "Successfully processed:",
    len(results)
)

print(
    "Saved:",
    OUTPUT_FILE
)

print(
    "First ID:",
    results[0]["transaction_id"]
)

print(
    "Last ID:",
    results[-1]["transaction_id"]
)

print(
    "=" * 70
)