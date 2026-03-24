"""
Agent 3 — Narrative Generation
LangGraph node: calls MiniMax LLM, parses JSON output, populates state.narrative to FIU-IND spec.
"""

from __future__ import annotations

import json
from datetime import datetime
from agents.shared.schemas import (
    SARCase, SARNarrative, Part1ReportDetails, Part2PrincipalOfficer,
    Part3ReportingBranch, LinkedIndividual, LinkedEntity, LinkedAccount,
    Part7SuspicionDetails, Part8ActionTaken
)
from agents.agent3_narrative.minimax_client import generate_narrative
from agents.agent3_narrative.fallback import generate_fallback_narrative

async def agent3_generate_narrative(state: SARCase) -> SARCase:
    try:
        raw_text = await generate_narrative(state)
        
        # Clean JSON markdown blocks
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0]
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0]
            
        data = json.loads(raw_text.strip())
    except Exception as e:
        state.error_log.append({
            "agent": "Agent 3 - Narrative Generation",
            "error": f"LLM JSON parsing failed: {e}. Using fallback.",
            "timestamp": datetime.now().isoformat(),
        })
        raw_text = generate_fallback_narrative(state)
        data = json.loads(raw_text.strip())

    try:
        p1 = Part1ReportDetails(**data.get("part1_report_details", {"date_of_sending": datetime.now().strftime("%Y-%m-%d"), "is_replacement": False}))
        p2 = Part2PrincipalOfficer(**data.get("part2_principal_officer", {}))
        p3 = Part3ReportingBranch(**data.get("part3_reporting_branch", {}))
        
        p4 = [LinkedIndividual(**ind) for ind in data.get("part4_linked_individuals", [])]
        p5 = [LinkedEntity(**ent) for ent in data.get("part5_linked_entities", [])]
        p6 = [LinkedAccount(**acc) for acc in data.get("part6_linked_accounts", [])]
        
        p7 = Part7SuspicionDetails(**data.get("part7_suspicion_details", {"reasons_for_suspicion": [], "grounds_of_suspicion": ""}))
        p8 = Part8ActionTaken(**data.get("part8_action_taken", {"under_investigation": False, "agency_details": ""}))

        state.narrative = SARNarrative(
            case_id=state.case_id,
            part1_report_details=p1,
            part2_principal_officer=p2,
            part3_reporting_branch=p3,
            part4_linked_individuals=p4,
            part5_linked_entities=p5,
            part6_linked_accounts=p6,
            part7_suspicion_details=p7,
            part8_action_taken=p8,
            generation_timestamp=datetime.now(),
        )

        state.audit_trail.append({
            "agent": "Agent 3 - Narrative Generation",
            "action": f"Generated FIU-IND STR JSON using MiniMax-Text-2.5",
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
        })

    except Exception as e:
        state.error_log.append({
            "agent": "Agent 3 - Schema Mapping",
            "error": f"Failed to map JSON to Pydantic: {e}",
            "timestamp": datetime.now().isoformat(),
        })

    return state
