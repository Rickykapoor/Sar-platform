import pytest
from agents.shared.schemas import SARCase
from agents.agent1_ingestion.node import agent1_ingest

@pytest.mark.asyncio
async def test_agent1_ingest():
    raw_tx = {
        "account_id": "ACC123",
        "amount": 10500,
        "type": "wire",
        "description": "Payment to John Doe"
    }
    state = SARCase(case_id="TEST-001", raw_transaction=raw_tx)
    new_state = await agent1_ingest(state)
    assert new_state.normalized is not None
    assert new_state.normalized.presidio_masked is True
