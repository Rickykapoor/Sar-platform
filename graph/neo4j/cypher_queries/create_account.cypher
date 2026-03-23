// MERGE Account node — idempotent, safe to call multiple times
MERGE (a:Account {account_id: $account_id})
ON CREATE SET
    a.created_at = $created_at,
    a.account_type = $account_type
RETURN a
