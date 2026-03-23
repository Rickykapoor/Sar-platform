# SAR Platform — Pitch Deck Content

## Slide 1: The Problem
- **Manual Overhead:** AML analysts spend 80% of their time collecting data and writing repetitive narratives.
- **Backlogs:** Financial institutions face massive backlogs of alerts, risking regulatory fines.
- **Inconsistencies:** Human review leads to subjective, varying quality in Suspicious Activity Reports (SARs).
- **Compliance Risk:** Missing fields or formatting errors lead to rejected filings.

## Slide 2: The Solution
- **AI-Powered Automation:** A multi-agent LangGraph pipeline that automates ingestion, risk scoring, and narrative generation.
- **Human-in-the-Loop:** Analysts transition from data gatherers to strategic reviewers.
- **Instant Triage:** Real-time ML models evaluate and categorize risk tiers instantly.
- **Regulatory Ready:** Auto-validates compliance checks before human approval is even requested.

## Slide 3: Architecture
- **Frontend:** Streamlit web application providing rapid, real-time feedback and state management.
- **Backend Core:** FastAPI routing asynchronous calls to the LangGraph pipeline engine.
- **Multi-Agent System:** 5 distinct LLM/ML agents (Ingestion, Risk, Narrative, Compliance, Audit).
- **Graph Database:** Neo4j stores connected entity data to detect complex typologies like smurfing and layering.

## Slide 4: Demo Flow
- **Ingestion:** Submitting an offshore wire transfer designed to evade thresholds.
- **Risk Scoring:** Explainable AI (SHAP) surfacing why the transaction was flagged RED.
- **Graph Analysis:** Visualizing the multi-hop relationships.
- **Review:** Streaming LLM narrative generation and real-time compliance validation.
- **Audit:** Cryptographic SHA256 sealing of the final case log.

## Slide 5: Business Impact
- **80% Reduction** in manual SAR drafting time (from ~90 mins to under 15 mins).
- **$2M+ Annual Savings** per 100 AML investigators in reduced operational costs.
- **100% Auditability** through immutable cryptographic hashes and step-by-step logs.
- **Decreased False Positives** through explainable ML risk triage.

## Slide 6: The Team
- **Anshul:** UX Engineering & Audit Interfacing 
- **Ricky:** API Architecture & LLM Engineering
- **Nisarg:** Graph Database Architecture
- **Ashwin:** Infrastructure, Testing & Integrations
