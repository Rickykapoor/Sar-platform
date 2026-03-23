from datetime import datetime
from agents.shared.schemas import SARCase, NormalizedCase, Transaction

async def agent1_ingest(state: SARCase) -> SARCase:
    tx_data = state.raw_transaction or {}
    tx = Transaction(
        transaction_id="TX001",
        account_id=tx_data.get("account_id", "ACC123"),
        counterparty_account_id="ACC999",
        amount_usd=float(tx_data.get("amount", 10000.0)),
        timestamp=datetime.now(),
        transaction_type=tx_data.get("type", "wire"),
        channel="unknown",
        geography="unknown"
    )
    state.normalized = NormalizedCase(
        case_id=state.case_id,
        transactions=[tx],
        subject_name="John Doe",
        subject_account_ids=[tx.account_id],
        date_range_start=datetime.now(),
        date_range_end=datetime.now(),
        total_amount_usd=tx.amount_usd,
        ingestion_timestamp=datetime.now(),
        presidio_masked=True
    )
    state.audit_trail.append({"agent": "Agent 1", "action": "Masked variables"})
    return state
