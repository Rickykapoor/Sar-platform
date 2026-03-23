"""
Agent 5 — Audit Node
Owned by: Anshul

Responsibilities:
- Serialize the full SARCase to JSON and compute a SHA256 immutable hash
- Populate state.audit (AuditRecord)
- Append a final entry to state.audit_trail
- Write an AuditEvent node to Neo4j via GraphWriter (safe no-op if unavailable)

This is the LAST node in the LangGraph pipeline before END.
Agent 6 (human review) is NOT in the graph — it is triggered by the API.
Agent 5 — Audit Trail Writer
LangGraph node: hashes full case state, writes to Neo4j, populates state.audit.
"""

from __future__ import annotations

import hashlib
import logging
import os
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from agents.shared.schemas import AuditRecord, SARCase

logger = logging.getLogger(__name__)


def _try_write_neo4j(state: SARCase, event: dict) -> str:
    """
    Attempt to write an AuditEvent node to Neo4j via GraphWriter.
    Returns the neo4j node id string on success, or a placeholder on failure.
    Importing GraphWriter inside the function keeps Agent 5 independent of
    Nisarg's Day 1 branch — if the import fails we log and continue.
    """
    try:
        from graph.neo4j.init_schema import GraphWriter  # type: ignore[attr-defined]
        from neo4j import GraphDatabase
        from dotenv import load_dotenv

        load_dotenv(".env.local")
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "sarplatform123")

        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        writer = GraphWriter(driver)
        node_id = writer.write_audit_event(event)
        driver.close()
        return str(node_id)
    except ImportError:
        logger.warning(
            "Agent 5: GraphWriter not yet available (Nisarg Day 1 in progress). "
            "Skipping Neo4j write — audit hash is still recorded in state."
        )
        return f"pending-neo4j-{uuid.uuid4().hex[:8]}"
    except Exception as exc:
        logger.error("Agent 5: Neo4j write failed: %s", exc)
        return f"neo4j-error-{uuid.uuid4().hex[:8]}"
import json
import uuid
from datetime import datetime

from agents.shared.schemas import SARCase, AuditRecord


def _serialize_state(state: SARCase) -> str:
    """Serialize SARCase to a deterministic JSON string for hashing."""
    # Use model_dump with explicit mode to handle datetime serialization
    data = state.model_dump(mode="json")
    return json.dumps(data, sort_keys=True, default=str)


