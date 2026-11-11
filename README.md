Ran check README.md file info

# 🛡️ Banking Fraud Detection — Multi-Agent AI System

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B.svg)](https://streamlit.io/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0%2B-blueviolet.svg)](https://langchain-ai.github.io/langgraph/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3%2B-F7931E.svg)](https://scikit-learn.org/)
[![Groq LLM](https://img.shields.io/badge/Groq-Llama--3-f55036.svg)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An **enterprise-grade, explainable, multi-agent AI system** for detecting fraudulent digital payment transactions.  
Combining **behavioral profile tracking**, **stratified ML risk scoring**, **deterministic transaction validation**, and **consensus decision synthesis**, orchestrated via **LangGraph**, served through a **FastAPI** REST backend, and visualized inside the interactive **FraudGuard Threat Analysis Console** built with **Streamlit**.

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Multi-Agent Pipeline](#-multi-agent-pipeline)
  - [Agent 1: Behavior Analyzer](#agent-1--behavior-analyzer)
  - [Agent 2: Risk Assessor](#agent-2--risk-assessor)
  - [Agent 3: Transaction Validator](#agent-3--transaction-validator)
  - [Agent 4: Decision Synthesizer](#agent-4--decision-synthesizer)
- [Dataset & Scientific Signal Analysis](#-dataset--scientific-signal-analysis)
  - [Dataset Overview](#dataset-overview)
  - [Honest Signal Report (Pure ML vs. Hybrid Domain Scoring)](#honest-signal-report)
  - [Risk Level Cohorts](#risk-level-cohorts)
- [Quick Start](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation & Setup](#installation--setup)
  - [Running the System](#running-the-system)
- [Run Modes](#-run-modes)
  - [1. Unified Launcher (FastAPI + Streamlit)](#1-unified-launcher-recommended)
  - [2. Interactive Streamlit Console](#2-interactive-streamlit-console)
  - [3. FastAPI REST Backend](#3-fastapi-rest-backend)
  - [4. CLI Headless Evaluation](#4-cli-headless-evaluation)
- [REST API Reference](#-rest-api-reference)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Deployment](#-deployment)
- [Project Structure](#-project-structure)
- [Limitations & Ethical Disclosure](#-limitations--ethical-disclosure)
- [Future Roadmap](#-future-roadmap)
- [License](#-license)

---

## 🌟 Key Features

- 🤖 **4-Agent Collaborative Intelligence**:
  - **Agent 1 (Behavior Analyzer)**: Computes user behavioral deviations against historical baselines with optional Groq Llama-3 reasoning.
  - **Agent 2 (Risk Assessor)**: Hybrid 80% behavioral domain rules + 20% Random Forest probability trained with 5-Fold Stratified Cross-Validation.
  - **Agent 3 (Transaction Validator)**: Independent deterministic rules evaluating transaction amount anomalies and login/failed attempt velocity.
  - **Agent 4 (Decision Synthesizer)**: Multi-agent consensus engine yielding unified 0–100 threat scores and triage verdicts (`LEGIT`, `SUSPICIOUS`, `FRAUD`).
- ⚡ **Unified 1-Click Process Orchestrator (`run.py`)**:
  - Automatically spins up both the FastAPI backend (port `8001`) and the Streamlit frontend (port `8503`).
  - Active HTTP health check polling ensures the backend is fully initialized before opening the UI.
  - Built-in Windows Job Object and POSIX signal handlers guarantee clean process tree teardown on exit.
- 🔄 **Resilient Dual-Mode Connectivity**:
  - Streamlit communicates over REST with FastAPI. If the API is offline or unreachable, the dashboard automatically and seamlessly falls back to an in-process local LangGraph engine with zero user disruption.
- 🔬 **Honest Scientific Methodology**:
  - No synthetic metric fabrication or label manipulation.
  - Complete transparency: documents weak ML generalization in synthetic tabular features and demonstrates why hybrid domain rules achieve **15× fraud lift** in the high-risk cohort (23.65% fraud rate vs. 1.53% baseline).
- 🎛️ **FraudGuard Threat Console**:
  - Dark-mode, cyberpunk-inspired financial operations UI.
  - Live SVG threat gauges, multi-agent radar signals, transaction search & filter, one-click test presets, and dynamic manual transaction simulator.

---

## 🏗️ System Architecture

```
                                  +------------------------------------------+
                                  |     FraudGuard Threat Console (app.py)   |
                                  |       Streamlit Interactive Dashboard    |
                                  |      • Dataset Explorer & Live Filters   |
                                  |      • Manual Transaction Simulator      |
                                  |      • SVG Threat Gauges & Risk Telemetry|
                                  +--------------------+---------------------+
                                                       |
                                        REST Requests  |  Direct In-Process Fallback
                                          (Port 8001)  |  (If FastAPI is Offline)
                                                       v
                                  +--------------------+---------------------+
                                  |       FastAPI REST Service (api.py)      |
                                  |         • GET  /health                   |
                                  |         • GET  /predict/{id}             |
                                  |         • POST /predict                  |
                                  +--------------------+---------------------+
                                                       |
                                                       v
+─────────────────────────────────────────────────────────────────────────────────────────────────────────────+
│                                        LangGraph Multi-Agent Engine                                         │
│                                                                                                             │
│   Shared Context (graph/context.py):                                                                        │
│   • Dataset Cache: 7,500 transactions (Data/Digital_Payment_Fraud_Detection_Dataset.csv)                    │
│   • Stratified 5-Fold OOF Tuned Random Forest Classifier                                                    │
│   • User Profile Memory: Baseline spend, location, channel, and device frequency maps                     │
│                                                                                                             │
│   StateGraph Execution Flow (graph/workflow.py):                                                            │
│                                                                                                             │
│     START                                                                                                   │
│       │                                                                                                     │
│       ▼                                                                                                     │
│     [Agent 1: Behavior Analyzer]                                                                            │
│     • Compares transaction to user's historical patterns                                                   │
│     • Flags amount spikes, device hops, unusual hours, and location mismatches                              │
│     • Optional Groq LLM explanation generator                                                              │
│       │                                                                                                     │
│       ▼                                                                                                     │
│     [Agent 2: Risk Assessor]                                                                                │
│     • Computes transparent domain risk score (IP risk, failed attempts, login velocity)                     │
│     • Extracts ML fraud probability estimate via Random Forest                                              │
│     • Blends: 80% Domain Rules + 20% ML Probability                                                         │
│       │                                                                                                     │
│       ▼                                                                                                     │
│     [Agent 3: Transaction Validator]                                                                        │
│     • Evaluates amount anomaly ratio relative to historical user mean                                       │
│     • Evaluates velocity score (failed attempts + login frequency)                                          │
│     • Deterministic, independent rule enforcement                                                           │
│       │                                                                                                     │
│       ▼                                                                                                     │
│     [Agent 4: Decision Synthesizer]                                                                         │
│     • Synthesizes multi-agent signals into unified 0–100 Fraud Score                                        │
│     • Evaluates consensus across agents and active risk indicators                                          │
│     • Final Verdict: LEGIT (<40) | SUSPICIOUS (40–69) | FRAUD (≥70)                                         │
│       │                                                                                                     │
│       ▼                                                                                                     │
│      END                                                                                                    │
+─────────────────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 🤖 Multi-Agent Pipeline

The core intelligence is structured as a typed state machine (`StateGraph(FraudState)`) where each agent operates on structured state attributes:

### Agent 1 — Behavior Analyzer
- **Implementation**: [`graph/nodes.py::behavior_node`](graph/nodes.py) / [`agent1_behavior.py`](agent1_behavior.py)
- **Role**: Compares incoming transactions against historical user activity (or cold-start user averages).
- **Features Evaluated**:
  - Transaction amount deviation from user's historical average
  - Device type change (e.g., Mobile → Web)
  - Device location deviation (e.g., Bangalore → London)
  - Time-of-day anomalies (late night vs. regular business hours)
  - Channel / payment mode deviations
- **Output**: `behavior_score` in `[0.0, 1.0]`, triggered behavioral flags, and optional Groq Llama-3 reasoning narrative.

### Agent 2 — Risk Assessor
- **Implementation**: [`graph/nodes.py::risk_node`](graph/nodes.py) / [`agent2_risk_v4.py`](agent2_risk_v4.py)
- **Role**: Combines domain expertise with an ML probability estimate to create a robust, leak-free risk score.
- **Formulas**:
  $$\text{domain\_risk} = 0.30 \cdot \text{ip\_risk} + 0.25 \cdot \text{failed\_risk} + 0.20 \cdot \text{login\_risk} + 0.15 \cdot \text{amt\_anomaly\_risk} + 0.10 \cdot \text{intl\_risk}$$
  $$\text{final\_risk\_score} = 0.80 \cdot \text{domain\_risk} + 0.20 \cdot \text{ml\_probability}$$
- **Output**: `risk_score` in `[0.0, 1.0]`, risk category (`LOW`, `MEDIUM`, `HIGH`), and breakdown metrics.

### Agent 3 — Transaction Validator
- **Implementation**: [`graph/nodes.py::validator_node`](graph/nodes.py) / [`agent3_validator.py`](agent3_validator.py)
- **Role**: Strictly deterministic rule-based validation checking velocity spikes and hard anomaly thresholds.
- **Scores**:
  - `anomaly_score`: Ratio of current transaction amount to historic average coupled with international transaction status.
  - `velocity_score`: Prior failed attempts within 24 hours combined with login frequency.
- **Output**: `anomaly_score`, `velocity_score`, and validation indicator list.

### Agent 4 — Decision Synthesizer
- **Implementation**: [`graph/nodes.py::synthesizer_node`](graph/nodes.py) / [`agent4_synthesizer.py`](agent4_synthesizer.py)
- **Role**: Fuses inputs from Agents 1, 2, and 3, checks for agent consensus, and assigns the final actionable verdict.
- **Decision Matrix**:
  | Final Score Range | Verdict | Action |
  |---|---|---|
  | **0.0 – 39.9** | `LEGIT` | Approve transaction automatically |
  | **40.0 – 69.9** | `SUSPICIOUS` | Step-up authentication / Human Analyst Review |
  | **70.0 – 100.0** | `FRAUD` | Block transaction immediately & alert security |

---

## 📊 Dataset & Scientific Signal Analysis

### Dataset Overview
- **Path**: `Data/Digital_Payment_Fraud_Detection_Dataset.csv`
- **Total Transactions**: 7,500
- **Total Features**: 15 (Transaction amount, payment mode, device type, location, IP risk score, login attempts, failed attempts, account age, etc.)
- **Class Distribution**: 7,011 Non-Fraud (93.48%) vs. 489 Fraud (6.52%)

### Honest Signal Report

> **Scientific Transparency**: Unlike academic papers or tutorials that artificially manipulate labels or overfit single-fold evaluations to show misleading "99% accuracy", this project provides an honest evaluation of tabular ML capabilities on synthetic datasets.

1. **Pure ML Evaluation (5-Fold Stratified Cross-Validation)**:
   - Evaluated models: Balanced Random Forest, Logistic Regression, HistGradientBoosting.
   - **Out-of-Fold (OOF) ROC-AUC**: `~0.51` (Random chance baseline = `0.50`)
   - **Out-of-Fold (OOF) PR-AUC**: `~0.07` (Prevalence baseline = `0.065`)
   - **Finding**: Single transaction features alone in this dataset exhibit virtually zero direct statistical dependency with the synthetic ground-truth labels (verified by running `python check_labels.py`).

2. **Hybrid Domain-Rule Scoring Evaluation (`evaluate_agent2.py`)**:
   - Evaluating the hybrid scoring system on all 7,500 transactions against ground-truth labels reveals strong operational separation:
   - **ROC-AUC**: **`0.7817`**
   - **PR-AUC**: **`0.2693`** (Over **4× higher** than prevalence baseline)

### Risk Level Cohorts

| Risk Tier | Risk Score Range | Total Transactions | Fraud Count | Observed Fraud Rate | Fraud Lift vs Baseline |
|---|---|---|---|---|---|
| **HIGH** | $\ge 0.55$ | 888 | 210 | **23.65%** | **3.63×** (15× vs. LOW) |
| **MEDIUM** | $0.35 - 0.54$ | 3,933 | 238 | **6.05%** | 0.93× |
| **LOW** | $< 0.35$ | 2,679 | 41 | **1.53%** | 0.23× |

---

## 🚀 Quick Start

### Prerequisites
- **Python**: 3.9, 3.10, 3.11, or 3.12
- **Groq API Key** (Free tier available at [console.groq.com](https://console.groq.com/)) — optional for deterministic scoring, required for live LLM explanations.

### Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/BANKING-FRAUD-DETECTION-SYSTEM.git
   cd BANKING-FRAUD-DETECTION-SYSTEM
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # On macOS/Linux:
   python3 -m venv .venv
   source .venv/bin/activate

   # On Windows:
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and paste your Groq API key:
   # GROQ_API_KEY=gsk_...
   ```

---

## 💻 Run Modes

### 1. Unified Launcher (Recommended)
Launches the FastAPI backend and Streamlit dashboard simultaneously with health checking and automatic shutdown.

- **On Windows**:
  ```cmd
  start.bat
  ```
  *or*
  ```cmd
  python run.py
  ```
- **On Linux / macOS**:
  ```bash
  chmod +x start.sh
  ./start.sh
  ```
  *or*
  ```bash
  python3 run.py
  ```

- **What happens**:
  1. Starts FastAPI on `http://127.0.0.1:8001`
  2. Polls `/health` until the machine learning pipeline and dataset are ready
  3. Launches the Streamlit console on `http://localhost:8503`
  4. Automatically opens your default web browser

---

### 2. Interactive Streamlit Console
To run only the frontend dashboard:
```bash
streamlit run app.py
```
- Available at: `http://localhost:8501`
- Automatically connects to FastAPI if running on port 8001; otherwise falls back instantly to the local in-process LangGraph engine.

---

### 3. FastAPI REST Backend
To run only the REST API service:
```bash
uvicorn api:api --reload --host 127.0.0.1 --port 8001
```
- API Base: `http://127.0.0.1:8001`
- Interactive OpenAPI Docs: `http://127.0.0.1:8001/docs`

---

### 4. CLI Headless Evaluation
Run transactions directly through the LangGraph engine without starting a web server:

```bash
# Analyze a specific dataset transaction by ID:
python run_graph.py --transaction T5

# Run batch evaluation on the first 100 transactions:
python run_graph.py --limit 100

# Enable live Groq LLM explanations and export to JSON:
python run_graph.py --limit 20 --llm --output analysis_results.json
```

---

## 📡 REST API Reference

### 1. Health Check
```http
GET /health
```
**Response**:
```json
{
  "status": "ok",
  "transactions_loaded": 7500,
  "model": "RandomForestClassifier",
  "weak_signal": true
}
```

### 2. Predict Existing Transaction by ID
```http
GET /predict/{transaction_id}
```
**Example**: `GET http://127.0.0.1:8001/predict/T1`

### 3. Predict Custom Transaction
```http
POST /predict
Content-Type: application/json
```
**Request Body**:
```json
{
  "user_id": "U3756",
  "transaction_amount": 85000.0,
  "transaction_type": "Transfer",
  "payment_mode": "Net banking",
  "device_type": "Web",
  "device_location": "Bangalore",
  "account_age_days": 15,
  "transaction_hour": 3,
  "previous_failed_attempts": 3,
  "avg_transaction_amount": 2500.0,
  "is_international": 1,
  "ip_risk_score": 0.88,
  "login_attempts_last_24h": 6
}
```

**Response**:
```json
{
  "result": {
    "fraud_score": 82.4,
    "decision": "FRAUD",
    "confidence": 91.5,
    "risk_indicators": [
      "Extremely high amount anomaly (34.0x average)",
      "International transaction",
      "High IP risk score (0.88)",
      "High failed attempts velocity (3)"
    ]
  },
  "agent1_behavior": {
    "behavior_score": 0.85,
    "risk_indicators": ["Amount 34.0x historical average", "International transfer"]
  },
  "agent2_risk": {
    "risk_score": 0.792,
    "risk_level": "HIGH",
    "details": {
      "domain_risk": 0.812,
      "ml_probability": 0.712
    }
  },
  "agent3_validation": {
    "anomaly_score": 0.95,
    "velocity_score": 0.75
  }
}
```

---

## 🧪 Testing & Quality Assurance

The project comes with a comprehensive suite of unit tests, API tests, and browser-driven end-to-end (E2E) automation tests:

```bash
# 1. Run agent mathematics, scoring rules, and threshold unit tests:
python test_agents.py

# 2. Run API health and failover fallback tests:
python test_check_health.py

# 3. Run dataset correlation diagnostic:
python check_labels.py

# 4. (Optional) Run Playwright browser UI end-to-end tests:
pip install playwright
playwright install chromium
python e2e_sidebar_test.py
```

---

## ☁️ Deployment

The repository includes a ready-to-use `render.yaml` blueprint for deploying on [Render.com](https://render.com) as a multi-service stack:

1. **Fork or push this repository** to your GitHub account.
2. Log into **Render** and choose **New > Blueprint**.
3. Connect your repository. Render will automatically read `render.yaml` and provision:
   - `fraud-api`: FastAPI backend running via Uvicorn.
   - `fraud-dashboard`: Streamlit frontend with automatic discovery of the backend service.
4. Add your `GROQ_API_KEY` under the service environment variables.

---

## 📁 Project Structure

```
BANKING-FRAUD-DETECTION-SYSTEM/
├── Data/
│   └── Digital_Payment_Fraud_Detection_Dataset.csv   # 7,500 transaction dataset
│
├── graph/                                            # LangGraph Multi-Agent Architecture
│   ├── __init__.py
│   ├── state.py                                      # FraudState typed schema
│   ├── context.py                                    # Shared dataset memory, ML pipeline & caches
│   ├── nodes.py                                      # Agent 1-4 node implementations
│   └── workflow.py                                   # StateGraph compilation & invocation
│
├── app.py                                            # Streamlit Threat Analysis Console
├── api.py                                            # FastAPI REST backend service
├── run.py                                            # Unified process orchestrator (FastAPI + Streamlit)
├── run_graph.py                                      # Headless LangGraph CLI runner
├── start.bat                                         # Windows 1-click startup script
├── start.sh                                          # Linux/macOS 1-click startup script
│
├── test_agents.py                                    # Agent unit & rule validation tests
├── test_check_health.py                              # FastAPI health & fallback tests
├── e2e_sidebar_test.py                               # Playwright UI end-to-end test suite
├── check_labels.py                                   # Dataset feature vs label correlation diagnostic
│
├── agent1_behavior.py                                # Standalone Agent 1 script
├── agent2_risk_v4.py                                 # Standalone Agent 2 script
├── agent3_validator.py                               # Standalone Agent 3 script
├── agent4_synthesizer.py                             # Standalone Agent 4 script
├── evaluate_system.py                                # End-to-end accuracy evaluation
├── evaluate_agent2.py                                # Agent 2 full-dataset ROC/PR evaluation
│
├── requirements.txt                                  # Production Python dependencies
├── render.yaml                                       # Render Blueprint multi-service config
├── .env.example                                      # Environment variables template
├── .gitignore                                        # Git ignore patterns
└── README.md                                         # Project documentation
```

---

## ⚠️ Limitations & Ethical Disclosure

- **Operational Risk Signal vs. Probability**: Scores produced by the system represent calibrated operational risk indices (0–100), not pure Bayesian fraud probabilities.
- **Dataset Scale**: While the full dataset comprises 7,500 records, batch LLM behavioral analysis is scoped to samples (e.g., 100 transactions) to maintain fast execution and manage API quota.
- **Feature Limitations**: Real-world fraud detection benefits significantly from device fingerprint hashes, IP ASN reputation graphs, merchant codes, and multi-hop account transfer networks not present in basic tabular payment logs.
