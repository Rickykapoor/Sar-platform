# SAR Platform — Modular Implementation Plan
### AML Intelligence Engine: Graph Context, Behavioral Deviation, Typology Detection

> **Document Type:** Technical Implementation Specification  
> **Platform:** SAR (Suspicious Activity Report) Intelligence Platform  
> **Regulatory Scope:** FIU-IND, RBI Data Localisation Circular (2018), DPDP Act 2023  
> **Stack:** Python 3.11 · Neo4j 5.x · XGBoost · SHAP · FastAPI · Redis · PostgreSQL · Docker/Kubernetes

---

## Table of Contents

1. [Module 1 — Neo4j Multi-Hop Graph Context Engine](#module-1)
2. [Module 2 — Behavioral Deviation & XGBoost Risk Scoring](#module-2)
3. [Module 3 — Outflow Typology & Lifecycle Monitoring Agent](#module-3)
4. [Module 4 — Time-Window Aggregation Engine](#module-4)
5. [Module 5 — Fan-In Pattern Detection (Graph Signature Analysis)](#module-5)
6. [Module 6 — PII Stripping Layer (Regulatory Compliance)](#module-6)
7. [Module 7 — Zero Trust Security Wrapper](#module-7)
8. [Data Schema & Neo4j Graph Model](#data-schema)
9. [Inter-Module Orchestration](#orchestration)
10. [Infrastructure & Deployment](#infrastructure)

---

## Module 1 — Neo4j Multi-Hop Graph Context Engine

### Objective
Evaluate not just the subject account but the **entire upstream funding chain** up to 4 hops backward. Identify whether the subject is a **Pass-Through Node** in a smurfing or layering network.

### Sub-Components

#### 1.1 Graph Schema Design (`graph_schema.cypher`)

```cypher
// Node Types
(:Account {
  account_id: STRING,         // SHA-256 hashed internally
  account_type: STRING,       // "SAVINGS" | "CURRENT" | "CRYPTO_EXCHANGE"
  kyc_tier: STRING,           // "FULL_KYC" | "MIN_KYC" | "UNVERIFIED"
  declared_income_band: STRING,
  state_of_origin: STRING,
  risk_score: FLOAT,
  is_flagged: BOOLEAN,
  created_at: DATETIME
})

(:Transaction {
  txn_id: STRING,
  amount: FLOAT,
  currency: STRING,           // "INR" | "USD" | "USDT"
  channel: STRING,            // "NEFT" | "IMPS" | "ATM" | "SWIFT" | "CRYPTO"
  timestamp: DATETIME,
  is_cash: BOOLEAN,
  city: STRING,
  state: STRING,
  ip_hash: STRING             // hashed for privacy
})

(:Entity {
  entity_id: STRING,
  entity_type: STRING,        // "INDIVIDUAL" | "COMPANY" | "SHELL_CO"
  jurisdiction: STRING
})

// Relationship Types
(account1:Account)-[:SENT {amount: FLOAT, timestamp: DATETIME}]->(txn:Transaction)
(txn:Transaction)-[:RECEIVED_BY]->(account2:Account)
(account:Account)-[:OWNED_BY]->(entity:Entity)
(entity:Entity)-[:CONTROLS]->(account:Account)
```

#### 1.2 Multi-Hop Traversal Query Engine (`graph_traversal.py`)

```python
# graph_traversal.py
from neo4j import GraphDatabase
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class HopAnalysisResult:
    subject_account_id: str
    hops_analyzed: int
    pass_through_score: float          # 0.0 to 1.0
    upstream_cash_deposit_count: int
    upstream_unique_states: list[str]
    smurfing_indicator: bool
    suspicious_entities: list[dict]
    graph_signature: str               # "PASS_THROUGH" | "FAN_IN" | "LAYERING" | "CLEAN"

class GraphContextEngine:

    def __init__(self, uri: str, auth: tuple):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def analyze_upstream_network(
        self,
        account_id: str,
        max_hops: int = 4,
        lookback_days: int = 90
    ) -> HopAnalysisResult:
        """
        Core traversal: Walk backward up to max_hops from the subject account.
        Aggregate all upstream funding sources and compute pass-through score.
        """
        with self.driver.session() as session:

            upstream_result = session.run("""
                MATCH path = (source:Account)-[:SENT*1..{max_hops}]->
                             (txn:Transaction)-[:RECEIVED_BY*0..1]->
                             (subject:Account {account_id: $account_id})
                WHERE txn.timestamp >= datetime() - duration({days: $lookback_days})
                RETURN
                    source.account_id           AS source_id,
                    source.account_type         AS source_type,
                    source.state_of_origin      AS source_state,
                    source.kyc_tier             AS kyc_tier,
                    txn.amount                  AS amount,
                    txn.is_cash                 AS is_cash,
                    txn.city                    AS txn_city,
                    length(path)                AS hop_depth
            """.format(max_hops=max_hops),
            account_id=account_id,
            lookback_days=lookback_days
            )

            upstream_records = upstream_result.data()

            cash_deposits    = [r for r in upstream_records if r["is_cash"]]
            unique_states    = list(set(r["source_state"] for r in upstream_records))
            unlinked_sources = self._count_unlinked_sources(session, upstream_records)

            # Pass-Through Score formula:
            # (cash_ratio * 0.4) + (state_diversity * 0.3) + (unlinked_ratio * 0.3)
            cash_ratio       = len(cash_deposits) / max(len(upstream_records), 1)
            state_diversity  = min(len(unique_states) / 5.0, 1.0)
            unlinked_ratio   = unlinked_sources / max(len(upstream_records), 1)

            pass_through_score = (
                cash_ratio      * 0.4 +
                state_diversity * 0.3 +
                unlinked_ratio  * 0.3
            )

            smurfing_indicator = (
                len(cash_deposits) >= 10 and
                len(unique_states) >= 3 and
                pass_through_score > 0.65
            )

            return HopAnalysisResult(
                subject_account_id=account_id,
                hops_analyzed=max_hops,
                pass_through_score=round(pass_through_score, 4),
                upstream_cash_deposit_count=len(cash_deposits),
                upstream_unique_states=unique_states,
                smurfing_indicator=smurfing_indicator,
                suspicious_entities=self._get_flagged_entities(session, account_id),
                graph_signature=self._classify_graph_signature(
                    pass_through_score, smurfing_indicator, unlinked_sources
                )
            )

    def _count_unlinked_sources(self, session, records: list) -> int:
        """
        'Unlinked' = source accounts with NO shared owner, phone, address,
        or device fingerprint — yet all fund the same target. Smurfing signal.
        """
        source_ids = [r["source_id"] for r in records]
        result = session.run("""
            MATCH (a:Account) WHERE a.account_id IN $source_ids
            WHERE NOT (a)-[:SHARES_DEVICE|SHARES_ADDRESS|CO_OWNED_BY]-()
            RETURN count(a) AS unlinked_count
        """, source_ids=source_ids)
        return result.single()["unlinked_count"]

    def _classify_graph_signature(
        self, score: float, smurfing: bool, unlinked_count: int
    ) -> str:
        if smurfing and unlinked_count >= 8:
            return "FAN_IN_SMURFING"
        elif score > 0.65:
            return "PASS_THROUGH"
        elif score > 0.40:
            return "LAYERING_SUSPECTED"
        return "CLEAN"

    def _get_flagged_entities(self, session, account_id: str) -> list[dict]:
        result = session.run("""
            MATCH (a:Account {account_id: $account_id})-[:OWNED_BY]->(e:Entity)
            WHERE e.jurisdiction IN ['FATF_GREY', 'SANCTIONS_LIST']
               OR e.entity_type = 'SHELL_CO'
            RETURN e.entity_id, e.entity_type, e.jurisdiction
        """, account_id=account_id)
        return [dict(r) for r in result]
```

#### 1.3 Graph Writer (`graph_writer.py`)

```python
# graph_writer.py
# Ingests raw transaction events and writes to Neo4j atomically.
# Called by the pipeline ingestion layer on every new transaction event.
# Uses MERGE (not CREATE) to prevent duplicate nodes.

class GraphWriter:

    def upsert_transaction_event(self, event: dict, session):
        session.run("""
            MERGE (sender:Account {account_id: $sender_id})
            ON CREATE SET sender.kyc_tier       = $sender_kyc,
                          sender.state_of_origin = $sender_state,
                          sender.created_at      = datetime()

            MERGE (receiver:Account {account_id: $receiver_id})

            CREATE (txn:Transaction {
                txn_id:    $txn_id,
                amount:    $amount,
                channel:   $channel,
                timestamp: datetime($timestamp),
                is_cash:   $is_cash,
                city:      $city
            })

            CREATE (sender)-[:SENT {amount: $amount, timestamp: datetime($timestamp)}]->(txn)
            CREATE (txn)-[:RECEIVED_BY]->(receiver)
        """, **event)
```

---

## Module 2 — Behavioral Deviation & XGBoost Risk Scoring

### Objective
Compute **amount_vs_history_ratio** and related behavioral features. Feed into a trained XGBoost classifier. Generate SHAP-based human-readable explanations for every alert.

### Sub-Components

#### 2.1 Transaction History Store Schema (PostgreSQL)

```sql
-- Table: account_behavioral_profiles
CREATE TABLE account_behavioral_profiles (
    account_id              VARCHAR(64) PRIMARY KEY,    -- pseudonymised
    income_tier             VARCHAR(20),                -- "FREELANCER_MICRO" | "SMB" | "CORPORATE"
    declared_monthly_income NUMERIC(15,2),
    avg_monthly_inflow_6m   NUMERIC(15,2),
    avg_monthly_inflow_3m   NUMERIC(15,2),
    avg_txn_count_monthly   INTEGER,
    avg_txn_amount          NUMERIC(15,2),
    std_txn_amount          NUMERIC(15,2),
    typical_channels        TEXT[],                     -- e.g. ["IMPS", "NEFT"]
    typical_counterparties  INTEGER,                    -- distinct senders per month
    last_updated            TIMESTAMPTZ DEFAULT NOW()
);

-- Table: transaction_events (rolling store, partitioned by month)
CREATE TABLE transaction_events (
    txn_id          VARCHAR(64),
    account_id      VARCHAR(64),
    amount          NUMERIC(15,2),
    channel         VARCHAR(20),
    txn_timestamp   TIMESTAMPTZ,
    counterparty_id VARCHAR(64),
    is_inflow       BOOLEAN,
    city            VARCHAR(60),
    is_cash         BOOLEAN
) PARTITION BY RANGE (txn_timestamp);
-- Create monthly partitions: transaction_events_2025_01, _02, etc.

-- Index for fast baseline lookups
CREATE INDEX idx_account_ts ON transaction_events (account_id, txn_timestamp DESC);
```

#### 2.2 Baseline Calculator (`baseline_calculator.py`)

```python
# baseline_calculator.py
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime, timedelta

class BaselineCalculator:

    def __init__(self, db_engine):
        self.engine = db_engine

    def compute_behavioral_features(
        self, account_id: str, trigger_txn: dict
    ) -> dict:
        """
        Computes deviation features relative to the account's 6-month history.
        Returns feature dict ready for XGBoost inference.
        """
        history_df = pd.read_sql("""
            SELECT amount, txn_timestamp, channel, counterparty_id, is_cash
            FROM transaction_events
            WHERE account_id = %(account_id)s
              AND is_inflow = TRUE
              AND txn_timestamp >= NOW() - INTERVAL '180 days'
            ORDER BY txn_timestamp DESC
        """, self.engine, params={"account_id": account_id})

        if history_df.empty:
            return self._new_account_feature_vector(trigger_txn)

        trigger_amount = trigger_txn["amount"]

        avg_amount_6m = history_df["amount"].mean()
        std_amount_6m = history_df["amount"].std() or 1.0

        amount_vs_history_ratio = trigger_amount / avg_amount_6m
        z_score_amount          = (trigger_amount - avg_amount_6m) / std_amount_6m

        history_df["month"]  = history_df["txn_timestamp"].dt.to_period("M")
        monthly_inflow       = history_df.groupby("month")["amount"].sum()
        avg_monthly_inflow   = monthly_inflow.mean()

        typical_unique_senders   = history_df["counterparty_id"].nunique()
        typical_channels         = history_df["channel"].value_counts(normalize=True)
        trigger_channel_freq     = typical_channels.get(trigger_txn["channel"], 0.0)

        large_txns = history_df[history_df["amount"] >= trigger_amount * 0.7]
        days_since_similar = (
            (datetime.now() - large_txns["txn_timestamp"].max()).days
            if not large_txns.empty else 999
        )

        last_7d            = history_df[
            history_df["txn_timestamp"] >= datetime.now() - timedelta(days=7)
        ]
        velocity_7d_count  = len(last_7d)
        velocity_7d_amount = last_7d["amount"].sum()

        return {
            "trigger_amount":               trigger_amount,
            "avg_amount_6m":                avg_amount_6m,
            "avg_monthly_inflow_6m":        avg_monthly_inflow,
            # --- Deviation Features (primary XGBoost inputs) ---
            "amount_vs_history_ratio":      round(amount_vs_history_ratio, 4),
            "z_score_amount":               round(z_score_amount, 4),
            "days_since_similar_txn":       days_since_similar,
            "trigger_channel_freq":         round(trigger_channel_freq, 4),
            "typical_unique_senders_6m":    typical_unique_senders,
            "velocity_7d_count":            velocity_7d_count,
            "velocity_7d_amount":           velocity_7d_amount,
            "income_mismatch_ratio": (
                trigger_amount / max(trigger_txn.get("declared_monthly_income", 1), 1)
            )
        }

    def _new_account_feature_vector(self, trigger_txn: dict) -> dict:
        """For accounts with <30 days of history — assign conservative high-risk defaults."""
        return {
            "amount_vs_history_ratio":  99.0,
            "z_score_amount":           99.0,
            "days_since_similar_txn":   999,
            "trigger_channel_freq":     0.0,
            "typical_unique_senders_6m": 0,
            "velocity_7d_count":        1,
            "velocity_7d_amount":       trigger_txn["amount"],
            "income_mismatch_ratio":    99.0,
        }
```

#### 2.3 XGBoost Model Specification (`risk_model.py`)

```python
# risk_model.py
import xgboost as xgb
import shap
import pandas as pd
from dataclasses import dataclass

FEATURE_COLUMNS = [
    # Deviation features (Module 2)
    "amount_vs_history_ratio",
    "z_score_amount",
    "days_since_similar_txn",
    "trigger_channel_freq",
    "typical_unique_senders_6m",
    "velocity_7d_count",
    "velocity_7d_amount",
    "income_mismatch_ratio",
    # Graph features (Module 1)
    "graph_pass_through_score",
    "upstream_cash_deposit_count",
    "upstream_unique_states_count",
    "fan_in_node_count",
    # Typology features (Module 3)
    "outflow_velocity_48h",
    "atm_withdrawal_ratio_48h",
    "crypto_transfer_flag_48h",
    # Aggregation features (Module 4)
    "rolling_30d_total",
    "rolling_90d_total",
    "rolling_180d_total",
    "rolling_30d_vs_income_ratio",
    "rolling_90d_txn_count",
]

@dataclass
class RiskScoringResult:
    risk_score: float
    risk_tier: str                  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    shap_explanations: list[dict]   # top 5 driving features
    alert_narrative: str            # SHAP-driven compliance narrative

class RiskScoringEngine:

    def __init__(self, model_path: str):
        self.model    = xgb.Booster()
        self.model.load_model(model_path)
        self.explainer = shap.TreeExplainer(self.model)

    def score(self, feature_dict: dict) -> RiskScoringResult:
        df      = pd.DataFrame([feature_dict])[FEATURE_COLUMNS].fillna(0)
        dmatrix = xgb.DMatrix(df)

        raw_score   = float(self.model.predict(dmatrix)[0])
        shap_values = self.explainer.shap_values(df)
        shap_series = pd.Series(shap_values[0], index=FEATURE_COLUMNS)
        top_features = shap_series.abs().nlargest(5)

        explanations = []
        for feat_name, shap_val in top_features.items():
            explanations.append({
                "feature":      feat_name,
                "value":        round(float(feature_dict.get(feat_name, 0)), 4),
                "shap_impact":  round(float(shap_val), 4),
                "direction":    "INCREASES_RISK" if shap_val > 0 else "REDUCES_RISK"
            })

        narrative = self._build_narrative(explanations, raw_score, feature_dict)

        return RiskScoringResult(
            risk_score=round(raw_score, 4),
            risk_tier=self._tier(raw_score),
            shap_explanations=explanations,
            alert_narrative=narrative
        )

    def _tier(self, score: float) -> str:
        if score >= 0.85: return "CRITICAL"
        if score >= 0.65: return "HIGH"
        if score >= 0.40: return "MEDIUM"
        return "LOW"

    def _build_narrative(
        self, explanations: list, score: float, features: dict
    ) -> str:
        lines = [f"Risk Score: {score:.2%} ({self._tier(score)}).", "Key Drivers:"]

        ratio = features.get("amount_vs_history_ratio", 1.0)
        if ratio > 3.0:
            lines.append(
                f"  - Transaction amount is {ratio:.0f}x the account's 6-month average. "
                f"Deviation from historical baseline is {(ratio-1)*100:.0f}% above average."
            )

        graph_score = features.get("graph_pass_through_score", 0)
        if graph_score > 0.65:
            lines.append(
                f"  - Graph analysis (4-hop upstream) scored {graph_score:.0%} pass-through "
                f"probability. Upstream chain includes "
                f"{features.get('upstream_cash_deposit_count', 0)} cash deposits from "
                f"{features.get('upstream_unique_states_count', 0)} states."
            )

        if features.get("crypto_transfer_flag_48h", 0):
            lines.append(
                "  - Funds transferred to crypto exchange within 48h of receipt — "
                "consistent with Money Mule / Layering typology."
            )

        for exp in explanations:
            lines.append(
                f"  - [{exp['feature']}={exp['value']}] SHAP: {exp['shap_impact']:+.4f} "
                f"({exp['direction']})"
            )

        return "\n".join(lines)
```

#### 2.4 XGBoost Training Configuration

```python
# train_risk_model.py
XGB_PARAMS = {
    "objective":        "binary:logistic",
    "eval_metric":      ["auc", "aucpr"],  # AUC-PR critical for imbalanced AML data
    "max_depth":        6,
    "learning_rate":    0.05,
    "n_estimators":     500,
    "subsample":        0.8,
    "colsample_bytree": 0.8,
    "scale_pos_weight": 50,                # ~1 suspicious per 50 transactions
    "min_child_weight": 10,                # prevents overfitting on rare fraud
    "reg_alpha":        0.1,
    "reg_lambda":       1.0,
    "seed":             42,
    "tree_method":      "hist",            # GPU-compatible
}

# CRITICAL: Use GroupKFold with account_id as group key.
# Standard KFold causes data leakage across the same account.
from sklearn.model_selection import GroupKFold
cv = GroupKFold(n_splits=5)
```

---

## Module 3 — Outflow Typology & Lifecycle Monitoring Agent

### Objective
Monitor the **48-72 hour post-inflow window** for cash-out signatures. Classify recognised typologies: Money Mule, Layering, Pass-Through, Smurfing Inflow.

### Sub-Components

#### 3.1 Typology Definitions Registry (`typology_registry.py`)

```python
# typology_registry.py
TYPOLOGY_REGISTRY = {

    "MONEY_MULE_RAPID_CASHOUT": {
        "description": "Large inflow followed by full ATM withdrawal within 48 hours.",
        "conditions": {
            "inflow_to_atm_hours":   ("<=", 48),
            "atm_withdrawal_pct":    (">=", 0.85),   # 85%+ of inflow withdrawn via ATM
            "atm_transaction_count": (">=", 1),
        },
        "fiu_ind_typology_code": "ML-MULE-01",
        "risk_weight":            0.92,
    },

    "LAYERING_CRYPTO_OFFLOAD": {
        "description": "Inflow routed to crypto exchange within 72 hours.",
        "conditions": {
            "inflow_to_crypto_hours": ("<=", 72),
            "crypto_transfer_pct":    (">=", 0.70),
            "crypto_exchange_in_ofac": ("==", True),
        },
        "fiu_ind_typology_code": "ML-LAYER-03",
        "risk_weight":            0.95,
    },

    "PASS_THROUGH_IMMEDIATE": {
        "description": "Inflow forwarded to third party within 24 hours, <5% retained.",
        "conditions": {
            "inflow_to_outward_hours": ("<=", 24),
            "retained_balance_pct":    ("<=", 0.05),
            "outward_destinations":    (">=", 1),
        },
        "fiu_ind_typology_code": "ML-PASS-02",
        "risk_weight":            0.88,
    },

    "SMURFING_INFLOW_AGGREGATION": {
        "description": "Multiple sub-threshold inflows aggregating to large amount.",
        "conditions": {
            "inflow_count_30d":    (">=", 10),
            "avg_inflow_amount":   ("<=", 200000),  # sub-2L per transaction
            "total_inflow_30d":    (">=", 1000000), # but >10L in aggregate
            "unique_sender_count": (">=", 5),
        },
        "fiu_ind_typology_code": "ML-SMRF-01",
        "risk_weight":            0.85,
    },
}
```

#### 3.2 Lifecycle Event Monitor (`lifecycle_monitor.py`)

```python
# lifecycle_monitor.py
# Runs as a Celery worker. Evaluates every outflow within the 72h window
# that was opened by a HIGH/CRITICAL inflow event.

import redis, json
from celery import Celery
from datetime import datetime

app = Celery("lifecycle_monitor", broker="redis://localhost:6379/0")

class LifecycleMonitorAgent:

    def __init__(self, redis_client: redis.Redis, db_engine):
        self.redis  = redis_client
        self.engine = db_engine

    def on_new_inflow_event(
        self, account_id: str, inflow_amount: float, txn_id: str
    ):
        """
        Opens a 72-hour monitoring window in Redis when a HIGH/CRITICAL inflow is scored.
        All subsequent outflows are evaluated against this window.
        """
        window_key  = f"monitor_window:{account_id}"
        window_data = {
            "account_id":    account_id,
            "inflow_amount": inflow_amount,
            "inflow_txn_id": txn_id,
            "inflow_ts":     datetime.utcnow().isoformat(),
            "outflows":      [],
        }
        self.redis.setex(window_key, 72 * 3600, json.dumps(window_data))

    def on_outflow_event(self, account_id: str, outflow: dict):
        """
        Called on every outflow event. If account is under active monitoring,
        appends outflow and re-evaluates typology conditions.
        """
        window_key = f"monitor_window:{account_id}"
        raw = self.redis.get(window_key)
        if not raw:
            return None

        window_data = json.loads(raw)
        window_data["outflows"].append(outflow)
        self.redis.setex(window_key, 72 * 3600, json.dumps(window_data))

        return self._evaluate_typologies(window_data)

    def _evaluate_typologies(self, window: dict) -> list[str]:
        inflow_ts     = datetime.fromisoformat(window["inflow_ts"])
        inflow_amount = window["inflow_amount"]
        outflows      = window["outflows"]
        matched       = []

        # --- MONEY_MULE_RAPID_CASHOUT ---
        atm_outflows = [o for o in outflows if o.get("channel") == "ATM"]
        if atm_outflows:
            first_atm_ts = min(
                datetime.fromisoformat(o["timestamp"]) for o in atm_outflows
            )
            hours_to_atm = (first_atm_ts - inflow_ts).total_seconds() / 3600
            atm_total    = sum(o["amount"] for o in atm_outflows)
            atm_pct      = atm_total / inflow_amount

            if hours_to_atm <= 48 and atm_pct >= 0.85:
                matched.append("MONEY_MULE_RAPID_CASHOUT")

        # --- LAYERING_CRYPTO_OFFLOAD ---
        crypto_outflows = [o for o in outflows if o.get("channel") == "CRYPTO_EXCHANGE"]
        if crypto_outflows:
            first_crypto_ts = min(
                datetime.fromisoformat(o["timestamp"]) for o in crypto_outflows
            )
            hours_to_crypto = (first_crypto_ts - inflow_ts).total_seconds() / 3600
            crypto_total    = sum(o["amount"] for o in crypto_outflows)
            crypto_pct      = crypto_total / inflow_amount

            if hours_to_crypto <= 72 and crypto_pct >= 0.70:
                matched.append("LAYERING_CRYPTO_OFFLOAD")

        # --- PASS_THROUGH_IMMEDIATE ---
        total_outflow = sum(o["amount"] for o in outflows)
        retained_pct  = 1.0 - (total_outflow / inflow_amount)
        first_outflow_ts = min(
            datetime.fromisoformat(o["timestamp"]) for o in outflows
        ) if outflows else None

        if first_outflow_ts:
            hours_to_first = (first_outflow_ts - inflow_ts).total_seconds() / 3600
            if hours_to_first <= 24 and retained_pct <= 0.05:
                matched.append("PASS_THROUGH_IMMEDIATE")

        return matched
```

---

## Module 4 — Time-Window Aggregation Engine

### Objective
Compute **continuous rolling aggregations** at 30d / 90d / 180d windows. Compare against declared income tiers to detect structural income mismatch over time — even when no single transaction triggers a threshold.

### Sub-Components

#### 4.1 Aggregation Engine (`aggregation_engine.py`)

```python
# aggregation_engine.py
import pandas as pd
import numpy as np
from sqlalchemy import text

class AggregationEngine:

    WINDOWS = {"30d": 30, "90d": 90, "180d": 180}

    # RBI PMLA psychological thresholds by account tier
    THRESHOLD_INR = {
        "FREELANCER_MICRO":   500_000,     # 5L
        "FREELANCER_MID":   1_000_000,     # 10L
        "SMB":              5_000_000,     # 50L
        "CORPORATE":       50_000_000,     # 5Cr
    }

    def compute_rolling_features(
        self, account_id: str, income_tier: str, engine
    ) -> dict:

        df = pd.read_sql(text("""
            SELECT amount, txn_timestamp, channel, is_cash, counterparty_id
            FROM transaction_events
            WHERE account_id = :account_id
              AND is_inflow = TRUE
              AND txn_timestamp >= NOW() - INTERVAL '180 days'
        """), engine, params={"account_id": account_id})

        if df.empty:
            return {f"rolling_{w}_total": 0 for w in self.WINDOWS}

        df["txn_timestamp"] = pd.to_datetime(df["txn_timestamp"], utc=True)
        now       = pd.Timestamp.utcnow()
        features  = {}
        threshold = self.THRESHOLD_INR.get(income_tier, 500_000)

        for label, days in self.WINDOWS.items():
            cutoff    = now - pd.Timedelta(days=days)
            window_df = df[df["txn_timestamp"] >= cutoff]

            total_inflow    = window_df["amount"].sum()
            txn_count       = len(window_df)
            unique_senders  = window_df["counterparty_id"].nunique()
            cash_inflow     = window_df[window_df["is_cash"]]["amount"].sum()

            features[f"rolling_{label}_total"]            = round(total_inflow, 2)
            features[f"rolling_{label}_txn_count"]        = txn_count
            features[f"rolling_{label}_unique_senders"]   = unique_senders
            features[f"rolling_{label}_cash_pct"]         = round(
                cash_inflow / max(total_inflow, 1), 4
            )
            features[f"rolling_{label}_vs_income_ratio"]  = round(
                total_inflow / max(threshold, 1), 4
            )
            features[f"rolling_{label}_threshold_breach"] = int(total_inflow > threshold)

        # Month-over-month inflow trend slope (linear regression on last 3 months)
        df["month"]  = df["txn_timestamp"].dt.to_period("M")
        monthly      = df.groupby("month")["amount"].sum().sort_index()
        if len(monthly) >= 3:
            x = np.arange(len(monthly[-3:]))
            y = monthly[-3:].values
            features["monthly_inflow_trend_slope"] = round(float(np.polyfit(x, y, 1)[0]), 2)
        else:
            features["monthly_inflow_trend_slope"] = 0.0

        return features

    def generate_aggregation_alert(self, features: dict, account_id: str) -> list | None:
        """
        Returns alerts for any rolling window that has breached the income threshold.
        This fires even if no individual transaction was suspicious (structural detection).
        """
        alerts = []
        for label in self.WINDOWS:
            if features.get(f"rolling_{label}_threshold_breach"):
                total   = features[f"rolling_{label}_total"]
                ratio   = features[f"rolling_{label}_vs_income_ratio"]
                senders = features[f"rolling_{label}_unique_senders"]
                alerts.append({
                    "window":                label,
                    "total_inflow_inr":      total,
                    "income_mismatch_ratio": ratio,
                    "unique_senders":        senders,
                    "narrative": (
                        f"{label.upper()} rolling inflow of INR {total:,.0f} exceeds "
                        f"declared income threshold by {(ratio-1)*100:.0f}%. "
                        f"Funded by {senders} distinct counterparties. "
                        f"Pattern consistent with structured accumulation."
                    )
                })
        return alerts if alerts else None
```

---

## Module 5 — Fan-In Pattern Detection (Graph Signature Analysis)

### Objective
Detect the **Fan-In (Many-to-One)** graph topology: multiple unrelated accounts funding a single subject — even when transactions are spread over months and individually sub-threshold.

### Sub-Components

#### 5.1 Fan-In Detector (`fan_in_detector.py`)

```python
# fan_in_detector.py
# Runs as a scheduled Celery job (every 6 hours) AND on-demand
# when new edges are added to the subject account's node in Neo4j.

from neo4j import GraphDatabase
from dataclasses import dataclass
import numpy as np

@dataclass
class FanInSignal:
    account_id: str
    fan_in_count: int               # distinct sender nodes in window
    cross_city_flag: bool           # senders from 4+ different cities
    cross_state_flag: bool          # senders from 3+ different states
    sequential_timing_flag: bool    # deposits suspiciously evenly spaced (CV < 0.3)
    low_kyc_ratio: float            # fraction of MIN_KYC/UNVERIFIED senders
    typology_match: str             # "FAN_IN_SMURFING" | "FAN_IN_LAYERING" | "NORMAL"
    neo4j_subgraph_id: str          # ID for rendering in Streamlit UI

class FanInDetector:

    def __init__(self, driver):
        self.driver = driver

    def detect_fan_in(
        self,
        account_id: str,
        lookback_days: int = 90,
        min_senders: int = 5
    ) -> FanInSignal | None:

        with self.driver.session() as session:

            result = session.run("""
                MATCH (sender:Account)-[:SENT]->(txn:Transaction)-[:RECEIVED_BY]->(target:Account)
                WHERE target.account_id = $account_id
                  AND txn.timestamp >= datetime() - duration({days: $days})
                WITH sender,
                     collect(txn)              AS transactions,
                     collect(txn.city)         AS cities,
                     collect(txn.timestamp)    AS timestamps
                WHERE size(transactions) >= 1
                RETURN
                    sender.account_id        AS sender_id,
                    sender.state_of_origin   AS sender_state,
                    sender.kyc_tier          AS kyc_tier,
                    size(transactions)       AS txn_count,
                    reduce(s=0, t IN transactions | s + t.amount) AS total_sent,
                    cities                   AS sender_cities,
                    timestamps               AS txn_timestamps
                ORDER BY total_sent DESC
            """, account_id=account_id, days=lookback_days)

            rows = result.data()

            if len(rows) < min_senders:
                return None

            all_states  = [r["sender_state"] for r in rows if r["sender_state"]]
            all_cities  = [c for r in rows for c in r["sender_cities"] if c]
            all_ts      = sorted([t for r in rows for t in r["txn_timestamps"]])

            unique_states = set(all_states)
            unique_cities = set(all_cities)

            cross_state_flag    = len(unique_states) >= 3
            cross_city_flag     = len(unique_cities) >= 4
            sequential_flag     = self._detect_sequential_timing(all_ts)

            low_kyc_count = sum(
                1 for r in rows if r["kyc_tier"] in ("MIN_KYC", "UNVERIFIED")
            )
            low_kyc_ratio = low_kyc_count / len(rows)

            # Typology classification
            if cross_state_flag and sequential_flag and low_kyc_ratio > 0.5:
                typology = "FAN_IN_SMURFING"
            elif cross_state_flag and cross_city_flag:
                typology = "FAN_IN_LAYERING"
            elif len(rows) >= 8:
                typology = "FAN_IN_SUSPECTED"
            else:
                typology = "NORMAL"

            subgraph_id = self._persist_subgraph_snapshot(
                session, account_id, [r["sender_id"] for r in rows]
            )

            return FanInSignal(
                account_id=account_id,
                fan_in_count=len(rows),
                cross_city_flag=cross_city_flag,
                cross_state_flag=cross_state_flag,
                sequential_timing_flag=sequential_flag,
                low_kyc_ratio=round(low_kyc_ratio, 4),
                typology_match=typology,
                neo4j_subgraph_id=subgraph_id
            )

    def _detect_sequential_timing(self, timestamps: list) -> bool:
        """
        Detects unnaturally regular deposit timing (machine-coordinated smurfing).
        Uses Coefficient of Variation (CV) of inter-arrival gaps.
        CV < 0.3 = suspiciously regular for human actors.
        """
        if len(timestamps) < 4:
            return False

        ts_sorted = sorted(timestamps)
        gaps = [
            (ts_sorted[i+1] - ts_sorted[i]).total_seconds()
            for i in range(len(ts_sorted) - 1)
        ]
        mean_gap = np.mean(gaps)
        if mean_gap == 0:
            return False

        cv = np.std(gaps) / mean_gap
        return cv < 0.3

    def _persist_subgraph_snapshot(
        self, session, target_id: str, sender_ids: list
    ) -> str:
        import uuid
        subgraph_id = str(uuid.uuid4())
        session.run("""
            CREATE (snap:SubgraphSnapshot {
                id:                $subgraph_id,
                target_account_id: $target_id,
                sender_ids:        $sender_ids,
                created_at:        datetime(),
                typology:          'FAN_IN'
            })
        """, subgraph_id=subgraph_id, target_id=target_id, sender_ids=sender_ids)
        return subgraph_id
```

#### 5.2 Scheduled Fan-In Scan (Celery Task)

```python
# celery_tasks.py
@app.task
def run_fan_in_scan():
    """Runs every 6 hours. Scans all accounts active in past 90 days."""
    active_accounts = get_active_accounts_last_90d()
    detector        = FanInDetector(driver=get_neo4j_driver())

    for account_id in active_accounts:
        signal = detector.detect_fan_in(
            account_id, lookback_days=90, min_senders=5
        )
        if signal and signal.typology_match != "NORMAL":
            alert_service.raise_alert(
                account_id=account_id,
                alert_type="FAN_IN_PATTERN",
                severity="HIGH" if "SMURFING" in signal.typology_match else "MEDIUM",
                metadata=signal.__dict__
            )
```

---

## Module 6 — PII Stripping Layer (Regulatory Compliance)

### Objective
Ensure **zero customer PII reaches external LLM APIs** (Groq, Gemini, MiniMax). Comply with RBI Data Localisation Circular (2018) and DPDP Act 2023. All tokenisation/de-tokenisation happens server-side with a cryptographic audit trail.

### Implementation (`pii_stripper.py`)

```python
# pii_stripper.py
import re, hashlib, json, datetime
from dataclasses import dataclass

@dataclass
class StrippingResult:
    stripped_prompt: str
    token_map: dict                 # {TOKEN: REAL_VALUE} — NEVER sent to LLM
    pii_categories_found: list[str]

class PIIStripper:

    # Regex patterns for Indian financial PII
    PATTERNS = {
        "PAN":         r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
        "AADHAAR":     r'\b[2-9]{1}[0-9]{11}\b',
        "IFSC":        r'\b[A-Z]{4}0[A-Z0-9]{6}\b',
        "MOBILE":      r'\b[6-9]\d{9}\b',
        "ACCOUNT_NUM": r'\b\d{9,18}\b',
        "AMOUNT_INR":  r'₹[\d,]+(?:\.\d{2})?|\bINR\s*[\d,]+',
        "EMAIL":       r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    }

    def strip_and_tokenize(
        self, prompt: str, case_context: dict
    ) -> StrippingResult:

        token_map  = {}
        stripped   = prompt
        found_cats = []
        counters   = {}

        def _replace(match: re.Match, prefix: str) -> str:
            counters[prefix] = counters.get(prefix, 0) + 1
            token      = f"[{prefix}_{counters[prefix]:03d}]"
            real_value = match.group(0)
            if real_value not in token_map.values():
                token_map[token] = real_value
            return token

        # 1. Named entities from case context (pre-matched)
        for i, name in enumerate(case_context.get("customer_names", []), 1):
            token = f"[PERSON_{i:03d}]"
            if name in stripped:
                stripped = stripped.replace(name, token)
                token_map[token] = name
                found_cats.append("PERSON")

        # 2. Regex-based replacement for structured Indian financial PII
        for category, pattern in self.PATTERNS.items():
            def replacer(m, cat=category):
                return _replace(m, cat)
            new_stripped = re.sub(pattern, replacer, stripped)
            if new_stripped != stripped:
                found_cats.append(category)
            stripped = new_stripped

        return StrippingResult(
            stripped_prompt=stripped,
            token_map=token_map,
            pii_categories_found=list(set(found_cats))
        )

    def reinsert_pii(self, llm_response: str, token_map: dict) -> str:
        """Re-inserts real PII values after LLM response is received on-premises."""
        result = llm_response
        for token, real_value in sorted(token_map.items(), key=lambda x: -len(x[0])):
            result = result.replace(token, real_value)
        return result

    def generate_audit_entry(self, result: StrippingResult, case_id: str) -> dict:
        """
        Creates an immutable audit log entry proving PII was stripped before any API call.
        The token_map is hashed (not stored in plain text in the audit log).
        """
        token_map_hash = hashlib.sha256(
            json.dumps(result.token_map, sort_keys=True).encode()
        ).hexdigest()

        return {
            "case_id":              case_id,
            "timestamp":            datetime.datetime.utcnow().isoformat(),
            "pii_categories_found": result.pii_categories_found,
            "token_count":          len(result.token_map),
            "token_map_sha256":     token_map_hash,
            "stripped_prompt_hash": hashlib.sha256(
                result.stripped_prompt.encode()
            ).hexdigest(),
        }
```

---

## Module 7 — Zero Trust Security: UI Layer Implementation

### Overview

Zero Trust at the UI layer means the Streamlit frontend **never implicitly trusts any session, role claim, or user action**. Every rendered component, every API call, and every state transition is gated on a verified, unexpired, cryptographically signed identity token. The UI is treated as an **untrusted client** — even if it is running on the bank's internal network.

The implementation has five sub-layers applied in sequence:

```
Browser Request
      │
      ▼
[7.1] Keycloak OIDC Authentication Gate
      → SSO login + TOTP MFA enforced before app.py loads
      │
      ▼
[7.2] ZeroTrustSessionManager (st.session_state)
      → JWT stored, validated, and refreshed in session state
      → Device posture check on every session init
      │
      ▼
[7.3] Role-Gated UI Renderer
      → Every Streamlit component conditionally rendered by role
      → Forbidden pages render nothing — no error hints
      │
      ▼
[7.4] Per-Request JWT Injector
      → Every httpx call from UI to API carries Bearer token
      → Token auto-refreshed if within 5-minute expiry window
      │
      ▼
[7.5] UI Audit Logger
      → Every button click, page view, case open, and approval
        is written to the immutable audit trail with user identity
```

---

### 7.1 Keycloak OIDC Authentication Gate (`auth_gate.py`)

Keycloak is deployed **self-hosted on-premises** (mandatory for RBI data localisation). It is configured as an OIDC provider. The Streamlit app never sees the user's password — it only receives a signed JWT after Keycloak completes the auth flow.

**Keycloak Realm Configuration (exported JSON fragment):**

```json
{
  "realm": "sar-platform",
  "enabled": true,
  "sslRequired": "all",
  "otpPolicyType": "totp",
  "otpPolicyAlgorithm": "HmacSHA256",
  "otpPolicyPeriod": 30,
  "requiredActions": ["CONFIGURE_TOTP"],
  "roles": {
    "realm": [
      { "name": "ANALYST_L1",         "description": "View alerts only" },
      { "name": "ANALYST_L2",         "description": "View + annotate alerts" },
      { "name": "COMPLIANCE_OFFICER", "description": "Approve and submit STR" },
      { "name": "AUDITOR",            "description": "Read-only graph + audit trail" }
    ]
  },
  "clients": [{
    "clientId": "sar-streamlit-ui",
    "protocol": "openid-connect",
    "redirectUris": ["https://sar-internal.bank.in/callback"],
    "webOrigins":   ["https://sar-internal.bank.in"],
    "accessTokenLifespan": 900,
    "refreshTokenMaxReuse": 0,
    "pkceCodeChallengeMethod": "S256"
  }]
}
```

> **Key settings:** TOTP MFA is a `requiredAction` — no account can log in without configuring it first. Access tokens expire in **15 minutes** (900 seconds). PKCE (Proof Key for Code Exchange) is enforced to prevent auth code interception.

**OIDC Callback Handler (`auth_gate.py`):**

```python
# auth_gate.py
# Handles the OIDC redirect callback and token exchange with Keycloak.
# Called once per login. After this, ZeroTrustSessionManager takes over.

import streamlit as st
import httpx
import jwt
import os
from urllib.parse import urlencode
import secrets
import hashlib
import base64

KEYCLOAK_BASE    = os.environ["KEYCLOAK_BASE_URL"]          # https://keycloak.internal/
REALM            = "sar-platform"
CLIENT_ID        = "sar-streamlit-ui"
REDIRECT_URI     = os.environ["STREAMLIT_REDIRECT_URI"]
JWKS_URI         = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/certs"
TOKEN_URI        = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/token"
AUTH_URI         = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/auth"

def _generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256)."""
    code_verifier  = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return code_verifier, code_challenge

def build_login_redirect_url() -> str:
    """
    Constructs the Keycloak authorization URL.
    Generates a new PKCE pair and anti-CSRF state token on every call.
    Both are stored in st.session_state for later verification.
    """
    code_verifier, code_challenge = _generate_pkce_pair()
    state = secrets.token_urlsafe(32)

    st.session_state["pkce_verifier"] = code_verifier
    st.session_state["oauth_state"]   = state

    params = {
        "client_id":             CLIENT_ID,
        "redirect_uri":          REDIRECT_URI,
        "response_type":         "code",
        "scope":                 "openid profile email roles",
        "state":                 state,
        "code_challenge":        code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTH_URI}?{urlencode(params)}"

def exchange_code_for_tokens(auth_code: str, returned_state: str) -> dict:
    """
    Called after Keycloak redirects back with ?code=...&state=...
    Verifies the anti-CSRF state, then exchanges the auth code for tokens.
    Returns: { access_token, refresh_token, id_token }
    """
    # Anti-CSRF state verification
    if returned_state != st.session_state.get("oauth_state"):
        raise ValueError("OAuth state mismatch — possible CSRF attack. Session terminated.")

    response = httpx.post(TOKEN_URI, data={
        "grant_type":    "authorization_code",
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "code":          auth_code,
        "code_verifier": st.session_state["pkce_verifier"],
    }, timeout=10)

    response.raise_for_status()
    tokens = response.json()

    # Clear PKCE artifacts from session immediately after use
    del st.session_state["pkce_verifier"]
    del st.session_state["oauth_state"]

    return tokens

def verify_and_decode_jwt(access_token: str) -> dict:
    """
    Fetches Keycloak's public JWKS and verifies the token's RS256 signature.
    Does NOT trust the token's claims without cryptographic verification.
    """
    jwks_client = jwt.PyJWKClient(JWKS_URI)
    signing_key = jwks_client.get_signing_key_from_jwt(access_token)

    payload = jwt.decode(
        access_token,
        signing_key.key,
        algorithms=["RS256"],
        audience=CLIENT_ID,
        options={"require": ["exp", "iat", "sub", "realm_access"]},
    )
    return payload
```

---

### 7.2 Zero Trust Session Manager (`zt_session.py`)

After login, every subsequent Streamlit rerun (which happens on every user interaction) passes through the `ZeroTrustSessionManager`. It validates the token's expiry, enforces session inactivity timeout, and performs a **device posture check** on the very first request.

```python
# zt_session.py
import streamlit as st
import time
import httpx
from datetime import datetime, timezone
from auth_gate import verify_and_decode_jwt, TOKEN_URI, CLIENT_ID

# --- Configuration Constants ---
SESSION_INACTIVITY_TIMEOUT_SECONDS = 900   # 15 minutes — matches token lifetime
TOKEN_REFRESH_THRESHOLD_SECONDS    = 300   # Refresh if <5 min remaining
ALLOWED_IP_CIDR                    = os.environ.get("ALLOWED_IP_CIDR", "10.0.0.0/8")

class ZeroTrustSessionManager:

    def enforce(self) -> dict:
        """
        Main enforcement entry point. Called at the top of every Streamlit page.
        Returns the verified user payload if the session is valid.
        Redirects to login and halts rendering if anything fails.
        """

        # Step 1: No session at all — redirect to Keycloak login
        if "access_token" not in st.session_state:
            self._render_login_redirect()
            st.stop()

        # Step 2: Verify the JWT cryptographic signature (not just expiry)
        try:
            payload = verify_and_decode_jwt(st.session_state["access_token"])
        except Exception as e:
            self._terminate_session(f"Token verification failed: {e}")
            st.stop()

        # Step 3: Check token expiry — refresh if within threshold
        exp = payload.get("exp", 0)
        now = int(time.time())
        time_remaining = exp - now

        if time_remaining <= 0:
            self._terminate_session("Session token has expired. Please log in again.")
            st.stop()

        if time_remaining < TOKEN_REFRESH_THRESHOLD_SECONDS:
            payload = self._attempt_token_refresh(payload)

        # Step 4: Inactivity timeout (separate from token expiry)
        last_active = st.session_state.get("last_active_ts", now)
        if (now - last_active) > SESSION_INACTIVITY_TIMEOUT_SECONDS:
            self._terminate_session(
                "Session expired due to inactivity. Please log in again."
            )
            st.stop()

        # Step 5: Device posture check (first request in session only)
        if not st.session_state.get("posture_checked"):
            self._check_device_posture(payload)
            st.session_state["posture_checked"] = True

        # Step 6: Update last active timestamp
        st.session_state["last_active_ts"] = now

        return payload

    def _attempt_token_refresh(self, current_payload: dict) -> dict:
        """
        Uses the refresh token to silently obtain a new access token.
        If refresh fails (refresh token expired or revoked), terminates session.
        """
        refresh_token = st.session_state.get("refresh_token")
        if not refresh_token:
            self._terminate_session("Refresh token missing. Please log in again.")
            st.stop()

        response = httpx.post(TOKEN_URI, data={
            "grant_type":    "refresh_token",
            "client_id":     CLIENT_ID,
            "refresh_token": refresh_token,
        }, timeout=10)

        if response.status_code != 200:
            self._terminate_session(
                "Session could not be refreshed. Please log in again."
            )
            st.stop()

        new_tokens = response.json()
        st.session_state["access_token"]  = new_tokens["access_token"]
        st.session_state["refresh_token"] = new_tokens["refresh_token"]

        return verify_and_decode_jwt(new_tokens["access_token"])

    def _check_device_posture(self, payload: dict):
        """
        Validates the request context on session initialisation.
        Checks IP range. Extend this to check User-Agent, device cert, etc.
        Terminates session if the context is outside policy.
        """
        import ipaddress

        # Streamlit does not expose client IP natively.
        # In production, NGINX reverse proxy injects X-Forwarded-For header,
        # which is read from the query params via st.experimental_get_query_params
        # or from a custom header injected at the NGINX layer.
        client_ip_str = st.session_state.get("client_ip", "10.0.0.1")

        try:
            client_ip   = ipaddress.ip_address(client_ip_str)
            allowed_net = ipaddress.ip_network(ALLOWED_IP_CIDR, strict=False)
            if client_ip not in allowed_net:
                self._terminate_session(
                    f"Access denied: IP {client_ip_str} is outside the permitted network."
                )
                st.stop()
        except ValueError:
            self._terminate_session("Invalid client IP address in request context.")
            st.stop()

    def _terminate_session(self, reason: str):
        """Clears all session state and renders a clean access-denied message."""
        st.session_state.clear()
        st.error(f"Access Terminated: {reason}")
        login_url = build_login_redirect_url()
        st.markdown(f"[Log in again]({login_url})")

    def _render_login_redirect(self):
        st.title("SAR Intelligence Platform")
        st.info("You must authenticate via SSO to access this platform.")
        login_url = build_login_redirect_url()
        st.markdown(f"**[Click here to authenticate]({login_url})**")


# Module-level singleton
zt_session = ZeroTrustSessionManager()
```

---

### 7.3 Role-Gated UI Renderer (`role_gate.py`)

Every Streamlit component — pages, buttons, data tables, graph panels — is wrapped in a role check decorator before it renders. A user who lacks the required role sees **nothing** for that component. There are no "Access Denied" messages that reveal what the component does or that it exists — this is a deliberate Zero Trust UI posture (no information leakage about capabilities the user does not have).

**Role Definitions:**

```python
# role_gate.py
import streamlit as st
import functools
from typing import Callable

# Role hierarchy: each role inherits all permissions of roles below it
ROLE_PERMISSIONS = {
    "ANALYST_L1": {
        "view_alert_queue",
        "view_case_summary",
        "view_transaction_list",
    },
    "ANALYST_L2": {
        "view_alert_queue",
        "view_case_summary",
        "view_transaction_list",
        "view_graph_panel",          # Neo4j subgraph visualisation
        "annotate_case",
        "view_shap_explanation",
    },
    "COMPLIANCE_OFFICER": {
        "view_alert_queue",
        "view_case_summary",
        "view_transaction_list",
        "view_graph_panel",
        "annotate_case",
        "view_shap_explanation",
        "view_typology_report",
        "approve_sar",               # Submit to FIU-IND
        "export_str_document",
        "view_pii_unmasked",         # Only role that sees real PAN/account numbers
    },
    "AUDITOR": {
        "view_graph_panel",
        "view_audit_trail",          # SHA-256 hash chain only
        "view_case_summary",
    },
}

def get_user_permissions(role: str) -> set:
    return ROLE_PERMISSIONS.get(role, set())

def requires_permission(permission: str):
    """
    Decorator for Streamlit render functions.
    If the current user lacks the permission, the function body is never executed.
    The UI renders nothing for that section — no error, no hint.

    Usage:
        @requires_permission("approve_sar")
        def render_approve_button(case_id: str):
            if st.button("Submit STR to FIU-IND"):
                ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            user_role  = st.session_state.get("user_role", "")
            user_perms = get_user_permissions(user_role)
            if permission not in user_perms:
                # Render nothing. Do not hint that this section exists.
                return None
            return fn(*args, **kwargs)
        return wrapper
    return decorator
```

**Applied to `app.py` — Role-gated page rendering:**

```python
# app.py (Streamlit entry point)
import streamlit as st
from zt_session import zt_session
from role_gate import requires_permission
from ui_audit_logger import UIAuditLogger

# ── Zero Trust Enforcement Gate ───────────────────────────────────────────────
# This is the FIRST call in the file. Nothing renders before identity is verified.
user_payload = zt_session.enforce()

user_role    = user_payload["realm_access"]["roles"][0]
user_id      = user_payload["sub"]            # Keycloak UUID
user_name    = user_payload.get("name", "")

st.session_state["user_role"] = user_role
st.session_state["user_id"]   = user_id

audit = UIAuditLogger(user_id=user_id, user_role=user_role)

# ── Navigation (role-sensitive sidebar) ───────────────────────────────────────
# Only show pages the user is permitted to access
perms = get_user_permissions(user_role)

nav_options = []
if "view_alert_queue"    in perms: nav_options.append("Alert Queue")
if "view_graph_panel"    in perms: nav_options.append("Graph Explorer")
if "view_typology_report" in perms: nav_options.append("Typology Reports")
if "view_audit_trail"    in perms: nav_options.append("Audit Trail")
if "export_str_document" in perms: nav_options.append("STR Export")

page = st.sidebar.selectbox("Navigation", nav_options)
audit.log_page_view(page)

# ── Page Routing ──────────────────────────────────────────────────────────────
if page == "Alert Queue":
    render_alert_queue()
elif page == "Graph Explorer":
    render_graph_panel()
elif page == "Typology Reports":
    render_typology_reports()
elif page == "Audit Trail":
    render_audit_trail()
elif page == "STR Export":
    render_str_export()

# ── Approval Section (COMPLIANCE_OFFICER only) ────────────────────────────────
@requires_permission("approve_sar")
def render_approval_panel(case_id: str):
    st.divider()
    st.subheader("STR Submission")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Approve & Submit to FIU-IND", type="primary"):
            audit.log_sar_approval(case_id)
            response = api_client.approve_sar(case_id)
            st.success(f"STR submitted. Reference: {response['fiu_ref']}")
    with col2:
        if st.button("Reject & Close Case"):
            audit.log_case_rejection(case_id)
            api_client.reject_case(case_id)

# ── PII Display (COMPLIANCE_OFFICER only) ────────────────────────────────────
@requires_permission("view_pii_unmasked")
def render_unmasked_account_details(case_data: dict):
    """
    All other roles see masked values (XXXXXX1234).
    Only COMPLIANCE_OFFICER sees real account numbers via this gated component.
    """
    st.write(f"**Account No:** {case_data['account_number']}")
    st.write(f"**PAN:** {case_data['pan']}")
    audit.log_pii_access(case_data['case_id'])

# ── SHAP Panel (ANALYST_L2 and above) ────────────────────────────────────────
@requires_permission("view_shap_explanation")
def render_shap_panel(shap_data: dict):
    st.subheader("Risk Score Explanation")
    for driver in shap_data["explanations"]:
        bar_width = int(abs(driver["shap_impact"]) * 100)
        colour    = "red" if driver["direction"] == "INCREASES_RISK" else "green"
        st.markdown(
            f"`{driver['feature']}` = **{driver['value']}** "
            f"→ Impact: `{driver['shap_impact']:+.4f}` "
            f"<span style='color:{colour}'>({driver['direction']})</span>",
            unsafe_allow_html=True,
        )

# ── Graph Panel (ANALYST_L2 and above) ──────────────────────────────────────
@requires_permission("view_graph_panel")
def render_graph_panel():
    st.subheader("Neo4j Transaction Network")
    subgraph_id = st.session_state.get("active_subgraph_id")
    if subgraph_id:
        graph_data = api_client.get_subgraph(subgraph_id)
        # Rendered via pyvis NetworkX → HTML component embedded in Streamlit
        render_pyvis_graph(graph_data)
        audit.log_graph_access(subgraph_id)
```

---

### 7.4 Per-Request JWT Injector (`api_client.py`)

Every HTTP call from the Streamlit UI to the FastAPI backend carries the current JWT as a Bearer token. The client auto-refreshes the token if it is within the expiry window before making the call, so no API request ever fires with a stale or expired token.

```python
# api_client.py
import httpx
import streamlit as st
import time
from auth_gate import verify_and_decode_jwt, TOKEN_URI, CLIENT_ID

API_BASE = "https://sar-api.internal"    # FastAPI backend — internal network only

class ZeroTrustAPIClient:
    """
    All Streamlit-to-backend communication goes through this client.
    It is the single choke point that enforces:
      - Bearer token injection on every request
      - Pre-flight token refresh if near expiry
      - Request signing (optional: HMAC of request body)
    """

    def _get_valid_token(self) -> str:
        """
        Validates the token expiry before every API call.
        Triggers a silent refresh if within TOKEN_REFRESH_THRESHOLD_SECONDS.
        """
        token   = st.session_state.get("access_token", "")
        payload = verify_and_decode_jwt(token)
        exp     = payload.get("exp", 0)
        now     = int(time.time())

        if (exp - now) < 300:
            # Pre-flight refresh
            refresh_token = st.session_state.get("refresh_token", "")
            resp = httpx.post(TOKEN_URI, data={
                "grant_type":    "refresh_token",
                "client_id":     CLIENT_ID,
                "refresh_token": refresh_token,
            }, timeout=10)
            if resp.status_code == 200:
                new_tokens = resp.json()
                st.session_state["access_token"]  = new_tokens["access_token"]
                st.session_state["refresh_token"] = new_tokens["refresh_token"]
                return new_tokens["access_token"]

        return token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_valid_token()}",
            "Content-Type":  "application/json",
            "X-Request-ID":  self._generate_request_id(),    # for audit correlation
        }

    def _generate_request_id(self) -> str:
        import uuid
        return str(uuid.uuid4())

    # --- Typed API Methods ---

    def get_case(self, case_id: str) -> dict:
        r = httpx.get(f"{API_BASE}/api/v1/get_case/{case_id}", headers=self._headers())
        r.raise_for_status()
        return r.json()

    def approve_sar(self, case_id: str) -> dict:
        r = httpx.post(
            f"{API_BASE}/api/v1/approve_sar",
            json={"case_id": case_id},
            headers=self._headers()
        )
        r.raise_for_status()
        return r.json()

    def get_subgraph(self, subgraph_id: str) -> dict:
        r = httpx.get(
            f"{API_BASE}/api/v1/view_graph/{subgraph_id}",
            headers=self._headers()
        )
        r.raise_for_status()
        return r.json()

    def export_str(self, case_id: str) -> bytes:
        r = httpx.get(
            f"{API_BASE}/api/v1/export_str/{case_id}",
            headers=self._headers()
        )
        r.raise_for_status()
        return r.content     # Returns PDF bytes for st.download_button


# Module-level singleton — imported and reused across all Streamlit pages
api_client = ZeroTrustAPIClient()
```

---

### 7.5 UI Audit Logger (`ui_audit_logger.py`)

Every meaningful user action on the UI — page views, case opens, graph accesses, approvals, PII views, rejections — is written to the immutable audit trail. The audit log is **append-only** (PostgreSQL INSERT, no UPDATE/DELETE on this table), timestamped, and linked to the user's Keycloak UUID so it cannot be repudiated.

```python
# ui_audit_logger.py
import datetime
import hashlib
import json
import psycopg2
import os

class UIAuditLogger:

    def __init__(self, user_id: str, user_role: str):
        self.user_id   = user_id
        self.user_role = user_role
        self.conn      = psycopg2.connect(os.environ["AUDIT_DB_URL"])

    def _write(self, event_type: str, metadata: dict):
        """
        Core write method. Every audit entry includes:
        - user_id (Keycloak UUID — non-repudiable identity)
        - event_type
        - metadata as JSON
        - SHA-256 hash of (user_id + event_type + metadata + timestamp)
          so tampering with any field breaks the hash chain
        """
        timestamp = datetime.datetime.utcnow().isoformat()
        payload_str = json.dumps({
            "user_id":    self.user_id,
            "role":       self.user_role,
            "event":      event_type,
            "metadata":   metadata,
            "timestamp":  timestamp,
        }, sort_keys=True)

        entry_hash = hashlib.sha256(payload_str.encode()).hexdigest()

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ui_audit_log
                    (user_id, user_role, event_type, metadata, timestamp, entry_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                self.user_id,
                self.user_role,
                event_type,
                json.dumps(metadata),
                timestamp,
                entry_hash,
            ))
        self.conn.commit()

    # --- Typed audit methods ---

    def log_page_view(self, page: str):
        self._write("PAGE_VIEW", {"page": page})

    def log_case_open(self, case_id: str):
        self._write("CASE_OPEN", {"case_id": case_id})

    def log_graph_access(self, subgraph_id: str):
        self._write("GRAPH_ACCESS", {"subgraph_id": subgraph_id})

    def log_pii_access(self, case_id: str):
        """
        PII views are a separate, elevated-priority audit event.
        Written with an extra severity flag for compliance review.
        """
        self._write("PII_VIEW_UNMASKED", {
            "case_id":  case_id,
            "severity": "HIGH",
            "note":     "Unmasked account/PAN viewed by COMPLIANCE_OFFICER",
        })

    def log_sar_approval(self, case_id: str):
        self._write("SAR_APPROVED", {"case_id": case_id})

    def log_case_rejection(self, case_id: str):
        self._write("CASE_REJECTED", {"case_id": case_id})

    def log_str_export(self, case_id: str):
        self._write("STR_EXPORTED", {"case_id": case_id})

    def log_session_terminated(self, reason: str):
        self._write("SESSION_TERMINATED", {"reason": reason})
```

**Audit Log Table DDL (append-only, no UPDATE/DELETE grants):**

```sql
CREATE TABLE ui_audit_log (
    id          BIGSERIAL PRIMARY KEY,
    user_id     VARCHAR(64)  NOT NULL,          -- Keycloak UUID
    user_role   VARCHAR(30)  NOT NULL,
    event_type  VARCHAR(50)  NOT NULL,
    metadata    JSONB        NOT NULL,
    timestamp   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    entry_hash  VARCHAR(64)  NOT NULL            -- SHA-256 tamper seal
);

-- Append-only enforcement: revoke destructive privileges from app user
REVOKE UPDATE, DELETE, TRUNCATE ON ui_audit_log FROM sar_app_user;

-- Index for compliance queries: "show me all actions by user X in the last 30 days"
CREATE INDEX idx_audit_user_ts ON ui_audit_log (user_id, timestamp DESC);
CREATE INDEX idx_audit_event   ON ui_audit_log (event_type, timestamp DESC);
```

---

### 7.6 ZT UI File Structure

```
ui/
├── app.py                    # Entry point — zt_session.enforce() called first
├── auth_gate.py              # OIDC PKCE flow, Keycloak token exchange
├── zt_session.py             # Session validation, inactivity timeout, posture check
├── role_gate.py              # @requires_permission decorator, ROLE_PERMISSIONS map
├── api_client.py             # ZeroTrustAPIClient — JWT injected on every call
├── ui_audit_logger.py        # Append-only audit trail for all UI actions
├── pages/
│   ├── alert_queue.py        # Requires: view_alert_queue
│   ├── graph_explorer.py     # Requires: view_graph_panel
│   ├── typology_reports.py   # Requires: view_typology_report
│   ├── audit_trail.py        # Requires: view_audit_trail
│   └── str_export.py         # Requires: export_str_document
└── components/
    ├── shap_panel.py         # Requires: view_shap_explanation
    ├── approval_panel.py     # Requires: approve_sar
    └── account_details.py    # Masked by default; unmasked only for view_pii_unmasked
```

---

### 7.7 Zero Trust UI — Control Summary

| Control | Implementation | Principle |
|---|---|---|
| SSO + MFA | Keycloak OIDC, TOTP required action | Never Trust — verify identity every session |
| PKCE auth flow | S256 code challenge, state token anti-CSRF | Prevent auth code interception |
| JWT verification | RS256 signature check via JWKS on every rerun | Never trust the token without cryptographic proof |
| Token expiry (15 min) | Keycloak access token TTL = 900s | Limit blast radius of stolen tokens |
| Inactivity timeout | 15-min inactivity check in ZeroTrustSessionManager | Zero Trust session hygiene |
| Pre-flight token refresh | api_client refreshes before every API call | Continuous verification |
| Device posture check | IP CIDR validation on session init | Context-aware access |
| Role-gated rendering | @requires_permission on every component | Least-privilege UI |
| No access-denied hints | Forbidden components render nothing | No information leakage |
| PII masking by default | Only COMPLIANCE_OFFICER role sees unmasked data | Data minimisation |
| JWT on every API call | ZeroTrustAPIClient injects Bearer header | Backend never trusts UI implicitly |
| Append-only audit trail | REVOKE UPDATE/DELETE on ui_audit_log | Non-repudiation |
| SHA-256 audit hashing | Every audit entry has a tamper-seal hash | Immutable evidence chain |

---

## Data Schema & Neo4j Graph Model

```
NODES
─────────────────────────────────────────────────────────────────────
:Account                         :Transaction
  account_id (pseudonymised)       txn_id
  account_type                     amount
  kyc_tier                         channel
  declared_income_band             is_cash
  state_of_origin                  city / state
  risk_score                       timestamp
  is_flagged                       ip_hash

:Entity                          :SubgraphSnapshot
  entity_id                        id
  entity_type                      target_account_id
  jurisdiction                     sender_ids[]
                                   typology
                                   created_at

RELATIONSHIPS
─────────────────────────────────────────────────────────────────────
(Account)-[:SENT {amount, timestamp}]-------->(Transaction)
(Transaction)-[:RECEIVED_BY]---------------->(Account)
(Account)-[:OWNED_BY]------------------------>(Entity)
(Entity)-[:CONTROLS]------------------------>(Account)
(Account)-[:SHARES_DEVICE]------------------>(Account)  ← device fingerprint
(Account)-[:SHARES_ADDRESS]----------------->(Account)  ← KYC address linkage
(Account)-[:CO_OWNED_BY]------------------->(Entity)   ← common beneficial owner
```

---

## Inter-Module Orchestration

```
Incoming Transaction Event
        │
        ▼
[Module 6 — PII Stripper]
Tokenise all PII before any downstream processing
        │
        ▼
┌─────────────────────────────────────────────────┐
│  PARALLEL (asyncio.gather)                      │
│                                                 │
│  [Module 1] Graph Context Engine                │
│  → 4-hop upstream traversal                     │
│  → Pass-through / smurfing score                │
│  → graph_signature, fan_in_count               │
│                                                 │
│  [Module 2] Baseline Calculator                 │
│  → amount_vs_history_ratio                      │
│  → z_score_amount, income_mismatch_ratio        │
│                                                 │
│  [Module 4] Aggregation Engine                  │
│  → 30d / 90d / 180d window totals               │
│  → threshold_breach flags                       │
└─────────────────────────────────────────────────┘
        │
        ▼  (merge all feature dicts)
[Module 2 — XGBoost Scorer]
Full 20-feature vector → risk_score, risk_tier, SHAP narrative
        │
   ┌────┴──────────────────────┐
   │  risk_tier >= HIGH?       │
   └────────┬──────────────────┘
            │ YES
            ▼
[Module 3 — Lifecycle Monitor]
→ Open 72h monitoring window in Redis
→ Subscribe to outflow events
→ Classify typology on each outflow
            │
            ▼
[Module 5 — Fan-In Detector] (async, scheduled every 6h)
→ Detect Fan-In signatures over 90-day window
→ Coefficient of variation timing analysis
→ Cross-state / cross-city sender mapping
            │
            ▼
Alert Service → STR / SAR Generation Agent
→ PII re-inserted server-side (Module 6 token_map)
→ SHA-256 audit trail entry written
→ Analyst review queue populated
→ Streamlit UI — case opened for Compliance Officer
```

---

## Infrastructure & Deployment

### Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| API Framework | FastAPI | 0.111 | Backend API, JWT Zero Trust middleware |
| Graph DB | Neo4j Enterprise | 5.15 | Multi-hop traversal, Fan-In detection |
| Relational DB | PostgreSQL | 16 | Transaction history, behavioral profiles |
| Cache / Queue | Redis | 7 | Lifecycle monitoring windows, Celery broker |
| ML Framework | XGBoost | 2.0 | Risk scoring (binary classification) |
| Explainability | SHAP | 0.44 | TreeExplainer for analyst-readable narratives |
| Task Queue | Celery | 5.3 | Async Fan-In scans, 6h scheduled jobs |
| PII Detection | presidio-analyzer | 2.2 | Pre-LLM PII entity detection |
| Secret Mgmt | HashiCorp Vault | 1.16 | Runtime secret injection — no .env keys |
| Service Mesh | Istio | 1.21 | mTLS between all containers |
| Identity Provider | Keycloak (self-hosted, on-prem) | 24 | OIDC SSO + TOTP MFA — on-prem for RBI compliance |
| UI | Streamlit | 1.35 | Analyst / Compliance Officer review UI |
| OIDC Client Lib | python-jose + PyJWKClient | — | RS256 JWT verification against Keycloak JWKS |
| HTTP Client (UI) | httpx | 0.27 | ZeroTrustAPIClient — JWT injected on every request |
| Container Orch | Docker + Kubernetes | — | Deployment, strict network segmentation |
| Monitoring | Prometheus + Grafana | — | Latency, alert volumes, model drift tracking |

### Compliance Control Mapping

| Control | Implementation | Regulation |
|---|---|---|
| Data localisation | All processing on-prem / India-hosted cloud only | RBI 2018 Circular |
| Zero PII to LLM APIs | Module 6 PIIStripper mandatory pre-LLM gateway | DPDP Act 2023 |
| SSO + TOTP MFA | Keycloak OIDC, TOTP required action — no password-only login | RBI IT Framework |
| PKCE auth flow | S256 code challenge on every login — prevents code interception | Zero Trust / OAuth 2.1 |
| JWT cryptographic verification | RS256 via JWKS on every Streamlit rerun | Zero Trust |
| 15-min token TTL + inactivity timeout | Access token expiry + session_state timeout in ZTSessionManager | ISO 27001 |
| Role-gated UI rendering | @requires_permission on every component — no hints on forbidden views | Least Privilege |
| PII masked by default | Only COMPLIANCE_OFFICER role sees unmasked PAN/account — role_gate.py | DPDP Act 2023 |
| Per-request JWT injection | ZeroTrustAPIClient injects Bearer on every httpx call | Zero Trust |
| Append-only UI audit trail | REVOKE UPDATE/DELETE on ui_audit_log + SHA-256 entry hashes | PMLA 2002 |
| Device posture check | IP CIDR validation on session init in ZeroTrustSessionManager | RBI IT Framework |
| GroupKFold CV | Subject-level leakage prevention in model training | Model Governance |

---

*Document Version: 1.0 | Classification: Internal — Confidential*  
*Platform: SAR Intelligence Engine | Regulatory Jurisdiction: India (FIU-IND)*
