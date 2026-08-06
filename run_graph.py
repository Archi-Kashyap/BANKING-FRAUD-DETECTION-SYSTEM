import argparse
import json

from graph.context import get_context
from graph.workflow import analyze_transaction, build_workflow

OUTPUT_FILE = "graph_results.json"


def main():
    parser = argparse.ArgumentParser(description="Run the multi-agent fraud graph")
    parser.add_argument("--transaction", help="single transaction id, e.g. T5")
    parser.add_argument("--limit", type=int, default=100, help="how many rows to run")
    parser.add_argument("--output", default=OUTPUT_FILE)
    parser.add_argument("--llm", action="store_true", help="add Groq explanations")
    args = parser.parse_args()

    print("=" * 70)
    print("        LANGGRAPH MULTI-AGENT FRAUD DETECTION")
    print("=" * 70)

    ctx = get_context(use_llm=args.llm)
    app = build_workflow(ctx)

    if args.transaction:
        row_index, transaction = ctx.get_transaction(args.transaction)
        state = analyze_transaction(app, transaction, row_index)
        print(json.dumps(state["result"], indent=4))
        return

    results = []
    total = min(args.limit, len(ctx.df))

    for row_index in range(total):
        transaction = ctx.df.iloc[row_index].to_dict()
        state = analyze_transaction(app, transaction, row_index)
        results.append(state["result"])

        if (row_index + 1) % 20 == 0 or (row_index + 1) == total:
            print(f"Processed {row_index + 1}/{total}")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    counts = {"LEGIT": 0, "SUSPICIOUS": 0, "FRAUD": 0}
    for item in results:
        counts[item["decision"]] += 1

    print("\n" + "=" * 70)
    print("             WORKFLOW COMPLETE")
    print("=" * 70)
    print(f"Processed:  {len(results)}")
    print(f"LEGIT:      {counts['LEGIT']}")
    print(f"SUSPICIOUS: {counts['SUSPICIOUS']}")
    print(f"FRAUD:      {counts['FRAUD']}")
    print(f"Saved:      {args.output}")


if __name__ == "__main__":
    main()
