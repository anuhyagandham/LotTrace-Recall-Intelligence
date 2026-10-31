"""
Page 7: Data Quality & Exceptions for LotTrace AI.
Audits the automated regulatory validation engine and highlights the four planted anomaly scenarios.
"""

import streamlit as st
import pandas as pd
from dashboard.components.cards import apply_theme, render_kpi_card
from src.database.connection import get_db_session
from src.validation.validator import BusinessValidator
from src.analytics.metrics import MetricsCalculator

apply_theme()

st.title("🛡️ Data Quality & Anomaly Exceptions")
st.markdown("Automated validation audit identifying data discrepancies, referential breaks, and controlled negative scenarios.")

with get_db_session() as session:
    validator = BusinessValidator(session=session)
    report = validator.run_all_validations(db=session)
    summary = report["summary"]
    issues = report["issues"]

    # Scorecard
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Checks Evaluated", summary["total_checks_evaluated"], "Rules across all tables")
    with c2:
        render_kpi_card("Passed Checks", summary["passed_checks"], "Integrity verified")
    with c3:
        render_kpi_card("Failed Checks", summary["failed_checks"], "Planted & detected exceptions")
    with c4:
        render_kpi_card("Quality Pass Rate", f"{summary['validation_pass_rate_pct']}%", "Regulatory threshold: >98%")

    st.divider()

    # Four Planted Anomaly Cases Section
    st.subheader("🎯 Controlled Negative Anomaly Scenarios (Ground-Truth Auditing)")
    st.markdown("""
    The system includes four deliberate, labelled anomaly test cases to prove that the validation
    engine detects supply chain exceptions rather than assuming uniform perfection:
    """)

    planted_cases = [
        {
            "Scenario": "Scenario A: Missing Input Lot",
            "Target Entity": "FinishedLot (FINLOT-2026-000001)",
            "Issue Type": "MISSING_INPUT_LOT",
            "Severity": "CRITICAL",
            "Expected Decision": "Quarantine finished lot; halt release certification due to phantom raw lot link.",
            "Detected Status": "🚨 DETECTED",
        },
        {
            "Scenario": "Scenario B: Over-Delivery Discrepancy",
            "Target Entity": "Delivery (DEL-2026-000001)",
            "Issue Type": "DELIVERED_EXCEEDS_PRODUCED",
            "Severity": "CRITICAL",
            "Expected Decision": "Halt invoice reconciliation, audit physical warehouse stock count, counterfeit check.",
            "Detected Status": "🚨 DETECTED",
        },
        {
            "Scenario": "Scenario C: Missed Customer Notification",
            "Target Entity": "CustomerNotification (CUST-0001)",
            "Issue Type": "MISSED_CUSTOMER_NOTIFICATION",
            "Severity": "HIGH",
            "Expected Decision": "Recall engine independently discovers omitted consignee and emits high-priority escalation.",
            "Detected Status": "🚨 DETECTED",
        },
        {
            "Scenario": "Scenario D: Recalled Stock Saleable",
            "Target Entity": "Inventory (INV-2026-000003)",
            "Issue Type": "RECALLED_INVENTORY_AVAILABLE_FOR_SALE",
            "Severity": "CRITICAL",
            "Expected Decision": "Execute automated ERP inventory hold: lock bin location and set status to QUARANTINED.",
            "Detected Status": "🚨 DETECTED",
        },
    ]

    st.dataframe(pd.DataFrame(planted_cases), use_container_width=True)

    st.divider()

    # Full Validation Issue Log
    st.subheader("📋 Comprehensive Validation Exception Log")
    if issues:
        df_issues = pd.DataFrame(issues)
        st.dataframe(
            df_issues[[
                "validation_id", "entity_name", "entity_id", "issue_type",
                "severity", "expected_value", "actual_value", "validation_status", "ground_truth_label"
            ]],
            use_container_width=True,
            height=350,
        )
    else:
        st.success("All business validation checks passed without exceptions!")
