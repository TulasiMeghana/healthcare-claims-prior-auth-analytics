from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "warehouse" / "healthcare_analytics.duckdb"

st.set_page_config(page_title="Healthcare Claims Analytics", layout="wide")
st.title("Healthcare Claims & Prior Authorization Analytics")
st.caption("Synthetic portfolio project: claims operations, denial analytics, prior authorization queue, and data quality monitoring.")

if not DB_PATH.exists():
    st.error("Warehouse not found. Run `python src/generate_synthetic_data.py` and `python src/run_pipeline.py` first.")
    st.stop()

@st.cache_data
def query(sql: str) -> pd.DataFrame:
    with duckdb.connect(DB_PATH.as_posix(), read_only=True) as con:
        return con.execute(sql).df()

monthly = query("SELECT * FROM mart_monthly_claim_kpis ORDER BY service_month")
payer = query("SELECT * FROM mart_payer_performance")
provider = query("SELECT * FROM mart_provider_performance")
auth_turnaround = query("SELECT * FROM mart_authorization_turnaround")
queue = query("SELECT * FROM mart_prior_auth_queue LIMIT 500")
aging = query("SELECT * FROM mart_claim_aging_buckets")
denials = query("SELECT * FROM mart_denial_reasons")
quality = query("SELECT * FROM mart_data_quality_checks ORDER BY severity, check_name")

latest = monthly.sort_values("service_month").tail(1).iloc[0]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Latest Month Claims", f"{int(latest['claim_count']):,}")
col2.metric("Denial Rate", f"{latest['denial_rate_pct']:.2f}%")
col3.metric("Open Balance", f"${latest['open_balance']:,.0f}")
col4.metric("Avg Claim Age", f"{latest['avg_claim_age_days']:.1f} days")

st.divider()

left, right = st.columns(2)
with left:
    st.subheader("Monthly Denial Rate")
    fig = px.line(monthly, x="service_month", y="denial_rate_pct", markers=True)
    fig.update_layout(yaxis_title="Denial Rate %", xaxis_title="Service Month")
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Claim Aging Buckets")
    fig = px.bar(aging, x="aging_bucket", y="open_balance", text="claim_count")
    fig.update_layout(yaxis_title="Open Balance", xaxis_title="Aging Bucket")
    st.plotly_chart(fig, width="stretch")

left, right = st.columns(2)
with left:
    st.subheader("Payer Performance")
    st.dataframe(
        payer[["payer_name", "payer_type", "claim_count", "denial_rate_pct", "paid_rate_pct", "open_balance", "avg_claim_age_days"]],
        width="stretch",
        hide_index=True,
    )

with right:
    st.subheader("Top Denial Reasons")
    fig = px.bar(denials, x="denial_reason", y="denied_claims")
    fig.update_layout(yaxis_title="Denied Claims", xaxis_title="Reason")
    st.plotly_chart(fig, width="stretch")

st.subheader("Provider Performance Outliers")
st.dataframe(
    provider[["provider_name", "specialty", "region", "claim_count", "denial_rate_pct", "open_balance", "avg_claim_age_days"]].head(25),
    width="stretch",
    hide_index=True,
)

st.subheader("Prior Authorization Turnaround")
st.dataframe(
    auth_turnaround[["payer_name", "specialty", "clinical_priority", "authorization_count", "approval_rate_pct", "denial_rate_pct", "pending_rate_pct", "avg_turnaround_days"]].head(50),
    width="stretch",
    hide_index=True,
)

st.subheader("Prior Authorization Follow-Up Queue")
st.dataframe(
    queue[["authorization_id", "request_date", "authorization_status", "clinical_priority", "request_age_days", "payer_name", "provider_name", "specialty", "queue_priority", "denial_reason"]],
    width="stretch",
    hide_index=True,
)

st.subheader("Data Quality Report")
failed = quality[quality["status"] == "FAIL"]
if failed.empty:
    st.success("All quality checks passed.")
else:
    st.warning(f"{len(failed)} checks failed. Review before trusting dashboard metrics.")
st.dataframe(quality,width="stretch", hide_index=True)
