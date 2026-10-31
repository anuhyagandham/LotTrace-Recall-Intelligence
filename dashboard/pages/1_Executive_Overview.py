"""
Page 1: Executive Overview Dashboard for LotTrace AI.
"""

import streamlit as st
import pandas as pd
from dashboard.components.cards import apply_theme, render_kpi_card
from dashboard.components.charts import plot_recall_gauge, plot_bar_chart
from src.database.connection import get_db_session
from src.analytics.metrics import MetricsCalculator

apply_theme()

st.title("📊 Executive Overview & Recall Scorecard")
st.markdown("High-level operational metrics, product safety performance, and dataset integrity summary.")

with get_db_session() as session:
    calc = MetricsCalculator(session=session)
    dataset_metrics = calc.get_dataset_metrics(db=session)
    recall_metrics = calc.get_recall_performance_metrics(db=session)
    quality_metrics = calc.get_data_quality_metrics(db=session)

# Row 1: Primary Recall Safety KPIs
st.subheader("🚨 Product Recall Containment Scorecard")
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card("Total Recalls Active", recall_metrics["total_recalls"], "Class I & Class II")
with c2:
    render_kpi_card("Affected Finished Lots", recall_metrics["total_affected_finished_lots"], "Traceable downstream")
with c3:
    render_kpi_card("Affected Customers", recall_metrics["total_affected_customers"], "Consignees identified")
with c4:
    render_kpi_card("Quarantined Stock (Units)", f"{recall_metrics['quantity_quarantined']:,.1f}", "Warehouse hold verified")

# Row 2: Regulatory Metrics & Performance
st.subheader("📈 Containment Effectiveness & Data Quality")
col_g1, col_g2, col_g3 = st.columns(3)
with col_g1:
    st.plotly_chart(plot_recall_gauge(recall_metrics["average_notification_coverage_pct"], "Notification Coverage (%)"), use_container_width=True)
with col_g2:
    st.plotly_chart(plot_recall_gauge(recall_metrics["average_recovery_rate_pct"], "Recovery Rate (%)"), use_container_width=True)
with col_g3:
    st.plotly_chart(plot_recall_gauge(recall_metrics["average_recall_completion_pct"], "Action Completion (%)"), use_container_width=True)

# Row 3: Supply Chain Dataset Volume
st.subheader("📦 Relational Dataset Footprint")
c_d1, c_d2, c_d3, c_d4, c_d5 = st.columns(5)
with c_d1:
    render_kpi_card("Suppliers", dataset_metrics["total_suppliers"])
with c_d2:
    render_kpi_card("Raw Material Lots", dataset_metrics["total_material_lots"])
with c_d3:
    render_kpi_card("Work Orders", dataset_metrics["total_production_orders"])
with c_d4:
    render_kpi_card("Finished Lots", dataset_metrics["total_finished_lots"])
with c_d5:
    render_kpi_card("Deliveries", dataset_metrics["total_deliveries"])

# Bar chart of dataset breakdown
df_volume = pd.DataFrame([
    {"Entity": "Suppliers", "Count": dataset_metrics["total_suppliers"]},
    {"Entity": "Raw Lots", "Count": dataset_metrics["total_material_lots"]},
    {"Entity": "Production Orders", "Count": dataset_metrics["total_production_orders"]},
    {"Entity": "Finished Lots", "Count": dataset_metrics["total_finished_lots"]},
    {"Entity": "Shipments", "Count": dataset_metrics["total_shipments"]},
    {"Entity": "Deliveries", "Count": dataset_metrics["total_deliveries"]},
    {"Entity": "Customers", "Count": dataset_metrics["total_customers"]},
])
st.plotly_chart(plot_bar_chart(df_volume, "Entity", "Count", "Total Operational Record Distribution"), use_container_width=True)
