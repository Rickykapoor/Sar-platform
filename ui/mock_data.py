"""
ui/mock_data.py
Owned by: Anshul

Realistic SARCase-shaped mock data for local UI development.
Used when the FastAPI backend (localhost:8000) is not yet running.

Scenario: Structuring — multiple sub-threshold cash deposits to evade BSA reporting.
"""

from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_NOW = datetime(2026, 3, 24, 2, 0, 0)
_CASE_ID = "CASE-2026-00147"
_HASH = "a3f8c2d9e1b74650f2a891cd3e70b82f5d6a1c4e9f3b28d7e0c5a94f1b6d2e8a"


def _iso(offset_minutes: int = 0) -> str:
    return (_NOW + timedelta(minutes=offset_minutes)).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# Full SARCase-shaped mock dict (matches agents/shared/schemas.py structure)
# ─────────────────────────────────────────────────────────────────────────────

MOCK_CASE: dict = {
    "case_id": _CASE_ID,
    "status": "in_review",

    # Raw transaction (as submitted to the API)
    "raw_transaction": {
        "account_id": "ACC-8821-US",
        "counterparty_account_id": "ACC-0034-OFF",
        "amount_usd": 9_800.00,
        "transaction_type": "cash_deposit",
        "channel": "branch",
        "geography": "offshore",
        "timestamp": _iso(-90),
    },

    # ── Agent 1 — Normalized Case ──────────────────────────────────────────
    "normalized": {
        "case_id": _CASE_ID,
        "transactions": [
            {
                "transaction_id": "TX-2026-001",
                "account_id": "ACC-8821-US",
                "counterparty_account_id": "ACC-0034-OFF",
                "amount_usd": 9_800.00,
                "timestamp": _iso(-90),
                "transaction_type": "cash_deposit",
                "channel": "branch",
                "geography": "offshore",
            },
            {
                "transaction_id": "TX-2026-002",
                "account_id": "ACC-8821-US",
                "counterparty_account_id": "ACC-0034-OFF",
                "amount_usd": 9_500.00,
                "timestamp": _iso(-85),
                "transaction_type": "cash_deposit",
                "channel": "branch",
                "geography": "offshore",
            },
            {
                "transaction_id": "TX-2026-003",
                "account_id": "ACC-8821-US",
                "counterparty_account_id": "ACC-9912-OFF",
                "amount_usd": 9_700.00,
                "timestamp": _iso(-80),
                "transaction_type": "wire",
                "channel": "online",
                "geography": "offshore",
            },
        ],
        "subject_name": "Marcus T. Holloway",
        "subject_account_ids": ["ACC-8821-US"],
        "date_range_start": _iso(-180),
        "date_range_end": _iso(0),
        "total_amount_usd": 29_000.00,
        "ingestion_timestamp": _iso(-88),
        "presidio_masked": True,
    },

    # ── Agent 2 — Risk Assessment ──────────────────────────────────────────
    "risk_assessment": {
        "case_id": _CASE_ID,
        "risk_tier": "red",
        "risk_score": 0.92,
        "matched_typology": "Structuring",
        "typology_confidence": 0.94,
        "signals": [
            {
                "signal_type": "BSA_THRESHOLD_AVOIDANCE",
                "description": "Multiple cash deposits just below $10,000 BSA reporting threshold within 24 hours.",
                "confidence": 0.97,
                "supporting_transaction_ids": ["TX-2026-001", "TX-2026-002"],
            },
            {
                "signal_type": "HIGH_RISK_GEOGRAPHY",
                "description": "Funds routed to offshore account in high-risk jurisdiction.",
                "confidence": 0.91,
                "supporting_transaction_ids": ["TX-2026-001", "TX-2026-002", "TX-2026-003"],
            },
            {
                "signal_type": "UNUSUAL_FREQUENCY",
                "description": "3 transactions within 10-minute window — atypical for this account.",
                "confidence": 0.88,
                "supporting_transaction_ids": ["TX-2026-001", "TX-2026-002", "TX-2026-003"],
            },
            {
                "signal_type": "ROUND_NUMBER_PATTERN",
                "description": "All amounts are rounded to nearest $100 — indicative of deliberate sizing.",
                "confidence": 0.83,
                "supporting_transaction_ids": ["TX-2026-001", "TX-2026-002", "TX-2026-003"],
            },
        ],
        # SHAP feature importance (for bar chart on Risk Analysis page)
        "shap_values": {
            "amount_vs_threshold": 0.41,
            "geography_risk_score": 0.28,
            "transaction_frequency": 0.16,
            "round_number_flag": 0.09,
            "dormant_account_flag": 0.06,
        },
        "neo4j_pattern_found": True,
        "assessment_timestamp": _iso(-85),
    },

    # ── Agent 3 — SAR Narrative ────────────────────────────────────────────
    "narrative": {
        "case_id": _CASE_ID,
        "subject_information": (
            "Marcus T. Holloway, account holder since 2019. Account ACC-8821-US. "
            "No prior SAR filings. Employment: self-employed consultant."
        ),
        "suspicious_activity_description": (
            "Between 02:00 and 02:10 UTC on March 24 2026, the subject conducted "
            "three consecutive cash deposits of $9,800, $9,500, and $9,700 — all "
            "deliberately structured below the $10,000 BSA reporting threshold. "
            "Funds were immediately wired to an offshore counterparty (ACC-0034-OFF) "
            "in a high-risk jurisdiction. Pattern is consistent with structuring as "
            "defined under 31 U.S.C. §5324."
        ),
        "narrative_body": (
            "FinCEN SAR — Case Reference: CASE-2026-00147\n\n"
            "SUBJECT INFORMATION\n"
            "Marcus T. Holloway (DOB redacted per Presidio masking). Account ACC-8821-US "
            "held at First National Bank, Denver, CO. Account opened March 2019. "
            "No prior SAR history on file.\n\n"
            "SUSPICIOUS ACTIVITY\n"
            "On March 24 2026, our AI-powered transaction monitoring system detected "
            "three structuring transactions totalling $29,000 USD executed within a "
            "10-minute window. Each deposit was deliberately set below the $10,000 "
            "Currency Transaction Report (CTR) filing threshold — a hallmark pattern "
            "of structuring under 31 U.S.C. §5324(a)(3). Funds were routed "
            "immediately to offshore Account ACC-0034-OFF in an FATF grey-listed "
            "jurisdiction. Our XGBoost risk model assigned a score of 0.92 (RED tier) "
            "and our SHAP analysis identified BSA threshold avoidance as the primary "
            "risk driver (SHAP=0.41).\n\n"
            "SUPPORTING EVIDENCE\n"
            "Transaction IDs: TX-2026-001, TX-2026-002, TX-2026-003. "
            "All three transactions exhibit round-hundred sizing ($9,800 / $9,500 / $9,700). "
            "The 10-minute execution window is 14 standard deviations from the "
            "account's historical transaction frequency baseline.\n\n"
            "LAW ENFORCEMENT NOTE\n"
            "This institution has filed this SAR based on reasonable grounds to suspect "
            "money laundering activity. We are prepared to provide full transaction "
            "records and account history upon lawful request. Contact: BSA Officer, "
            "First National Bank, compliance@firstnational.example.com."
        ),
        "supporting_evidence_refs": [
            "TX-2026-001",
            "TX-2026-002",
            "TX-2026-003",
            "XGBoost model v2.1 — risk_score=0.92",
            "SHAP feature analysis — top driver: amount_vs_threshold=0.41",
        ],
        "model_version_used": "MiniMax-Text-2.5 (via OpenCode free proxy)",
        "generation_timestamp": _iso(-70),
    },

    # ── Agent 4 — Compliance Result ────────────────────────────────────────
    "compliance": {
        "case_id": _CASE_ID,
        "bsa_compliant": False,
        "all_fields_complete": True,
        "fincen_format_valid": True,
        "compliance_issues": [
            "BSA threshold avoidance: multiple transactions below $10,000 CTR limit within 24h.",
            "High-risk geography: offshore counterparty account in FATF grey-listed jurisdiction.",
            "Structuring pattern (31 U.S.C. §5324): three deliberately sized sub-threshold deposits.",
            "Unusual transaction frequency: 3 transactions in 10 minutes — 14σ above account baseline.",
        ],
        "validated_timestamp": _iso(-60),
    },

    # ── Agent 5 — Audit Record ─────────────────────────────────────────────
    "audit": {
        "case_id": _CASE_ID,
        "neo4j_audit_node_id": "AE-CASE-2026-00147-a1b2c3d4",
        "agent_decisions": [],   # populated from audit_trail below
        "shap_explanations": {
            "amount_vs_threshold": 0.41,
            "geography_risk_score": 0.28,
            "transaction_frequency": 0.16,
            "round_number_flag": 0.09,
            "dormant_account_flag": 0.06,
        },
        "data_sources_cited": [
            "agents/agent1_ingestion",
            "agents/agent2_risk",
            "agents/agent3_narrative",
            "agents/agent4_compliance",
        ],
        "audit_timestamp": _iso(-45),
        "immutable_hash": _HASH,
    },

    # ── Analyst info (set by Agent 6) ──────────────────────────────────────
    "analyst_approved_by": None,
    "final_filed_timestamp": None,

    # ── audit_trail: at least 5 entries (one per agent) ───────────────────
    "audit_trail": [
        {
            "agent": "Agent 1 - Ingestion",
            "action": "Raw transaction ingested. Presidio PII masking applied. 3 transactions normalised. NormalizedCase populated.",
            "confidence": 1.0,
            "timestamp": _iso(-88),
        },
        {
            "agent": "Agent 2 - Risk",
            "action": "XGBoost model scored transaction at 0.92 (RED). Matched typology: Structuring (confidence 0.94). Neo4j pattern match confirmed.",
            "confidence": 0.94,
            "timestamp": _iso(-85),
        },
        {
            "agent": "Agent 3 - Narrative",
            "action": "SAR narrative generated via MiniMax-Text-2.5. 4 sections produced. Narrative body: 847 characters.",
            "confidence": 0.96,
            "timestamp": _iso(-70),
        },
        {
            "agent": "Agent 4 - Compliance",
            "action": "8 compliance rules evaluated. 4 issues flagged. BSA non-compliant. FinCEN format valid.",
            "confidence": 0.99,
            "timestamp": _iso(-60),
        },
        {
            "agent": "Agent 5 - Audit",
            "action": f"Audit record created. SHA256 hash computed over full case state. Neo4j AuditEvent node: AE-CASE-2026-00147-a1b2c3d4",
            "confidence": 1.0,
            "timestamp": _iso(-45),
            "immutable_hash": _HASH,
        },
    ],

    "error_log": [],
}

