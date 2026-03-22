# SAR Platform — Master Context File
# Read this file at the start of EVERY OpenCode session, no exceptions.
# Last updated: March 22 2026
# This file is the single source of truth for the entire project.

---

## What We Are Building

An AI-powered Suspicious Activity Report (SAR) generator for banks.
Hackathon project. Deadline: March 26 2026 midnight.
Judges evaluate: working demo + code quality + business impact equally.

The system has two loops:

OUTER LOOP — Prediction Engine:
  Every bank transaction → ML ensemble scores it → GREEN / AMBER / RED
  RED transactions automatically enter the inner SAR pipeline

INNER LOOP — 6 Agent SAR Pipeline:
  Agent 1 (Ingestion) → Agent 2 (Risk) → Agent 3 (Narrative) →
  Agent 4 (Compliance) → Agent 5 (Audit) → Agent 6 (Human Review)
  Output: regulator-ready SAR document + immutable audit trail in Neo4j

---

## Team and Ownership — Do Not Touch Other People's Files

  Person 1 (P1) — Backend + ML
    OWNS: main.py, agents/pipeline.py, agents/agent1_ingestion/,
          agents/agent2_risk/, prediction_engine/

  Person 2 (P2) — AI + Graph
    OWNS: agents/agent3_narrative/, agents/agent4_compliance/,
          agents/agent5_audit/, graph/neo4j/

  Person 3 (P3) — UI + Infra
    OWNS: ui/, agents/agent6_review/, infra/, docker-compose.yml

  SHARED (coordinate before editing):
    agents/shared/schemas.py — the Pydantic contracts between all agents
    MASTER_CONTEXT.md — this file
    requirements.txt

---

## Tech Stack — Exact Versions

  Runtime:        Python 3.11
  API framework:  FastAPI 0.115.4 + uvicorn
  AI framework:   LangGraph 0.2.45 + LangChain 0.3.7
  LLM:            Minimax API (MiniMax-Text-01 model)
  Data models:    Pydantic v2 (2.9.2) — BaseModel everywhere
  Graph DB:       Neo4j 5.14 Enterprise — bolt://localhost:7687
  Relational DB:  PostgreSQL 16 — localhost:5432 (not heavily used in demo)
  Cache:          Redis 7 — localhost:6379
  Vector store:   Weaviate 1.24 — localhost:8080
  Streaming:      Apache Kafka 3.6 — localhost:9092 (mocked by simulator)
  ML models:      XGBoost + scikit-learn + SHAP
  Frontend:       Streamlit + pyvis for graph rendering
  Containers:     Docker Compose (no Kubernetes for hackathon)

---

## Running Services — Ports

  FastAPI backend:    http://localhost:8000
  FastAPI docs:       http://localhost:8000/docs
  Streamlit UI:       http://localhost:8501
  Neo4j browser:      http://localhost:7474  (neo4j / sarplatform123)
  Neo4j bolt:         bolt://localhost:7687
  PostgreSQL:         localhost:5432         (saruser / sarpass123 / sardb)
  Redis:              localhost:6379
  Kafka:              localhost:9092
  Weaviate:           http://localhost:8080

  Start everything:   ./infra/start_all.sh
  Check health:       ./infra/check_services.sh

---

## The Master State Object — SARCase

This Pydantic model flows through ALL 6 agents.
Every agent receives SARCase and returns SARCase with its section populated.
NEVER create a new SARCase inside an agent — always update and return the one received.

  class SARCase(BaseModel):
    case_id: str                              # generated at pipeline start
    status: SARStatus                         # PENDING → IN_REVIEW → FILED/DISMISSED
    raw_transaction: Optional[dict]           # set before pipeline starts
    normalized: Optional[NormalizedCase]      # set by Agent 1
    risk_assessment: Optional[RiskAssessment] # set by Agent 2
    narrative: Optional[SARNarrative]         # set by Agent 3
    compliance: Optional[ComplianceResult]    # set by Agent 4
    audit: Optional[AuditRecord]              # set by Agent 5
    analyst_approved_by: Optional[str]        # set by Agent 6
    final_filed_timestamp: Optional[datetime] # set by Agent 6
    audit_trail: list[dict]                   # every agent appends here
    error_log: list[dict]                     # errors append here, never crash

