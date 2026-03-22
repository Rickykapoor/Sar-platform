# SAR Platform — OpenCode Session Context

Read MASTER_CONTEXT.md in the project root before doing anything.
That file contains everything: schemas, endpoints, agent patterns,
Neo4j schema, git workflow, environment variables, and demo flow.

Quick reminder of hard rules:
1. Agent function signature: async def agent_name(state: SARCase) -> SARCase
2. Never raise exceptions in agents — catch and append to state.error_log
3. Neo4j AuditEvent nodes are append-only — never UPDATE or DELETE
4. All Pydantic models are in agents/shared/schemas.py — import from there
5. All Minimax prompts go in agents/agent3_narrative/prompts.py — not inline