async def agent5_write_audit(state: SARCase) -> SARCase:
    """
    LangGraph node — Agent 5: Audit Trail Writer.

    Receives the complete SARCase after all upstream agents have run.
    Produces an immutable SHA256 hash of the entire case, creates an AuditRecord,
    and appends a final audit_trail entry.
    """
    try:
        # ------------------------------------------------------------------ #
        # 1. Serialize entire SARCase to canonical JSON string
        # ------------------------------------------------------------------ #
        # model_dump_json() serialises all Pydantic types (datetime, enums …)
        # consistently.  We exclude the audit field itself so the hash covers
        # only upstream agent outputs — this makes the hash deterministic even
        # if we retry Agent 5.
        json_str: str = state.model_dump_json(exclude={"audit"})

        # ------------------------------------------------------------------ #
        # 2. Compute SHA256 immutable hash (64-character hex string)
        # ------------------------------------------------------------------ #
        immutable_hash: str = hashlib.sha256(json_str.encode("utf-8")).hexdigest()

        # ------------------------------------------------------------------ #
        # 3. Build the AuditEvent payload for Neo4j
        # ------------------------------------------------------------------ #
        audit_event: dict = {
            "event_id": f"AE-{state.case_id}-{uuid.uuid4().hex[:8]}",
            "agent": "Agent 5 - Audit",
            "action": "Generated immutable SHA256 audit hash for full SARCase",
            "confidence": 1.0,
            "timestamp": datetime.now().isoformat(),
            "immutable_hash": immutable_hash,
            "case_id": state.case_id,
        }

        # ------------------------------------------------------------------ #
        # 4. Attempt to write AuditEvent to Neo4j
        # ------------------------------------------------------------------ #
        neo4j_node_id = _try_write_neo4j(state, audit_event)

        # ------------------------------------------------------------------ #
        # 5. Populate state.audit using the committed AuditRecord schema
        #    Fields per agents/shared/schemas.py:
        #      case_id, neo4j_audit_node_id, agent_decisions, shap_explanations,
        #      data_sources_cited, audit_timestamp, immutable_hash
        # ------------------------------------------------------------------ #
        shap_explanations: dict = {}
        if state.risk_assessment is not None:
            # RiskAssessment doesn't store raw SHAP but we can surface signals
            shap_explanations = {
                signal.signal_type: signal.confidence
                for signal in state.risk_assessment.signals
            }

        state.audit = AuditRecord(
            case_id=state.case_id,
            neo4j_audit_node_id=neo4j_node_id,
            agent_decisions=list(state.audit_trail),   # snapshot of the timeline so far
            shap_explanations=shap_explanations,
            data_sources_cited=[
                "agents/agent1_ingestion",
                "agents/agent2_risk",
                "agents/agent3_narrative",
                "agents/agent4_compliance",
    Agent 5 — Audit Trail.

    Reads:   full SARCase state
    Writes:  state.audit (AuditRecord) with SHA256 immutable hash
    Writes:  Neo4j — SARCase node + AuditEvent node via GraphWriter
    Appends: state.audit_trail
    Never raises.
    """
    try:
        # 1. Serialize and hash the full state
        json_str = _serialize_state(state)
        immutable_hash = hashlib.sha256(json_str.encode()).hexdigest()

        # 2. Build the AuditRecord
        audit_node_id = str(uuid.uuid4())
        state.audit = AuditRecord(
            case_id=state.case_id,
            neo4j_audit_node_id=audit_node_id,
            agent_timeline=state.audit_trail.copy(),
            shap_explanations=state.risk_assessment.shap_values if state.risk_assessment else {},
            data_sources_cited=[
                "XGBoost prediction engine",
                "MiniMax-Text-2.5 LLM",
                "AML compliance rule engine",
                "Neo4j graph database",
            ],
            audit_timestamp=datetime.now(),
            immutable_hash=immutable_hash,
        )

        # ------------------------------------------------------------------ #
        # 6. Append final entry to audit_trail (AFTER building audit record)
        # ------------------------------------------------------------------ #
        state.audit_trail.append({
            "agent": "Agent 5 - Audit",
            "action": (
                f"Audit record created. SHA256 hash computed over full case state. "
                f"Neo4j AuditEvent node: {neo4j_node_id}"
            ),
            "confidence": 1.0,
            "timestamp": datetime.now().isoformat(),
            "immutable_hash": immutable_hash,
        })

        logger.info(
            "Agent 5: Audit complete for case %s | hash=%s…",
            state.case_id,
            immutable_hash[:16],
        )

    except Exception as exc:
        logger.error("Agent 5 unexpected error: %s", exc)
        state.error_log.append({
            "agent": "Agent 5 - Audit",
            "error": str(exc),
            "timestamp": datetime.now().isoformat(),
        })
        # Never raise — always return state so the pipeline can continue
        # 3. Append final entry to audit trail
        final_entry = {
            "agent": "Agent 5 - Audit Trail",
            "action": f"State hashed (SHA256: {immutable_hash[:16]}...) and written to Neo4j",
            "confidence": 1.0,
            "timestamp": datetime.now().isoformat(),
        }
        state.audit_trail.append(final_entry)

        # 4. Write to Neo4j via GraphWriter (lazy import to avoid circular deps)
        try:
            from graph.neo4j.graph_writer import GraphWriter
            gw = GraphWriter()
            gw.write_sar_case(state)
            # Write each audit trail entry as an immutable AuditEvent node
            for entry in state.audit_trail:
                gw.write_audit_event({**entry, "case_id": state.case_id})
            gw.close()
        except Exception as neo4j_err:
            # Neo4j being down must NOT crash the pipeline
            state.error_log.append({
                "agent": "Agent 5 - Audit Trail",
                "error": f"Neo4j write failed (non-fatal): {neo4j_err}",
                "timestamp": datetime.now().isoformat(),
            })

    except Exception as e:
        state.error_log.append({
            "agent": "Agent 5 - Audit Trail",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })

    return state
