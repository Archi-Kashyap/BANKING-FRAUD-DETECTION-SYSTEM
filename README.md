# Banking Fraud Detection — Multi-Agent System

A **multi-agent AI pipeline** for detecting fraudulent digital payment transactions.  
The system combines **behavioral analysis**, **ML-assisted risk scoring**, **rule-based validation**, and **decision synthesis** across four specialized agents orchestrated via **LangGraph**, exposed through a **FastAPI** REST backend and an interactive **Streamlit** dashboard.

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
17. [Appendix: Legacy Batch Pipeline](#17-appendix-legacy-batch-pipeline)
18. [Project Structure](#18-project-structure)

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

The system uses a unified multi-agent architecture powered by **LangGraph**, exposed via a high-performance **FastAPI** REST backend and an interactive **Streamlit** dashboard ("FraudGuard Threat Analysis Console").

```
       +------------------------------------+             +------------------------------------+
       |   Streamlit Dashboard (app.py)     |             |    FastAPI REST Backend (api.py)   |
       | "FraudGuard Threat Analysis Console"|             | Port 8001: /health, /predict/{id}  |
       |  • Dataset Explorer & Filters      |             |            POST /predict           |
       |  • Manual Transaction Form         |             |                                    |
       |  • Threat Gauges & HUD Breakdown   |             |                                    |
       +-----------------+------------------+             +-----------------+------------------+
                         |           \                                      |
                         |            \   HTTP REST Requests                |
                         |             \  (Port 8001)                       |
                         |              +---------------------------------> |
                         |                                                  |
                         | Direct In-Process Fallback                       | Server-Side
                         | (when API is offline)                            | Graph Invocation
                         |                                                  |
                         +------------------------+-------------------------+
                                                  |
                                                  v
+───────────────────────────────────────────────────────────────────────────────────────────────+
│                                  LangGraph Engine (graph/)                                    │
│                                                                                               │
│  Shared Execution Context (graph/context.py):                                                 │
│  • Dataset Cache: 7,500 transactions (Data/Digital_Payment_Fraud_Detection_Dataset.csv)       │
│  • ML Model Pipeline: Stratified 5-Fold OOF Tuned Random Forest Classifier                    │
│  • User Historical Profiles: Baseline spend, location, channel, and device frequency maps    │
│                                                                                               │
│  StateGraph Execution Flow (graph/workflow.py):                                               │
│                                                                                               │
│  START                                                                                        │
│    │                                                                                          │
│    ▼                                                                                          │
│  [Agent 1: Behavior Analyzer] (graph/nodes.py::behavior_node)                                 │
│  • Compares transaction to user's historical patterns                                        │
│  • Evaluates amount, location, channel, device, and time-of-day deviations                    │
│  • Optional Groq LLM behavioral narrative generation                                         │
│    │                                                                                          │
│    ▼                                                                                          │
│  [Agent 2: Risk Assessor] (graph/nodes.py::risk_node)                                         │
│  • Computes transparent domain risk score (IP risk, failed/login attempts)                    │
│  • Generates ML fraud probability estimate via Random Forest                                  │
│  • Blends 80% domain rules + 20% ML probability                                               │
│    │                                                                                          │
│    ▼                                                                                          │
│  [Agent 3: Transaction Validator] (graph/nodes.py::validator_node)                           │
│  • Deterministic anomaly score (amount anomaly ratio + international flag)                    │
│  • Deterministic velocity score (failed attempts + login velocity)                            │
│    │                                                                                          │
│    ▼                                                                                          │
│  [Agent 4: Decision Synthesizer] (graph/nodes.py::synthesizer_node)                          │
│  • Synthesizes multi-agent scores into unified fraud score (0–100)                            │
│  • Evaluates consensus across agents and active risk indicators                               │
│  • Assigns final verdict: LEGIT (<40), SUSPICIOUS (40–69), or FRAUD (≥70)                     │
│    │                                                                                          │
│    ▼                                                                                          │
│   END                                                                                         │
+───────────────────────────────────────────────────────────────────────────────────────────────+
                                                  ▲
                                                  │
       +------------------------------------------+-----------------------------+
       |               CLI Analysis & Automated Test Suites                     |
       |  • run_graph.py: Direct CLI execution (--transaction T5 or --limit)   |
       |  • test_agents.py: Agent rule, math, & threshold unit tests            |
       |  • e2e_sidebar_test.py: Playwright end-to-end browser test suite       |
       +------------------------------------------------------------------------+
```

### Architectural Design Highlights

1. **Decoupled Frontend & Backend with Resilient Fallback**:
   - `FastAPI (api.py)` serves as the high-throughput inference API with `/health`, `/predict/{transaction_id}`, and `/predict` (POST) endpoints.
   - `Streamlit (app.py)` acts as the analyst threat console. It communicates with FastAPI over HTTP on port 8001. If FastAPI is offline, Streamlit automatically and instantly falls back to an in-process instance of the LangGraph engine (`get_local_engine()`), guaranteeing zero UI disruption.
2. **LangGraph State Machine (`graph/`)**:
   - Built on LangGraph `StateGraph(FraudState)`, defining a strictly typed sequential DAG: `START -> behavior_analyzer -> risk_assessor -> transaction_validator -> decision_synthesizer -> END`.
   - Each agent node consumes the state, executes specialized domain/ML logic, and writes structured outputs (`behavior`, `risk`, `validation`, `result`).
   - Shared context (`graph/context.py`) loads the dataset once, prepares user historical caches, and fits the Random Forest classifier.
3. **Flexible Invocation Interfaces**:
   - **Interactive Web UI**: `streamlit run app.py`
   - **REST API**: `uvicorn api:api --reload --port 8001`
   - **CLI Analysis**: `python run_graph.py --transaction T5` or `python run_graph.py --limit 100`
   - **Legacy Batch Pipeline**: Independent historical scripts writing intermediate JSON files (see [Appendix: Legacy Batch Pipeline](#appendix-legacy-batch-pipeline)).

---

## 4. Agents

The fraud detection pipeline is composed of four specialized agents. In the modern architecture, each agent is implemented as a specialized node in `graph/nodes.py` operating on a typed `FraudState` dictionary within the LangGraph engine (`graph/workflow.py`), while remaining runnable as standalone batch scripts (`agent*.py`).

### Agent 1 — Behavior Analyzer (`graph/nodes.py::behavior_node` / `agent1_behavior.py`)

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

### Agent 2 — Risk Assessor (`graph/nodes.py::risk_node` / `agent2_risk_v4.py`)

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

### Agent 3 — Transaction Validator (`graph/nodes.py::validator_node` / `agent3_validator.py`)

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

### Agent 4 — Decision Synthesizer (`graph/nodes.py::synthesizer_node` / `agent4_synthesizer.py`)

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

<a id="6-ml-methodology--honest-signal-report"></a>
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

The ML models fail to generalize in cross-validation because the raw features (ip_risk_score, failed_attempts, login_attempts, amount, account age) do not provide a learnable pattern that holds across folds. Running `python check_labels.py` demonstrates that all single-feature ROC-AUCs in `Digital_Payment_Fraud_Detection_Dataset.csv` hover around 0.50 (random chance):

| Feature | Single-Feature ROC-AUC | Random Chance Baseline |
|---|---|---|
| `transaction_amount` | **0.4882** | 0.5000 |
| `ip_risk_score` | **0.5042** | 0.5000 |
| `login_attempts_last_24h` | **0.5189** | 0.5000 |
| `account_age_days` | **0.5347** | 0.5000 |
| `previous_failed_attempts` | **0.5176** | 0.5000 |
| `avg_transaction_amount` | **0.5066** | 0.5000 |
| `transaction_hour` | **0.5060** | 0.5000 |
| `is_international` | **0.4910** | 0.5000 |

Because the synthetic labels carry minimal statistical dependency on raw transaction attributes, machine learning models (such as `RandomForestClassifier`) achieve an out-of-fold PR-AUC of only ~0.07 against an imbalanced prevalence baseline of 0.065.

### Honest UI Telemetry & Hybrid Architecture

To ensure complete transparency and prevent giving users or stakeholders the false impression that a standalone ML model drives classifications:
- **Model Display**: The UI sidebar explicitly labels the engine as **`Model: Hybrid (Rules + RF)`**.
- **Telemetry Transparency**: The UI displays an active transparency badge: **`ML Signal: Supporting (Weak Dataset Baseline)`**.
- **Architecture Rationale**: Agent 2 uses expert behavioral rules as primary signal while the Random Forest classifier provides secondary supporting input, ensuring high operational safety without relying on uncorrelated synthetic labels.

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
- A [Groq API key](https://console.groq.com/) (free — optional for core deterministic scoring, required for live LLM explanations)

### Setup

```bash
# 1. Clone or navigate to the project directory
cd BANKING-FRAUD-DETECTION-SYSTEM

# 2. Create a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
copy .env.example .env    # Windows
# cp .env.example .env    # macOS/Linux
# Then edit .env and configure your GROQ_API_KEY

# 5. (Optional) Install Playwright for UI E2E tests
pip install playwright
playwright install chromium
```

---

## 11. How to Run

The system offers three primary run modes: the **Streamlit Web Dashboard**, the **FastAPI REST Backend**, and the **LangGraph CLI Runner**, along with automated testing suites.

### 1. Interactive Streamlit Dashboard (Recommended)

Launch the full-featured Threat Analysis Console in your browser:

```bash
streamlit run app.py
```

- **URL**: Opens automatically at `http://localhost:8501`.
- **Key Features**:
  - **Dataset Mode**: Filter, search, and analyze transactions from the 7,500-record dataset.
  - **Quick Test Presets**: Test one-click scenarios (Clean UPI transaction, High-Risk international fraud attack).
  - **Manual Entry Mode**: Input arbitrary transaction parameters (amounts, payment mode, IP risk score, device type, failed attempts) for live evaluation.
  - **Explainability**: Live threat gauges, individual agent score breakdowns (Behavior, Risk, Anomaly, Velocity), consensus signals, and reasoning narratives.
- **Dual-Mode Connectivity**: The UI automatically checks for the FastAPI backend on port 8001. If the API is running, requests are routed via HTTP; if the API is offline, it seamlessly falls back to the in-process local LangGraph engine with zero UI delay.

---

### 2. FastAPI REST Backend

Run the high-performance async REST backend:

```bash
uvicorn api:api --reload --port 8001
```

- **Service URL**: `http://127.0.0.1:8001`
- **Interactive OpenAPI Documentation**: `http://127.0.0.1:8001/docs`
- **API Endpoints**:
  - `GET /health` — Health check, loaded dataset size, and ML model status.
  - `GET /predict/{transaction_id}` — Evaluates an existing dataset transaction through the multi-agent graph (e.g. `http://127.0.0.1:8001/predict/T5`).
  - `POST /predict` — Evaluates an arbitrary transaction JSON payload. Example:
    ```bash
    curl -X POST "http://127.0.0.1:8001/predict" \
      -H "Content-Type: application/json" \
      -d '{
        "user_id": "U1001",
        "transaction_amount": 75000.0,
        "transaction_type": "Transfer",
        "payment_mode": "Net banking",
        "device_type": "Web",
        "device_location": "Bangalore",
        "account_age_days": 12,
        "transaction_hour": 3,
        "previous_failed_attempts": 3,
        "avg_transaction_amount": 2500.0,
        "is_international": 1,
        "ip_risk_score": 0.85,
        "login_attempts_last_24h": 6
      }'
    ```

> **Client-Server Workflow**: Run `uvicorn api:api --reload --port 8001` in one terminal and `streamlit run app.py` in another. The Streamlit sidebar status badge will indicate `API online, 7,500 rows loaded`.

---

### 3. CLI Analysis via LangGraph (`run_graph.py`)

Run transactions directly through the LangGraph engine from the terminal without starting a web server:

```bash
# Analyze a single transaction by ID and display complete JSON result
python run_graph.py --transaction T5

# Run batch analysis across the first N dataset transactions (defaults to 100)
python run_graph.py --limit 100

# Run batch analysis with live Groq LLM explanations saved to custom output
python run_graph.py --limit 20 --llm --output my_results.json
```

**CLI Options:**
| Option | Description | Default |
|---|---|---|
| `--transaction <ID>` | Single transaction ID (e.g., `T5`, `T145`) to analyze | None |
| `--limit <N>` | Total number of dataset transactions to run sequentially | `100` |
| `--output <path>` | File path for output JSON results | `graph_results.json` |
| `--llm` | Include live Groq LLM explanations for behavioral reasoning | Disabled (fast deterministic) |

---

### 4. Running Automated Tests

Run the test suites to verify agent math correctness and web UI functionality:

```bash
# Run agent logic, threshold, and math unit tests
python test_agents.py

# Run Playwright end-to-end browser tests on the Streamlit dashboard
python e2e_sidebar_test.py
```

---

## 12. Output Files

| File | Generator | Scope | Description |
|---|---|---|---|
| `graph_results.json` | `run_graph.py` | Configurable (default 100) | Full multi-agent LangGraph analysis results per transaction |
| `agent1_results.json` | `agent1_behavior.py` (legacy) | 100 | Behavioral deviation scores |
| `agent2_results.json` | `agent2_risk_v4.py` (legacy) | 7,500 | Hybrid risk scores |
| `agent3_results.json` | `agent3_validator.py` (legacy) | 7,500 | Anomaly and velocity scores |
| `agent4_results.json` | `agent4_synthesizer.py` (legacy) | 100 | Final fraud decisions |
| `system_evaluation.csv` | `evaluate_system.py` (legacy) | 100 | Agent 4 decisions vs ground truth |
| `agent2_evaluation.csv` | `evaluate_agent2.py` (legacy) | 7,500 | Agent 2 risk_score vs ground truth |

> **Note on `system_evaluation.csv`:** This evaluation is based on a 100-transaction sample
> containing only **one confirmed fraud case**. The 99% accuracy figure reflects the high
> proportion of legitimate transactions in that sample, **not** fraud detection capability.
> Precision, Recall, and F1 are 0.0 because Agent 4 does not classify any transaction as
> FRAUD in this sample (the single fraud case receives a SUSPICIOUS classification).
> **Do not describe this as "99% accurate fraud detection."** For a statistically meaningful
> evaluation of the risk scoring layer, see `agent2_evaluation.csv` (7,500 rows, ROC-AUC 0.78).

---

<a id="13-testing--validation"></a>
## 13. Testing / Validation

The repository includes both modern automated test suites and legacy JSON verification scripts:

### Modern Automated Test Suites

```bash
# 1. Agent Logic & Math Unit Tests
python test_agents.py

# 2. Playwright UI End-to-End Tests
python e2e_sidebar_test.py
```

- **Agent Unit Tests (`test_agents.py`)**:
  - **Agent 3**: Validates exact anomaly thresholds (5x=1.0, 3x=0.8, 2x=0.5, 1.5x=0.3) and velocity risk formulas across combinations of failed attempts and logins.
  - **Agent 2**: Validates domain risk calculations, IP weighting, and extreme value clipping.
  - **Agent 1**: Validates user history tracking, cold-start handling for first-time users (0.3 baseline), and risk indicator triggers.
  - **Agent 4**: Validates consensus synthesis, score weighting, and decision boundaries (`LEGIT`, `SUSPICIOUS`, `FRAUD`).
- **E2E Playwright Suite (`e2e_sidebar_test.py`)**:
  - Automatically spins up the Streamlit dashboard on an isolated port.
  - Validates initial page render, radio button navigation, dataset mode, manual entry mode, and dynamic form inputs.

### Legacy Output Checkers
For validating JSON files generated by the legacy batch pipeline (see [Appendix: Legacy Batch Pipeline](#appendix-legacy-batch-pipeline)):

```bash
python check_agent1.py    # Validates agent1_results.json
python check_agent2.py    # Validates agent2_results.json
python check_agent3.py    # Validates agent3_results.json
python check_agent4.py    # Validates agent4_results.json
```

Each checker validates record counts, unique IDs, score ranges (`[0, 1]` or `[0, 100]`), schema structure, and decision consistency.

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

<a id="appendix-legacy-batch-pipeline"></a>
## 17. Appendix: Legacy Batch Pipeline

Prior to the introduction of the LangGraph multi-agent orchestration (`graph/`), FastAPI REST service (`api.py`), and Streamlit dashboard (`app.py`), the system executed as a sequential 6-step CLI batch workflow dumping intermediate JSON files.

### Legacy 6-Step Execution Flow

Run the standalone agents in order. Each script depends on the previous script's JSON output:

```bash
# Step 1: Behavioral Analysis (Agent 1)
# Processes first 100 transactions using Groq LLM -> generates agent1_results.json
python agent1_behavior.py

# Step 2: Risk Assessment (Agent 2)
# Processes all 7,500 transactions — deterministic ML + domain rules -> generates agent2_results.json
python agent2_risk_v4.py

# Step 3: Transaction Validation (Agent 3)
# Processes all 7,500 transactions — deterministic rule-based scoring -> generates agent3_results.json
python agent3_validator.py

# Step 4: Decision Synthesis (Agent 4)
# Synthesizes results for the 100 transactions common to all agents -> generates agent4_results.json
python agent4_synthesizer.py

# Step 5: End-to-End Evaluation (Agent 4 vs ground truth, 100 transactions)
# Generates system_evaluation.csv
python evaluate_system.py

# Step 6: Agent 2 Full-Dataset Evaluation (optional but recommended)
# Evaluates risk_score against all 7,500 ground-truth labels -> generates agent2_evaluation.csv
python evaluate_agent2.py
```

### Legacy Expected Runtimes (Approximate)
| Script | Estimated Time | Description |
|---|---|---|
| `agent1_behavior.py` | 2–10 min | Groq API calls for 100 transactions |
| `agent2_risk_v4.py` | 3–8 min | ML training + 7,500 inference |
| `agent3_validator.py` | 1–3 min | Rule-based, Groq for 20 transactions |
| `agent4_synthesizer.py` | < 1 min | Combines agent outputs into decisions |
| `evaluate_system.py` | < 1 min | Accuracy/F1 evaluation on 100 sample rows |
| `evaluate_agent2.py` | < 1 min | ROC-AUC / PR-AUC on 7,500 dataset rows |

---

<a id="project-structure"></a>
## 18. Project Structure

```
BANKING-FRAUD-DETECTION-SYSTEM/
│
├── Data/
│   └── Digital_Payment_Fraud_Detection_Dataset.csv   # 7,500 transaction dataset
│
├── graph/                                            # LangGraph Multi-Agent Architecture
│   ├── __init__.py
│   ├── state.py                                      # FraudState typed schema
│   ├── context.py                                    # Shared context, ML pipeline & caches
│   ├── nodes.py                                      # Agent 1-4 node implementations
│   └── workflow.py                                   # StateGraph compilation & invocation
│
├── app.py                                            # Streamlit Threat Analysis Console
├── api.py                                            # FastAPI REST backend service (port 8001)
├── run_graph.py                                      # Unified LangGraph CLI runner
├── run.py                                            # Unified process orchestrator (API + Streamlit)
│
├── test_agents.py                                    # Agent unit & rule validation tests
├── test_check_health.py                              # FastAPI health & fallback unit tests
├── e2e_sidebar_test.py                               # Playwright UI end-to-end test suite
├── check_labels.py                                   # Dataset feature vs label correlation diagnostic
│
├── agent1_behavior.py                                # Legacy batch Agent 1
├── agent2_risk_v4.py                                 # Legacy batch Agent 2
├── agent3_validator.py                               # Legacy batch Agent 3
├── agent4_synthesizer.py                             # Legacy batch Agent 4
├── evaluate_system.py                                # Legacy system evaluation
├── evaluate_agent2.py                                # Legacy Agent 2 evaluation
│
├── check_agent1.py                                   # Legacy validator for Agent 1 JSON
├── check_agent2.py                                   # Legacy validator for Agent 2 JSON
├── check_agent3.py                                   # Legacy validator for Agent 3 JSON
├── check_agent4.py                                   # Legacy validator for Agent 4 JSON
│
├── requirements.txt                                  # Python dependencies
├── .env.example                                      # Environment variable template
├── .gitignore                                        # Git ignore rules
└── README.md                                         # System documentation
```

**Files intentionally NOT committed to Git** (see `.gitignore`):
- `.env` — contains real API key; never commit
- `venv/` — local virtual environment
- `agent*_results.json`, `graph_results.json` — generated outputs; re-create by running agents
- `system_evaluation.csv`, `agent2_evaluation.csv` — generated outputs
- `__pycache__/`, `*.pyc` — Python bytecode

---

## License

This project is provided for educational and research purposes.

---

*This system honestly represents its ML capabilities. It does not claim to be a  
highly accurate fraud detector. Its value lies in its transparent, explainable,  
reproducible multi-agent architecture that can be extended with better data.*
