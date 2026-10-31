"""
Page 5: Recall Management Console for LotTrace AI.
Interactive product safety recall initiation, downstream scope traversal, and containment execution.
"""

import streamlit as st
import pandas as pd
from dashboard.components.cards import apply_theme, render_kpi_card
from dashboard.components.charts import plot_recall_gauge
from src.database.connection import get_db_session
from src.models import RecallCase, MaterialLot, FinishedLot, RecallAction, CustomerNotification, RecallEvent
from src.recall.engine import RecallEngine
from src.genealogy.traversal import GenealogyService

apply_theme()

st.title("🚨 Product Recall Management Console")
st.markdown("Initiate new product recall dockets, traverse downstream affected scope, dispatch customer notices, and monitor field containment.")

with get_db_session() as session:
    engine = RecallEngine(session=session)
    genealogy_service = GenealogyService(session=session)

    tab_active, tab_create = st.tabs(["📋 Active Recall Dossiers", "➕ Initiate New Recall"])

    # -------------------------------------------------------------
    # Tab 1: Active Recall Cases & Processing
    # -------------------------------------------------------------
    with tab_active:
        recalls = session.query(RecallCase).all()
        if recalls:
            recall_options = {f"{r.recall_id} — {r.title} ({r.status})": r.recall_id for r in recalls}
            selected_label = st.selectbox("Select Recall Case for Operational Review", list(recall_options.keys()))
            selected_recall_id = recall_options[selected_label]

            recall = session.query(RecallCase).filter(RecallCase.recall_id == selected_recall_id).first()

            # KPI Scorecard for this recall
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                render_kpi_card("Current Status", recall.status, f"Severity: {recall.severity}")
            with c2:
                render_kpi_card("Notification Coverage", f"{recall.notification_coverage_pct}%", f"Customers: {recall.total_affected_customers}")
            with c3:
                render_kpi_card("Recovery Rate", f"{recall.recovery_rate_pct}%", f"Recovered: {recall.total_recovered_quantity:,.1f}")
            with c4:
                render_kpi_card("Recall Completion", f"{recall.recall_completion_pct}%", f"Actions: {len(recall.actions)}")

            # Process Button
            st.divider()
            col_b1, col_b2 = st.columns([1, 3])
            with col_b1:
                if st.button("🚀 Process / Re-Process Containment", key="btn_proc"):
                    with st.spinner("Executing downstream traversal, warehouse quarantine, and customer notices..."):
                        res = engine.process_recall(selected_recall_id, db=session)
                        st.success(f"Recall {selected_recall_id} processed successfully! Status: {res['status']}")
                        st.rerun()

            with col_b2:
                st.info("ℹ️ Processing executes idempotent multi-echelon containment: holds warehouse stock, issues notices to 100% of affected customers, and tallies return logistics.")

            # Gauge & Scope breakdown
            st.subheader("Containment Progress")
            g1, g2 = st.columns(2)
            with g1:
                st.plotly_chart(plot_recall_gauge(recall.notification_coverage_pct, "Customer Notification Coverage (%)"), use_container_width=True)
            with g2:
                st.plotly_chart(plot_recall_gauge(recall.recovery_rate_pct, "Field Stock Recovery Rate (%)"), use_container_width=True)

            # Details: Actions, Notifications, and Events
            t_act, t_notif, t_evt = st.tabs(["Operational Actions", "Customer Notifications", "Audit Event Ledger"])

            with t_act:
                actions = session.query(RecallAction).filter(RecallAction.recall_id == selected_recall_id).all()
                if actions:
                    df_act = pd.DataFrame([a.to_dict() for a in actions])
                    st.dataframe(df_act[["action_id", "action_type", "target_entity_type", "target_entity_id", "status", "assigned_to", "completed_date"]], use_container_width=True)
                else:
                    st.info("No operational actions registered yet. Click 'Process / Re-Process Containment' above.")

            with t_notif:
                notifs = session.query(CustomerNotification).filter(CustomerNotification.recall_id == selected_recall_id).all()
                if notifs:
                    df_not = pd.DataFrame([n.to_dict() for n in notifs])
                    st.dataframe(df_not[["notification_id", "customer_id", "customer_name", "notification_channel", "notification_status", "sent_at", "acknowledged_at"]], use_container_width=True)
                else:
                    st.info("No customer notifications dispatched yet.")

            with t_evt:
                events = session.query(RecallEvent).filter(RecallEvent.recall_id == selected_recall_id).order_by(RecallEvent.created_at).all()
                if events:
                    df_evt = pd.DataFrame([e.to_dict() for e in events])
                    st.dataframe(df_evt[["event_id", "previous_status", "new_status", "reason", "trigger_source", "created_at"]], use_container_width=True)
        else:
            st.info("No active recall cases found.")

    # -------------------------------------------------------------
    # Tab 2: Create a New Recall Case
    # -------------------------------------------------------------
    with tab_create:
        st.subheader("Initiate Product Recall Docket")
        with st.form("create_recall_form"):
            trigger_choice = st.radio("Trigger Source Type", ["Contaminated Raw Material Lot", "Contaminated Finished Product Lot"])

            if "Raw" in trigger_choice:
                raw_lots = session.query(MaterialLot).all()
                lot_opts = [f"{l.lot_id} — {l.material_name}" for l in raw_lots]
                selected_lot_str = st.selectbox("Select Contaminated Raw Material Lot", lot_opts)
                source_lot_id = selected_lot_str.split(" — ")[0]
                trigger_type = "CONTAMINATED_RAW_LOT"
            else:
                fin_lots = session.query(FinishedLot).all()
                lot_opts = [f"{l.lot_id} — {l.product.product_name if l.product else ''}" for l in fin_lots]
                selected_lot_str = st.selectbox("Select Contaminated Finished Lot", lot_opts)
                source_lot_id = selected_lot_str.split(" — ")[0]
                trigger_type = "CONTAMINATED_FINISHED_LOT"

            title_input = st.text_input("Recall Investigation Title", f"Safety Incident Docket for {source_lot_id}")
            severity_input = st.selectbox("FDA Hazard Classification", ["CLASS_I", "CLASS_II", "CLASS_III"])
            target_days_input = st.slider("Target Containment Window (Days)", 7, 60, 30)

            submitted = st.form_submit_button("🚨 Launch Recall Docket")
            if submitted:
                try:
                    res = engine.create_recall(
                        source_lot_id=source_lot_id,
                        title=title_input,
                        trigger_type=trigger_type,
                        severity=severity_input,
                        target_days=target_days_input,
                        db=session,
                    )
                    st.success(f"Recall docket {res['recall_id']} created! Affected finished lots: {res['recall']['total_affected_finished_lots']}, Affected customers: {res['recall']['total_affected_customers']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create recall: {e}")
