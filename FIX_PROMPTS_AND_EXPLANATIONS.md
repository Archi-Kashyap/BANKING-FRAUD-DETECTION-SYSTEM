# Banking Fraud Detection System — Issue Explanations & Remediation Prompts

This document provides a detailed breakdown of each defect identified during the codebase audit, accompanied by a dedicated, copy-pasteable **AI / Developer Fix Prompt** for each issue.

---

## Table of Contents
1. [DEF-01: Missing Batch JSON Artifacts Crashing Evaluation Scripts](#def-01-missing-batch-json-artifacts-crashing-evaluation-scripts)
2. [DEF-02: Unhandled KeyError: 'transaction_id' in Graph Nodes](#def-02-unhandled-keyerror-transaction_id-in-graph-nodes)
3. [DEF-03: Deceptive 'API Online' Status Masking Backend Outages](#def-03-deceptive-api-online-status-masking-backend-outages)
4. [DEF-04: 10-Second Blocking UI Freeze on Offline API Fallback](#def-04-10-second-blocking-ui-freeze-on-offline-api-fallback)
5. [DEF-05: Hardcoded Benchmark Shortcuts Bypassing Graph Execution](#def-05-hardcoded-benchmark-shortcuts-bypassing-graph-execution)
6. [DEF-06: Agent 3 Dictionary Indicators Serialized as Raw Strings](#def-06-agent-3-dictionary-indicators-serialized-as-raw-strings)
7. [DEF-07: Frontend Discards Graph Explainability and Recomputes Heuristics](#def-07-frontend-discards-graph-explainability-and-recomputes-heuristics)
8. [DEF-08: Lack of Unified Process Orchestration (FastAPI + Streamlit)](#def-08-lack-of-unified-process-orchestration-fastapi--streamlit)
9. [DEF-09: Massive Zombie and Commented-Out Code Clutter](#def-09-massive-zombie-and-commented-out-code-clutter)
10. [DEF-10: Outdated Documentation and Reality Drift in README](#def-10-outdated-documentation-and-reality-drift-in-readme)
11. [DEF-11: Synthetic Dataset Label Disconnection and ML Metric Misrepresentation](#def-11-synthetic-dataset-label-disconnection-and-ml-metric-misrepresentation)

---

## DEF-01: Missing Batch JSON Artifacts Crashing Evaluation Scripts

### Detailed Explanation
- **Impacted Files:** `check_agent1.py`, `check_agent2.py`, `check_agent3.py`, `check_agent4.py`, `evaluate_agent2.py`, `evaluate_system.py`
- **Severity:** `CRITICAL`
- **Root Cause:**
  The check and evaluation scripts were written to ingest pre-computed batch output files:
  - `agent1_results.json`
  - `agent2_results.json`
  - `agent3_results.json`
  - `agent4_results.json`

  For example, `check_agent1.py` executes:
  ```python
  with open("agent1_results.json", "r", encoding="utf-8") as f:
      results = json.load(f)
  ```
  Because these JSON files are not committed to git and are never automatically generated on setup, running any of the validation scripts crashes immediately with:
  ```text
  FileNotFoundError: [Errno 2] No such file or directory: 'agent1_results.json'
  ```
  Furthermore, generating `agent1_results.json` via `agent1_behavior.py` requires 100 sequential LLM calls to Groq, which takes several minutes and exhausts API rate limits.

### Remediation Prompt (DEF-01)
```text
Task: Fix missing batch JSON file crashes in check and evaluation scripts

Problem:
The verification scripts (`check_agent1.py`, `check_agent2.py`, `check_agent3.py`, `check_agent4.py`, `evaluate_agent2.py`, `evaluate_system.py`) crash with `FileNotFoundError` because `agent1_results.json`, `agent2_results.json`, `agent3_results.json`, and `agent4_results.json` are not tracked in the repository.

Requirements:
1. Update `check_agent1.py`, `check_agent2.py`, `check_agent3.py`, `check_agent4.py`, `evaluate_agent2.py`, and `evaluate_system.py` with robust file validation:
   - Check if the target JSON file exists using `os.path.exists()`.
   - If missing, check if `graph_results.json` exists as an alternative source, or provide an automated helper function that runs the multi-agent graph via `graph.context.get_context()` and `graph.workflow.analyze_transaction()` for the first 25 transactions without requiring live LLM API calls.
   - If the file cannot be generated or found, print a clear, friendly error message explaining how to generate the file (e.g., "File agent1_results.json not found. Run python run_graph.py --limit 100 --output agent4_results.json to generate pipeline results.") and exit cleanly with code 0 or 1 instead of an unhandled traceback.
2. Verify all modified check scripts by running:
   - python check_agent1.py
   - python check_agent2.py
   - python check_agent3.py
   - python check_agent4.py
   - python evaluate_agent2.py
   - python evaluate_system.py
```

---

## DEF-02: Unhandled KeyError: 'transaction_id' in Graph Nodes

### Detailed Explanation
- **Impacted Files:** `graph/nodes.py` (Lines 161, 226, 333, 501)
- **Severity:** `CRITICAL`
- **Root Cause:**
  All four agent nodes in LangGraph assume that every transaction dictionary has a `'transaction_id'` key and access it directly with subscript notation:
  ```python
  # graph/nodes.py:161 (behavior_node)
  "transaction_id": str(tx["transaction_id"]),

  # graph/nodes.py:226 (risk_node)
  "transaction_id": str(tx["transaction_id"]),

  # graph/nodes.py:333 (validator_node)
  "transaction_id": str(tx["transaction_id"]),

  # graph/nodes.py:501 (synthesizer_node)
  "transaction_id": str(state["transaction"]["transaction_id"]),
  ```
  If an engineer or API caller executes `analyze_transaction(graph, payload)` where `payload` represents a new, unindexed manual transaction that lacks `"transaction_id"`, the graph crashes during execution with:
  ```text
  KeyError: 'transaction_id'
  During task with name 'behavior_analyzer'
  ```

### Remediation Prompt (DEF-02)
```text
Task: Fix unhandled KeyError: 'transaction_id' across all LangGraph nodes

Problem:
In `graph/nodes.py`, the nodes access `tx["transaction_id"]` directly. If a payload without `"transaction_id"` is passed to `analyze_transaction()`, all four nodes (`behavior_node`, `risk_node`, `validator_node`, and `synthesizer_node`) raise an unhandled `KeyError`.

Requirements:
1. In `graph/nodes.py`, inspect lines 161, 226, 333, and 501 (and any other occurrences of `tx["transaction_id"]`):
   - Replace `str(tx["transaction_id"])` with safe dictionary retrieval: `str(tx.get("transaction_id", "MANUAL"))`.
   - In `synthesizer_node`, replace `str(state["transaction"]["transaction_id"])` with `str(state.get("transaction", {}).get("transaction_id", "MANUAL"))`.
2. In `graph/workflow.py`, ensure `analyze_transaction(app, transaction, row_index=None)` validates that `transaction` has a `"transaction_id"` key, setting `transaction["transaction_id"] = "MANUAL"` if absent.
3. Test your fix by running the following Python command in the terminal:
   python -c "from graph.context import get_context; from graph.workflow import build_workflow, analyze_transaction; ctx = get_context(verbose=False); graph = build_workflow(ctx); res = analyze_transaction(graph, {'user_id': 'U1234', 'transaction_amount': 500.0, 'transaction_type': 'Payment', 'payment_mode': 'UPI', 'device_type': 'Android', 'device_location': 'Delhi', 'account_age_days': 100, 'transaction_hour': 12, 'previous_failed_attempts': 0, 'avg_transaction_amount': 500.0, 'is_international': 0, 'ip_risk_score': 0.1, 'login_attempts_last_24h': 1}); print('SUCCESS:', res['result']['decision'])"
   Ensure it executes with exit code 0 and prints SUCCESS.
```

---

## DEF-03: Deceptive 'API Online' Status Masking Backend Outages

### Detailed Explanation
- **Impacted Files:** `app.py` (Lines 107–120, Lines 670–713, Lines 1413–1422)
- **Severity:** `HIGH`
- **Root Cause:**
  In `app.py`, the `check_health()` function queries `http://127.0.0.1:8001/health`:
  ```python
  def check_health():
      try:
          r = requests.get(f"{API_URL}/health", timeout=1.5)
          if r.status_code == 200:
              return r.json()
      except Exception:
          pass
      rows = len(df_dataset) if not df_dataset.empty else 7500
      return {
          "status": "online",           # <-- Fabricated "online" status!
          "transactions_loaded": rows,
          "model": "Random Forest",
      }
  ```
  When the FastAPI server is not running, the request times out or throws `ConnectionError`. Instead of returning an offline status, the exception handler fabricates `{"status": "online", ...}`.
  The Streamlit sidebar displays a green pulsing dot with `"API online, 7,500 rows loaded"`, which completely misleads the user into thinking the remote API is operational.

### Remediation Prompt (DEF-03)
```text
Task: Fix misleading 'API online' status badge in Streamlit sidebar

Problem:
In `app.py`, `check_health()` catches failed connection attempts to the FastAPI server and returns `{"status": "online"}`, causing the UI to always display "API online" even when the API is completely down.

Requirements:
1. In `app.py`, refactor `check_health()`:
   - When `requests.get` succeeds with HTTP 200, return the API response with `"online": True`.
   - When `requests.get` fails or times out, return:
     ```python
     {
         "online": False,
         "status": "local",
         "transactions_loaded": len(df_dataset) if not df_dataset.empty else 7500,
         "model": "Random Forest (Local Engine)",
     }
     ```
2. Update the sidebar status card rendering (around line 1413 in `app.py`):
   - If `health.get("online", False)` is True:
     - Keep green styling (`background: #051b12; border: 1px solid #134e2b; color: #00ff88;`).
     - Display: `API online, {health['transactions_loaded']:,} rows loaded`.
   - If `health.get("online", False)` is False:
     - Render an amber / cyan local mode card (`background: #071726; border: 1px solid #1b3a57; color: #38bdf8;`):
     - Dot: `#38bdf8` (blue/cyan) or `#eab308` (amber).
     - Display: `Local engine active, {health['transactions_loaded']:,} rows loaded`.
3. Verify that running `streamlit run app.py` without FastAPI running clearly indicates `Local engine active` instead of falsely reporting `API online`.
```

---

## DEF-04: 10-Second Blocking UI Freeze on Offline API Fallback

### Detailed Explanation
- **Impacted Files:** `app.py` (Lines 121–131)
- **Severity:** `HIGH`
- **Root Cause:**
  `app.py` uses `call_api()` to query the FastAPI backend:
  ```python
  def call_api(method, path, payload=None):
      try:
          if method == "GET":
              response = requests.get(f"{API_URL}{path}", timeout=10) # 10-second timeout!
          else:
              response = requests.post(f"{API_URL}{path}", json=payload, timeout=10)
          if response.status_code == 200:
              return response.json()
      except Exception:
          pass
      return None
  ```
  Because the timeout is set to 10 seconds, when the API is offline (the default setup), clicking "Analyze transaction" on any dataset transaction blocks the Python thread for 10 seconds before failing and executing the local fallback. This causes severe lag and makes the dashboard feel unresponsive.

### Remediation Prompt (DEF-04)
```text
Task: Eliminate 10-second UI freeze when FastAPI is offline in Streamlit app

Problem:
In `app.py`, `call_api()` has a 10-second timeout on HTTP requests. When the FastAPI server is not running on port 8001, every transaction analysis attempt hangs for 10 seconds before falling back to `get_local_engine()`.

Requirements:
1. In `app.py`, optimize the API calling strategy:
   - Cache API availability using `st.session_state` or a fast check so that if the API was already found offline during `check_health()`, the app skips the network request immediately and invokes the local engine directly without delay.
   - Reduce the connection timeout in `call_api()` from `10` seconds to `1.0` second (`timeout=1.0`).
2. Ensure that when the API is offline, clicking "Analyze transaction" responds instantaneously (< 500ms) via `get_local_engine()`.
3. Verify by running the Streamlit app locally, clicking "Analyze transaction" on multiple transaction IDs (e.g. `T5`, `T145`, `T200`), and confirming that results appear without the 10-second freeze.
```

---

## DEF-05: Hardcoded Benchmark Shortcuts Bypassing Graph Execution

### Detailed Explanation
- **Impacted Files:** `app.py` (Lines 136–161, Lines 249–288, Lines 1497–1504)
- **Severity:** `HIGH`
- **Root Cause:**
  To guarantee that prototype demo cases matched expected values, `app.py` contains hardcoded bypass branches:
  ```python
  # app.py:136
  if clean_id == "T3768":
      return {
          "verdict": "SAFE",
          "fraud_score": 11.7,
          "confidence": 81.6,
          ...
      }

  # app.py:249
  if (
      payload.get("user_id") == "U9999"
      and abs(float(payload.get("transaction_amount", 0)) - 90000.0) < 1.0
      ...
  ):
      return {
          "verdict": "FRAUD",
          "fraud_score": 89.6,
          ...
      }
  ```
  These short-circuits mean that when demonstrating transaction `T3768` or the manual fraud preset (`U9999`), the real LangGraph multi-agent pipeline is never executed. If a bug is introduced into the graph, it remains hidden during standard demo flows.

### Remediation Prompt (DEF-05)
```text
Task: Remove hardcoded demo shortcuts in app.py to enforce real graph execution

Problem:
In `app.py`, `analyze_dataset_tx()` has a hardcoded branch for `"T3768"` and `analyze_manual_tx()` has a hardcoded branch for `"U9999"`. These shortcuts return static dictionaries and bypass the actual LangGraph agents and ML model.

Requirements:
1. In `app.py`:
   - Remove the `if clean_id == "T3768":` shortcut in `analyze_dataset_tx()`.
   - Remove the `if payload.get("user_id") == "U9999" ...:` shortcut in `analyze_manual_tx()`.
   - Remove the hardcoded preview chip block for `T3768` around line 1497, ensuring all preview chips are dynamically derived from `df_dataset`.
2. Ensure that analyzing `T3768` and `U9999` flows through `call_api()` or `get_local_engine()`, calculating real scores through `graph/workflow.py`.
3. If the actual graph outputs for `T3768` and `U9999` differ slightly from prototype numbers, adjust the graph thresholds or weights in `graph/nodes.py` rather than hardcoding fake return dictionaries in the UI layer.
4. Run `python e2e_sidebar_test.py` and `python test_agents.py` to verify that all end-to-end tests continue to pass.
```

---

## DEF-06: Agent 3 Dictionary Indicators Serialized as Raw Strings

### Detailed Explanation
- **Impacted Files:** `graph/nodes.py` (Lines 34–39)
- **Severity:** `MEDIUM`
- **Root Cause:**
  Agent 3 (`validator_node`) generates indicators as Python dictionaries containing structured metadata:
  ```python
  # graph/nodes.py:343
  indicators.append({
      "indicator": "Failed transaction attempts",
      "score": failed_risk,
      "description": f"{int(failed)} failed attempts.",
  })
  ```
  However, the helper function `get_indicators()` in `graph/nodes.py` converts every item in the indicator list using `str()`:
  ```python
  def get_indicators(data):
      indicators = data.get("risk_indicators", []) or []
      if isinstance(indicators, list):
          return [str(x).strip() for x in indicators if str(x).strip()]
  ```
  Because `str()` is called on a dictionary, the output becomes raw Python dictionary literal text:
  `"{'indicator': 'Failed transaction attempts', 'score': 0.3, 'description': '1 failed attempts.'}"`
  This raw dict text appears in API responses, CLI logs, and graph results.

### Remediation Prompt (DEF-06)
```text
Task: Fix raw Python dictionary serialization in risk indicators in graph/nodes.py

Problem:
Agent 3 in `graph/nodes.py` returns risk indicators as dictionaries (e.g. `{"indicator": "...", "description": "..."}`). The helper function `get_indicators()` calls `str(x)` on each item, causing raw Python dict strings like `"{'indicator': 'Failed transaction attempts', ...}"` to appear in the final output.

Requirements:
1. In `graph/nodes.py`, update `get_indicators(data)`:
   ```python
   def get_indicators(data):
       indicators = data.get("risk_indicators", []) or []
       if not isinstance(indicators, list):
           indicators = [indicators]
       formatted = []
       for item in indicators:
           if isinstance(item, dict):
               # Prefer human-readable description, fall back to indicator title
               desc = item.get("description") or item.get("indicator")
               if desc:
                   formatted.append(str(desc).strip())
           elif item is not None:
               s = str(item).strip()
               if s:
                   formatted.append(s)
       return formatted
   ```
2. Verify the fix by running:
   python -c "from graph.nodes import get_indicators; test_data = {'risk_indicators': [{'indicator': 'Failed attempts', 'description': '3 failed logins detected.'}, 'International payment']}; print(get_indicators(test_data))"
   Ensure the output is: `['3 failed logins detected.', 'International payment']`.
3. Run `python run_graph.py --transaction T5` and confirm that no raw curly-brace dict strings appear in `risk_indicators`.
```

---

## DEF-07: Frontend Discards Graph Explainability and Recomputes Heuristics

### Detailed Explanation
- **Impacted Files:** `app.py` (Lines 198–221, Lines 320–339)
- **Severity:** `MEDIUM`
- **Root Cause:**
  When `app.py` receives results from the multi-agent graph, it ignores `res["risk_indicators"]`. Instead, it recomputes a disconnected set of indicators directly inside `app.py`:
  ```python
  # app.py:204
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
  ```
  This creates a split-brain condition: the backend agents might detect behavioral deviations or ML anomalies, but the frontend "Why this verdict" HUD displays only what its own hardcoded threshold checks evaluate.

### Remediation Prompt (DEF-07)
```text
Task: Connect multi-agent graph explainability indicators directly to Streamlit UI

Problem:
In `app.py`, `analyze_dataset_tx()` and `analyze_manual_tx()` ignore the `risk_indicators` produced by the LangGraph agents. Instead, they recompute a separate set of hardcoded heuristics, discarding the multi-agent system's reasoning.

Requirements:
1. In `app.py`, inside `analyze_dataset_tx()`:
   - Extract indicators from the graph result: `graph_indicators = res.get("risk_indicators", [])`.
   - If `graph_indicators` is populated, use it as `indicators`.
   - If empty or as a fallback, retain the dataset heuristic indicators.
2. In `app.py`, inside `analyze_manual_tx()`:
   - Similarly, extract `graph_indicators = res.get("risk_indicators", [])` and pass them to the returned dictionary.
3. In the UI rendering section (around line 1796 of `app.py`), ensure that all indicators returned by the agents are cleanly formatted in the "Why this verdict" HUD cards.
4. Run `python e2e_sidebar_test.py` to confirm the UI displays the agent indicators accurately.
```

---

## DEF-08: Lack of Unified Process Orchestration (FastAPI + Streamlit)

### Detailed Explanation
- **Impacted Files:** Project Root (`api.py`, `app.py`)
- **Severity:** `MEDIUM`
- **Root Cause:**
  The project is split into two independent services:
  - FastAPI server (`api.py`) on port 8001
  - Streamlit dashboard (`app.py`) on port 8503 (or 8501)

  There is no startup script (`run.py`, `start.bat`, or `Procfile`) to launch both services concurrently. When users clone the repo and run `streamlit run app.py`, the backend API remains offline, forcing the app into degraded local fallback mode.

### Remediation Prompt (DEF-08)
```text
Task: Create a unified process orchestration launcher for FastAPI and Streamlit

Problem:
There is no automated script to start both the FastAPI backend (`api.py` on port 8001) and the Streamlit frontend (`app.py` on port 8503). Users must manually open two terminals and run separate commands.

Requirements:
1. Create a `run.py` script in the project root:
   - Use Python's `subprocess` or `multiprocessing` to start:
     1. `uvicorn api:api --host 127.0.0.1 --port 8001 --log-level info`
     2. `streamlit run app.py --server.port 8503 --server.headless false`
   - Include health-check polling: wait for `http://127.0.0.1:8001/health` to respond before launching the browser.
   - Handle graceful shutdown: when `Ctrl+C` is pressed, terminate both child processes cleanly without leaving orphaned Python processes.
2. Create a Windows batch script `start.bat` and Unix shell script `start.sh` that invoke `python run.py`.
3. Test running `python run.py` and confirm that both the API and Streamlit UI start up and communicate properly.
```

---

## DEF-09: Massive Zombie and Commented-Out Code Clutter

### Detailed Explanation
- **Impacted Files:** `evaluate_system.py`, `agent3_validator.py`, `agent4_synthesizer.py`, `agent2_risk_v4.py`
- **Severity:** `LOW`
- **Root Cause:**
  Throughout development, older implementations were commented out rather than deleted or committed to git history:
  - `evaluate_system.py`: Lines 1–559 are commented out (over 55% of the file).
  - `agent3_validator.py`: 748 out of 1,522 lines (49% of the file) are commented out.
  
  This zombie code makes it difficult to navigate files, breaks syntax highlighting in some editors, and confuses developers auditing the codebase.

### Remediation Prompt (DEF-09)
```text
Task: Prune zombie and commented-out code blocks across evaluation and agent files

Problem:
`evaluate_system.py` contains 559 lines of commented-out legacy code, and `agent3_validator.py` contains 748 lines of commented-out code, causing severe codebase bloat.

Requirements:
1. Clean `evaluate_system.py`:
   - Remove lines 1–559 of commented-out legacy code.
   - Keep only the active implementation starting at `import json`.
   - Ensure imports and functions are clean, PEP 8 compliant, and free of commented dead code.
2. Clean `agent3_validator.py`:
   - Remove legacy commented blocks (e.g. lines 430–500, lines 950–1020).
   - Retain only the active classes, calculation rules, and execution entry points.
3. Clean `agent4_synthesizer.py` and `agent2_risk_v4.py` of any obsolete commented blocks.
4. Verify by running `python test_agents.py` to confirm that all logic and unit tests still pass.
```

---

## DEF-10: Outdated Documentation and Reality Drift in README

### Detailed Explanation
- **Impacted Files:** `README.md`
- **Severity:** `LOW`
- **Root Cause:**
  `README.md` documents only an obsolete 6-step CLI batch workflow:
  ```bash
  python agent1_behavior.py
  python agent2_risk_v4.py
  python agent3_validator.py
  python agent4_synthesizer.py
  python evaluate_system.py
  ```
  The documentation has **zero mention** of:
  - `app.py` (The main Streamlit dashboard)
  - `api.py` (The FastAPI REST backend)
  - `graph/` (The LangGraph multi-agent architecture)
  - `run_graph.py` (The unified graph CLI runner)
  - `e2e_sidebar_test.py` (The Playwright automated test suite)

  Any new user following the README instructions will run broken batch scripts and will never discover the web interface.

### Remediation Prompt (DEF-10)
```text
Task: Update README.md to document modern LangGraph, Streamlit, and FastAPI architecture

Problem:
`README.md` describes an outdated 6-step sequential batch script pipeline and makes no mention of the Streamlit dashboard (`app.py`), FastAPI service (`api.py`), or LangGraph architecture (`graph/`).

Requirements:
1. Update `README.md` Section 3 ("Architecture"):
   - Add architecture diagram showing `FastAPI (api.py)` and `Streamlit (app.py)` connected to `LangGraph Engine (graph/)`.
2. Update Section 10 & 11 ("Installation" and "How to Run"):
   - Add instructions for running the Streamlit app: `streamlit run app.py`.
   - Add instructions for running the FastAPI backend: `uvicorn api:api --reload --port 8001`.
   - Add instructions for CLI analysis: `python run_graph.py --transaction T5`.
   - Add instructions for running automated tests: `python test_agents.py` and `python e2e_sidebar_test.py`.
3. Move the legacy batch pipeline instructions into a "Legacy Batch Pipeline" appendix section.
```

---

## DEF-11: Synthetic Dataset Label Disconnection and ML Metric Misrepresentation

### Detailed Explanation
- **Impacted Files:** `check_labels.py`, `Data/Digital_Payment_Fraud_Detection_Dataset.csv`, `graph/context.py`, `app.py`
- **Severity:** `INFORMATIONAL`
- **Root Cause:**
  Running `python check_labels.py` proves that all single-feature ROC-AUCs in `Digital_Payment_Fraud_Detection_Dataset.csv` hover around 0.50 (random chance):
  - `transaction_amount`: 0.4882
  - `ip_risk_score`: 0.5042
  - `login_attempts_last_24h`: 0.5189
  - `account_age_days`: 0.5347
  
  The dataset's `fraud_label` column has virtually no statistical dependency on transaction features. Consequently, the trained `RandomForestClassifier` achieves an out-of-fold PR-AUC of only ~0.07 (barely above prevalence baseline 0.065). The system's predictive performance relies almost entirely on deterministic domain rules, but user-facing interfaces may give users the impression that a high-accuracy ML model is driving the classifications.

### Remediation Prompt (DEF-11)
```text
Task: Clarify ML model limitations and weak signal transparency across UI and docs

Problem:
The synthetic dataset labels have near-zero statistical correlation with transaction features (all feature ROC-AUCs ≈ 0.50). The Random Forest model provides only supporting signal, while domain heuristics do all meaningful separation. The UI telemetry should honestly communicate this to users.

Requirements:
1. In `app.py`, update the sidebar telemetry section (lines 1426–1430):
   - Replace `Model: Random Forest` with:
     - `Model: Hybrid (Rules + RF)`
     - Add tooltip or note: `ML Signal: Supporting (Weak Dataset Baseline)`.
2. In the "▶ How it works" expander in `app.py`:
   - Include a concise note under Agent 2: "Uses expert behavioral rules as primary signal; Random Forest model provides secondary support due to low synthetic dataset feature correlation."
3. In `README.md`, ensure the "ML Methodology & Honest Signal Report" section remains prominent so users and stakeholders understand why hybrid domain scoring is utilized instead of pure ML classification.
4. Verify by inspecting the rendered sidebar in `app.py` to ensure transparency labels display cleanly.
```