Full schema in: agents/shared/schemas.py

---

## Agent Node Function Signature — Follow This Exactly

  Every agent MUST follow this pattern:

  async def agent_N_name(state: SARCase) -> SARCase:
      try:
          # 1. read from state (previous agent outputs)
          # 2. do work
          # 3. populate state.your_section = YourModel(...)
          # 4. append to state.audit_trail
          state.audit_trail.append({
              "agent": "Agent N - Name",
              "action": "description of what was done",
              "confidence": 0.95,  # float 0-1
              "timestamp": datetime.now().isoformat()
          })
          # 5. return updated state
          return state
      except Exception as e:
          state.error_log.append({
              "agent": "Agent N - Name",
              "error": str(e),
              "timestamp": datetime.now().isoformat()
          })
          return state  # NEVER raise — always return state

---

## LangGraph Pipeline Structure

  File: agents/pipeline.py
  
  Graph order:
  START
    → agent1_ingest          (P1 owns)
    → validate_gate_1        (checks state.normalized is not None)
    → agent2_assess_risk     (P1 owns)
    → validate_gate_2        (checks state.risk_assessment is not None)
    → check_if_red           (conditional: GREEN → skip to END, RED/AMBER → continue)
    → agent3_generate_narrative  (P2 owns)
    → validate_gate_3        (checks state.narrative is not None)
    → agent4_check_compliance    (P2 owns)
    → validate_gate_4        (checks state.compliance is not None)
    → agent5_write_audit     (P2 owns)
    → END
  
  Agent 6 is NOT in the graph — it is triggered by human approval in the UI.
  
  Pipeline entry point:
  async def run_pipeline(raw_transaction: dict) -> SARCase
  
  FastAPI calls run_pipeline. UI calls FastAPI. Neo4j is written by Agent 5.

---

## Neo4j Schema — Node Labels and Relationships

  Node labels:
    Account       { account_id: str, created_at: datetime }
    Transaction   { transaction_id: str, amount_usd: float, timestamp: datetime,
                    transaction_type: str, geography: str }
    SARCase       { case_id: str, status: str, risk_score: float, tier: str,
                    immutable_hash: str, created_at: datetime }
    RiskSignal    { signal_id: str, signal_type: str, description: str,
                    confidence: float }
    AuditEvent    { event_id: str, agent: str, action: str,
                    confidence: float, timestamp: datetime }

  Relationships:
    (Account)-[:SENT]->(Transaction)
    (Transaction)-[:RECEIVED_BY]->(Account)
    (SARCase)-[:CONTAINS]->(Transaction)
    (SARCase)-[:FLAGGED_BY]->(RiskSignal)
    (SARCase)-[:HAS_AUDIT]->(AuditEvent)

  Constraints file: graph/neo4j/init_schema.py
  Cypher queries:   graph/neo4j/cypher_queries/

  RULE: AuditEvent nodes are APPEND ONLY.
  Never UPDATE or DELETE any AuditEvent or SARCase node.
  Only CREATE new nodes. This is what makes the audit trail immutable.

---

## FastAPI Endpoints — Complete List

  P1 builds and owns all of these:

  POST   /submit-transaction          → scores risk, creates case, returns SARCase
  GET    /cases                       → returns list of all cases
  GET    /case/{id}                   → returns single case
  POST   /case/{id}/run-pipeline      → runs full 6-agent pipeline on stored case
  GET    /case/{id}/pipeline-status   → returns which agents completed
  POST   /case/{id}/generate-narrative→ triggers Agent 3 only (for UI button)
  POST   /case/{id}/approve           → triggers Agent 6, sets status FILED
  POST   /case/{id}/dismiss           → sets status DISMISSED
  GET    /case/{id}/graph             → returns nodes+edges for pyvis visualization
  GET    /health                      → {"status": "ok"}

  All endpoints return JSON.
  All endpoints handle errors and never return 500 without a message.
  CORS is open (allow all origins) for local development.

