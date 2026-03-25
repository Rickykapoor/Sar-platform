"""
main.py
FastAPI Backend for SAR Platform.
Serves 10 endpoints for the UI to interact with the LangGraph pipeline.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(".env.local")

from agents.shared.schemas import SARCase, SARStatus
from agents.pipeline import app as pipeline_app
from agents.agent3_narrative.node import agent3_generate_narrative
from agents.agent6_review.node import agent6_review
from prediction_engine.simulator import (
    get_structuring_scenario,
    get_layering_scenario,
    get_smurfing_scenario
)
from graph.neo4j.graph_api import get_case_graph

app = FastAPI(title="SAR Platform API", version="1.0.0")

# Setup CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory database for hackathon purposes
import json
import os

DB: Dict[str, SARCase] = {}

if os.path.exists("mock_db.json"):
    try:
        with open("mock_db.json", "r") as f:
            data = json.load(f)
            DB = {k: SARCase(**v) for k, v in data.items()}
        print(f"Loaded {len(DB)} mock cases from mock_db.json")
    except Exception as e:
        print(f"Failed to load mock_db.json: {e}")


class ApproveRequest(BaseModel):
    analyst_name: str = "Analyst-1"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    """Basic health endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ---------------------------------------------------------------------------
# Transaction submission
# ---------------------------------------------------------------------------

