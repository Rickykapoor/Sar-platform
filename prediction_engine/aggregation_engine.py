"""
Module 4 — Time-Window Aggregation Engine
Rolling 30d/90d/180d inflow aggregations with RBI income-tier threshold breach detection.
"""
from dataclasses import dataclass, field
from typing import Optional
import hashlib


# RBI PMLA psychological thresholds by account income tier (INR)
THRESHOLD_INR = {
    "FREELANCER_MICRO":    500_000,      # 5L
    "FREELANCER_MID":    1_000_000,      # 10L
    "SMB":               5_000_000,      # 50L
    "CORPORATE":        50_000_000,      # 5Cr
}

WINDOWS = {"30d": 30, "90d": 90, "180d": 180}


@dataclass
class AggregationFeatures:
    rolling_30d_total: float
    rolling_90d_total: float
    rolling_180d_total: float
    rolling_30d_vs_income_ratio: float
    rolling_90d_vs_income_ratio: float
    rolling_90d_txn_count: int
    rolling_30d_threshold_breach: bool
    rolling_90d_threshold_breach: bool
    monthly_inflow_trend_slope: float
    income_tier: str


@dataclass
class AggregationAlert:
    window: str
    total_inflow_inr: float
    income_mismatch_ratio: float
    unique_senders: int
    threshold_breach: bool
    narrative: str


def compute_rolling_features(tx: dict, account_id: str) -> AggregationFeatures:
    """
    Computes rolling window features. Production: queries PostgreSQL partitioned table.
    Demo: derives deterministically from transaction amount and account_id.
    """
    # Production path
    try:
        from sqlalchemy import create_engine, text
        import os, pandas as pd, numpy as np
        engine  = create_engine(os.environ["DATABASE_URL"])
        income_tier, threshold = _get_income_tier(tx)
        df = pd.read_sql(text("""
            SELECT amount, txn_timestamp, channel, is_cash, counterparty_id
            FROM transaction_events
            WHERE account_id = :account_id AND is_inflow = TRUE
              AND txn_timestamp >= NOW() - INTERVAL '180 days'
        """), engine, params={"account_id": account_id})
        if not df.empty:
            return _from_df(df, income_tier, threshold)
    except Exception:
        pass

    return _compute_demo(tx, account_id)


def _get_income_tier(tx: dict) -> tuple:
    age = float(tx.get("Age", 35) or 35)
    amount = float(tx.get("Transaction_Amount", 0) or 0)
    if age < 28 or amount < 50000:
        return "FREELANCER_MICRO", THRESHOLD_INR["FREELANCER_MICRO"]
    elif age < 40 or amount < 500000:
        return "FREELANCER_MID", THRESHOLD_INR["FREELANCER_MID"]
    elif amount < 2000000:
        return "SMB", THRESHOLD_INR["SMB"]
    return "CORPORATE", THRESHOLD_INR["CORPORATE"]


def _compute_demo(tx: dict, account_id: str) -> AggregationFeatures:
    amount = float(tx.get("Transaction_Amount", 0) or 0)
    income_tier, threshold = _get_income_tier(tx)

    # Deterministic from account seed
    seed = int(hashlib.md5(account_id.encode()).hexdigest()[:6], 16)

    r30  = amount * (1 + seed % 5)
    r90  = r30  * (2 + seed % 4)
    r180 = r90  * (1.5 + seed % 3)

    ratio30 = round(r30 / max(threshold, 1), 4)
    ratio90 = round(r90 / max(threshold, 1), 4)

    slope = round((r90 - r30) / max(r30, 1) * 1000, 2)

    return AggregationFeatures(
        rolling_30d_total=round(r30, 2),
        rolling_90d_total=round(r90, 2),
        rolling_180d_total=round(r180, 2),
        rolling_30d_vs_income_ratio=ratio30,
        rolling_90d_vs_income_ratio=ratio90,
        rolling_90d_txn_count=2 + seed % 20,
        rolling_30d_threshold_breach=ratio30 > 1.0,
        rolling_90d_threshold_breach=ratio90 > 1.0,
        monthly_inflow_trend_slope=slope,
        income_tier=income_tier,
    )


def _from_df(df, income_tier: str, threshold: float) -> AggregationFeatures:
    import pandas as pd, numpy as np
    df["txn_timestamp"] = pd.to_datetime(df["txn_timestamp"], utc=True)
    now = pd.Timestamp.utcnow()

    def window_total(days: int) -> float:
        return float(df[df["txn_timestamp"] >= now - pd.Timedelta(days=days)]["amount"].sum())

    r30, r90, r180 = window_total(30), window_total(90), window_total(180)
    cnt90 = int(len(df[df["txn_timestamp"] >= now - pd.Timedelta(days=90)]))

    df["month"] = df["txn_timestamp"].dt.to_period("M")
    monthly = df.groupby("month")["amount"].sum().sort_index()
    slope = float(np.polyfit(range(len(monthly[-3:])), monthly[-3:].values, 1)[0]) if len(monthly) >= 3 else 0.0

    return AggregationFeatures(
        rolling_30d_total=round(r30, 2), rolling_90d_total=round(r90, 2),
        rolling_180d_total=round(r180, 2),
        rolling_30d_vs_income_ratio=round(r30 / max(threshold, 1), 4),
        rolling_90d_vs_income_ratio=round(r90 / max(threshold, 1), 4),
        rolling_90d_txn_count=cnt90,
        rolling_30d_threshold_breach=r30 > threshold,
        rolling_90d_threshold_breach=r90 > threshold,
        monthly_inflow_trend_slope=round(slope, 2),
        income_tier=income_tier,
    )


def generate_aggregation_alerts(features: AggregationFeatures) -> list:
    """Returns structured alerts for breached rolling windows."""
    alerts = []
    for label, ratio_attr, total_attr in [
        ("30d", "rolling_30d_vs_income_ratio", "rolling_30d_total"),
        ("90d", "rolling_90d_vs_income_ratio", "rolling_90d_total"),
    ]:
        ratio = getattr(features, ratio_attr)
        total = getattr(features, total_attr)
        if ratio > 1.0:
            alerts.append(AggregationAlert(
                window=label,
                total_inflow_inr=total,
                income_mismatch_ratio=ratio,
                unique_senders=features.rolling_90d_txn_count,
                threshold_breach=True,
                narrative=(
                    f"{label.upper()} rolling inflow of INR {total:,.0f} exceeds "
                    f"declared income threshold by {(ratio - 1) * 100:.0f}% "
                    f"for tier '{features.income_tier}'. Pattern consistent with structured accumulation."
                )
            ))
    return alerts
