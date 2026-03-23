"""
Agent 3 — Narrative Generation
Prompt templates for MiniMax-Text-2.5.
RULE: No prompts in node.py — always import from here.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.shared.schemas import SARCase

# ---------------------------------------------------------------------------
# Simulated Weaviate RAG — 3 hardcoded SAR reference examples
# ---------------------------------------------------------------------------
_SAR_EXAMPLES = """
=== SAR EXAMPLE 1 — Structuring ===
On 14 separate occasions between January 3 and January 29, 2024, the subject
made cash deposits in amounts ranging from $8,500 to $9,900 at multiple branch
locations. No single deposit exceeded the $10,000 CTR threshold. Total deposited:
$134,200. Transaction pattern is consistent with structuring under 31 U.S.C. § 5324.
Account history shows no prior large-volume cash activity.

=== SAR EXAMPLE 2 — Wire Fraud / Layering ===
Between February 1 and February 28, 2024, the subject initiated 22 international
wire transfers totalling $2,340,000 to counterparties in high-risk jurisdictions
(Cayman Islands, Panama, Malta). Funds were received from a domestic shell company
incorporated 11 days prior. The layering pattern suggests deliberate obfuscation of
fund origins consistent with money-laundering typology.

=== SAR EXAMPLE 3 — Smurfing ===
Multiple individuals made structured deposits into a single beneficiary account over
a 10-day period. Each depositor contributed amounts between $4,000 and $4,999,
cumulatively totalling $89,400. No legitimate business relationship was identified
among the depositors. Pattern consistent with smurfing (coordinated structuring by
multiple actors) under BSA guidelines.
"""

# ---------------------------------------------------------------------------
# SYSTEM PROMPT — FinCEN-compliant SAR writing style
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = f"""You are a senior Bank Secrecy Act (BSA) compliance officer and
financial intelligence analyst. Your task is to draft a Suspicious Activity Report
(SAR) narrative in the formal format required by the U.S. Financial Crimes
Enforcement Network (FinCEN).

REQUIREMENTS:
- Use professional, precise, regulatory language (no colloquialisms).
- Be factual: base every claim on the data provided.
- Structure the narrative in exactly FOUR labelled sections:
    [SUBJECT INFORMATION] — who the subject is, account details, relationship to institution
    [SUSPICIOUS ACTIVITY DESCRIPTION] — what was observed, dates, amounts, pattern
    [NARRATIVE BODY] — full analytical narrative explaining the AML concern (≥100 words)
    [LAW ENFORCEMENT NOTE] — relevant regulations, typology match, recommended follow-up
- Do NOT speculate beyond the provided data.
- Never include placeholder text like "N/A" or "TBD".
- Output only the four labelled sections — no preamble, no sign-off.

REFERENCE SAR EXAMPLES (for writing style only):
{_SAR_EXAMPLES}
"""


# ---------------------------------------------------------------------------
# User prompt builder — injects live case data
# ---------------------------------------------------------------------------
def build_user_prompt(state: "SARCase") -> str:
    """Build the user-facing prompt from the current SARCase state."""

    # Safely extract fields with fallbacks
    case_id = state.case_id

    # Normalized case fields
    subject_name = "Unknown"
    account_ids = []
    total_amount = 0.0
    date_start = "N/A"
    date_end = "N/A"
    tx_count = 0
    geographies: list[str] = []

    if state.normalized:
        subject_name = state.normalized.subject_name
        account_ids = state.normalized.subject_account_ids
        total_amount = state.normalized.total_amount_usd
        date_start = state.normalized.date_range_start.strftime("%Y-%m-%d")
        date_end = state.normalized.date_range_end.strftime("%Y-%m-%d")
        tx_count = len(state.normalized.transactions)
        geographies = list({t.geography for t in state.normalized.transactions})

    # Risk assessment fields
    risk_score = 0.0
    risk_tier = "UNKNOWN"
    typology = "Unknown"
    typology_conf = 0.0
    signals_text = "None identified."

    if state.risk_assessment:
        risk_score = state.risk_assessment.risk_score
        risk_tier = state.risk_assessment.risk_tier.value.upper()
        typology = state.risk_assessment.matched_typology
        typology_conf = state.risk_assessment.typology_confidence
        if state.risk_assessment.signals:
            signals_text = "\n".join(
                f"  - [{s.signal_type}] {s.description} (confidence: {s.confidence:.0%})"
                for s in state.risk_assessment.signals
            )

    account_ids_str = ", ".join(account_ids) if account_ids else "N/A"
    geographies_str = ", ".join(geographies) if geographies else "N/A"

    return f"""Draft a SAR narrative for the following case. Use all four labelled sections.

CASE ID: {case_id}
SUBJECT NAME: {subject_name}
ACCOUNT ID(S): {account_ids_str}
REPORTING PERIOD: {date_start} to {date_end}
TOTAL TRANSACTION VOLUME: ${total_amount:,.2f}
TRANSACTION COUNT: {tx_count}
GEOGRAPHIES INVOLVED: {geographies_str}

ML RISK SCORE: {risk_score:.3f} ({risk_tier} tier)
MATCHED AML TYPOLOGY: {typology} (confidence: {typology_conf:.0%})

RISK SIGNALS DETECTED:
{signals_text}

Write the SAR narrative now. Begin with [SUBJECT INFORMATION].
"""
