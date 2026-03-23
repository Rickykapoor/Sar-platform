"""
ui/app.py  — Day 2 (fully wired to real API + mock fallback)
Owned by: Anshul

5-page Streamlit UI for the SAR Platform.
  Page 1: Submit Transaction   — form with preset scenarios + live submit
  Page 2: Risk Analysis        — live score, tier badge, SHAP chart, signals
  Page 3: Graph View           — pyvis live render / placeholder
  Page 4: SAR Review           — narrative, compliance checklist, approve/dismiss
  Page 5: Audit Trail          — expandable per-agent entries + SHA256

When the backend is unreachable every page falls back to ui/mock_data.py.

Run:
    .venv\\Scripts\\streamlit.exe run ui/app.py
"""

from __future__ import annotations

import logging
import os
import sys

# ── Project root on sys.path so "from ui import …" works from any cwd ──────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st

from ui import api_client
from ui.mock_data import (
    MOCK_CASE,
    STRUCTURING_SCENARIO,
    LAYERING_SCENARIO,
    SMURFING_SCENARIO,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SAR Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Global CSS  (dark theme)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
[data-testid="stSidebar"]          { background-color: #0f172a; }
[data-testid="stSidebar"] *        { color: #e2e8f0 !important; }
.stApp                             { background-color: #0f172a; color: #e2e8f0; }
h1                                 { color: #f1f5f9 !important; }
h2, h3                             { color: #cbd5e1 !important; }

.sar-card {
    background: #1e293b; border: 1px solid #334155;
    border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 1rem;
}
.badge-red    { background:#ef4444; color:#fff;    padding:4px 14px; border-radius:99px; font-weight:700; display:inline-block; }
.badge-amber  { background:#f59e0b; color:#1a1a1a; padding:4px 14px; border-radius:99px; font-weight:700; display:inline-block; }
.badge-green  { background:#22c55e; color:#1a1a1a; padding:4px 14px; border-radius:99px; font-weight:700; display:inline-block; }
.badge-filed  { background:#6366f1; color:#fff;    padding:4px 14px; border-radius:99px; font-weight:700; display:inline-block; }

.hash-box {
    font-family: monospace; background: #0f172a; border: 1px solid #475569;
    border-radius: 8px; padding: 10px 16px; font-size: 0.78rem;
    color: #94a3b8; word-break: break-all;
}
.issue-item { background:#1e1010; border-left:3px solid #ef4444; padding:8px 12px; margin-bottom:6px; border-radius:0 8px 8px 0; font-size:.85rem; }
.pass-item  { background:#0f1e0f; border-left:3px solid #22c55e; padding:8px 12px; margin-bottom:6px; border-radius:0 8px 8px 0; font-size:.85rem; }
.narrative-box {
    background:#1e293b; border:1px solid #334155; border-radius:10px;
    padding:1rem 1.25rem; font-size:.88rem; line-height:1.7;
    white-space:pre-wrap; color:#e2e8f0;
}
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────
if "current_case" not in st.session_state:
    st.session_state.current_case = None
if "using_mock" not in st.session_state:
    st.session_state.using_mock = False
if "form_prefill" not in st.session_state:
    st.session_state.form_prefill = {}
if "all_cases" not in st.session_state:
    st.session_state.all_cases = []


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_case_data() -> dict:
    """Active live case, or mock if backend is down."""
    return st.session_state.current_case or MOCK_CASE


def _tier_badge(tier: str) -> str:
    t = (tier or "").lower()
    if t in ("red", "critical"):
        return '<span class="badge-red">🔴 RED</span>'
    if t == "amber":
        return '<span class="badge-amber">🟡 AMBER</span>'
    return '<span class="badge-green">🟢 GREEN</span>'


def _refresh_case(case_id: str) -> dict | None:
    """Re-fetch the case from the API and store in session state."""
    data = api_client.get_case(case_id)
    if data:
        st.session_state.current_case = data
    return data


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏦 SAR Platform")
    st.markdown("---")

    backend_up = api_client.health_check()
    st.session_state.using_mock = not backend_up
    if backend_up:
        st.success("✅ Backend online")
    else:
        st.warning("⚠️ Backend offline\nShowing mock data")

    st.markdown("---")
    page = st.radio(
        "📋 Navigation",
        [
            "1 · Submit Transaction",
            "2 · Risk Analysis",
            "3 · Graph View",
            "4 · SAR Review",
            "5 · Audit Trail",
        ],
    )

    # Case selector when backend is online
    if backend_up:
        st.markdown("---")
        cases = api_client.get_all_cases() or []
        st.session_state.all_cases = cases
        if cases:
            case_ids = [c.get("case_id", "?") for c in cases]
            chosen_id = st.selectbox("📂 Select case", case_ids)
            if chosen_id:
                chosen = next((c for c in cases if c.get("case_id") == chosen_id), None)
                if chosen:
                    st.session_state.current_case = chosen

    st.markdown("---")
    case = _get_case_data()
    st.markdown(f"**Active case:** `{case.get('case_id', '—')}`")
    status = case.get("status", "—")
    if status == "filed":
        st.markdown('<span class="badge-filed">FILED</span>', unsafe_allow_html=True)
    elif status == "dismissed":
        st.markdown("🚫 DISMISSED")
    else:
        st.markdown(f"`{status.upper()}`")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1 — Submit Transaction
# ─────────────────────────────────────────────────────────────────────────────
if page == "1 · Submit Transaction":
    st.title("📤 Submit Transaction")

    if st.session_state.using_mock:
        st.warning("⚠️ Backend offline — form results will use mock data.")

    # Preset buttons
    st.markdown("### Quick Presets")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔴 Structuring Demo", use_container_width=True):
            st.session_state.form_prefill = STRUCTURING_SCENARIO
    with c2:
        if st.button("🟡 Layering Demo", use_container_width=True):
            st.session_state.form_prefill = LAYERING_SCENARIO
    with c3:
        if st.button("🟠 Smurfing Demo", use_container_width=True):
            st.session_state.form_prefill = SMURFING_SCENARIO

    pre = st.session_state.form_prefill
    st.markdown("---")
    st.markdown("### Transaction Details")

    with st.form("submit_form"):
        ca, cb = st.columns(2)
        with ca:
            account_id = st.text_input("Account ID", value=pre.get("account_id", ""), placeholder="ACC-XXXX-US")
            amounts = pre.get("amount_usd", 1000.0)
            amount_usd = st.number_input("Amount (USD)", min_value=0.01, value=float(amounts), step=100.0)
            types = ["cash_deposit", "wire", "ach_transfer", "check", "crypto"]
            tx_type_val = pre.get("transaction_type", "cash_deposit")
            tx_type_idx = types.index(tx_type_val) if tx_type_val in types else 0
            transaction_type = st.selectbox("Transaction Type", types, index=tx_type_idx)
        with cb:
            counterparty_id = st.text_input("Counterparty Account ID", value=pre.get("counterparty_account_id", ""), placeholder="ACC-XXXX-OFF")
            geography = st.text_input("Geography / Jurisdiction", value=pre.get("geography", ""), placeholder="offshore, switzerland, us …")
            channels = ["branch", "online", "atm", "mobile"]
            ch_val = pre.get("channel", "branch")
            ch_idx = channels.index(ch_val) if ch_val in channels else 0
            channel = st.selectbox("Channel", channels, index=ch_idx)

        submitted = st.form_submit_button("🚀 Submit & Score", use_container_width=True)

    if submitted:
        payload = {
            "account_id": account_id,
            "counterparty_account_id": counterparty_id,
            "amount_usd": amount_usd,
            "transaction_type": transaction_type,
            "channel": channel,
            "geography": geography,
        }

        if st.session_state.using_mock:
            st.info("Backend offline — showing mock response.")
            result = MOCK_CASE
        else:
            with st.spinner("Scoring transaction … running ML pipeline …"):
                result = api_client.submit_transaction(payload)
            if result is None:
                st.error("❌ Backend error. Check that `uvicorn main:app` is running on :8000.")
                result = None

        if result:
            st.session_state.current_case = result
            tier = (result.get("risk_assessment") or {}).get("risk_tier", "unknown")
            score = (result.get("risk_assessment") or {}).get("risk_score", 0.0)

            st.markdown("---")
            st.markdown("### 🎯 Result")
            r1, r2 = st.columns([1, 3])
            with r1:
                st.metric("Risk Score", f"{score:.2%}")
            with r2:
                st.markdown(f"**Tier:** {_tier_badge(tier)}", unsafe_allow_html=True)
                st.markdown(f"**Case ID:** `{result.get('case_id')}`")

            if (tier or "").lower() in ("red", "amber", "critical"):
                st.error("⚠️ HIGH RISK — SAR pipeline triggered automatically. Navigate to Risk Analysis →")
            else:
                st.success("✅ LOW RISK — No SAR filing required.")

            # Pipeline status widget
            if not st.session_state.using_mock:
                status_data = api_client.get_pipeline_status(result.get("case_id", ""))
                if status_data:
                    with st.expander("🔄 Pipeline Status"):
                        for agent, done in status_data.items():
                            icon = "✅" if done else "⏳"
                            st.markdown(f"{icon} **{agent}**")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2 — Risk Analysis
# ─────────────────────────────────────────────────────────────────────────────
elif page == "2 · Risk Analysis":
    st.title("📊 Risk Analysis")

    case = _get_case_data()
    if st.session_state.using_mock:
        st.warning("⚠️ Backend offline — showing mock data")
    else:
        # Offer a refresh button
        if st.button("🔄 Refresh from API"):
            with st.spinner("Fetching …"):
                _refresh_case(case.get("case_id", ""))
            case = _get_case_data()

    ra = case.get("risk_assessment")
    if not ra:
        st.info("No risk assessment yet. Submit a transaction first.")
        st.stop()

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Risk Score", f"{ra.get('risk_score', 0):.2%}")
    with m2:
        st.metric("Typology Confidence", f"{ra.get('typology_confidence', 0):.2%}")
    with m3:
        st.metric("Matched Typology", ra.get("matched_typology", "—"))
    with m4:
        st.metric("Neo4j Pattern", "✅ Yes" if ra.get("neo4j_pattern_found") else "❌ No")

    st.markdown(f"**Risk Tier:** {_tier_badge(ra.get('risk_tier', ''))}", unsafe_allow_html=True)
    st.markdown(f"> 💡 **Typology:** {ra.get('matched_typology','—')} — confidence `{ra.get('typology_confidence',0):.0%}`")

    st.markdown("---")
    st.markdown("### 🔬 Feature Importance (SHAP)")
    shap_values = ra.get("shap_values") or {}
    if shap_values:
        import pandas as pd
        shap_df = (
            pd.DataFrame({"Feature": list(shap_values.keys()), "SHAP": list(shap_values.values())})
            .set_index("Feature")
            .sort_values("SHAP", ascending=False)
        )
        st.bar_chart(shap_df, color="#ef4444")
    else:
        st.info("SHAP values not available.")

    st.markdown("---")
    st.markdown("### ⚠️ Risk Signals")
    signals = ra.get("signals", [])
    if not signals:
        st.info("No risk signals recorded.")
    else:
        for sig in signals:
            with st.expander(
                f"🚨 {sig.get('signal_type','SIGNAL')}  —  Confidence: {sig.get('confidence',0):.0%}"
            ):
                st.warning(sig.get("description", "—"))
                tx_ids = sig.get("supporting_transaction_ids", [])
                if tx_ids:
                    st.markdown(f"**Supporting txns:** `{', '.join(tx_ids)}`")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3 — Graph View
# ─────────────────────────────────────────────────────────────────────────────
elif page == "3 · Graph View":
    st.title("🕸️ Transaction Graph")

    case = _get_case_data()
    case_id = case.get("case_id", "")

    if st.session_state.using_mock:
        st.warning("⚠️ Backend offline — showing placeholder")

    graph_data = None
    if not st.session_state.using_mock and case_id:
        with st.spinner("Loading graph from Neo4j …"):
            graph_data = api_client.get_case_graph(case_id)

    if graph_data and graph_data.get("nodes"):
        try:
            from pyvis.network import Network
            import streamlit.components.v1 as components

            net = Network(height="500px", width="100%", bgcolor="#1e293b", font_color="#e2e8f0")
            net.set_options('{"physics":{"enabled":true}}')
            COLOR_MAP = {
                "Account": "#3b82f6",
                "Transaction": "#f59e0b",
                "SARCase": "#ef4444",
                "RiskSignal": "#f97316",
                "AuditEvent": "#22c55e",
            }
            for node in graph_data.get("nodes", []):
                net.add_node(
                    node["id"],
                    label=node.get("label", node["id"]),
                    color=COLOR_MAP.get(node.get("type", ""), "#94a3b8"),
                    title=node.get("type", "Node"),
                )
            for edge in graph_data.get("edges", []):
                net.add_edge(edge["source"], edge["target"], label=edge.get("relationship", ""))

            components.html(net.generate_html(), height=520)
        except ImportError:
            st.error("pyvis not installed. Run: `.venv\\Scripts\\pip install pyvis`")
    else:
        st.markdown(
            """
<div class="sar-card" style="text-align:center;padding:4rem;">
    <h2 style="color:#94a3b8;">🕸️ Graph Placeholder</h2>
    <p style="color:#64748b;">
        Nisarg wires live Neo4j data here on Day 2.<br>
        <strong style="color:#3b82f6;">● Account</strong>&nbsp;&nbsp;
        <strong style="color:#f59e0b;">● Transaction</strong>&nbsp;&nbsp;
        <strong style="color:#ef4444;">● SARCase</strong>&nbsp;&nbsp;
        <strong style="color:#f97316;">● RiskSignal</strong>&nbsp;&nbsp;
        <strong style="color:#22c55e;">● AuditEvent</strong>
    </p>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### Node Legend")
    legends = [("Account","#3b82f6"),("Transaction","#f59e0b"),("SARCase","#ef4444"),("RiskSignal","#f97316"),("AuditEvent","#22c55e")]
    for col, (label, color) in zip(st.columns(5), legends):
        col.markdown(f"<span style='color:{color};font-size:1.5rem;'>●</span> **{label}**", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4 — SAR Review
# ─────────────────────────────────────────────────────────────────────────────
elif page == "4 · SAR Review":
    st.title("📝 SAR Review")

    case = _get_case_data()
    case_id = case.get("case_id", "")

    if st.session_state.using_mock:
        st.warning("⚠️ Backend offline — showing mock data. Approve/Dismiss buttons disabled.")

    # ── Narrative ──
    st.markdown("### 📄 SAR Narrative")
    narrative = case.get("narrative") or {}
    narrative_body = narrative.get("narrative_body", "")

    if not st.session_state.using_mock and not narrative_body:
        if st.button("✨ Generate Narrative", use_container_width=True):
            placeholder = st.empty()
            with st.spinner("Generating narrative via MiniMax-Text-2.5 …"):
                result = api_client.generate_narrative(case_id)
            if result:
                st.session_state.current_case = result
                case = result
                narrative = result.get("narrative") or {}
                narrative_body = narrative.get("narrative_body", "")
                placeholder.success("✅ Narrative generated!")
            else:
                st.error("❌ Failed to generate narrative — backend error.")

    if narrative_body:
        # Simulate streaming: show token-by-token reveal via st.empty updating
        if "narrative_streamed" not in st.session_state:
            st.session_state.narrative_streamed = False

        if not st.session_state.narrative_streamed:
            stream_area = st.empty()
            displayed = ""
            words = narrative_body.split(" ")
            chunk_size = max(1, len(words) // 40)
            for i in range(0, len(words), chunk_size):
                displayed = " ".join(words[: i + chunk_size])
                stream_area.markdown(
                    f'<div class="narrative-box">{displayed}</div>',
                    unsafe_allow_html=True,
                )
            st.session_state.narrative_streamed = True
        else:
            st.markdown(f'<div class="narrative-box">{narrative_body}</div>', unsafe_allow_html=True)

        st.caption(
            f"Model: {narrative.get('model_version_used','—')} · "
            f"Generated: {narrative.get('generation_timestamp','—')}"
        )
    elif st.session_state.using_mock:
        # Show mock narrative
        mock_narrative = MOCK_CASE.get("narrative", {}).get("narrative_body", "")
        st.markdown(f'<div class="narrative-box">{mock_narrative}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Compliance checklist ──
    st.markdown("### ✅ Compliance Checklist")
    compliance = case.get("compliance") or {}
    issues = compliance.get("compliance_issues", [])

    if compliance:
        check_cols = st.columns(3)
        with check_cols[0]:
            b = "✅" if compliance.get("bsa_compliant") else "❌"
            st.markdown(f"{b} **BSA Compliant**")
        with check_cols[1]:
            b = "✅" if compliance.get("all_fields_complete") else "❌"
            st.markdown(f"{b} **All Fields Complete**")
        with check_cols[2]:
            b = "✅" if compliance.get("fincen_format_valid") else "❌"
            st.markdown(f"{b} **FinCEN Format Valid**")

        st.markdown(f"**Issues found: {len(issues)}**")
        if not issues:
            st.markdown('<div class="pass-item">✅ No compliance issues — clear to file.</div>', unsafe_allow_html=True)
        else:
            for issue in issues:
                st.markdown(f'<div class="issue-item">❌ {issue}</div>', unsafe_allow_html=True)
    else:
        st.info("Compliance check not yet run.")

    st.markdown("---")

    # ── Analyst decision ──
    st.markdown("### 🏛️ Analyst Decision")
    current_status = case.get("status", "pending")

    if current_status == "filed":
        st.success(f"✅ **FILED** — Approved by: {case.get('analyst_approved_by', '—')}")
        st.markdown(f"Filed at: `{case.get('final_filed_timestamp', '—')}`")
    elif current_status == "dismissed":
        st.error("🚫 **DISMISSED**")
    else:
        analyst_name = st.text_input("👤 Analyst Name", placeholder="Enter your full name")
        btn1, btn2 = st.columns(2)

        with btn1:
            approve_clicked = st.button(
                "✅ Approve and File SAR",
                use_container_width=True,
                disabled=st.session_state.using_mock,
            )
        with btn2:
            dismiss_clicked = st.button(
                "🚫 Dismiss Case",
                use_container_width=True,
                disabled=st.session_state.using_mock,
            )

        if approve_clicked:
            if not analyst_name.strip():
                st.error("⚠️ Please enter your analyst name before approving.")
            else:
                with st.spinner("Filing SAR …"):
                    result = api_client.approve_case(case_id, analyst_name.strip())
                if result:
                    st.session_state.current_case = result
                    st.session_state.narrative_streamed = False  # allow re-render
                    st.balloons()
                    st.success(f"✅ SAR filed successfully by **{analyst_name}**!")
                    st.rerun()
                else:
                    st.error("❌ Approval failed — check backend logs.")

        if dismiss_clicked:
            with st.spinner("Dismissing case …"):
                result = api_client.dismiss_case(case_id)
            if result:
                st.session_state.current_case = result
                st.warning("🚫 Case dismissed.")
                st.rerun()
            else:
                st.error("❌ Dismiss failed — check backend logs.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 5 — Audit Trail
# ─────────────────────────────────────────────────────────────────────────────
elif page == "5 · Audit Trail":
    st.title("🔍 Audit Trail")

    case = _get_case_data()
    case_id = case.get("case_id", "")

    if st.session_state.using_mock:
        st.warning("⚠️ Backend offline — showing mock data")
    else:
        if st.button("🔄 Refresh from API"):
            with st.spinner("Fetching …"):
                _refresh_case(case_id)
            case = _get_case_data()

    audit_trail = case.get("audit_trail", [])
    error_log = case.get("error_log", [])

    # ── Timeline ──
    if not audit_trail:
        st.info("No audit trail entries yet. Run the pipeline first.")
    else:
        st.markdown(
            f"**{len(audit_trail)} agent decisions recorded** — immutable, append-only."
        )
        st.markdown("---")
        for i, entry in enumerate(audit_trail, 1):
            agent_name = entry.get("agent", f"Step {i}")
            timestamp = entry.get("timestamp", "—")
            confidence = entry.get("confidence", None)
            action = entry.get("action", "—")

            with st.expander(f"**{i}. {agent_name}**  ·  `{timestamp}`"):
                st.markdown(f"**Action:** {action}")
                if confidence is not None:
                    st.progress(confidence)
                    st.caption(f"Confidence: {confidence:.0%}")
                if entry.get("analyst"):
                    st.markdown(f"**Analyst:** {entry['analyst']}")
                if entry.get("immutable_hash"):
                    st.markdown("**Entry hash:**")
                    st.markdown(
                        f'<div class="hash-box">{entry["immutable_hash"]}</div>',
                        unsafe_allow_html=True,
                    )

    # ── Immutable SHA256 hash ──
    st.markdown("---")
    st.markdown("### 🔐 Immutable Case Hash (SHA256)")

    audit_record = case.get("audit") or {}
    immutable_hash = audit_record.get("immutable_hash", "") if audit_record else ""

    if immutable_hash:
        st.markdown(
            f'<div class="hash-box">🔒 {immutable_hash}</div>',
            unsafe_allow_html=True,
        )
        st.caption("Immutable — cannot be modified. Generated by Agent 5 over the full SARCase JSON.")

        if st.button("📋 Copy Hash", help="Displays hash to copy"):
            st.code(immutable_hash, language=None)
    else:
        st.info("Hash not yet generated. Run the full pipeline (requires backend).")

    # ── Error log ──
    if error_log:
        st.markdown("---")
        st.markdown("### ⚠️ Error Log")
        for err in error_log:
            with st.expander(f"❌ {err.get('agent','Unknown')} · {err.get('timestamp','')}"):
                st.code(err.get("error", "—"))
