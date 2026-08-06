from langgraph.graph import END, START, StateGraph

from .context import get_context
from .nodes import behavior_node, risk_node, synthesizer_node, validator_node
from .state import FraudState


def _bind(node, ctx):
    def run(state):
        return node(state, ctx)
    return run


def build_workflow(ctx=None):
    """START -> Agent 1 -> Agent 2 -> Agent 3 -> Agent 4 -> END"""
    ctx = ctx or get_context()

    graph = StateGraph(FraudState)

    graph.add_node("behavior_analyzer", _bind(behavior_node, ctx))
    graph.add_node("risk_assessor", _bind(risk_node, ctx))
    graph.add_node("transaction_validator", _bind(validator_node, ctx))
    graph.add_node("decision_synthesizer", _bind(synthesizer_node, ctx))

    graph.add_edge(START, "behavior_analyzer")
    graph.add_edge("behavior_analyzer", "risk_assessor")
    graph.add_edge("risk_assessor", "transaction_validator")
    graph.add_edge("transaction_validator", "decision_synthesizer")
    graph.add_edge("decision_synthesizer", END)

    return graph.compile()


def analyze_transaction(app, transaction, row_index=None):
    """Runs one transaction through the graph and returns the final state."""
    return app.invoke({"transaction": transaction, "row_index": row_index})


def analyze_by_id(app, ctx, transaction_id):
    row_index, transaction = ctx.get_transaction(transaction_id)
    return analyze_transaction(app, transaction, row_index)
