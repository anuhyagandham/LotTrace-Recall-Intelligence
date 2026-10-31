"""
Page 6: Genealogy Explorer for LotTrace AI.
Interactive multi-echelon network visualization of upstream and downstream supply chain links.
"""

import streamlit as st
import pandas as pd
from dashboard.components.cards import apply_theme, render_kpi_card
from dashboard.components.charts import plot_genealogy_sankey
from src.database.connection import get_db_session
from src.models import MaterialLot, FinishedLot
from src.genealogy.traversal import GenealogyService

apply_theme()

st.title("🕸️ Interactive Genealogy Explorer")
st.markdown("Traverse complete upstream formulation trees or downstream distribution networks with automated contamination path tracing.")

with get_db_session() as session:
    service = GenealogyService(session=session)

    direction = st.radio("Select Traceability Traversal Direction", ["Downstream (Raw Material Lot → Finished Lots → Shipments → Customers)", "Upstream (Finished Lot → Work Order → Consumed Materials → Suppliers)"])

    if "Downstream" in direction:
        raw_lots = session.query(MaterialLot).all()
        lot_labels = [f"{l.lot_id} — {l.material_name} ({'CONTAMINATED' if l.is_contaminated else 'NORMAL'})" for l in raw_lots]
        selected_label = st.selectbox("Select Root Raw Material Lot", lot_labels)
        selected_lot_id = selected_label.split(" — ")[0]

        genealogy = service.get_downstream_genealogy(selected_lot_id, db=session)

        # Overview Scorecard
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi_card("Affected Work Orders", genealogy["total_affected_production_orders"])
        with c2:
            render_kpi_card("Affected Finished Lots", genealogy["total_affected_finished_lots"])
        with c3:
            render_kpi_card("Affected Shipments", genealogy["total_affected_shipments"])
        with c4:
            render_kpi_card("Affected Customers", genealogy["total_affected_customers"])

        # Sankey Flow Visualization
        st.subheader("Downstream Flow Network")
        st.plotly_chart(plot_genealogy_sankey(genealogy["graph"]), use_container_width=True)

        # Detailed Tables
        t_fin, t_cust = st.tabs(["Downstream Finished Lots", "Affected Healthcare Customers"])
        with t_fin:
            if genealogy["affected_finished_lots"]:
                st.dataframe(pd.DataFrame(genealogy["affected_finished_lots"]), use_container_width=True)
            else:
                st.info("No downstream finished lots traced.")
        with t_cust:
            if genealogy["affected_customers"]:
                st.dataframe(pd.DataFrame(genealogy["affected_customers"]), use_container_width=True)
            else:
                st.info("No downstream customers impacted.")

    else:
        fin_lots = session.query(FinishedLot).all()
        fin_labels = [f"{f.lot_id} — {f.product.product_name if f.product else ''} ({'CONTAMINATED' if f.is_contaminated else 'NORMAL'})" for f in fin_lots]
        selected_fin_label = st.selectbox("Select Root Finished Lot", fin_labels)
        selected_fin_lot_id = selected_fin_label.split(" — ")[0]

        upstream = service.get_upstream_genealogy(selected_fin_lot_id, db=session)

        c1, c2, c3 = st.columns(3)
        with c1:
            render_kpi_card("Production Work Order", upstream.get("production_order_id", "N/A"))
        with c2:
            render_kpi_card("Consumed Raw Lots", upstream.get("total_consumed_raw_lots", 0))
        with c3:
            render_kpi_card("Master Suppliers", upstream.get("total_suppliers", 0))

        st.subheader("Upstream Supply Flow Network")
        st.plotly_chart(plot_genealogy_sankey(upstream["graph"]), use_container_width=True)

        t_mat, t_sup = st.tabs(["Consumed Raw Materials", "Vendor Master Details"])
        with t_mat:
            if upstream.get("consumed_materials"):
                st.dataframe(pd.DataFrame(upstream["consumed_materials"]), use_container_width=True)
        with t_sup:
            if upstream.get("suppliers"):
                st.dataframe(pd.DataFrame(upstream["suppliers"]), use_container_width=True)
