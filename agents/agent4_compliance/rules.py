"""
Agent 4 — Compliance Engine
8 AML rule functions. Each takes SARCase, returns Optional[str].
None  = rule passed (no issue)
str   = issue description (non-compliant)
Keep each function < 20 lines per TASKS.md requirement.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.shared.schemas import SARCase

_HIGH_RISK_GEOGRAPHIES = {
    "offshore", "cayman islands", "panama", "malta", "british virgin islands",
    "seychelles", "vanuatu", "iran", "north korea", "myanmar", "cuba",
    "syria", "russia", "belarus",
}

BSA_CTR_THRESHOLD = 10_000.0          # USD — mandatory CTR filing
STRUCTURING_LOWER = 9_500.0           # USD — structuring watch band start
STRUCTURING_UPPER = BSA_CTR_THRESHOLD


# ---------------------------------------------------------------------------
# Rule 1 — BSA $10,000 Currency Transaction Report threshold
# ---------------------------------------------------------------------------
def check_bsa_threshold(state: "SARCase") -> Optional[str]:
    """Flag if total transaction volume exceeds $10,000 USD (CTR required)."""
    if not state.normalized:
        return None
    total = state.normalized.total_amount_usd
    if total > BSA_CTR_THRESHOLD:
        return (
            f"BSA CTR threshold exceeded: total volume ${total:,.2f} > "
            f"${BSA_CTR_THRESHOLD:,.2f}. Currency Transaction Report required."
        )
    return None


# ---------------------------------------------------------------------------
# Rule 2 — Structuring ($9,500–$10,000 band)
# ---------------------------------------------------------------------------
def check_structuring_threshold(state: "SARCase") -> Optional[str]:
    """Flag transactions in the $9,500–$10,000 structuring watch band."""
    if not state.normalized:
        return None
    flagged = [
        t for t in state.normalized.transactions
        if STRUCTURING_LOWER <= t.amount_usd < STRUCTURING_UPPER
    ]
    if flagged:
        ids = ", ".join(t.transaction_id for t in flagged[:5])
        return (
            f"Structuring indicator: {len(flagged)} transaction(s) in "
            f"${STRUCTURING_LOWER:,.0f}–${STRUCTURING_UPPER:,.0f} band. "
            f"IDs: {ids}"
        )
    return None


# ---------------------------------------------------------------------------
# Rule 3 — High-risk geography
# ---------------------------------------------------------------------------
def check_geography_risk(state: "SARCase") -> Optional[str]:
    """Flag if any transaction involves a high-risk / sanctioned geography."""
    if not state.normalized:
        return None
    risky = [
        t for t in state.normalized.transactions
        if t.geography.lower() in _HIGH_RISK_GEOGRAPHIES
    ]
    if risky:
        geos = ", ".join({t.geography for t in risky})
        return (
            f"High-risk geography detected in {len(risky)} transaction(s): {geos}. "
            f"Enhanced due diligence required."
        )
    return None


# ---------------------------------------------------------------------------
# Rule 4 — FinCEN 314(a) match placeholder
# ---------------------------------------------------------------------------
def check_fincen_314a(state: "SARCase") -> Optional[str]:
    """
    Placeholder: flag if risk_assessment indicates a FinCEN 314(a) list match.
    In production, this calls the FinCEN API. For demo, we derive from risk signals.
    """
    if not state.risk_assessment:
        return None
    for signal in state.risk_assessment.signals:
        if "314a" in signal.signal_type.lower() or "fincen" in signal.description.lower():
            return (
                f"FinCEN 314(a) potential match identified: {signal.description}. "
                f"Manual verification required before SAR filing."
            )
    return None


# ---------------------------------------------------------------------------
# Rule 5 — Unusual transaction frequency
# ---------------------------------------------------------------------------
def check_transaction_frequency(state: "SARCase") -> Optional[str]:
    """Flag if more than 5 transactions occurred on any single calendar day."""
    if not state.normalized:
        return None
    from collections import Counter
    day_counts = Counter(
        t.timestamp.date() for t in state.normalized.transactions
    )
    excessive = {str(day): cnt for day, cnt in day_counts.items() if cnt > 5}
    if excessive:
        details = "; ".join(f"{d}: {c} txns" for d, c in excessive.items())
        return (
            f"Unusual transaction frequency: >5 transactions on single day(s): {details}."
        )
    return None


# ---------------------------------------------------------------------------
# Rule 6 — Round-number transactions
# ---------------------------------------------------------------------------
def check_round_numbers(state: "SARCase") -> Optional[str]:
    """Flag transactions with amounts exactly divisible by $1,000 (smurfing indicator)."""
    if not state.normalized:
        return None
    round_txns = [
        t for t in state.normalized.transactions
        if t.amount_usd % 1000 == 0 and t.amount_usd > 0
    ]
    if len(round_txns) >= 3:
        ids = ", ".join(t.transaction_id for t in round_txns[:5])
        return (
            f"Round-number transactions: {len(round_txns)} transaction(s) exactly "
            f"divisible by $1,000 — potential indicator of structured deposits. IDs: {ids}"
        )
    return None


# ---------------------------------------------------------------------------
# Rule 7 — Dormant account activity
# ---------------------------------------------------------------------------
def check_dormant_account(state: "SARCase") -> Optional[str]:
    """
    Flag if risk signals or typology mention dormant account reactivation.
    In production: query account history DB. For demo, derive from signals.
    """
    if not state.risk_assessment:
        return None
    for signal in state.risk_assessment.signals:
        if "dormant" in signal.description.lower() or "dormant" in signal.signal_type.lower():
            return (
                f"Dormant account activity detected: {signal.description}. "
                f"Account reactivation with high-volume transactions is an AML red flag."
            )
    return None


# ---------------------------------------------------------------------------
# Rule 8 — Multiple jurisdiction flag
# ---------------------------------------------------------------------------
def check_multiple_jurisdictions(state: "SARCase") -> Optional[str]:
    """Flag if transactions span more than 2 distinct geographies."""
    if not state.normalized:
        return None
    geographies = {t.geography for t in state.normalized.transactions}
    if len(geographies) > 2:
        return (
            f"Multiple jurisdictions involved: {len(geographies)} geographies detected "
            f"({', '.join(sorted(geographies))}). Cross-border layering risk."
        )
    return None


# ---------------------------------------------------------------------------
# All rules — ordered list for node.py to iterate
# ---------------------------------------------------------------------------
ALL_RULES = [
    check_bsa_threshold,
    check_structuring_threshold,
    check_geography_risk,
    check_fincen_314a,
    check_transaction_frequency,
    check_round_numbers,
    check_dormant_account,
    check_multiple_jurisdictions,
]