---

## Minimax API — How to Call It

  Model:       MiniMax-Text-01
  Base URL:    https://api.minimax.chat/v1/text/chatcompletion_v2
  Auth:        Bearer token in Authorization header
  API Key:     stored in .env.local as MINIMAX_API_KEY
               load with: os.getenv("MINIMAX_API_KEY")

  Always use:
    temperature: 0.1    (low = consistent, factual output)
    max_tokens: 800     (enough for SAR narrative)
    timeout: 30 seconds

  SAR narrative system prompt is in: agents/agent3_narrative/prompts.py
  Do NOT inline prompts in node.py — always import from prompts.py

  If Minimax fails: use the fallback template in agents/agent3_narrative/fallback.py
  Never let a Minimax failure crash the pipeline.

---

## Pydantic Validation Rules — Enforced at Every Agent Boundary

  After each agent runs, a validation gate checks the output.
  If the gate fails: the case goes to error state, pipeline continues, never crashes.

  Agent 1 gate: state.normalized is not None
                state.normalized.presidio_masked == True
                len(state.normalized.transactions) > 0

  Agent 2 gate: state.risk_assessment is not None
                0.0 <= state.risk_assessment.risk_score <= 1.0
                state.risk_assessment.risk_tier in [GREEN, AMBER, RED, CRITICAL]

  Agent 3 gate: state.narrative is not None (only if tier is RED or AMBER)
                len(state.narrative.narrative_body) > 100

  Agent 4 gate: state.compliance is not None
                len(state.compliance.compliance_issues) is a list (can be empty)

  Agent 5 gate: state.audit is not None
                state.audit.immutable_hash is not None and len > 0

---

## Environment Variables — Everyone Needs These

  File: .env.local (never commit this file)
  Load with: from dotenv import load_dotenv; load_dotenv('.env.local')

  NEO4J_URI=bolt://localhost:7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=sarplatform123
  POSTGRES_URI=postgresql://saruser:sarpass123@localhost:5432/sardb
  REDIS_URL=redis://localhost:6379
  WEAVIATE_URL=http://localhost:8080
  KAFKA_BOOTSTRAP_SERVERS=localhost:9092
  KAFKA_TOPIC_TRANSACTIONS=transactions
  KAFKA_TOPIC_FLAGGED=flagged_transactions
  VLLM_BASE_URL=http://localhost:8000/v1
  MINIMAX_API_KEY=get_this_from_team_lead
  AWS_REGION=us-east-1
  AWS_ACCESS_KEY_ID=
  AWS_SECRET_ACCESS_KEY=

---

## Git Workflow — Exactly How We Work

  Branch structure:
    main        → never touch directly
    develop     → merge into at end of each day
    feat/p1-*   → P1 feature branches
    feat/p2-*   → P2 feature branches
    feat/p3-*   → P3 feature branches

  Daily routine:
    Morning (start of work):
      git checkout develop
      git pull origin develop
      git checkout -b feat/p1-agent1-ingestion  (use your own prefix)

    During work:
      commit every time a task is complete
      commit message format: feat(agent1): add ingestion node with pydantic gate
      never commit broken code — if it does not run, stash it

    Evening sync (9pm every night):
      git add .
      git commit -m "feat(dayX-pN): summary of what you built today"
      git push origin feat/your-branch
      open a PR to develop on GitHub
      tag the other two people to review
      merge after 1 approval

    Never push to main directly.
    Never force push.
    If merge conflict: message the team, resolve together.

---

