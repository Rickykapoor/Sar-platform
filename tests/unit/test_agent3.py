"""
Unit tests for Agent 3 — Narrative Generation.
Run: pytest tests/unit/test_agent3.py -v
"""

import pytest
from datetime import datetime
from agents.shared.schemas import (
    SARCase, NormalizedCase, RiskAssessment, RiskTier, RiskSignal, Transaction
)
from agents.agent3_narrative.fallback import generate_fallback_narrative


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------
def _make_full_state() -> SARCase:
    tx = Transaction(
        transaction_id="TX001",
        account_id="ACC001",
        counterparty_account_id="ACC002",
        amount_usd=9800.0,
        timestamp=datetime(2024, 1, 15, 10, 30),
        transaction_type="wire",
        channel="online",
        geography="offshore",
    )
    normalized = NormalizedCase(
        case_id="CASE-TEST-001",
        transactions=[tx],
        subject_name="John Doe",
        subject_account_ids=["ACC001"],
        date_range_start=datetime(2024, 1, 1),
        date_range_end=datetime(2024, 1, 31),
        total_amount_usd=9800.0,
        ingestion_timestamp=datetime.now(),
        presidio_masked=True,
    )
    risk = RiskAssessment(
        case_id="CASE-TEST-001",
        risk_tier=RiskTier.RED,
        risk_score=0.93,
        matched_typology="structuring",
        typology_confidence=0.88,
        signals=[
            RiskSignal(
                signal_type="structuring",
                description="Multiple sub-threshold deposits detected",
                confidence=0.91,
                supporting_transaction_ids=["TX001"],
            )
        ],
        neo4j_pattern_found=True,
        assessment_timestamp=datetime.now(),
    )
    return SARCase(
        case_id="CASE-TEST-001",
        normalized=normalized,
        risk_assessment=risk,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_fallback_narrative_length():
    """Fallback narrative must always exceed 100 characters."""
    state = _make_full_state()
    narrative = generate_fallback_narrative(state)
    assert isinstance(narrative, str), "Narrative must be a string"
    assert len(narrative) > 100, f"Narrative too short: {len(narrative)} chars"


def test_fallback_narrative_has_sections():
    """Fallback must include all four SAR sections."""
    state = _make_full_state()
    narrative = generate_fallback_narrative(state)
    assert "[SUBJECT INFORMATION]" in narrative
    assert "[SUSPICIOUS ACTIVITY DESCRIPTION]" in narrative
    assert "[NARRATIVE BODY]" in narrative
    assert "[LAW ENFORCEMENT NOTE]" in narrative


def test_fallback_with_minimal_state():
    """Fallback must not crash even with bare-minimum state."""
    state = SARCase(case_id="CASE-MINIMAL")
    narrative = generate_fallback_narrative(state)
    assert len(narrative) > 100


@pytest.mark.asyncio
async def test_agent3_node_produces_narrative():
    """After running agent3, state.narrative must be populated with narrative_body > 100."""
    from agents.agent3_narrative.node import agent3_generate_narrative

    state = _make_full_state()
    result = await agent3_generate_narrative(state)

    assert result.narrative is not None, "state.narrative must be set"
    assert len(result.narrative.narrative_body) > 100, (
        f"narrative_body too short: {len(result.narrative.narrative_body)} chars"
    )
    # Audit trail must have been appended
    assert any(
        "Agent 3" in entry.get("agent", "") for entry in result.audit_trail
    ), "Agent 3 must append to audit_trail"


@pytest.mark.asyncio
async def test_agent3_never_crashes():
    """Agent 3 must return state even with completely empty input."""
    from agents.agent3_narrative.node import agent3_generate_narrative

    state = SARCase(case_id="CASE-EMPTY")
    result = await agent3_generate_narrative(state)
    # Should not raise — error goes to error_log or narrative is populated via fallback
    assert isinstance(result, SARCase)
