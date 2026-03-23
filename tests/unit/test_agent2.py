import pytest
from datetime import datetime
from agents.shared.schemas import SARCase, NormalizedCase, Transaction, RiskTier
from agents.agent2_risk.node import agent2_assess_risk

@pytest.mark.asyncio
async def test_agent2_assess_risk():
    tx = Transaction(
        transaction_id="TX001",
        account_id="ACC123",
        counterparty_account_id="ACC999",
        amount_usd=10500.0,
        timestamp=datetime.now(),
        transaction_type="wire",
        channel="unknown",
        geography="unknown"
    )
    state = SARCase(
        case_id="TEST-002",
        normalized=NormalizedCase(
            case_id="TEST-002",
            transactions=[tx],
            subject_name="John Doe",
            subject_account_ids=["ACC123"],
            date_range_start=datetime.now(),
            date_range_end=datetime.now(),
            total_amount_usd=10500.0,
            ingestion_timestamp=datetime.now(),
            presidio_masked=True
        )
    )
    new_state = await agent2_assess_risk(state)
    assert new_state.risk_assessment is not None
    assert 0.0 <= new_state.risk_assessment.risk_score <= 1.0
    assert new_state.risk_assessment.risk_tier in [RiskTier.CRITICAL, RiskTier.RED, RiskTier.AMBER, RiskTier.GREEN]
