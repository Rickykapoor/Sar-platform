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
"""
Unit tests for Agent 2 (Risk Assessment)
"""

import pytest
from agents.shared.schemas import SARCase, NormalizedCase, Transaction
from agents.agent1_ingestion.node import agent1_ingest
from agents.agent2_risk.node import agent2_assess_risk
from prediction_engine.simulator import get_structuring_scenario, get_layering_scenario

@pytest.mark.asyncio
async def test_agent2_structuring_risk():
    # Arrange
    scenario = get_structuring_scenario()
    # We only pass the first transaction of the scenario through Agent 1 for this test
    # (In reality, pipeline receives the whole dict, but our schema extracts one tx for demo purposes)
    tx = scenario["transactions"][0]
    state = SARCase(case_id="C-STRUCT", raw_transaction=tx)
    
    # Act
    state = await agent1_ingest(state)
    state = await agent2_assess_risk(state)

    # Assert
    assert state.risk_assessment is not None
    assert state.risk_assessment.risk_score >= 0.0
    assert state.risk_assessment.matched_typology in ["Structuring", "Wire Fraud / General Attempt"]
    assert "transaction_frequency_7d" in state.risk_assessment.shap_values
    assert len(state.audit_trail) == 2  # 1 from agent1, 1 from agent2

@pytest.mark.asyncio
async def test_agent2_layering_risk():
    # Arrange
    scenario = get_layering_scenario()
    tx = scenario["transactions"][0]
    state = SARCase(case_id="C-LAYER", raw_transaction=tx)
    
    # Act
    state = await agent1_ingest(state)
    state = await agent2_assess_risk(state)

    # Assert
    assert state.risk_assessment is not None
    assert state.risk_assessment.matched_typology in ["Layering", "Wire Fraud / General Attempt"]
    assert len(state.risk_assessment.signals) > 0
