// CREATE SARCase node and CONTAINS relationship to each Transaction
// Uses CREATE (not MERGE) because each case_id is unique per constraint
CREATE (s:SARCase {
    case_id:        $case_id,
    status:         $status,
    risk_score:     $risk_score,
    tier:           $tier,
    immutable_hash: $immutable_hash,
    created_at:     $created_at
})

WITH s
UNWIND $transaction_ids AS tx_id
MATCH (t:Transaction {transaction_id: tx_id})
MERGE (s)-[:CONTAINS]->(t)

WITH s
UNWIND $risk_signal_ids AS sig_id
MATCH (r:RiskSignal {signal_id: sig_id})
MERGE (s)-[:FLAGGED_BY]->(r)

RETURN s
