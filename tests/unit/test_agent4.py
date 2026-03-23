import pytest
from agents.shared.schemas import SARCase, ComplianceResult
from agents.agent4_compliance.node import agent4_check_compliance

@pytest.mark.asyncio
async def test_agent4_check_compliance():
    state = SARCase(case_id="TEST-004")
    new_state = await agent4_check_compliance(state)
    assert new_state.compliance is not None
    assert isinstance(new_state.compliance.compliance_issues, list)
