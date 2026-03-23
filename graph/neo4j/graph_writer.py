"""
graph/neo4j/graph_writer.py
GraphWriter — writes SAR case data into Neo4j.
RULE: AuditEvent nodes are APPEND ONLY. Never UPDATE or DELETE them.
Uses env vars: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver

load_dotenv(".env.local")

if TYPE_CHECKING:
    from agents.shared.schemas import SARCase


def _get_driver() -> Driver:
    """Create a Neo4j driver from environment variables."""
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "sarplatform123")
    return GraphDatabase.driver(uri, auth=(user, password))


class GraphWriter:
    """
    Writes SAR pipeline data into Neo4j.
    Instantiate once and reuse (driver is thread-safe).
    """

    def __init__(self, driver: Driver | None = None) -> None:
        self._driver = driver or _get_driver()

    # ------------------------------------------------------------------
    # Write a full SARCase (accounts, transactions, SAR node, signals)
    # ------------------------------------------------------------------
    def write_sar_case(self, state: "SARCase") -> None:
        """
        Write Account, Transaction, RiskSignal, and SARCase nodes to Neo4j.
        Safe to call multiple times — uses MERGE on stable IDs.
        """
        if not state.normalized or not state.risk_assessment:
            return

        with self._driver.session() as session:
            # 1. Write Account nodes
            for tx in state.normalized.transactions:
                session.run(
                    """
                    MERGE (a:Account {account_id: $account_id})
                    ON CREATE SET a.created_at = $created_at, a.account_type = 'checking'
                    """,
                    account_id=tx.account_id,
                    created_at=datetime.now().isoformat(),
                )
                session.run(
                    """
                    MERGE (a:Account {account_id: $account_id})
                    ON CREATE SET a.created_at = $created_at, a.account_type = 'counterparty'
                    """,
                    account_id=tx.counterparty_account_id,
                    created_at=datetime.now().isoformat(),
                )

            # 2. Write Transaction nodes + relationships
            for tx in state.normalized.transactions:
                session.run(
                    """
                    MERGE (t:Transaction {transaction_id: $transaction_id})
                    ON CREATE SET
                        t.amount_usd       = $amount_usd,
                        t.timestamp        = $timestamp,
                        t.transaction_type = $transaction_type,
                        t.channel          = $channel,
                        t.geography        = $geography
                    WITH t
                    MATCH (s:Account {account_id: $sender_id})
                    MERGE (s)-[:SENT]->(t)
                    WITH t
                    MATCH (r:Account {account_id: $receiver_id})
                    MERGE (t)-[:RECEIVED_BY]->(r)
                    """,
                    transaction_id=tx.transaction_id,
                    amount_usd=tx.amount_usd,
                    timestamp=tx.timestamp.isoformat(),
                    transaction_type=tx.transaction_type,
                    channel=tx.channel,
                    geography=tx.geography,
                    sender_id=tx.account_id,
                    receiver_id=tx.counterparty_account_id,
                )

            # 3. Write RiskSignal nodes
            signal_ids = []
            for i, signal in enumerate(state.risk_assessment.signals):
                sig_id = f"{state.case_id}_sig_{i}"
                signal_ids.append(sig_id)
                session.run(
                    """
                    MERGE (r:RiskSignal {signal_id: $signal_id})
                    ON CREATE SET
                        r.signal_type    = $signal_type,
                        r.description    = $description,
                        r.confidence     = $confidence
                    """,
                    signal_id=sig_id,
                    signal_type=signal.signal_type,
                    description=signal.description,
                    confidence=signal.confidence,
                )

            # 4. Write SARCase node + CONTAINS + FLAGGED_BY relationships
            tx_ids = [t.transaction_id for t in state.normalized.transactions]
            immutable_hash = state.audit.immutable_hash if state.audit else ""

            session.run(
                """
                MERGE (s:SARCase {case_id: $case_id})
                ON CREATE SET
                    s.status         = $status,
                    s.risk_score     = $risk_score,
                    s.tier           = $tier,
                    s.immutable_hash = $immutable_hash,
                    s.created_at     = $created_at
                WITH s
                UNWIND $tx_ids AS tx_id
                MATCH (t:Transaction {transaction_id: tx_id})
                MERGE (s)-[:CONTAINS]->(t)
                WITH s
                UNWIND $signal_ids AS sig_id
                MATCH (r:RiskSignal {signal_id: sig_id})
                MERGE (s)-[:FLAGGED_BY]->(r)
                """,
                case_id=state.case_id,
                status=state.status.value,
                risk_score=state.risk_assessment.risk_score,
                tier=state.risk_assessment.risk_tier.value,
                immutable_hash=immutable_hash,
                created_at=datetime.now().isoformat(),
                tx_ids=tx_ids,
                signal_ids=signal_ids,
            )

    # ------------------------------------------------------------------
    # Append-only AuditEvent write
    # ------------------------------------------------------------------
    def write_audit_event(self, event: dict) -> None:
        """
        CREATE a new AuditEvent node linked to the SARCase.
        APPEND ONLY — never call UPDATE or DELETE on AuditEvent nodes.
        """
        event_id = str(uuid.uuid4())
        case_id = event.get("case_id", "")

        with self._driver.session() as session:
            session.run(
                """
                CREATE (e:AuditEvent {
                    event_id:   $event_id,
                    agent:      $agent,
                    action:     $action,
                    confidence: $confidence,
                    timestamp:  $timestamp
                })
                WITH e
                MATCH (s:SARCase {case_id: $case_id})
                CREATE (s)-[:HAS_AUDIT]->(e)
                """,
                event_id=event_id,
                agent=event.get("agent", "unknown"),
                action=event.get("action", ""),
                confidence=float(event.get("confidence", 0.0)),
                timestamp=event.get("timestamp", datetime.now().isoformat()),
                case_id=case_id,
            )

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        self._driver.close()
