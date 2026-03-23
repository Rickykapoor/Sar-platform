import pytest
from agents.shared.schemas import SARCase, ComplianceResult
from agents.agent4_compliance.node import agent4_check_compliance

@pytest.mark.asyncio
async def test_agent4_check_compliance():
    state = SARCase(case_id="TEST-004")
    new_state = await agent4_check_compliance(state)
    assert new_state.compliance is not None
    assert isinstance(new_state.compliance.compliance_issues, list)
"""
Unit tests for Agent 4 — Compliance Engine.
Run: pytest tests/unit/test_agent4.py -v
"""

import pytest
from datetime import datetime
from agents.shared.schemas import (
    SARCase, NormalizedCase, RiskAssessment, RiskTier, RiskSignal, Transaction
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------
def _make_structuring_state() -> SARCase:
    """Build a RED-tier structuring case that should trigger multiple rules."""
    txns = [
        Transaction(
            transaction_id=f"TX{i:03d}",
            account_id="ACC001",
            counterparty_account_id="ACC002",
            amount_usd=9800.0,
            timestamp=datetime(2024, 1, i + 1, 10, 0),
            transaction_type="cash_deposit",
            channel="branch",
            geography="offshore",
        )
        for i in range(6)   # 6 transactions — triggers frequency rule
    ]
    normalized = NormalizedCase(
        case_id="CASE-COMP-001",
        transactions=txns,
        subject_name="Jane Smith",
        subject_account_ids=["ACC001"],
        date_range_start=datetime(2024, 1, 1),
        date_range_end=datetime(2024, 1, 6),
        total_amount_usd=58_800.0,
        ingestion_timestamp=datetime.now(),
        presidio_masked=True,
    )
    risk = RiskAssessment(
        case_id="CASE-COMP-001",
        risk_tier=RiskTier.RED,
        risk_score=0.95,
        matched_typology="structuring",
        typology_confidence=0.92,
        signals=[
            RiskSignal(
                signal_type="structuring",
                description="Sub-threshold cash deposits",
                confidence=0.95,
                supporting_transaction_ids=["TX000"],
            )
        ],
        neo4j_pattern_found=True,
        assessment_timestamp=datetime.now(),
    )
    return SARCase(
        case_id="CASE-COMP-001",
        normalized=normalized,
        risk_assessment=risk,
    )


# ---------------------------------------------------------------------------
# Individual rule tests
# ---------------------------------------------------------------------------
def test_bsa_threshold_rule():
    from agents.agent4_compliance.rules import check_bsa_threshold
    state = _make_structuring_state()
    result = check_bsa_threshold(state)
    assert result is not None, "Should flag total > $10,000"
    assert "BSA" in result


def test_geography_risk_rule():
    from agents.agent4_compliance.rules import check_geography_risk
    state = _make_structuring_state()
    result = check_geography_risk(state)
    assert result is not None, "offshore geography should be flagged"


def test_no_false_positive_on_clean_state():
    from agents.agent4_compliance.rules import check_bsa_threshold
    clean_state = SARCase(case_id="CASE-CLEAN")
    # No normalized data — should return None (can't evaluate, not a flag)
    result = check_bsa_threshold(clean_state)
    assert result is None


def test_round_number_rule():
    from agents.agent4_compliance.rules import check_round_numbers
    txns = [
        Transaction(
            transaction_id=f"TX{i}",
            account_id="A1",
            counterparty_account_id="A2",
            amount_usd=5000.0,    # exactly $5,000 — round number
            timestamp=datetime(2024, 1, i + 1),
            transaction_type="wire",
            channel="online",
            geography="US",
        )
        for i in range(4)
    ]
    normalized = NormalizedCase(
        case_id="CASE-ROUND",
        transactions=txns,
        subject_name="Rob Round",
        subject_account_ids=["A1"],
        date_range_start=datetime(2024, 1, 1),
        date_range_end=datetime(2024, 1, 4),
        total_amount_usd=20_000.0,
        ingestion_timestamp=datetime.now(),
        presidio_masked=True,
    )
    state = SARCase(case_id="CASE-ROUND", normalized=normalized)
    result = check_round_numbers(state)
    assert result is not None


# ---------------------------------------------------------------------------
# Node-level tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_agent4_compliance_issues_is_list():
    """compliance_issues must always be a list — never None."""
    from agents.agent4_compliance.node import agent4_check_compliance

    state = _make_structuring_state()
    result = await agent4_check_compliance(state)

    assert result.compliance is not None, "state.compliance must be set"
    assert isinstance(result.compliance.compliance_issues, list), (
        "compliance_issues must be a list"
    )


@pytest.mark.asyncio
async def test_agent4_structuring_issues_detected():
    """Structuring scenario should produce at least one compliance issue."""
    from agents.agent4_compliance.node import agent4_check_compliance

    state = _make_structuring_state()
    result = await agent4_check_compliance(state)

    assert len(result.compliance.compliance_issues) > 0, (
        "Expected compliance issues for structuring scenario"
    )


@pytest.mark.asyncio
async def test_agent4_never_crashes():
    """Agent 4 must return SARCase even with empty state."""
    from agents.agent4_compliance.node import agent4_check_compliance

    state = SARCase(case_id="CASE-EMPTY")
    result = await agent4_check_compliance(state)
    assert isinstance(result, SARCase)
    assert isinstance(result.compliance.compliance_issues, list)
