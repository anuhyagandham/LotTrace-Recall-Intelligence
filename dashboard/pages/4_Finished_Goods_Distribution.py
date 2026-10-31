"""
Page 4: Finished Goods & Distribution for LotTrace AI.
"""

import streamlit as st
import pandas as pd
from dashboard.components.cards import apply_theme, render_kpi_card
from src.database.connection import get_db_session
from src.models import FinishedLot, Shipment, ShipmentItem, Delivery, Inventory

apply_theme()

st.title("🚚 Finished Goods & Outbound Distribution")
st.markdown("Audit finished product batches, warehouse inventory allocations, carrier freight movements, and customer delivery records.")

with get_db_session() as session:
    tab1, tab2, tab3 = st.tabs(["📦 Finished Lots", "🚛 Freight Shipments", "🏥 Customer Deliveries"])

    with tab1:
        st.subheader("Finished Goods Batch Catalog")
        fin_lots = session.query(FinishedLot).limit(100).all()
        df_fin = pd.DataFrame([f.to_dict() for f in fin_lots])
        if not df_fin.empty:
            st.dataframe(
                df_fin[[
                    "lot_id", "product_name", "quantity_produced", "quantity_available",
                    "unit_of_measure", "quality_status", "is_contaminated", "manufactured_date", "expiry_date"
                ]],
                use_container_width=True,
                height=350,
            )

    with tab2:
        st.subheader("Outbound Freight Shipments")
        shipments = session.query(Shipment).limit(100).all()
        df_shp = pd.DataFrame([s.to_dict() for s in shipments])
        if not df_shp.empty:
            st.dataframe(
                df_shp[["shipment_id", "tracking_number", "carrier", "status", "origin_warehouse", "destination_region", "ship_date"]],
                use_container_width=True,
                height=350,
            )

    with tab3:
        st.subheader("Customer Consignee Deliveries")
        deliveries = session.query(Delivery).limit(100).all()
        df_del = pd.DataFrame([d.to_dict() for d in deliveries])
        if not df_del.empty:
            st.dataframe(
                df_del[["delivery_id", "shipment_id", "customer_name", "quantity_delivered", "status", "received_by", "delivery_date"]],
                use_container_width=True,
                height=350,
            )
