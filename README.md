# Banking Fraud Detection — Multi-Agent System

A **multi-agent AI pipeline** for detecting fraudulent digital payment transactions.  
The system combines **behavioral analysis**, **ML-assisted risk scoring**, **rule-based validation**, and **decision synthesis** across four specialized agents.

---

## Table of Contents

1. [Project Objective](#1-project-objective)
2. [Problem Statement](#2-problem-statement)
3. [Architecture](#3-architecture)
4. [Agents](#4-agents)
5. [Dataset](#5-dataset)
6. [ML Methodology & Honest Signal Report](#6-ml-methodology--honest-signal-report)
7. [Behavioral Risk Scoring](#7-behavioral-risk-scoring)
8. [Hybrid Scoring](#8-hybrid-scoring)
9. [Risk Levels](#9-risk-levels)
10. [Installation](#10-installation)
11. [How to Run](#11-how-to-run)
12. [Output Files](#12-output-files)
13. [Testing / Validation](#13-testing--validation)
14. [Reproducibility](#14-reproducibility)
15. [Limitations](#15-limitations)
16. [Future Improvements](#16-future-improvements)

---

## 1. Project Objective

Build a production-grade, explainable, reproducible multi-agent fraud detection system for digital payment transactions that:

- **Honestly** represents ML predictive capability
- **Transparently** scores risk using interpretable behavioral rules
- **Correctly** synthesizes multiple independent agent signals
- **Never** fabricates metrics or modifies ground-truth labels

---

## 2. Problem Statement

Digital payment fraud is a significant and growing challenge.  
Traditional single-model approaches struggle with:

- Severely imbalanced class distributions (fraud is rare)
- Weak or unavailable fraud signal in transaction-level features
- Lack of explainability in model decisions
- Brittleness when retraining on small fraud samples

This system addresses these challenges by combining:

- **LLM-assisted behavioral analysis** (Agent 1)
- **Transparent, deterministic behavioral risk scoring with ML support** (Agent 2)
- **Deterministic rule-based transaction validation** (Agent 3)
- **Multi-agent consensus synthesis** (Agent 4)

---

## 3. Architecture

```
Dataset (7,500 transactions)
         │
         ├──────────────────────────────────┐
         │                                  │
    [Agent 1]                          [Agent 2]
  Behavior Analyzer                  Risk Assessor
  (first 100 txns)                  (all 7,500 txns)
  Uses Groq LLM                     Uses ML + domain rules
         │                                  │
         │                          [Agent 3]
         │                     Transaction Validator
         │                         (all 7,500 txns)
         │                    Deterministic anomaly rules
         │                                  │
         └──────────────┬───────────────────┘
                        │
                   [Agent 4]
               Decision Synthesizer
          (100 txns present in Agent 1)
          Combines all three agents
                        │
               [Evaluation System]
              Compares predictions vs
              ground-truth fraud_label
                        │
             system_evaluation.csv
```

**Why Agent 1 processes 100 and Agent 2/3 process 7,500:**

Agent 1 calls a real LLM (Groq) for each transaction to generate behavioral narratives.  
Processing 7,500 transactions per run would be slow and incur significant API costs.  
Therefore Agent 1 is designed to analyze the first 100 transactions for demonstration.  
Agent 2 and Agent 3 run on the full dataset to produce complete risk models.  
Agent 4 synthesizes results only for the 100 transactions processed by all agents.  
This is an **intentional architectural design decision**, not an accidental truncation.

---

## 4. Agents

### Agent 1 — Behavior Analyzer (`agent1_behavior.py`)

**Input:** `Data/Digital_Payment_Fraud_Detection_Dataset.csv` (first 100 rows)  
**Output:** `agent1_results.json`

**Role:** Analyzes each transaction against the same user's historical transactions  
(earlier rows in the dataset) to identify behavioral deviations.

**What it computes:**
- Amount deviation from user historical average
- Location deviation (new vs. seen location)
- Transaction type deviation
- Payment mode deviation
- Device deviation
- Time-of-day deviation

**Output per transaction:**
```json
{
  "transaction_id": "T1",
  "user_id": "U3756",
  "agent": "behavior_analyzer",
  "behavior_score": 0.30,
  "risk_indicators": ["..."],
  "reasoning": "...",
  "historical_transaction_count": 0
}
```

**Note:** `behavior_score` is on a `[0.0, 1.0]` scale, where 1.0 = maximum behavioral deviation.

---

### Agent 2 — Risk Assessor (`agent2_risk_v4.py`)

**Input:** `Data/Digital_Payment_Fraud_Detection_Dataset.csv` (all 7,500 rows)  
**Output:** `agent2_results.json`

**Role:** Produces a final hybrid risk score per transaction using a combination of transparent behavioral domain rules and a machine learning model.

**Key design properties:**
- **Leak-free:** All ML evaluation uses 5-fold stratified out-of-fold (OOF) cross-validation; `fraud_label` is never available during inference
- **Deterministic:** `random_state=42` throughout; identical output on every run
- **Honest signal reporting:** Detects and reports weak ML predictive signal when present

**Models evaluated:**
- Logistic Regression (balanced)
- Logistic Regression (unbalanced)
- Random Forest (balanced)
- Random Forest (unbalanced)
- HistGradientBoosting

Best model selected by PR-AUC (more informative than ROC-AUC on imbalanced data).

**Output per transaction:**
```json
{
  "transaction_id": "T1",
  "user_id": "U3756",
  "agent": "risk_assessor",
  "risk_score": 0.3164,
  "risk_level": "LOW",
  "risk_indicators": ["..."],
  "details": {
    "ml_probability": 0.0627,
    "domain_risk": 0.2954,
    "ip_risk": 0.42,
    "failed_attempts": 1,
    "login_attempts": 4,
    "transaction_amount": 12500.0,
    "average_transaction_amount": 11000.0,
    "amount_to_average_ratio": 1.1364
  },
  "reasoning": "..."
}
```

---

### Agent 3 — Transaction Validator (`agent3_validator.py`)

**Input:** `Data/Digital_Payment_Fraud_Detection_Dataset.csv` (all 7,500 rows)  
**Output:** `agent3_results.json`

**Role:** Applies deterministic rule-based scoring to detect transaction-level anomalies and velocity patterns. Operates completely independently from Agents 1 and 2.

**Scores computed:**
- `anomaly_score`: Weighted combination of amount anomaly + international risk
- `velocity_score`: Weighted combination of failed attempt risk + login attempt risk

**Output per transaction:**
```json
{
  "transaction_id": "T1",
  "user_id": "U3756",
  "agent": "transaction_validator",
  "anomaly_score": 0.0,
  "velocity_score": 0.3,
  "amount_ratio": 1.136,
  "amount_difference": 1500.0,
  "risk_indicators": [...]
}
```

> **Note:** The first 20 transactions receive an optional LLM-generated narrative explanation. All scores are deterministic Python calculations regardless; LLM does not change scores.

---

### Agent 4 — Decision Synthesizer (`agent4_synthesizer.py`)

**Input:** `agent1_results.json`, `agent2_results.json`, `agent3_results.json`  
**Output:** `agent4_results.json`

**Role:** Combines the three agent outputs for each of the 100 transactions that Agent 1 analyzed. Produces a final fraud score and decision.

**Decision thresholds (aligned with validation contract):**
| Score Range | Decision |
|---|---|
| ≥ 70 | FRAUD |
| 40 – 69 | SUSPICIOUS |
| < 40 | LEGIT |

**Output per transaction:**
```json
{
  "transaction_id": "T1",
  "user_id": "U3756",
  "agent": "decision_synthesizer",
  "fraud_score": 23.74,
  "decision": "LEGIT",
  "confidence": 75.0,
  "agent_scores": {
    "behavior_score": 0.3,
    "risk_score": 0.3164,
    "anomaly_score": 0.0,
    "velocity_score": 0.3
  },
  "agent_findings": {
    "agent1_high": false,
    "agent2_high": false,
    "agent3_high": false,
    "consensus": 0,
    "evidence_count": 1
  },
  "reasoning": "...",
  "risk_indicators": [...]
}
```

---

## 5. Dataset

| Property | Value |
|---|---|
| File | `Data/Digital_Payment_Fraud_Detection_Dataset.csv` |
| Rows | 7,500 |
| Columns | 15 |
| Non-fraud transactions | 7,011 |
| Fraud transactions | 489 |
| Fraud prevalence | **6.52%** |

**Columns:**

| Column | Type | Description |
|---|---|---|
| `transaction_id` | string | Unique transaction identifier |
| `user_id` | string | User identifier |
| `transaction_amount` | float | Amount of the transaction |
| `transaction_type` | categorical | Type of transaction |
| `payment_mode` | categorical | Payment mode used |
| `device_type` | categorical | Device used |
| `device_location` | categorical | Location of device |
| `account_age_days` | int | Age of account in days |
| `transaction_hour` | int | Hour of transaction (0–23) |
| `previous_failed_attempts` | int | Prior failed transaction attempts |
| `avg_transaction_amount` | float | User's historical average transaction |
| `is_international` | binary | 1 = international transaction |
| `ip_risk_score` | float [0,1] | IP address risk score |
| `login_attempts_last_24h` | int | Login attempts in past 24 hours |
| `fraud_label` | binary | Ground truth: 1 = fraud, 0 = legitimate |

---

## 6. ML Methodology & Honest Signal Report

> **IMPORTANT:** The available dataset contains weak predictive signal for `fraud_label`
> when evaluated using ML models alone.
> Agent 2 therefore treats ML output as a **supporting signal** and combines it with a
> transparent operational behavioral risk score. The ML model is NOT presented as a
> reliable fraud classifier.

### Two Distinct Evaluations — Do Not Confuse

This project contains **two separate, clearly distinguished evaluations**:

| Evaluation | Script | Scope | Metric |
|---|---|---|---|
| ML model OOF evaluation | Agent 2 internal | 7,500 rows, CV only | ROC-AUC, PR-AUC for ML probability |
| Behavioral risk_score evaluation | `evaluate_agent2.py` | All 7,500 rows | ROC-AUC, PR-AUC for final risk_score |
| End-to-end pipeline evaluation | `evaluate_system.py` | 100 rows (Agent 4) | Accuracy, Precision, Recall, F1 |

### ML Model OOF Results (5-Fold Stratified Cross-Validation)

All models evaluated with `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`:

| Model | OOF ROC-AUC | OOF PR-AUC |
|---|---|---|
| Logistic Regression (balanced) | ~0.51 | ~0.07 |
| Logistic Regression (none) | ~0.51 | ~0.07 |
| Random Forest (balanced) | ~0.51 | ~0.07 |
| Random Forest (none) | ~0.51 | ~0.07 |
| HistGradientBoosting | ~0.51 | ~0.07 |

**Interpretation of ML-only OOF results:**
- Fraud prevalence PR-AUC baseline = 0.065
- All ML models: ROC-AUC ≈ 0.50 (random), PR-AUC ≈ 0.07 (≈ baseline)
- **Conclusion:** Univariate analysis and cross-validated model evaluation found little evidence of useful predictive signal in the ML-only probability estimates against `fraud_label`.

This finding is scientifically valid and honestly reported. It does **not** mean the features are statistically independent of fraud; it means the ML probability estimates generalize poorly across cross-validation folds.

### Agent 2 Behavioral Risk Score Evaluation (`evaluate_agent2.py`)

The **final hybrid risk_score** (80% domain rules + 20% ML probability) evaluated against all 7,500 ground-truth labels:

| Metric | Value | Baseline |
|---|---|---|
| ROC-AUC | **0.7817** | 0.5000 (random) |
| PR-AUC | **0.2693** | 0.0652 (prevalence) |

**Risk level fraud rates:**

| Risk Level | Fraud Count | Total | Fraud % |
|---|---|---|---|
| HIGH (≥ 0.55) | 210 | 888 | **23.65%** |
| MEDIUM (0.35–0.54) | 238 | 3,933 | 6.05% |
| LOW (< 0.35) | 41 | 2,679 | **1.53%** |

**Interpretation:** The behavioral domain rules (ip_risk, failed_attempts, login_attempts, amount_anomaly, international) provide meaningful separation. HIGH-risk transactions have a 23.65% fraud rate versus 1.53% for LOW-risk — a **15× lift**. This confirms that the domain-expert behavioral scoring is doing the useful work, while ML probability makes only a supporting contribution.

> **Important distinction:** The ROC-AUC 0.78 belongs to the **final hybrid risk_score** (an operational signal). The ML OOF ROC-AUC of ~0.51 belongs to **ML probability alone**. These must not be mixed. The risk_score is not a calibrated fraud probability.

### Why the ML Signal is Weak

The ML models fail to generalize in cross-validation because the raw features (ip_risk_score, failed_attempts, login_attempts, amount, account age) do not provide a learnable pattern that holds across folds. This is common in fraud datasets. The behavioral domain rules, however, are constructed from expert knowledge about fraud patterns and provide meaningful risk stratification.

---

## 7. Behavioral Risk Scoring

Agent 2 computes a **domain risk score** using transparent, interpretable rules:

| Component | Formula | Weight |
|---|---|---|
| IP Risk | `clip(ip_risk_score, 0, 1)` | 0.30 |
| Failed Attempt Risk | `clip(previous_failed_attempts / 4.0, 0, 1)` | 0.25 |
| Login Attempt Risk | `clip(login_attempts_last_24h / 9.0, 0, 1)` | 0.20 |
| Amount Anomaly Risk | `clip(|log(amount/avg)| / log(5), 0, 1)` | 0.15 |
| International Risk | `is_international` (binary) | 0.10 |

**Combined:**
```
domain_risk = 0.30 * ip_risk
            + 0.25 * failed_risk
            + 0.20 * login_risk
            + 0.15 * amt_anomaly_risk
            + 0.10 * intl_risk
```

These weights are **operational scoring policy parameters**, not calibrated fraud probabilities.  
They reflect expert judgment about the relative importance of each factor for payment fraud.

---

## 8. Hybrid Scoring

Agent 2 combines domain expertise with ML output:

```
final_risk_score = 0.80 × domain_risk + 0.20 × ml_probability
```

The 80/20 split means:
- Domain rules dominate because they are interpretable and stable
- ML adds a small adaptive signal but cannot override strong behavioral evidence
- This is appropriate given the weak ML signal detected

> **The `risk_score` is an operational risk signal, NOT a calibrated fraud probability.**

---

## 9. Risk Levels

| Level | Threshold | Interpretation |
|---|---|---|
| HIGH | risk_score ≥ 0.55 | Elevated behavioral risk; review recommended |
| MEDIUM | 0.35 ≤ risk_score < 0.55 | Moderate risk signals detected |
| LOW | risk_score < 0.35 | Low behavioral risk |

**Observed distribution across 7,500 transactions:**
| Level | Count | % |
|---|---|---|
| HIGH | ~888 | ~11.8% |
| MEDIUM | ~3,933 | ~52.4% |
| LOW | ~2,679 | ~35.7% |

---

## 10. Installation

### Prerequisites

- Python 3.9 or higher
- A [Groq API key](https://console.groq.com/) (free)

### Setup

```bash
# 1. Clone or download the project
cd "project 2.0"

# 2. Create a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
copy .env.example .env
# Then edit .env and add your real GROQ_API_KEY
```

---

## 11. How to Run

Run the agents in order. Each agent depends on the previous agent's output.

```bash
# Step 1: Behavioral Analysis (Agent 1)
# Processes first 100 transactions using Groq LLM
python agent1_behavior.py

# Step 2: Risk Assessment (Agent 2)
# Processes all 7,500 transactions — no LLM required, fully deterministic
python agent2_risk_v4.py

# Step 3: Transaction Validation (Agent 3)
# Processes all 7,500 transactions — deterministic rule-based scoring
python agent3_validator.py

# Step 4: Decision Synthesis (Agent 4)
# Synthesizes results for the 100 transactions common to all agents
python agent4_synthesizer.py

# Step 5: End-to-End Evaluation (Agent 4 vs ground truth, 100 transactions)
python evaluate_system.py

# Step 6: Agent 2 Full-Dataset Evaluation (optional but recommended)
# Evaluates risk_score against all 7,500 ground-truth labels
# Provides ROC-AUC, PR-AUC, risk level breakdown
python evaluate_agent2.py
```

**Expected runtimes (approximate):**
| Agent | Estimated Time |
|---|---|
| Agent 1 | 2–10 min (Groq API calls for 100 transactions) |
| Agent 2 | 3–8 min (ML training + 7,500 inference) |
| Agent 3 | 1–3 min (rule-based, Groq for 20 transactions) |
| Agent 4 | < 1 min |
| Evaluation | < 1 min |

---

## 12. Output Files

| File | Agent | Records | Description |
|---|---|---|---|
| `agent1_results.json` | Agent 1 | 100 | Behavioral deviation scores |
| `agent2_results.json` | Agent 2 | 7,500 | Hybrid risk scores |
| `agent3_results.json` | Agent 3 | 7,500 | Anomaly and velocity scores |
| `agent4_results.json` | Agent 4 | 100 | Final fraud decisions |
| `system_evaluation.csv` | `evaluate_system.py` | 100 | Agent 4 decisions vs ground truth |
| `agent2_evaluation.csv` | `evaluate_agent2.py` | 7,500 | Agent 2 risk_score vs ground truth |

> **Note on `system_evaluation.csv`:** This evaluation is based on a 100-transaction sample
> containing only **one confirmed fraud case**. The 99% accuracy figure reflects the high
> proportion of legitimate transactions in that sample, **not** fraud detection capability.
> Precision, Recall, and F1 are 0.0 because Agent 4 does not classify any transaction as
> FRAUD in this sample (the single fraud case receives a SUSPICIOUS classification).
> **Do not describe this as "99% accurate fraud detection."** For a statistically meaningful
> evaluation of the risk scoring layer, see `agent2_evaluation.csv` (7,500 rows, ROC-AUC 0.78).

---

## 13. Testing / Validation

Run the validation scripts after each agent:

```bash
python check_agent1.py    # Validates agent1_results.json
python check_agent2.py    # Validates agent2_results.json
python check_agent3.py    # Validates agent3_results.json
python check_agent4.py    # Validates agent4_results.json
```

Each checker validates:
- Correct record count
- No duplicate transaction IDs
- All scores within expected ranges [0, 1] or [0, 100]
- All required fields present
- Decision/score consistency

---

## 14. Reproducibility

Agent 2 is fully deterministic:

- `random_state=42` passed to all sklearn estimators
- `numpy.random.seed(42)` set globally
- `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`
- No floating-point non-determinism from parallelism (deterministic path)

**Verified:** SHA256 hash of `agent2_results.json` is identical across multiple runs.

Agent 3 and Agent 4 are fully deterministic (pure Python arithmetic, no randomness).

**Agent 1** calls a live LLM API — the `reasoning` text may vary slightly between runs,  
but the `behavior_score` is computed deterministically from raw dataset values.

---

## 15. Limitations

### ML Signal

The most important limitation of this project is that the dataset does not contain  
strong predictive signal for fraud. All evaluated ML models produce ROC-AUC ≈ 0.50  
(approximately random) and PR-AUC ≈ 0.07 (barely above the 0.065 prevalence baseline).

This is **not a bug** and has not been artificially masked. The system honestly reports  
this finding and appropriately down-weights ML probability to only 20% of the final score.

### Scale Limitation (100 vs 7,500)

Agent 1 is designed to analyze only 100 transactions due to LLM API call overhead.  
Agent 4 synthesizes results only for the 100 transactions that Agent 1 has processed.  
The final evaluation therefore covers 100 transactions, not the full 7,500.

This is an **intentional design trade-off** that allows LLM behavioral analysis to be  
included while keeping runtime reasonable. In production, Agent 1 could be parallelized  
or replaced with a faster behavioral model.

### No Historical User Data

Agent 2 behavioral features are computed from single-row transaction data.  
True behavioral fraud detection requires time-series user transaction history  
(e.g., rolling averages, velocity windows, session patterns).

### No Temporal Validation

All ML cross-validation uses random stratified splits, not time-based splits.  
A production system should always use temporal forward-chasing validation to  
prevent data leakage across time.

### Risk Score Is Not a Calibrated Probability

The `risk_score` produced by Agent 2 is an **operational risk signal**, not a  
calibrated fraud probability. It should not be interpreted as "this transaction  
has X% probability of being fraud."

### Fraud Prevalence in Test Sample

The 100-transaction Agent 1 sample contains exactly **1 fraud case** (1%).  
The full dataset has 489 frauds across 7,500 transactions (6.52%).  
Evaluation metrics computed over this 100-transaction sample are statistically  
insufficient for strong conclusions.

---

## 16. Future Improvements

The following improvements are **not yet implemented** but would meaningfully improve system performance:

1. **Richer transaction history per user** — rolling averages, standard deviations, velocity windows
2. **Time-series / temporal features** — time since last transaction, hourly/daily/weekly patterns
3. **Temporal cross-validation** — train on earlier dates, validate on later dates
4. **Merchant information** — merchant category code (MCC), merchant reputation
5. **IP / device reputation** — device fingerprinting, IP geolocation history
6. **Network graph features** — account-to-account transfer graphs, ring fraud detection
7. **Confirmed fraud feedback loop** — use confirmed fraud cases to retrain models online
8. **Calibrated fraud probabilities** — Platt scaling or isotonic regression for proper probability output
9. **Larger, real-world labeled dataset** — current signal is weak; more diverse labeled fraud examples would improve ML performance significantly
10. **Agent 1 scale-up** — async LLM calls or local LLM to process all 7,500 transactions
11. **Explainability layer** — SHAP values per transaction for model explanation

---

## Project Structure

```
project 2.0/
│
├── Data/
│   └── Digital_Payment_Fraud_Detection_Dataset.csv
│
├── agent1_behavior.py        # Agent 1: LLM behavioral analysis
├── agent2_risk_v4.py         # Agent 2: ML + domain risk scoring
├── agent3_validator.py       # Agent 3: Deterministic rule validation
├── agent4_synthesizer.py     # Agent 4: Multi-agent decision synthesis
├── evaluate_system.py        # End-to-end evaluation (100 tx vs ground truth)
├── evaluate_agent2.py        # Agent 2 full-dataset evaluation (7,500 rows)
│
├── check_agent1.py           # Validation script for Agent 1 output
├── check_agent2.py           # Validation script for Agent 2 output
├── check_agent3.py           # Validation script for Agent 3 output
├── check_agent4.py           # Validation script for Agent 4 output
│
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template (no real keys)
├── .gitignore                # Git ignore rules (.env, venv, outputs)
└── README.md                 # This file
```

**Files intentionally NOT committed to Git** (see `.gitignore`):
- `.env` — contains real API key; never commit
- `venv/` — local virtual environment
- `agent*_results.json` — generated outputs; re-create by running agents
- `system_evaluation.csv`, `agent2_evaluation.csv` — generated outputs
- `__pycache__/`, `*.pyc` — Python bytecode

---

## License

This project is provided for educational and research purposes.

---

*This system honestly represents its ML capabilities. It does not claim to be a  
highly accurate fraud detector. Its value lies in its transparent, explainable,  
reproducible multi-agent architecture that can be extended with better data.*
