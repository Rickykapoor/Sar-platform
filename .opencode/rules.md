# Coding conventions for this project

## Python style
- Python 3.11 strict type hints everywhere
- No Any types, use Union Optional or proper generics
- Pydantic v2 BaseModel for all data contracts between agents
- Async first, use async/await and async Neo4j driver
- Google style docstrings with Args Returns Raises sections

## LangGraph agents
- Each agent is a LangGraph StateGraph node
- State object is a Pydantic v2 model
- Node function signature: async def node_name(state: AgentState) -> AgentState

## vLLM calls
- Always use InferenceClient with grammar parameter
- Grammar must be a valid GBNF string matching the Pydantic output schema
- Include timeout=30 and max_retries=3 on every call

## Neo4j
- Use neo4j-driver 5.x async session only
- Queries loaded from /graph/neo4j/cypher_queries/ files never inline
- Node labels: Transaction, Account, Customer, RiskSignal, AuditEvent, SARCase
- Relationships: SENT, RECEIVED, FLAGGED_BY, CAUSED, PART_OF

## Git commits
- Format: type(scope): description
- Types: feat, fix, test, refactor, docs, infra
- Examples:
  - feat(agent1): add Presidio PII masking to ingestion pipeline
  - test(agent2): add contract test for risk score schema

## Testing
- pytest and pytest-asyncio
- Mock all vLLM calls in unit tests
- Run pytest tests/ -v before every PR
