from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from graph.context import get_context
from graph.workflow import analyze_transaction, build_workflow

engine = {}


@asynccontextmanager
async def lifespan(app):
    ctx = get_context()
    engine["ctx"] = ctx
    engine["graph"] = build_workflow(ctx)
    yield
    engine.clear()


api = FastAPI(
    title="Multi-Agent Fraud Detection API",
    version="1.0",
    lifespan=lifespan,
)


class Transaction(BaseModel):
    user_id: str = Field(min_length=1)
    transaction_amount: float = Field(gt=0)
    transaction_type: str = Field(min_length=1)
    payment_mode: str = Field(min_length=1)
    device_type: str = Field(min_length=1)
    device_location: str = Field(min_length=1)
    account_age_days: int = Field(ge=0)
    transaction_hour: int = Field(ge=0, le=23)
    previous_failed_attempts: int = Field(ge=0)
    avg_transaction_amount: float = Field(ge=0)
    is_international: int = Field(ge=0, le=1)
    ip_risk_score: float = Field(ge=0, le=1)
    login_attempts_last_24h: int = Field(ge=0)
    transaction_id: str = "MANUAL"


def run(transaction, row_index=None):
    state = analyze_transaction(engine["graph"], transaction, row_index)
    return {
        "result": state["result"],
        "agent1_behavior": state["behavior"],
        "agent2_risk": state["risk"],
        "agent3_validation": state["validation"],
    }


@api.get("/health")
def health():
    ctx = engine["ctx"]
    return {
        "status": "ok",
        "transactions_loaded": len(ctx.df),
        "model": ctx.model_name,
        "weak_signal": ctx.weak_signal,
    }


@api.get("/predict/{transaction_id}")
def predict_by_id(transaction_id: str):
    try:
        row_index, transaction = engine["ctx"].get_transaction(transaction_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown transaction: {transaction_id}")
    return run(transaction, row_index)


@api.post("/predict")
def predict(transaction: Transaction):
    return run(transaction.model_dump())
