from datetime import datetime
from agents.shared.schemas import SARCase, SARNarrative

async def agent3_generate_narrative(state: SARCase) -> SARCase:
    dummy_text = "This is a placeholder narrative for the SAR case. " * 5
    state.narrative = SARNarrative(
        case_id=state.case_id,
        subject_information="John Doe, Account ACC123",
        suspicious_activity_description="Multiple large wire transfers",
        narrative_body=dummy_text,
        supporting_evidence_refs=["TX001"],
        model_version_used="mock-model",
        generation_timestamp=datetime.now()
    )
    state.audit_trail.append({"agent": "Agent 3", "action": "Generated narrative"})
    return state
