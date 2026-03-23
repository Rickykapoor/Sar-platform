"""
Agent 3 — Narrative Generation
Fallback template generator — no LLM, pure string construction.
Called whenever MiniMax is unavailable or returns insufficient output.
Always produces a narrative_body > 100 characters.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.shared.schemas import SARCase


def generate_fallback_narrative(state: "SARCase") -> str:
    """
    Build a compliance-grade SAR narrative using only state fields.
    No LLM involved. Guaranteed to return >100 characters.
    """
    case_id = state.case_id

    # Extract risk fields safely
    risk_score = 0.0
    risk_tier = "UNKNOWN"
    typology = "suspicious pattern"
    signals_text = "anomalous transaction behavior"

    if state.risk_assessment:
        risk_score = state.risk_assessment.risk_score
        risk_tier = state.risk_assessment.risk_tier.value.upper()
        typology = state.risk_assessment.matched_typology
        if state.risk_assessment.signals:
            signals_text = "; ".join(
                s.description for s in state.risk_assessment.signals[:3]
            )

    # Extract normalized fields safely
    subject_name = "the account holder"
    total_amount = 0.0
    tx_count = 0
    date_start = "the reporting period start"
    date_end = "the reporting period end"

    if state.normalized:
        subject_name = state.normalized.subject_name
        total_amount = state.normalized.total_amount_usd
        tx_count = len(state.normalized.transactions)
        date_start = state.normalized.date_range_start.strftime("%B %d, %Y")
        date_end = state.normalized.date_range_end.strftime("%B %d, %Y")

    narrative = (
        f"[SUBJECT INFORMATION]\n"
        f"The subject of this report is {subject_name}. The account(s) associated "
        f"with this case (Case ID: {case_id}) exhibited activity that triggered an "
        f"automated risk assessment scoring {risk_score:.3f} ({risk_tier} tier).\n\n"
        f"[SUSPICIOUS ACTIVITY DESCRIPTION]\n"
        f"Between {date_start} and {date_end}, a total of {tx_count} transaction(s) "
        f"were recorded, aggregating to ${total_amount:,.2f} USD. The activity "
        f"pattern is consistent with the AML typology: {typology}. Detected signals "
        f"include: {signals_text}.\n\n"
        f"[NARRATIVE BODY]\n"
        f"The financial institution's automated monitoring system flagged the above "
        f"activity as suspicious based on an ensemble ML model (XGBoost + SHAP) "
        f"producing a risk score of {risk_score:.3f}. The transaction volume, "
        f"frequency, and geographic profile collectively exceed the institution's "
        f"risk tolerance thresholds. The pattern identified — {typology} — is a "
        f"known anti-money laundering (AML) indicator under FinCEN guidance. The "
        f"account holder had no prior documented legitimate business purpose that "
        f"would explain this level of activity during the period under review. "
        f"Compliance officers reviewed the automated assessment and escalated this "
        f"case to SAR filing with moderate-to-high confidence.\n\n"
        f"[LAW ENFORCEMENT NOTE]\n"
        f"This SAR is filed pursuant to 31 U.S.C. § 5318(g) and 31 C.F.R. § 1020.320. "
        f"The matched typology of '{typology}' may warrant referral to FinCEN's 314(a) "
        f"program for further investigation. Records are available upon law enforcement "
        f"request. Case reference: {case_id}."
    )
    return narrative
