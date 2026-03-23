// MERGE Transaction node and create SENT / RECEIVED_BY relationships
MERGE (t:Transaction {transaction_id: $transaction_id})
ON CREATE SET
    t.amount_usd       = $amount_usd,
    t.timestamp        = $timestamp,
    t.transaction_type = $transaction_type,
    t.channel          = $channel,
    t.geography        = $geography

WITH t
MATCH (sender:Account {account_id: $sender_account_id})
MERGE (sender)-[:SENT]->(t)

WITH t
MATCH (receiver:Account {account_id: $receiver_account_id})
MERGE (t)-[:RECEIVED_BY]->(receiver)

RETURN t
