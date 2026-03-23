from datetime import datetime
from agents.shared.schemas import SARCase, ComplianceResult

async def agent4_check_compliance(state: SARCase) -> SARCase:
    state.compliance = ComplianceResult(
        case_id=state.case_id,
        compliance_issues=["Test issue 1", "Test issue 2"],
        bsa_compliant=True,
        all_fields_complete=True,
        fincen_format_valid=True,
        validated_timestamp=datetime.now()
    )
    state.audit_trail.append({"agent": "Agent 4", "action": "Checked compliance"})
    return state
