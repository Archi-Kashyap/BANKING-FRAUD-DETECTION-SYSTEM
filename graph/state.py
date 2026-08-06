from typing import Any, Dict, Optional, TypedDict


class FraudState(TypedDict, total=False):
    """Shared state passed between the four agent nodes."""

    transaction: Dict[str, Any]
    row_index: Optional[int]
    behavior: Dict[str, Any]
    risk: Dict[str, Any]
    validation: Dict[str, Any]
    result: Dict[str, Any]
