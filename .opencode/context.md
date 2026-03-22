# SAR Narrative Generator — AI Session Context

## What we are building
AI-powered Suspicious Activity Report (SAR) generator for banks.

Two loops:
1. Outer loop: Prediction engine detects suspicious transactions from Kafka stream
2. Inner loop: 6 LangGraph agents generate, validate, and file the SAR

## Tech stack
- Python 3.11, LangGraph, vLLM, Pydantic v2
- Mistral 7B and Llama 3.1 8B via vLLM with guided decoding
- Llama 3.1 70B via AWS Bedrock for narrative only, called once per case
- Neo4j 5.x for entity graph and append-only audit trail
- PostgreSQL 16 with TimescaleDB for case storage
- Weaviate for RAG vector store
- Redis 7 for caching and session state
- Apache Kafka 3.6 for transaction streaming
- Microsoft Presidio for PII masking before any LLM call

## Agent ownership
- Agent 1 ingestion and Agent 2 risk: Person A
- Agent 3 narrative and Agent 4 compliance: Person B
- Prediction engine: shared
- Neo4j schema and Cypher: shared
- Infra: shared

## Hard rules
1. Never pass raw PII to any LLM, always use Presidio masked version
2. Every SLM call must use vLLM guided decoding with GBNF grammar
3. Every agent boundary must have a Pydantic v2 validator
4. Neo4j audit nodes are append-only, no UPDATE no DELETE ever
5. All Cypher queries go in /graph/neo4j/cypher_queries/ never inline
6. Every new function needs a unit test in /tests/unit/
