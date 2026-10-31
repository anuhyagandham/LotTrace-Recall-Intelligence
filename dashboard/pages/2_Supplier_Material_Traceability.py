"""
Page 2: Supplier & Material Traceability for LotTrace AI.
"""

import streamlit as st
import pandas as pd
from dashboard.components.cards import apply_theme, render_kpi_card
from src.database.connection import get_db_session
from src.models import Supplier, MaterialLot, ProductionConsumption

apply_theme()

st.title("🏭 Supplier & Raw Material Traceability")
st.markdown("Inspect approved vendor master records, received raw material batches, and consumption histories.")

with get_db_session() as session:
    tab1, tab2 = st.tabs(["🧪 Raw Material Lots", "🏢 Approved Suppliers"])

    with tab1:
        st.subheader("Raw Material Batch Search & Status Audit")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            cat_filter = st.selectbox("Filter Material Category", ["ALL"] + [c[0] for c in session.query(MaterialLot.material_category).distinct().all()])
        with col_f2:
            status_filter = st.selectbox("Quality Status", ["ALL", "RELEASED", "CONTAMINATED", "QUARANTINED"])
        with col_f3:
            lot_search = st.text_input("Search Lot ID / Material Name", "")

        q = session.query(MaterialLot)
        if cat_filter != "ALL":
            q = q.filter(MaterialLot.material_category == cat_filter)
        if status_filter != "ALL":
            q = q.filter(MaterialLot.quality_status == status_filter)
        if lot_search:
            q = q.filter(MaterialLot.lot_id.ilike(f"%{lot_search}%") | MaterialLot.material_name.ilike(f"%{lot_search}%"))

        lots = q.limit(200).all()
        lots_data = [l.to_dict() for l in lots]

        if lots_data:
            df_lots = pd.DataFrame(lots_data)
            st.dataframe(
                df_lots[[
                    "lot_id", "material_name", "material_category", "supplier_id",
                    "initial_quantity", "current_quantity", "unit_of_measure",
                    "unit_cost", "quality_status", "is_contaminated", "received_date", "expiry_date"
                ]],
                use_container_width=True,
                height=350,
            )

            st.divider()
            selected_lot_id = st.selectbox("Select Lot for Consumption Drilldown", df_lots["lot_id"].tolist())
            if selected_lot_id:
                consumptions = session.query(ProductionConsumption).filter(
                    ProductionConsumption.material_lot_id == selected_lot_id
                ).all()

                st.markdown(f"#### ⚙️ Work Orders Consuming Lot `{selected_lot_id}`")
                if consumptions:
                    cons_data = [c.to_dict() for c in consumptions]
                    st.dataframe(pd.DataFrame(cons_data), use_container_width=True)
                else:
                    st.info("This lot has not yet been consumed in any production work orders.")
        else:
            st.warning("No material lots match the selected filter criteria.")

    with tab2:
        st.subheader("Approved Suppliers Catalog")
        suppliers = session.query(Supplier).all()
        df_sup = pd.DataFrame([s.to_dict() for s in suppliers])
        st.dataframe(
            df_sup[["supplier_id", "supplier_code", "name", "category", "country", "contact_email", "status"]],
            use_container_width=True,
            height=400,
        )
