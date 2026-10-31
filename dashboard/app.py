"""
Main Streamlit Application for LotTrace AI.
End-to-End Supply Chain Traceability & Intelligent Product Recall Management System.
"""

import streamlit as st
from dashboard.components.cards import apply_theme, render_kpi_card
from src.database.connection import get_db_session
from src.analytics.metrics import MetricsCalculator

st.set_page_config(
    page_title="LotTrace AI — Enterprise Traceability & Recall",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()

st.title("🛡️ LotTrace AI")
st.subheader("End-to-End Supply Chain Traceability & Intelligent Product Recall Intelligence")

st.markdown("""
Welcome to **LotTrace AI**, a mission-critical platform designed to trace pharmaceutical and manufacturing lots
across suppliers, production orders, finished goods, freight shipments, and healthcare consignees.

### 📌 System Navigation & Capabilities
Use the left sidebar to navigate across dedicated operational consoles:
- **1. Executive Overview:** Enterprise KPI scorecard, active recalls, notification coverage, and recovery rates.
- **2. Supplier & Material Traceability:** Upstream supplier audits, material lot catalog, and contamination status.
- **3. Production Genealogy:** Manufacturing work orders, active BOM formulations, and yield reconciliation.
- **4. Finished Goods & Distribution:** Batch inventory, outbound freight shipments, and customer delivery logs.
- **5. Recall Management:** Interactive recall initiation docket, downstream impact calculator, and containment execution.
- **6. Genealogy Explorer:** Interactive multi-echelon network graph of upstream and downstream lot links.
- **7. Data Quality & Exceptions:** Automated regulatory validation engine, reconciliation exceptions, and 4 planted anomaly scenarios.
- **8. Analytics & Reports:** Executive analytics, supplier risk ranking, and downloadable audit datasets.
""")

st.divider()

# Quick Operational Health Check
with get_db_session() as session:
    calc = MetricsCalculator(session=session)
    dataset_metrics = calc.get_dataset_metrics()
    recall_metrics = calc.get_recall_performance_metrics()
    quality_metrics = calc.get_data_quality_metrics()

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card("Active Recalls", recall_metrics["total_recalls"], "Target: 100% Containment")
with c2:
    render_kpi_card("Notification Coverage", f"{recall_metrics['average_notification_coverage_pct']}%", "Regulatory Benchmark: >95%")
with c3:
    render_kpi_card("Field Recovery Rate", f"{recall_metrics['average_recovery_rate_pct']}%", "Reverse Logistics")
with c4:
    render_kpi_card("Data Quality Pass Rate", f"{quality_metrics['overall_validation_pass_rate_pct']}%", f"{quality_metrics['failed_checks']} Planted Exceptions")

st.info("💡 **Interview Walkthrough Tip:** Begin in *Executive Overview* to understand total system volume and safety scores, proceed to *Recall Management* to simulate containment, and inspect *Data Quality & Exceptions* to review the 4 controlled anomaly cases.")