# ─────────────────────────────────────────────────────────────────────────────
# Preset scenario raw_transaction dicts
# Used for the 3 preset buttons on Page 1 (Submit Transaction)
# Names match prediction_engine/simulator.py once Ricky builds it
# ─────────────────────────────────────────────────────────────────────────────

STRUCTURING_SCENARIO: dict = {
    "account_id": "ACC-8821-US",
    "counterparty_account_id": "ACC-0034-OFF",
    "amount_usd": 9_800.00,
    "transaction_type": "cash_deposit",
    "channel": "branch",
    "geography": "offshore",
    "note": "Multiple same-day sub-threshold deposits — classic structuring",
}

LAYERING_SCENARIO: dict = {
    "account_id": "ACC-5530-UK",
    "counterparty_account_id": "ACC-7890-CH",
    "amount_usd": 250_000.00,
    "transaction_type": "wire",
    "channel": "online",
    "geography": "switzerland",
    "note": "Rapid movement through multiple shell accounts to obscure origin",
}

SMURFING_SCENARIO: dict = {
    "account_id": "ACC-1100-MX",
    "counterparty_account_id": "ACC-3344-US",
    "amount_usd": 2_500.00,
    "transaction_type": "cash_deposit",
    "channel": "branch",
    "geography": "mexico",
    "note": "Coordinated small deposits by multiple individuals (smurfs)",
}
