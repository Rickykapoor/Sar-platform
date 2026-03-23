// CREATE AuditEvent node — APPEND ONLY.
// NEVER UPDATE or DELETE. This is what makes the audit trail immutable.
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

RETURN e
