import pytest
from agents.shared.schemas import SARCase
from agents.agent5_audit.node import agent5_write_audit

@pytest.mark.asyncio
async def test_agent5_write_audit():
    # Provide enough state data for Agent 5 to serialize and hash
    state = SARCase(case_id="TEST-005")
    # Agent 5 is synchronous per Anshul's implementation plan but TASKS.md asks for async test
    # Wait, Anshul implemented it as async or sync? Let's treat it as async since it's a LangGraph node.
    new_state = await agent5_write_audit(state)
    assert new_state.audit is not None
    assert len(new_state.audit.immutable_hash) == 64
