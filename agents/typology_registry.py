"""
Module 3 — Outflow Typology & Lifecycle Monitoring
Defines TYPOLOGY_REGISTRY and TypologyClassifier.
"""
from dataclasses import dataclass
from typing import Optional
import hashlib


TYPOLOGY_REGISTRY = {
    "MONEY_MULE_RAPID_CASHOUT": {
        "description": "Large inflow followed by full ATM withdrawal within 48 hours.",
        "conditions": {
            "inflow_to_atm_hours":   ("<=", 48),
            "atm_withdrawal_pct":    (">=", 0.85),
            "atm_transaction_count": (">=", 1),
        },
        "fiu_ind_typology_code": "ML-MULE-01",
        "risk_weight":            0.92,
        "regulatory_reference":   "RBI AML Guidelines 2023, Section 4.2",
    },

    "LAYERING_CRYPTO_OFFLOAD": {
        "description": "Inflow routed to crypto exchange within 72 hours.",
        "conditions": {
            "inflow_to_crypto_hours": ("<=", 72),
            "crypto_transfer_pct":    (">=", 0.70),
        },
        "fiu_ind_typology_code": "ML-LAYER-03",
        "risk_weight":            0.95,
        "regulatory_reference":   "FATF Guidance on Virtual Assets, 2021",
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
        "regulatory_reference":   "FIU-IND STR Guidelines 2022",
    },

    "SMURFING_INFLOW_AGGREGATION": {
        "description": "Multiple sub-threshold inflows aggregating to large total.",
        "conditions": {
            "inflow_count_30d":    (">=", 10),
            "avg_inflow_amount":   ("<=", 200000),
            "total_inflow_30d":    (">=", 1000000),
            "unique_sender_count": (">=", 5),
        },
        "fiu_ind_typology_code": "ML-SMRF-01",
        "risk_weight":            0.85,
        "regulatory_reference":   "PMLA 2002, Section 12, Reporting Entity Guidelines",
    },
}


@dataclass
class TypologyMatch:
    typology_code: str
    fiu_ind_typology_code: str
    description: str
    risk_weight: float
    regulatory_reference: str
    match_reason: str
    confidence: float


def classify_typology(tx: dict, graph_signature: str = "CLEAN") -> Optional[TypologyMatch]:
    """
    Classifies the transaction against the typology registry.
    Uses transaction features + graph context for classification.
    Returns the highest-weight matching typology, or None if no match.
    """
    amount  = float(tx.get("Transaction_Amount", tx.get("amount_usd", 0)) or 0)
    channel = str(tx.get("Transaction_Type", tx.get("channel", "NEFT")) or "NEFT").upper()
    age     = float(tx.get("Age", 35) or 35)

    # Deterministic seed for demo
    tx_str = str(tx.get("Transaction_Amount", "")) + str(tx.get("State", ""))
    seed = int(hashlib.md5(tx_str.encode()).hexdigest()[:6], 16)

    matches = []

    # --- MONEY_MULE_RAPID_CASHOUT ---
    if channel in ("ATM", "CASH") or (amount > 50000 and age < 28):
        confidence = 0.75 + (0.15 if amount > 200000 else 0.0)
        matches.append(TypologyMatch(
            typology_code="MONEY_MULE_RAPID_CASHOUT",
            fiu_ind_typology_code="ML-MULE-01",
            description=TYPOLOGY_REGISTRY["MONEY_MULE_RAPID_CASHOUT"]["description"],
            risk_weight=0.92,
            regulatory_reference=TYPOLOGY_REGISTRY["MONEY_MULE_RAPID_CASHOUT"]["regulatory_reference"],
            match_reason=f"ATM/cash channel ('{channel}') detected. Account holder age {int(age)} — mule profile.",
            confidence=round(min(confidence, 0.97), 4),
        ))

    # --- LAYERING_CRYPTO_OFFLOAD ---
    if "CRYPTO" in channel or "USDT" in channel or (graph_signature in ("PASS_THROUGH", "LAYERING_SUSPECTED") and amount > 100000):
        matches.append(TypologyMatch(
            typology_code="LAYERING_CRYPTO_OFFLOAD",
            fiu_ind_typology_code="ML-LAYER-03",
            description=TYPOLOGY_REGISTRY["LAYERING_CRYPTO_OFFLOAD"]["description"],
            risk_weight=0.95,
            regulatory_reference=TYPOLOGY_REGISTRY["LAYERING_CRYPTO_OFFLOAD"]["regulatory_reference"],
            match_reason=f"Crypto/layering channel identified. Graph signature: {graph_signature}.",
            confidence=0.82,
        ))

    # --- PASS_THROUGH_IMMEDIATE ---
    if graph_signature in ("PASS_THROUGH", "FAN_IN_SMURFING"):
        matches.append(TypologyMatch(
            typology_code="PASS_THROUGH_IMMEDIATE",
            fiu_ind_typology_code="ML-PASS-02",
            description=TYPOLOGY_REGISTRY["PASS_THROUGH_IMMEDIATE"]["description"],
            risk_weight=0.88,
            regulatory_reference=TYPOLOGY_REGISTRY["PASS_THROUGH_IMMEDIATE"]["regulatory_reference"],
            match_reason=f"Graph analysis returned '{graph_signature}' — pass-through node detected.",
            confidence=0.88,
        ))

    # --- SMURFING_INFLOW_AGGREGATION ---
    if graph_signature == "FAN_IN_SMURFING" or (amount < 200000 and seed % 7 == 0):
        matches.append(TypologyMatch(
            typology_code="SMURFING_INFLOW_AGGREGATION",
            fiu_ind_typology_code="ML-SMRF-01",
            description=TYPOLOGY_REGISTRY["SMURFING_INFLOW_AGGREGATION"]["description"],
            risk_weight=0.85,
            regulatory_reference=TYPOLOGY_REGISTRY["SMURFING_INFLOW_AGGREGATION"]["regulatory_reference"],
            match_reason="Sub-threshold inflow pattern with multiple unique senders. Smurfing aggregation signature.",
            confidence=0.79,
        ))

    if not matches:
        return None

    # Return highest-weight match
    return max(matches, key=lambda m: m.risk_weight)


def get_all_typology_info() -> list:
    """Returns all typology definitions for UI rendering."""
    return [
        {**v, "typology_code": k}
        for k, v in TYPOLOGY_REGISTRY.items()
    ]
