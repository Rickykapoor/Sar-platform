"""
Agent 6 — Human Review Node
Owned by: Anshul

Responsibilities:
- Accept analyst_name from the FastAPI /case/{id}/approve endpoint
- Set state.analyst_approved_by, state.status = FILED, state.final_filed_timestamp
- Append to state.audit_trail

NOTE: Agent 6 is NOT in the LangGraph pipeline.
It is called directly by the FastAPI endpoint when an analyst approves the case.
Usage:
    state = await agent6_approve(state, analyst_name="Jane Smith")
"""

from __future__ import annotations

import logging
from datetime import datetime

from agents.shared.schemas import SARCase, SARStatus

logger = logging.getLogger(__name__)


async def agent6_approve(state: SARCase, analyst_name: str) -> SARCase:
    """
    Human review approval handler — Agent 6.

    Called by the FastAPI POST /case/{id}/approve endpoint.
    Marks the case as FILED after analyst approval.

    Args:
        state:         Current SARCase (must have passed through Agents 1–5)
        analyst_name:  Name of the approving analyst (from API request body)

    Returns:
        Updated SARCase with status=FILED and analyst attribution.
    """
    try:
        # ------------------------------------------------------------------ #
        # 1. Record analyst attribution
        # ------------------------------------------------------------------ #
        state.analyst_approved_by = analyst_name.strip()

        # ------------------------------------------------------------------ #
        # 2. Set final status
        # ------------------------------------------------------------------ #
        state.status = SARStatus.FILED

        # ------------------------------------------------------------------ #
        # 3. Record filed timestamp
        # ------------------------------------------------------------------ #
        state.final_filed_timestamp = datetime.now()

        # ------------------------------------------------------------------ #
        # 4. Append to audit trail
        # ------------------------------------------------------------------ #
        state.audit_trail.append({
            "agent": "Agent 6 - Human Review",
            "action": (
                f"SAR case reviewed and approved by analyst '{analyst_name}'. "
                f"Status changed to FILED. Case is now regulator-ready."
            ),
            "confidence": 1.0,
            "timestamp": datetime.now().isoformat(),
            "analyst": analyst_name.strip(),
        })

        logger.info(
            "Agent 6: Case %s FILED by analyst '%s' at %s",
            state.case_id,
            analyst_name,
            state.final_filed_timestamp.isoformat(),
        )

    except Exception as exc:
        logger.error("Agent 6 unexpected error: %s", exc)
        state.error_log.append({
            "agent": "Agent 6 - Human Review",
            "error": str(exc),
            "timestamp": datetime.now().isoformat(),
        })
        # Never raise — always return state

    return state


async def agent6_dismiss(state: SARCase, analyst_name: str, reason: str = "") -> SARCase:
    """
    Human review dismissal handler.

    Called by the FastAPI POST /case/{id}/dismiss endpoint.
    Marks the case as DISMISSED.

    Args:
        state:         Current SARCase
        analyst_name:  Name of the dismissing analyst
        reason:        Optional dismissal reason
    """
    try:
        state.analyst_approved_by = analyst_name.strip()
        state.status = SARStatus.DISMISSED
        state.final_filed_timestamp = datetime.now()

        state.audit_trail.append({
            "agent": "Agent 6 - Human Review",
            "action": (
                f"SAR case dismissed by analyst '{analyst_name}'. "
                f"Reason: {reason or 'Not specified'}."
            ),
            "confidence": 1.0,
            "timestamp": datetime.now().isoformat(),
            "analyst": analyst_name.strip(),
        })

        logger.info(
            "Agent 6: Case %s DISMISSED by analyst '%s'",
            state.case_id,
            analyst_name,
        )

    except Exception as exc:
        logger.error("Agent 6 dismiss error: %s", exc)
        state.error_log.append({
            "agent": "Agent 6 - Human Review",
            "error": str(exc),
            "timestamp": datetime.now().isoformat(),
        })

    return state
