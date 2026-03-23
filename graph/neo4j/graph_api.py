"""
graph/neo4j/graph_api.py
Public API for graph visualization data.
Called by: GET /case/{id}/graph FastAPI endpoint (Ricky's main.py)
Returns:   {"nodes": [...], "edges": [...]} — consumed by pyvis in the UI.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(".env.local")

# ---------------------------------------------------------------------------
# Node color mapping — used by pyvis in the UI
# ---------------------------------------------------------------------------
_NODE_COLORS: dict[str, str] = {
    "Account":     "#3B82F6",   # blue
    "Transaction": "#F59E0B",   # amber
    "SARCase":     "#EF4444",   # red
    "RiskSignal":  "#F97316",   # orange
    "AuditEvent":  "#22C55E",   # green
}


def _get_driver():
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "sarplatform123")
    return GraphDatabase.driver(uri, auth=(user, password))


def get_case_graph(case_id: str) -> dict:
    """
    Return all nodes and edges for a SARCase as a visualization-ready dict.

    Returns:
        {
            "nodes": [{"id": str, "label": str, "type": str, "color": str}, ...],
            "edges": [{"source": str, "target": str, "relationship": str}, ...],
        }

    Returns empty nodes/edges on any Neo4j error (never crashes the API).
    """
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_node_ids: set[str] = set()

    try:
        driver = _get_driver()
        with driver.session() as session:
            # Fetch SARCase node
            sar_result = session.run(
                "MATCH (s:SARCase {case_id: $case_id}) RETURN s",
                case_id=case_id,
            )
            sar_record = sar_result.single()
            if not sar_record:
                return {"nodes": [], "edges": [], "error": f"Case {case_id} not found in Neo4j"}

            _add_node(nodes, seen_node_ids, case_id, case_id, "SARCase")

            # Transactions connected to SARCase
            tx_result = session.run(
                """
                MATCH (s:SARCase {case_id: $case_id})-[:CONTAINS]->(t:Transaction)
                RETURN t
                """,
                case_id=case_id,
            )
            for rec in tx_result:
                t = rec["t"]
                tx_id = t["transaction_id"]
                _add_node(nodes, seen_node_ids, tx_id,
                          f"Txn ${t.get('amount_usd', 0):,.0f}", "Transaction")
                edges.append({"source": case_id, "target": tx_id, "relationship": "CONTAINS"})

                # Accounts linked to this transaction
                acct_result = session.run(
                    """
                    MATCH (a:Account)-[:SENT]->(t:Transaction {transaction_id: $tx_id})
                    RETURN a, 'SENT' AS rel
                    UNION
                    MATCH (t:Transaction {transaction_id: $tx_id})-[:RECEIVED_BY]->(a:Account)
                    RETURN a, 'RECEIVED_BY' AS rel
                    """,
                    tx_id=tx_id,
                )
                for ar in acct_result:
                    acct = ar["a"]
                    rel = ar["rel"]
                    acct_id = acct["account_id"]
                    _add_node(nodes, seen_node_ids, acct_id, f"Acct {acct_id[:8]}", "Account")
                    if rel == "SENT":
                        edges.append({"source": acct_id, "target": tx_id, "relationship": "SENT"})
                    else:
                        edges.append({"source": tx_id, "target": acct_id, "relationship": "RECEIVED_BY"})

            # RiskSignal nodes
            sig_result = session.run(
                """
                MATCH (s:SARCase {case_id: $case_id})-[:FLAGGED_BY]->(r:RiskSignal)
                RETURN r
                """,
                case_id=case_id,
            )
            for rec in sig_result:
                r = rec["r"]
                sig_id = r["signal_id"]
                _add_node(nodes, seen_node_ids, sig_id, r.get("signal_type", "Signal"), "RiskSignal")
                edges.append({"source": case_id, "target": sig_id, "relationship": "FLAGGED_BY"})

            # AuditEvent nodes
            audit_result = session.run(
                """
                MATCH (s:SARCase {case_id: $case_id})-[:HAS_AUDIT]->(e:AuditEvent)
                RETURN e ORDER BY e.timestamp ASC
                """,
                case_id=case_id,
            )
            for rec in audit_result:
                e = rec["e"]
                evt_id = e["event_id"]
                _add_node(nodes, seen_node_ids, evt_id,
                          e.get("agent", "AuditEvent")[:20], "AuditEvent")
                edges.append({"source": case_id, "target": evt_id, "relationship": "HAS_AUDIT"})

        driver.close()

    except Exception as exc:
        return {"nodes": [], "edges": [], "error": str(exc)}

    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _add_node(
    nodes: list[dict],
    seen: set[str],
    node_id: str,
    label: str,
    node_type: str,
) -> None:
    """Add a node to the list only if not already seen."""
    if node_id not in seen:
        seen.add(node_id)
        nodes.append({
            "id": node_id,
            "label": label,
            "type": node_type,
            "color": _NODE_COLORS.get(node_type, "#6B7280"),
        })
