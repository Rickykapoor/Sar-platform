import pytest
from agents.shared.schemas import SARCase
from agents.agent3_narrative.node import agent3_generate_narrative

@pytest.mark.asyncio
async def test_agent3_generate_narrative():
    state = SARCase(case_id="TEST-003")
    new_state = await agent3_generate_narrative(state)
    assert new_state.narrative is not None
    assert len(new_state.narrative.narrative_body) > 100
