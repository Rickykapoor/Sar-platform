// Get the full subgraph for a SARCase — all connected nodes and relationships
MATCH (s:SARCase {case_id: $case_id})
OPTIONAL MATCH (s)-[r1:CONTAINS]->(t:Transaction)
OPTIONAL MATCH (t)-[r2:SENT|RECEIVED_BY]-(a:Account)
OPTIONAL MATCH (s)-[r3:FLAGGED_BY]->(sig:RiskSignal)
OPTIONAL MATCH (s)-[r4:HAS_AUDIT]->(e:AuditEvent)
RETURN
    s,
    collect(DISTINCT t)   AS transactions,
    collect(DISTINCT a)   AS accounts,
    collect(DISTINCT sig) AS risk_signals,
    collect(DISTINCT e)   AS audit_events,
    collect(DISTINCT r1)  AS contains_rels,
    collect(DISTINCT r2)  AS account_rels,
    collect(DISTINCT r3)  AS signal_rels,
    collect(DISTINCT r4)  AS audit_rels