@app.post("/submit-transaction")
async def submit_transaction(payload: dict):
    """
    Submits raw transaction payload.
    Initializes SARCase in PENDING state and stores it.
    Returns: {"case_id": "..."}
    """
    try:
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        case = SARCase(
            case_id=case_id,
            status=SARStatus.PENDING,
            raw_transaction=payload
        )
        case.audit_trail.append({
            "agent": "System API",
            "action": f"Transaction submitted and case {case_id} initialized.",
            "confidence": 1.0,
            "timestamp": datetime.now().isoformat()
        })
        DB[case_id] = case
        return {"case_id": case_id, "status": case.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


# ---------------------------------------------------------------------------
# Case listing and retrieval
# ---------------------------------------------------------------------------

@app.get("/cases")
async def get_cases():
    """Returns a list of all cases and their high-level statuses."""
    return [
        {
            "case_id": c.case_id,
            "status": c.status,
            "risk_tier": c.risk_assessment.risk_tier if c.risk_assessment else "pending",
            "subject": c.normalized.subject_name if c.normalized else "Unknown",
            "last_updated": c.audit_trail[-1]["timestamp"] if c.audit_trail else "Unknown"
        }
        for c in DB.values()
    ]


@app.get("/case/{case_id}")
async def get_case(case_id: str):
    """Returns the full SARCase JSON structure."""
    if case_id not in DB:
        raise HTTPException(status_code=404, detail="Case not found")
    return DB[case_id].model_dump()


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

@app.post("/case/{case_id}/run-pipeline")
async def run_pipeline(case_id: str):
    """
    Synchronously triggers the full LangGraph pipeline for the given case.
    Updates the in-memory master state.
    """
    if case_id not in DB:
        raise HTTPException(status_code=404, detail="Case not found")

    case_state = DB[case_id]
    if case_state.status not in [SARStatus.PENDING, SARStatus.IN_REVIEW]:
        raise HTTPException(status_code=400, detail=f"Case already processed (status={case_state.status})")

    try:
        # LangGraph StateGraph compiled with SARCase needs a dict input
        input_dict = case_state.model_dump()
        final_state_dict = await pipeline_app.ainvoke(input_dict)
        # Reconstruct SARCase from the result dict
        updated_case = SARCase(**final_state_dict)
        updated_case.status = SARStatus.IN_REVIEW
        DB[case_id] = updated_case
        return {
            "status": "success",
            "message": "Pipeline completed successfully",
            "case_id": case_id,
            "risk_tier": updated_case.risk_assessment.risk_tier if updated_case.risk_assessment else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Pipeline execution failed", "detail": str(e)})


@app.get("/case/{case_id}/pipeline-status")
async def get_pipeline_status(case_id: str):
    """Returns which agents have completed (non-None outputs in state)."""
    if case_id not in DB:
        raise HTTPException(status_code=404, detail="Case not found")
    case = DB[case_id]
    return {
        "case_id": case_id,
        "status": case.status,
        "agents_completed": {
            "agent1_ingestion": case.normalized is not None,
            "agent2_risk": case.risk_assessment is not None,
            "agent3_narrative": case.narrative is not None,
            "agent4_compliance": case.compliance is not None,
            "agent5_audit": case.audit is not None,
            "agent6_review": case.analyst_approved_by is not None,
        },
        "audit_trail_entries": len(case.audit_trail),
        "error_count": len(case.error_log),
    }


# ---------------------------------------------------------------------------
# Narrative generation (standalone for UI button)
# ---------------------------------------------------------------------------

@app.post("/case/{case_id}/generate-narrative")
async def generate_narrative(case_id: str):
    """
    Triggers Agent 3 narrative generation standalone (for the UI narrative button).
    The case must have passed Agent 2 (risk_assessment must be populated).
    """
    if case_id not in DB:
        raise HTTPException(status_code=404, detail="Case not found")

    case = DB[case_id]
    if not case.risk_assessment:
        raise HTTPException(
            status_code=400,
            detail="Risk assessment not complete. Run the pipeline first."
        )

    try:
        updated_case = await agent3_generate_narrative(case)
        DB[case_id] = updated_case
        if updated_case.narrative:
            return {
                "status": "success",
                "narrative": updated_case.narrative.model_dump(),
                "narrative_body": updated_case.narrative.narrative_body,
            }
        else:
            errors = [e.get("error") for e in updated_case.error_log if "Agent 3" in e.get("agent", "")]
            raise HTTPException(
                status_code=500,
                detail={"error": "Narrative generation failed", "errors": errors}
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


# ---------------------------------------------------------------------------
# Case approval and dismissal
# ---------------------------------------------------------------------------

@app.post("/case/{case_id}/approve")
async def approve_case(case_id: str, body: ApproveRequest = ApproveRequest()):
    """Analyst approves the generated SAR for filing."""
    if case_id not in DB:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        case = DB[case_id]
        case = await agent6_review(case, body.analyst_name)
        DB[case_id] = case
        return {"status": "success", "case_status": case.status, "filed_by": body.analyst_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.post("/case/{case_id}/dismiss")
async def dismiss_case(case_id: str):
    """Analyst dismisses the alert (false positive)."""
    if case_id not in DB:
        raise HTTPException(status_code=404, detail="Case not found")

    case = DB[case_id]
    case.status = SARStatus.DISMISSED
    case.audit_trail.append({
        "agent": "Analyst UI",
        "action": "Case dismissed as false positive",
        "confidence": 1.0,
        "timestamp": datetime.now().isoformat()
    })
    return {"status": "success", "case_status": case.status}


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------

@app.get("/case/{case_id}/audit")
async def get_case_audit(case_id: str):
    """Returns just the audit trail for a case."""
    if case_id not in DB:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"audit_trail": DB[case_id].audit_trail}


# ---------------------------------------------------------------------------
# Graph visualization
# ---------------------------------------------------------------------------

@app.get("/case/{case_id}/graph")
async def get_case_graph_endpoint(case_id: str):
    """Fetches nodes and edges for Pyvis visualization (from Neo4j)."""
    if case_id not in DB:
        raise HTTPException(status_code=404, detail="Case not found")

    graph_data = get_case_graph(case_id)
    if "error" in graph_data and not graph_data.get("nodes"):
        # Neo4j may be offline — return empty graph gracefully
        return {"nodes": [], "edges": [], "warning": graph_data.get("error")}

    return graph_data


# ---------------------------------------------------------------------------
# Demo simulation endpoints
# ---------------------------------------------------------------------------

@app.post("/demo/simulate/{scenario}")
async def simulate_scenario(scenario: str):
    """
    Demo endpoint: generates a raw transaction for a scenario and submits it.
    Options: structuring, layering, smurfing
    """
    scenario_map = {
        "structuring": get_structuring_scenario,
        "layering": get_layering_scenario,
        "smurfing": get_smurfing_scenario,
    }

    if scenario not in scenario_map:
        raise HTTPException(status_code=400, detail=f"Invalid scenario. Choose from: {list(scenario_map.keys())}")

    tx_payload = scenario_map[scenario]()
    result = await submit_transaction(tx_payload)

    return {
        "case_id": result["case_id"],
        "scenario_type": scenario,
        "raw_transaction": tx_payload
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
