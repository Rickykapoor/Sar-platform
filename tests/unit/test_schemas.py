"""Contract tests for shared Pydantic schemas."""
import pytest
from datetime import datetime
from agents.shared.schemas import (
    Transaction,
    RiskAssessment,
    RiskTier,
    RiskSignal,
    SARCase,
    SARStatus,
)


def test_transaction_valid():
    tx = Transaction(
        transaction_id="TX001",
        account_id="ACC001",
        counterparty_account_id="ACC002",
        amount_usd=9500.00,
        timestamp=datetime.now(),
        transaction_type="wire",
        channel="online",
        geography="US",
    )
    assert tx.amount_usd == 9500.00


def test_transaction_rejects_negative_amount():
    with pytest.raises(Exception):
        Transaction(
            transaction_id="TX002",
            account_id="ACC001",
            counterparty_account_id="ACC002",
            amount_usd=-100.0,
            timestamp=datetime.now(),
            transaction_type="wire",
            channel="online",
            geography="US",
        )


def test_risk_score_out_of_bounds():
    with pytest.raises(Exception):
        RiskAssessment(
            case_id="CASE001",
            risk_tier=RiskTier.RED,
            risk_score=1.5,
            matched_typology="structuring",
            typology_confidence=0.9,
            signals=[],
            neo4j_pattern_found=True,
            assessment_timestamp=datetime.now(),
        )


def test_sar_case_default_status():
    case = SARCase(case_id="CASE001")
    assert case.status == SARStatus.PENDING
    assert case.normalized is None
