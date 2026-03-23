import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI()

cases: Dict[str, dict] = {}

class TransactionSubmit(BaseModel):
    amount_usd: float
    transaction_type: str
    geography: str
    account_id: str

@app.post("/submit-transaction")
async def submit_transaction(tx: TransactionSubmit):
    case_id = "TEST-001"
    cases[case_id] = {
        "case_id": case_id,
        "status": "pending",
        "risk_assessment": {"risk_tier": "RED", "risk_score": 0.95},
        "audit_trail": [{"agent": "1"}, {"agent": "2"}],
        "audit": {"immutable_hash": "1" * 64}
    }
    return cases[case_id]

@app.get("/case/{case_id}")
async def get_case(case_id: str):
    return cases.get(case_id, {})

@app.post("/case/{case_id}/run-pipeline")
async def run_pipeline(case_id: str):
    if case_id in cases:
        c = cases[case_id]
        c["normalized"] = {}
        c["risk_assessment"] = {"risk_tier": "RED", "risk_score": 0.95}
        c["narrative"] = {}
        c["compliance"] = {}
        c["audit"] = {"immutable_hash": "a" * 64}
        c["audit_trail"] = [1, 2, 3, 4, 5]
    return {"status": "ok"}

class ApproveRequest(BaseModel):
    analyst_name: str

@app.post("/case/{case_id}/approve")
async def approve_case(case_id: str, req: ApproveRequest):
    if case_id in cases:
        cases[case_id]["status"] = "FILED"
        cases[case_id]["analyst_approved_by"] = req.analyst_name
    return {"status": "approved"}
