"""
batch_loader.py - Resilient Batch JSON Loader & Multi-Agent Graph Helper
========================================================================
Addresses DEF-01: Missing Batch JSON Artifacts Crashing Evaluation Scripts.

Provides robust loading and fallback generation for batch JSON artifacts:
- agent1_results.json
- agent2_results.json
- agent3_results.json
- agent4_results.json / graph_results.json

Resolution hierarchy:
1. Target JSON file on disk (checked via os.path.exists).
2. Alternative source: graph_results.json.
3. Automated helper function: executes multi-agent graph via
   graph.context.get_context() and graph.workflow.analyze_transaction()
   for the first N transactions (default 25) without live LLM calls.
4. Clean, friendly error message and exit code 1 if artifact cannot be found.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional


def run_graph_fallback(limit: int = 25, save_to_disk: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """
    Automated helper function that runs the multi-agent graph via
    graph.context.get_context() and graph.workflow.analyze_transaction()
    for the first `limit` transactions without requiring live LLM API calls.

    Returns a dict with keys: 'agent1', 'agent2', 'agent3', 'agent4'.
    Optionally saves the results to agent1_results.json, agent2_results.json,
    agent3_results.json, and agent4_results.json.
    """
    try:
        from graph.context import get_context
        from graph.workflow import build_workflow, analyze_transaction

        print(f"[INFO] Running multi-agent graph helper for first {limit} transactions (no LLM calls)...")
        ctx = get_context(use_llm=False, verbose=False)
        app = build_workflow(ctx)

        agent1_results: List[Dict[str, Any]] = []
        agent2_results: List[Dict[str, Any]] = []
        agent3_results: List[Dict[str, Any]] = []
        agent4_results: List[Dict[str, Any]] = []

        total = min(limit, len(ctx.df))
        for row_index in range(total):
            transaction = ctx.df.iloc[row_index].to_dict()
            state = analyze_transaction(app, transaction, row_index)
            agent1_results.append(state.get("behavior", {}))
            agent2_results.append(state.get("risk", {}))
            agent3_results.append(state.get("validation", {}))
            agent4_results.append(state.get("result", {}))

        batch = {
            "agent1": agent1_results,
            "agent2": agent2_results,
            "agent3": agent3_results,
            "agent4": agent4_results,
        }

        if save_to_disk:
            mapping = {
                "agent1": "agent1_results.json",
                "agent2": "agent2_results.json",
                "agent3": "agent3_results.json",
                "agent4": "agent4_results.json",
            }
            for key, filename in mapping.items():
                temp_filename = f"{filename}.tmp.{os.getpid()}"
                try:
                    with open(temp_filename, "w", encoding="utf-8") as f:
                        json.dump(batch[key], f, indent=4, ensure_ascii=False)
                    os.replace(temp_filename, filename)
                    print(f"[INFO] Saved auto-generated results to {filename} ({len(batch[key])} records)")
                except Exception as write_err:
                    if os.path.exists(temp_filename):
                        try:
                            os.remove(temp_filename)
                        except OSError:
                            pass
                    print(f"[WARNING] Could not save {filename}: {write_err}")

        return batch
    except Exception as exc:
        print(f"[WARNING] Graph fallback helper execution failed: {exc}")
        return {}


def extract_from_graph_results(agent_id: Any, graph_file: str = "graph_results.json") -> Optional[List[Dict[str, Any]]]:
    """
    Extracts or adapts records from graph_results.json (or agent4_results.json) for the specified agent.
    """
    candidates = [graph_file]
    if "agent4_results.json" not in candidates:
        candidates.append("agent4_results.json")

    target_source = None
    for cand in candidates:
        if os.path.exists(cand):
            target_source = cand
            break

    if not target_source:
        return None

    try:
        with open(target_source, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        if not isinstance(raw_data, list) or len(raw_data) == 0:
            return None

        agent_key = str(agent_id).strip().lower()

        # Agent 4 / System Synthesizer
        if agent_key in ["4", "agent4", "synthesizer", "system"]:
            return raw_data

        records: List[Dict[str, Any]] = []
        for item in raw_data:
            tx_id = str(item.get("transaction_id", ""))
            u_id = str(item.get("user_id", ""))
            agent_scores = item.get("agent_scores", {})

            if agent_key in ["1", "agent1", "behavior"]:
                raw_score = agent_scores.get(
                    "behavior_score",
                    item.get("behavior_score", 0.0) / 100.0 if item.get("behavior_score", 0.0) > 1.0 else item.get("behavior_score", 0.0)
                )
                records.append({
                    "transaction_id": tx_id,
                    "user_id": u_id,
                    "behavior_score": round(float(raw_score), 4),
                    "risk_indicators": item.get("risk_indicators", []),
                    "reasoning": str(item.get("agent1_reasoning") or item.get("reasoning", "")),
                    "agent": "behavior_analyzer",
                })

            elif agent_key in ["2", "agent2", "risk"]:
                raw_score = agent_scores.get(
                    "risk_score",
                    item.get("transaction_score", 0.0) / 100.0 if item.get("transaction_score", 0.0) > 1.0 else item.get("transaction_score", 0.0)
                )
                r_score = round(float(raw_score), 4)
                if r_score >= 0.55:
                    r_level = "HIGH"
                elif r_score >= 0.35:
                    r_level = "MEDIUM"
                else:
                    r_level = "LOW"

                records.append({
                    "transaction_id": tx_id,
                    "user_id": u_id,
                    "risk_score": r_score,
                    "risk_level": r_level,
                    "risk_indicators": item.get("risk_indicators", []),
                    "reasoning": str(item.get("agent2_reasoning") or item.get("reasoning", "")),
                    "agent": "risk_assessor",
                })

            elif agent_key in ["3", "agent3", "validator"]:
                raw_anomaly = agent_scores.get(
                    "anomaly_score",
                    item.get("anomaly_score", 0.0) / 100.0 if item.get("anomaly_score", 0.0) > 1.0 else item.get("anomaly_score", 0.0)
                )
                raw_velocity = agent_scores.get(
                    "velocity_score",
                    item.get("velocity_score", 0.0) / 100.0 if item.get("velocity_score", 0.0) > 1.0 else item.get("velocity_score", 0.0)
                )
                records.append({
                    "transaction_id": tx_id,
                    "user_id": u_id,
                    "agent": "transaction_validator",
                    "anomaly_score": round(float(raw_anomaly), 4),
                    "velocity_score": round(float(raw_velocity), 4),
                    "risk_indicators": item.get("risk_indicators", []),
                    "reasoning": str(item.get("agent3_reasoning") or item.get("reasoning", "")),
                })

        return records if records else None
    except Exception as exc:
        print(f"[WARNING] Could not parse alternative source {graph_file}: {exc}")
        return None


def load_agent_results(
    agent_id: Any,
    target_file: Optional[str] = None,
    fallback_file: str = "graph_results.json",
    run_limit: int = 25,
    auto_generate: bool = True,
    save_generated: bool = True
) -> List[Dict[str, Any]]:
    """
    Main robust loader for batch JSON artifacts.

    1. Checks if `target_file` exists via os.path.exists(). If so, loads it.
    2. If missing, checks if `fallback_file` (graph_results.json) exists as an alternative source.
    3. If fallback is missing or cannot be used, invokes run_graph_fallback() helper for `run_limit` rows.
    4. If file cannot be found or generated, prints a clear friendly error message and exits cleanly.
    """
    norm_id = str(agent_id).strip().lower()
    if norm_id in ["1", "agent1", "behavior"]:
        default_target = "agent1_results.json"
        agent_key = "agent1"
    elif norm_id in ["2", "agent2", "risk"]:
        default_target = "agent2_results.json"
        agent_key = "agent2"
    elif norm_id in ["3", "agent3", "validator"]:
        default_target = "agent3_results.json"
        agent_key = "agent3"
    elif norm_id in ["4", "agent4", "synthesizer", "system"]:
        default_target = "agent4_results.json"
        agent_key = "agent4"
    else:
        default_target = f"agent{agent_id}_results.json"
        agent_key = f"agent{agent_id}"

    target_file = target_file or default_target

    # 1. Target file exists on disk
    if os.path.exists(target_file):
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                print(f"[INFO] Loaded {len(data)} results from '{target_file}'.")
                return data
        except Exception as read_err:
            print(f"[WARNING] Error reading '{target_file}': {read_err}")

    # 2. Alternative source: graph_results.json
    print(f"[INFO] File '{target_file}' not found. Checking alternative source '{fallback_file}'...")
    extracted = extract_from_graph_results(agent_key, graph_file=fallback_file)
    if extracted:
        print(f"[INFO] Successfully loaded {len(extracted)} records from '{fallback_file}' as alternative source.")
        return extracted

    # 3. Automated helper function: run multi-agent graph
    if auto_generate:
        print(f"[INFO] Alternative source '{fallback_file}' not available. Running multi-agent graph helper...")
        batch = run_graph_fallback(limit=run_limit, save_to_disk=save_generated)
        if batch and agent_key in batch and len(batch[agent_key]) > 0:
            print(f"[INFO] Helper generated {len(batch[agent_key])} records for {agent_key}.")
            return batch[agent_key]

    # 4. Clean error exit
    print(f"File {target_file} not found. Run python run_graph.py --limit 100 --output agent4_results.json to generate pipeline results.")
    sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch JSON generator & loader helper")
    parser.add_argument("--limit", type=int, default=25, help="Number of transactions to run (default: 25)")
    parser.add_argument("--save", action="store_true", default=True, help="Save generated JSON files (default: True)")
    parser.add_argument("--no-save", action="store_false", dest="save", help="Do not save generated JSON files to disk")
    args = parser.parse_args()

    results = run_graph_fallback(limit=args.limit, save_to_disk=args.save)
    print(f"[DONE] Generated fallback results for {len(results)} agents.")
