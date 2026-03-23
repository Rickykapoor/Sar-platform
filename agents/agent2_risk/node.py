from datetime import datetime
from agents.shared.schemas import SARCase, RiskAssessment, RiskTier

async def agent2_assess_risk(state: SARCase) -> SARCase:
    state.risk_assessment = RiskAssessment(
        case_id=state.case_id,
        risk_score=0.92,
        risk_tier=RiskTier.RED,
        matched_typology="Structuring",
        typology_confidence=0.94,
        signals=[],
        neo4j_pattern_found=True,
        assessment_timestamp=datetime.now()
    )
    state.audit_trail.append({"agent": "Agent 2", "action": "Risk scored"})
    return state
