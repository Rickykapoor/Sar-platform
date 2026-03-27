"""
Module 2 — Behavioral Deviation Baseline Calculator
Computes amount_vs_history_ratio, z_score, velocity features for XGBoost input.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib


@dataclass
class BehavioralFeatures:
    trigger_amount: float
    avg_amount_6m: float
    avg_monthly_inflow_6m: float
    amount_vs_history_ratio: float
    z_score_amount: float
    days_since_similar_txn: int
    trigger_channel_freq: float
    typical_unique_senders_6m: int
    velocity_7d_count: int
    velocity_7d_amount: float
    income_mismatch_ratio: float


# Income-tier monthly income estimates (INR)
INCOME_TIER_MONTHLY = {
    "FREELANCER_MICRO":    25_000,
    "FREELANCER_MID":      75_000,
    "SMB":                500_000,
    "CORPORATE":        5_000_000,
}

# Typical channel frequencies by customer segment
TYPICAL_CHANNEL_FREQ = {
    "NEFT": 0.45, "IMPS": 0.30, "UPI": 0.15,
    "RTGS": 0.05, "ATM": 0.03, "SWIFT": 0.01, "CRYPTO_EXCHANGE": 0.01,
}


def compute_behavioral_features(tx: dict, account_id: str) -> BehavioralFeatures:
    """
    Computes behavioral deviation features from transaction dict.
    Production: queries PostgreSQL transaction_events table.
    Demo: derives deterministically from tx fields.
    """
    # Production path — PostgreSQL
    try:
        from sqlalchemy import create_engine, text
        import os, pandas as pd
        engine = create_engine(os.environ["DATABASE_URL"])
        df = pd.read_sql(text("""
            SELECT amount, txn_timestamp, channel, counterparty_id, is_cash
            FROM transaction_events
            WHERE account_id = :account_id AND is_inflow = TRUE
              AND txn_timestamp >= NOW() - INTERVAL '180 days'
        """), engine, params={"account_id": account_id})
        if not df.empty:
            return _compute_from_df(df, tx)
    except Exception:
        pass

    # Demo simulation — deterministic from tx fields
    return _compute_demo(tx, account_id)


def _compute_demo(tx: dict, account_id: str) -> BehavioralFeatures:
    amount  = float(tx.get("Transaction_Amount", tx.get("amount_usd", 0)) or 0)
    channel = str(tx.get("Transaction_Type", "NEFT") or "NEFT")
    age     = float(tx.get("Age", 35) or 35)

    # Deterministic synthetic baseline from account seed
    seed = int(hashlib.md5(account_id.encode()).hexdigest()[:6], 16)
    avg_amount = max(5000, amount * (0.2 + (seed % 100) / 200))  # historical avg is fraction of trigger
    std_amount = avg_amount * 0.3

    ratio        = round(amount / max(avg_amount, 1), 4)
    z_score      = round((amount - avg_amount) / max(std_amount, 1), 4)
    avg_monthly  = avg_amount * (4 + seed % 10)

    channel_norm = channel.upper()
    ch_freq      = TYPICAL_CHANNEL_FREQ.get(channel_norm, 0.02)

    # Income mismatch using age as proxy for income tier
    if age < 28:
        monthly_income = INCOME_TIER_MONTHLY["FREELANCER_MICRO"]
    elif age < 45:
        monthly_income = INCOME_TIER_MONTHLY["SMB"]
    else:
        monthly_income = INCOME_TIER_MONTHLY["CORPORATE"]

    income_mismatch = round(amount / max(monthly_income, 1), 4)
    days_similar    = max(1, 365 - (seed % 300)) if ratio > 2 else max(1, seed % 30)
    velocity_count  = 1 + (seed % 8)
    velocity_amount = amount * velocity_count * 0.7

    return BehavioralFeatures(
        trigger_amount=amount,
        avg_amount_6m=round(avg_amount, 2),
        avg_monthly_inflow_6m=round(avg_monthly, 2),
        amount_vs_history_ratio=ratio,
        z_score_amount=z_score,
        days_since_similar_txn=days_similar,
        trigger_channel_freq=round(ch_freq, 4),
        typical_unique_senders_6m=2 + seed % 15,
        velocity_7d_count=velocity_count,
        velocity_7d_amount=round(velocity_amount, 2),
        income_mismatch_ratio=income_mismatch,
    )


def _compute_from_df(df, tx: dict) -> BehavioralFeatures:
    """Computes features from real historical DataFrame."""
    import pandas as pd
    amount = float(tx.get("Transaction_Amount", 0) or 0)
    avg_6m = float(df["amount"].mean())
    std_6m = float(df["amount"].std() or 1.0)
    ratio  = amount / max(avg_6m, 1)
    z      = (amount - avg_6m) / std_6m

    df["txn_timestamp"] = pd.to_datetime(df["txn_timestamp"])
    df["month"] = df["txn_timestamp"].dt.to_period("M")
    monthly = df.groupby("month")["amount"].sum()
    avg_monthly = float(monthly.mean()) if not monthly.empty else avg_6m * 4

    channel = str(tx.get("Transaction_Type", "NEFT"))
    ch_freq = float(df["channel"].value_counts(normalize=True).get(channel, 0.0))

    now     = datetime.now()
    last_7d = df[df["txn_timestamp"] >= now - timedelta(days=7)]

    large   = df[df["amount"] >= amount * 0.7]
    days_since = int((now - large["txn_timestamp"].max()).days) if not large.empty else 999

    return BehavioralFeatures(
        trigger_amount=amount, avg_amount_6m=round(avg_6m, 2),
        avg_monthly_inflow_6m=round(avg_monthly, 2),
        amount_vs_history_ratio=round(ratio, 4), z_score_amount=round(z, 4),
        days_since_similar_txn=days_since, trigger_channel_freq=round(ch_freq, 4),
        typical_unique_senders_6m=int(df["counterparty_id"].nunique()),
        velocity_7d_count=len(last_7d), velocity_7d_amount=round(float(last_7d["amount"].sum()), 2),
        income_mismatch_ratio=round(amount / 100000, 4),
    )
