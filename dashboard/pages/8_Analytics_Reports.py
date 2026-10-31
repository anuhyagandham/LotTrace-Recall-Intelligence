"""
Page 8: Analytics & Reports for LotTrace AI.
Executive charts, supplier risk distributions, and exportable regulatory audit packages.
"""

import streamlit as st
import pandas as pd
from dashboard.components.cards import apply_theme, render_kpi_card
from dashboard.components.charts import plot_bar_chart
from src.database.connection import get_db_session
from src.models import Supplier, Product, RecallCase, MaterialLot
from src.analytics.metrics import MetricsCalculator
from config import CSV_EXPORT_DIR

apply_theme()

st.title("📊 Supply Chain Analytics & Exportable Reports")
st.markdown("Macro-level supply chain risk distributions, product recall velocity, and downloadable audit packages.")

with get_db_session() as session:
    calc = MetricsCalculator(session=session)
    recall_metrics = calc.get_recall_performance_metrics(db=session)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏢 Supplier Material Category Distribution")
        suppliers = session.query(Supplier).all()
        df_sup = pd.DataFrame([s.to_dict() for s in suppliers])
        if not df_sup.empty:
            cat_counts = df_sup["category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            st.plotly_chart(plot_bar_chart(cat_counts, "Category", "Count", "Approved Suppliers by Category"), use_container_width=True)

    with col2:
        st.subheader("📦 Product Category Portfolio")
        products = session.query(Product).all()
        df_prod = pd.DataFrame([p.to_dict() for p in products])
        if not df_prod.empty:
            p_counts = df_prod["category"].value_counts().reset_index()
            p_counts.columns = ["Category", "Count"]
            st.plotly_chart(plot_bar_chart(p_counts, "Category", "Count", "Product Catalog by Category"), use_container_width=True)

    st.divider()

    # Downloadable CSV Audit Reports Section
    st.subheader("📥 Downloadable Regulatory & Audit Data Files")
    st.markdown("Export operational datasets directly for FDA / GxP / supply chain auditing:")

    c_dl1, c_dl2, c_dl3, c_dl4 = st.columns(4)

    def get_csv_bytes(table_name: str) -> bytes:
        p = CSV_EXPORT_DIR / f"{table_name}.csv"
        if p.exists():
            with open(p, "rb") as f:
                return f.read()
        return b""

    with c_dl1:
        st.download_button(
            label="📄 Material Lots CSV",
            data=get_csv_bytes("material_lots"),
            file_name="material_lots.csv",
            mime="text/csv",
        )
    with c_dl2:
        st.download_button(
            label="📄 Finished Lots CSV",
            data=get_csv_bytes("finished_lots"),
            file_name="finished_lots.csv",
            mime="text/csv",
        )
    with c_dl3:
        st.download_button(
            label="📄 Recall Cases CSV",
            data=get_csv_bytes("recall_cases"),
            file_name="recall_cases.csv",
            mime="text/csv",
        )
    with c_dl4:
        st.download_button(
            label="📄 Validation Issues CSV",
            data=get_csv_bytes("validation_issues"),
            file_name="validation_issues.csv",
            mime="text/csv",
        )
