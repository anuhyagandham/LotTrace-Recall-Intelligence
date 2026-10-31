"""
Page 3: Production Genealogy for LotTrace AI.
"""

import streamlit as st
import pandas as pd
from dashboard.components.cards import apply_theme, render_kpi_card
from src.database.connection import get_db_session
from src.models import ProductionOrder, FinishedLot, BOM, ProductionConsumption
from src.validation.reconciliation import QuantityReconciler

apply_theme()

st.title("⚙️ Manufacturing Production Genealogy")
st.markdown("Track shop-floor work orders, bill-of-materials formulations, material consumption, and yield reconciliations.")

with get_db_session() as session:
    orders = session.query(ProductionOrder).order_by(ProductionOrder.order_id).limit(100).all()
    order_ids = [o.order_id for o in orders]

    selected_order_id = st.selectbox("Select Production Work Order", order_ids)

    if selected_order_id:
        order = session.query(ProductionOrder).filter(ProductionOrder.order_id == selected_order_id).first()
        recon = QuantityReconciler.reconcile_production_order(order)

        # Work Order Overview Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi_card("Planned Quantity", f"{order.planned_quantity:,.1f}", "Target batch volume")
        with c2:
            render_kpi_card("Produced Output", f"{order.produced_quantity:,.1f}", "Actual yield")
        with c3:
            yield_pct = round((order.produced_quantity / order.planned_quantity) * 100, 2) if order.planned_quantity > 0 else 0.0
            render_kpi_card("Production Yield", f"{yield_pct}%", f"Scrap: {order.scrap_quantity}")
        with c4:
            render_kpi_card("Reconciliation Status", "RECONCILED" if recon["is_reconciled"] else "DISCREPANCY", f"Variance: {recon['variance']}")

        st.divider()

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("📥 Input Raw Material Consumption")
            consumptions = session.query(ProductionConsumption).filter(
                ProductionConsumption.production_order_id == selected_order_id
            ).all()

            if consumptions:
                df_cons = pd.DataFrame([
                    {
                        "Lot ID": c.material_lot_id,
                        "Category": c.material_lot.material_category if c.material_lot else "N/A",
                        "Material Name": c.material_lot.material_name if c.material_lot else "N/A",
                        "Consumed Qty": c.quantity_consumed,
                        "UOM": c.unit_of_measure,
                        "Contaminated?": "⚠️ YES" if (c.material_lot and c.material_lot.is_contaminated) else "✅ No",
                    }
                    for c in consumptions
                ])
                st.dataframe(df_cons, use_container_width=True)
            else:
                st.info("No raw material consumptions recorded.")

        with col_right:
            st.subheader("📤 Output Finished Lots Produced")
            fin_lots = session.query(FinishedLot).filter(
                FinishedLot.production_order_id == selected_order_id
            ).all()

            if fin_lots:
                df_fin = pd.DataFrame([
                    {
                        "Finished Lot ID": f.lot_id,
                        "Product": f.product.product_name if f.product else "N/A",
                        "Qty Produced": f.quantity_produced,
                        "Qty Available": f.quantity_available,
                        "UOM": f.unit_of_measure,
                        "Quality Status": f.quality_status,
                        "Contaminated?": "⚠️ YES" if f.is_contaminated else "✅ No",
                    }
                    for f in fin_lots
                ])
                st.dataframe(df_fin, use_container_width=True)
            else:
                st.info("No finished lots generated for this work order.")

        # BOM Details
        st.divider()
        st.subheader("📋 Active Formulation Specification (BOM)")
        bom = order.bom
        if bom:
            st.markdown(f"**BOM ID:** `{bom.bom_id}` | **Version:** `{bom.version}` | **Expected Yield:** `{bom.yield_percentage}%` | **Effective From:** `{bom.effective_from}`")
            mat_specs = [m.to_dict() for m in bom.materials]
            st.dataframe(pd.DataFrame(mat_specs), use_container_width=True)