## Demo Flow — The 6 Screens Judges Will See

  This is the ONLY thing that matters. Everything we build serves these 6 screens.

  Screen 1 — Submit Transaction (Streamlit: Submit Transaction page)
    Click "Structuring Demo" preset → fills form → click Submit
    Show: transaction details, spinner, then RED result appears

  Screen 2 — Risk Analysis result (same page, scrolled down)
    Show: risk score 0.9+, SHAP feature importance bars,
          matched typology "structuring", list of risk signals

  Screen 3 — Neo4j Graph (Streamlit: Graph View page)
    Show: colorful graph — Account nodes (blue), Transaction (amber),
          SARCase (red), AuditEvent (green)
    Point to: the circular flow pattern between accounts

  Screen 4 — SAR Narrative streaming (Streamlit: SAR Review page)
    Click "Generate Narrative" → text streams in token by token
    Show: 4 sections appearing, compliance checklist turning green

  Screen 5 — Audit Trail (Streamlit: Audit Trail page)
    Show: timeline of 5+ agent decisions with timestamps
    Point to: the immutable SHA256 hash at the bottom

  Screen 6 — Human Approval (back to SAR Review page)
    Type analyst name → click Approve and File
    Show: st.balloons(), status changes to FILED in real time

  Total demo time: 4 minutes. Practice this 3 times before submission.

---

## What Good Looks Like for Each Task

  Before marking any task as done, verify:
  
  Backend task done:   curl command returns expected JSON with no errors
  Agent task done:     pytest test for that agent passes
  Neo4j task done:     MATCH (n) RETURN n in browser shows correct nodes
  UI task done:        the relevant page works with real data, no spinners stuck
  Integration done:    full pipeline runs on structuring scenario, all fields populated

---

## Files Map — Where Everything Lives

  main.py                              → FastAPI app, all endpoints
  agents/shared/schemas.py             → ALL Pydantic models, source of truth
  agents/pipeline.py                   → LangGraph StateGraph wiring
  agents/agent1_ingestion/node.py      → Agent 1 LangGraph node
  agents/agent2_risk/node.py           → Agent 2 LangGraph node
  agents/agent2_risk/typologies.py     → 4 AML typology definitions
  agents/agent3_narrative/node.py      → Agent 3 LangGraph node
  agents/agent3_narrative/minimax_client.py → all Minimax API calls
  agents/agent3_narrative/prompts.py   → system and user prompt templates
  agents/agent4_compliance/node.py     → Agent 4 LangGraph node
  agents/agent4_compliance/rules.py    → 8 compliance check functions
  agents/agent5_audit/node.py          → Agent 5 LangGraph node
  agents/agent6_review/node.py         → Agent 6 approval handler
  prediction_engine/model.py           → XGBoost scorer + SHAP
  prediction_engine/simulator.py       → 3 demo scenario generators
  graph/neo4j/init_schema.py           → schema init + GraphWriter class
  graph/neo4j/graph_api.py             → functions for visualization data
  graph/neo4j/cypher_queries/          → all .cypher files
  ui/app.py                            → Streamlit app, all 5 pages
  ui/api_client.py                     → all FastAPI calls from UI
  ui/mock_data.py                      → mock data for offline dev
  infra/start_all.sh                   → one command to start everything
  infra/check_services.sh              → health check all services
  tests/unit/                          → unit tests per module
  tests/integration/test_full_pipeline.py → end to end test
  docs/demo_script.md                  → word for word demo script
  docs/pitch_deck_content.md           → slide content

---

## Known Issues and Decisions Already Made

  Decision: No vLLM self-hosted. Too slow to set up for hackathon.
            Use Minimax API directly for all LLM calls.

  Decision: No Kafka consumer. Use Python asyncio queue + simulator instead.
            Mention Kafka in pitch as production architecture.

  Decision: No Kubernetes. Docker Compose is enough for demo.

  Decision: Presidio is mocked. Set presidio_masked=True in Agent 1.
            Mention it in pitch as a production feature.

  Decision: Weaviate RAG uses 3 hardcoded SAR templates injected as
            context strings in the Minimax prompt. Real RAG in production.

  Decision: PostgreSQL stores cases in memory (dict) for the demo.
            Add DB persistence only if time permits on Day 3.

---

## Questions? Conflicts? Blockers?

  Post in the team WhatsApp/Slack immediately.
  Do not spend more than 30 minutes stuck on anything.
  Tag the person who owns the relevant module.
  If a schema needs to change: all 3 people agree before anyone edits schemas.py.