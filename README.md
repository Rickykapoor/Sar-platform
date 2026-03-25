# 🏦 SAR Platform — AI-Powered Suspicious Activity Report Generator

> An AI-powered, multi-agent pipeline that automatically generates regulator-ready Suspicious Activity Reports (SAR) for banks — built for a hackathon demo by a 4-person team.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.4-green)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.45-purple)](https://github.com/langchain-ai/langgraph)
[![LLM](https://img.shields.io/badge/LLM-Groq%20Llama%203-orange)](#llm-groq-api-key-needed)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014-black)](https://nextjs.org/)

---

> [!IMPORTANT]
> **Read `MASTER_CONTEXT.md` at the start of EVERY work session.** It is the single source of truth. All decisions, schemas, and API specs live there.

> [!IMPORTANT]
> **Groq API Key Required.** The LLM (Llama 3 8B) uses the fast and free Groq API. You must set `GROQ_API_KEY` in the `.env.local` file.

> [!CAUTION]
> **Never commit `.env.local`** — it is in `.gitignore` but always double-check before pushing. **Never push directly to `main` or `develop`.** Always use PRs.

---

## 📖 What This Does

The SAR Platform processes every bank transaction through two intelligent loops:

**🔵 Outer Loop — Prediction Engine**
```
Every transaction → XGBoost ML ensemble → GREEN / AMBER / RED
```
RED transactions automatically enter the SAR pipeline.

**🔴 Inner Loop — 6-Agent SAR Pipeline**
```
Agent 1 → Agent 2 → Agent 3 → Agent 4 → Agent 5 → Agent 6
Ingestion  Risk     Narrative  Compliance  Audit   Human Review
```
Output: Regulator-ready SAR document + immutable audit trail in Neo4j.

---

## 👥 Team & Module Ownership

> [!IMPORTANT]
> **Only work in your assigned modules. If you need to touch another person's module, ask them first on WhatsApp.** Unauthorized edits will be blocked at PR review.

| Rank | Name | Role | Modules Owned |
|---|---|---|---|
| 1 — Tech Lead | **Ricky** | Backend + ML | `main.py`, `agents/pipeline.py`, `agents/agent1_ingestion/`, `agents/agent2_risk/`, `prediction_engine/` |
| 2 — Senior | **Nisarg** | AI + Graph | `agents/agent3_narrative/`, `agents/agent4_compliance/`, `agents/agent5_audit/`, `graph/neo4j/` |
| 3 | **Anshul** | UI + Review | `agents/agent6_review/`, `ui/nextjs/` |
| 4 — Junior | **Ashwin** | Infra + Tests | `infra/`, `docker-compose.yml`, `tests/` |

**Shared files** (all 4 must agree before editing):
- `agents/shared/schemas.py` — Pydantic contracts between all agents
- `requirements.txt`
- `MASTER_CONTEXT.md`

---

## 🧱 Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Runtime | Python 3.11 | Use exactly 3.11 |
| API | FastAPI 0.115.4 + uvicorn | Ricky owns |
| AI Pipeline | LangGraph 0.2.45 + LangChain 0.3.7 | Nisarg + Ricky |
| **LLM** | **Groq API (Llama 3 8B)** | **GROQ_API_KEY needed** |
| Data Models | Pydantic v2 (2.9.2) | BaseModel everywhere |
| Graph DB | Neo4j 5.14 Enterprise | Nisarg owns |
| Relational DB | PostgreSQL 16 | In-memory for demo |
| Cache | Redis 7 | Started by Docker |
| Vector Store | Weaviate 1.24 | Started by Docker |
| Streaming | Kafka 3.6 | Mocked by simulator |
| ML | XGBoost + scikit-learn + SHAP | Ricky owns |
| Frontend | Next.js 14/16 (App Router) + Tailwind | Anshul owns |
| Containers | Docker Compose | Ashwin owns |

---

## 🚀 Setup for New Team Members (Read Every Step)

### Prerequisites — Install These First

```bash
# 1. Docker Desktop (required for all services)
# Download from: https://www.docker.com/products/docker-desktop/
# After install, open Docker Desktop and wait for the whale icon to appear

# 2. Python 3.11 (exact version)
# macOS:
brew install python@3.11
# Windows: download from python.org/downloads/release/python-3110/

# 3. Git
git --version   # already installed on most machines
```

> [!WARNING]
> You MUST use Python **3.11** specifically. 3.12+ has breaking changes with some dependencies.

### Step 1 — Clone the repo

```bash
git clone https://github.com/Rickykapoor/Sar-platform.git
cd Sar-platform
```

### Step 2 — Create virtual environment

```bash
# Create venv (use python3.11 explicitly)
python3.11 -m venv .venv

# Activate it
source .venv/bin/activate       # macOS / Linux
# .venv\Scripts\activate        # Windows

# Verify you're using the right Python
python --version   # must say Python 3.11.x
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Set up environment variables

```bash
cp .env.example .env.local
```

Open `.env.local` in your editor. It looks like this:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=sarplatform123
POSTGRES_URI=postgresql://saruser:sarpass123@localhost:5432/sardb
REDIS_URL=redis://localhost:6379
WEAVIATE_URL=http://localhost:8080
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_TRANSACTIONS=transactions
KAFKA_TOPIC_FLAGGED=flagged_transactions
GROQ_API_KEY=your_key_here
```

> [!NOTE]
> **A Groq API Key is REQUIRED**. Set it in `.env.local` or the narrative generation will use local fallback templates.

### Step 5 — Start all infrastructure with Docker

> [!IMPORTANT]
> **Docker Desktop must be running** before this step. Open it and wait for the green "Running" status.

```bash
# Give execute permission (first time only)
chmod +x infra/start_all.sh infra/check_services.sh

# Start all Docker services (Neo4j, Postgres, Redis, Kafka, Weaviate)
./infra/start_all.sh
```

This starts: Neo4j, PostgreSQL, Redis, Zookeeper, Kafka, and Weaviate.
First run will download images (~3 GB). Subsequent runs are fast.

**Verify all services are healthy:**

```bash
./infra/check_services.sh
```

Expected output:
```
✅ Neo4j       localhost:7474   UP
✅ PostgreSQL  localhost:5432   UP
✅ Redis       localhost:6379   UP
✅ Kafka       localhost:9092   UP
✅ Weaviate    localhost:8080   UP
```

If any service shows DOWN, wait 30 seconds and retry. Neo4j takes ~60 seconds to start.

### Step 6 — Initialize Neo4j schema

```bash
python graph/neo4j/init_schema.py
```

This creates constraints and indexes. Only needs to run once per fresh Docker volume.

### Step 7 — Start the FastAPI backend

```bash
uvicorn main:app --reload --port 8000
```

Verify it works:

```bash
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

Open the interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Step 8 — Start the Next.js frontend (new terminal tab)

```bash
cd ui/nextjs
npm install
npm run dev
```

The UI opens automatically at [http://localhost:3000](http://localhost:3000).

### Step 9 — Run the test suite

```bash
pytest tests/ -v
python -m mypy agents/
```

All tests should pass. If a test fails before you've written any code, tell Ricky.

---

## 🐳 Docker Services — Detailed Reference

### Service Map

| Service | Image | Port | Purpose |
|---|---|---|---|
| Neo4j | `neo4j:5.14-enterprise` | 7474 (browser), 7687 (bolt) | Graph DB for audit trail |
| PostgreSQL | `timescale/timescaledb:latest-pg16` | 5432 | Relational DB (minimal use in demo) |
| Redis | `redis:7-alpine` | 6379 | Cache |
| Zookeeper | `confluentinc/cp-zookeeper:7.5.0` | 2181 | Kafka dependency |
| Kafka | `confluentinc/cp-kafka:7.5.0` | 9092 | Event streaming (mocked in demo) |
| Weaviate | `semitechnologies/weaviate:1.24.0` | 8080 | Vector store (hardcoded context in demo) |

### Docker commands you'll actually use

```bash
# Start everything
docker compose up -d

# Stop everything (keeps data)
docker compose stop

# Stop and DELETE all data volumes (fresh start)
docker compose down -v

# View logs for a specific service
docker compose logs -f neo4j
docker compose logs -f kafka

# Check what's running
docker compose ps

# Restart a single service
docker compose restart redis
```

### Neo4j browser

Open [http://localhost:7474](http://localhost:7474)
- Username: `neo4j`
- Password: `sarplatform123`

To verify data after running the pipeline:
```cypher
MATCH (n) RETURN n LIMIT 50
```

### Common Docker problems & fixes

| Problem | Fix |
|---|---|
| "Port already in use" | `lsof -i :7474` → kill that PID, then try again |
| Neo4j keeps restarting | Run `docker compose logs neo4j` to see why |
| Kafka not starting | Zookeeper must start before Kafka — check `docker compose ps` |
| "Cannot connect to Docker daemon" | Open Docker Desktop first |
| Services start but Neo4j is DOWN | Wait 60 seconds — it's slow to initialize |

---

## 🤖 LLM — Groq API

> [!IMPORTANT]
> The LLM **(Llama 3 8B)** uses the Groq API. You must set `GROQ_API_KEY` in `.env.local`.

**How it works in code (`agents/agent3_narrative/minimax_client.py`):**

```python
import openai
import os

client = openai.AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

response = await client.chat.completions.create(
    model="llama3-8b-8192",
    messages=[...],
    temperature=0.1,
    max_tokens=900,
)
```

If the LLM call fails for any reason, the **fallback template** in `agents/agent3_narrative/fallback.py` activates — the pipeline never crashes.

---

## 📁 Project Structure

```
Sar-platform/
├── main.py                               ← FastAPI app + all 10 endpoints (Ricky)
├── agents/
│   ├── shared/schemas.py                 ← ALL Pydantic models — SHARED, coordinate first
│   ├── pipeline.py                       ← LangGraph StateGraph wiring (Ricky)
│   ├── agent1_ingestion/node.py          ← Ingest + PII mask (Ricky)
│   ├── agent2_risk/
│   │   ├── node.py                       ← Risk scoring (Ricky)
│   │   └── typologies.py                 ← 4 AML typologies (Ricky)
│   ├── agent3_narrative/
│   │   ├── node.py                       ← Narrative generation (Nisarg)
│   │   ├── minimax_client.py             ← Free LLM calls via OpenCode (Nisarg)
│   │   ├── prompts.py                    ← All prompts here, never inline (Nisarg)
│   │   └── fallback.py                   ← Template fallback if LLM fails (Nisarg)
│   ├── agent4_compliance/
│   │   ├── node.py                       ← Compliance checks (Nisarg)
│   │   └── rules.py                      ← 8 compliance functions (Nisarg)
│   ├── agent5_audit/node.py              ← SHA256 hash + Neo4j write (Nisarg)
│   └── agent6_review/node.py            ← Human approval handler (Anshul)
├── prediction_engine/
│   ├── model.py                          ← XGBoost + SHAP (Ricky)
│   └── simulator.py                      ← 3 demo scenarios (Ricky)
├── graph/neo4j/
│   ├── init_schema.py                    ← Constraints + GraphWriter (Nisarg)
│   ├── graph_api.py                      ← Visualization data (Nisarg)
│   └── cypher_queries/                   ← All .cypher files (Nisarg)
├── ui/nextjs/
│   ├── app/                              ← Next.js App Router Pages (Anshul)
│   ├── components/                       ← React components (Anshul)
│   ├── lib/api.ts                        ← FastAPI clients (Anshul)
│   ├── package.json                      ← Node.js deps (Anshul)
│   └── tailwind.config.ts                ← Tailwind CSS v4 config (Anshul)
├── infra/
│   ├── start_all.sh                      ← Start all Docker services (Ashwin)
│   └── check_services.sh                 ← Health check all services (Ashwin)
├── tests/
│   ├── unit/                             ← Unit tests per module (Ashwin)
│   └── integration/test_full_pipeline.py ← End-to-end test (Ashwin)
├── docs/
│   ├── demo_script.md                    ← Word-for-word demo (Ashwin writes)
│   └── pitch_deck_content.md             ← Slide content (Ashwin writes)
├── docker-compose.yml                    ← All service definitions (Ashwin)
├── requirements.txt                      ← SHARED — coordinate before editing
├── .env.example                          ← Template — copy to .env.local
├── .env.local                            ← ⛔ NEVER COMMIT THIS
├── MASTER_CONTEXT.md                     ← 📖 Read every session
├── TASKS.md                              ← Sprint board
├── CONTRIBUTING.md                       ← Branch and PR rules
└── PR_STRATEGY.md                        ← Ricky's merge guide
```

---

## 🌐 Service Ports at a Glance

| Service | URL | Credentials |
|---|---|---|
| FastAPI Backend | http://localhost:8000 | — |
| FastAPI Docs (Swagger) | http://localhost:8000/docs | — |
| Next.js UI | http://localhost:3000 | — |
| Neo4j Browser | http://localhost:7474 | neo4j / sarplatform123 |
| Neo4j Bolt | bolt://localhost:7687 | — |
| PostgreSQL | localhost:5432 | saruser / sarpass123 / sardb |
| Redis | localhost:6379 | — |
| Kafka | localhost:9092 | — |
| Weaviate | http://localhost:8080 | — |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check — first thing to test |
| `POST` | `/submit-transaction` | Score risk, create SAR case, trigger pipeline |
| `GET` | `/cases` | List all cases |
| `GET` | `/case/{id}` | Get single case with full state |
| `POST` | `/case/{id}/run-pipeline` | Run full 6-agent pipeline |
| `GET` | `/case/{id}/pipeline-status` | Which agents completed |
| `POST` | `/case/{id}/generate-narrative` | Trigger Agent 3 (for UI button) |
| `POST` | `/case/{id}/approve` | Human approval → FILED |
| `POST` | `/case/{id}/dismiss` | Dismiss case |
| `GET` | `/case/{id}/graph` | Nodes + edges for Neo4j viz |

---

## 📋 Hard Rules — Read These Before Writing a Single Line

> [!CAUTION]
> **These are not suggestions. Breaking these rules creates bugs and blocks the whole team.**

### Code Rules

1. **Every agent function MUST follow this signature exactly:**
   ```python
   async def agent_N_name(state: SARCase) -> SARCase:
   ```

2. **Never `raise` inside an agent node.** Always catch exceptions and append to `state.error_log`, then return `state`. The pipeline must never crash.

3. **Never construct a new `SARCase()` inside an agent.** Always receive the state object and return it modified.

4. **Every agent MUST append to `state.audit_trail`** before returning.

5. **Never inline prompts.** All prompts live in `agents/agent3_narrative/prompts.py`. Import them.

6. **Load all config from environment variables** — never hardcode ports, passwords, or keys.

### Git Rules

7. **Never push directly to `main` or `develop`.** Always use a feature branch + PR.

8. **Never force push** to any shared branch (`main`, `develop`). Force push is only allowed on your own feature branch with `--force-with-lease`.

9. **Commit messages must follow the format:** `feat(scope): short description`

10. **Never commit `.env.local`** or any file containing real credentials.

11. **Only edit your own modules.** See the ownership table above.

12. **Shared files (`schemas.py`, `requirements.txt`) need team agreement** before anyone edits them.

### Collaboration Rules

13. **Post blockers in WhatsApp immediately** — do not sit stuck for more than 30 minutes.

14. **Tag the module owner before changing their code.** Even for a one-line fix.

15. **If you add a package to `requirements.txt`,** announce it in WhatsApp so everyone can reinstall.

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run just unit tests
pytest tests/unit/ -v

# Run just integration test (needs all services running)
pytest tests/integration/ -v

# Type checking
python -m mypy agents/

# Test a single endpoint manually
curl -X POST http://localhost:8000/submit-transaction \
  -H "Content-Type: application/json" \
  -d '{"amount_usd": 9800, "transaction_type": "wire", "geography": "offshore"}'
```

### "Done" Criteria per Task Type

| Task Type | How to Verify It's Done |
|---|---|
| Backend endpoint | `curl` returns correct JSON, no errors |
| Agent task | `pytest tests/unit/test_agentN.py -v` passes |
| Neo4j task | `MATCH (n) RETURN n` in browser shows correct nodes |
| UI task | Page works with real data, no stuck spinners |
| Integration | Full pipeline on structuring scenario, all fields populated |

---

## 📅 Daily Git Ritual

### Morning (start of day)

```bash
git checkout develop
git pull origin develop
git checkout -b feat/yourname-taskname
# e.g. git checkout -b feat/nisarg-minimax-client
```

### During the day

```bash
# Commit every completed task (not every 5 minutes)
git add <files you changed>
git commit -m "feat(agent3): add minimax client with fallback"
# Never commit broken code. Use git stash if needed.
```

### Evening (9pm)

```bash
git add .
git commit -m "feat(day1-nisarg): agent3 narrative and agent4 compliance complete"
git push origin feat/nisarg-day1

# Open PR on GitHub → target: develop
# Fill in PR description
# Tag at least 1 person to review
# Merge after 1 approval
```

---

## 🎬 Demo Flow (6 Screens — Practice This)

| # | Screen | What to show |
|---|---|---|
| 1 | Landing Page | Clean, black SaaS theme → "Open Demo Center" |
| 2 | Demo Center | Present 3 AML Scenarios → click "Run Scenario" |
| 3 | Case Detail | 5-tab interface. Show Pipeline status → Risk Analysis with SHAP charts. |
| 4 | SAR Report | AI streaming → Compliance Checklist → "Download PDF" (generates text-based PDF) |
| 5 | Audit Trail | 6-agent timeline + Immutable SHA256 copy-to-clipboard |
| 6 | Approval Flow | "Approve & File" → marks case as FILED |

> Total demo time: **4 minutes**. Practice this 3 times before submission.

---

## ❓ Getting Help

| Situation | What to do |
|---|---|
| Stuck on a bug > 30 min | Post in WhatsApp with error + what you tried |
| Need to change someone's module | Ask the owner, get explicit OK |
| Want to change schemas.py | Post in WhatsApp, get all 4 to agree, then edit |
| Need the LLM/API key | No key needed — it's free in OpenCode |
| Merge conflict | See `PR_STRATEGY.md` Part 3, or message Ricky |
| Docker service is down | See the Docker troubleshooting table above |
| PR questions | See `PR_STRATEGY.md` — it's Ricky's guide |
