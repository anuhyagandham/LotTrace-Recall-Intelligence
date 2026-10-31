"""
Audit Script for Tasks 3, 4, and 7:
- Task 3: Recall Workflows (Raw Material Recall & Finished Product Lot Recall)
- Task 4: Four Negative Scenarios (Planted Anomalies & Validation Detection)
- Task 7: Flask API Endpoints Verification
"""

import sys
import time
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.database.connection import get_db_session
from src.models import (
    RecallCase, RecallAction, RecallEvent, CustomerNotification,
    Inventory, MaterialLot, FinishedLot, ValidationIssue, Delivery
)
from src.recall.engine import RecallEngine
from src.validation.validator import BusinessValidator
from src.genealogy.traversal import GenealogyService
from app import create_app


def task3_audit_recalls():
    print("=" * 80)
    print("TASK 3: RECALL FUNCTIONALITY AUDIT")
    print("=" * 80)
    
    engine = RecallEngine()
    
    # -------------------------------------------------------------
    # Workflow 1: Contaminated Raw Material Recall
    # -------------------------------------------------------------
    print("\n--- Workflow 1: Contaminated Raw Material Recall ---")
    with get_db_session() as session:
        # Find raw material recall case (e.g. RC-2026-000001)
        raw_recall = session.query(RecallCase).filter(RecallCase.trigger_type == "CONTAMINATED_RAW_LOT").first()
        assert raw_recall is not None, "Raw material recall case not found"
        raw_recall_id = raw_recall.recall_id
        source_raw_lot = raw_recall.source_lot_id
        print(f"  Selected Case: {raw_recall_id} | Source Raw Lot: {source_raw_lot}")
        
    t0 = time.time()
    res1 = engine.process_recall(raw_recall_id)
    t_raw = time.time() - t0
    
    print(f"  Processed in {t_raw:.3f}s: Status = {res1['status']}")
    print(f"    Affected Finished Lots : {res1['metrics']['total_affected_finished_lots']}")
    print(f"    Affected Customers     : {res1['metrics']['total_affected_customers']}")
    print(f"    Recalled Quantity      : {res1['metrics']['total_recalled_quantity']}")
    print(f"    Quarantined Quantity   : {res1['metrics']['total_quarantined_quantity']}")
    print(f"    Recovered Quantity     : {res1['metrics']['total_recovered_quantity']}")
    print(f"    Notification Coverage  : {res1['metrics']['notification_coverage_pct']}%")
    print(f"    Recovery Rate          : {res1['metrics']['recovery_rate_pct']}%")
    print(f"    Recall Completion      : {res1['metrics']['recall_completion_pct']}%")
    print(f"    Actions Executed       : {res1['actions_count']}")
    
    # Test Idempotency for Workflow 1
    print("  Testing idempotency on second execution...")
    with get_db_session() as session:
        actions_count_before = session.query(RecallAction).filter(RecallAction.recall_id == raw_recall_id).count()
        notifs_count_before = session.query(CustomerNotification).filter(CustomerNotification.recall_id == raw_recall_id).count()
        
    res1_repeat = engine.process_recall(raw_recall_id)
    
    with get_db_session() as session:
        actions_count_after = session.query(RecallAction).filter(RecallAction.recall_id == raw_recall_id).count()
        notifs_count_after = session.query(CustomerNotification).filter(CustomerNotification.recall_id == raw_recall_id).count()
        
    print(f"    Actions before: {actions_count_before}, after: {actions_count_after} (Diff: {actions_count_after - actions_count_before})")
    print(f"    Notifs before : {notifs_count_before}, after: {notifs_count_after} (Diff: {notifs_count_after - notifs_count_before})")
    assert actions_count_before == actions_count_after, "Actions duplicated on rerun!"
    assert notifs_count_before == notifs_count_after, "Notifications duplicated on rerun!"
    print("    [PASS] Workflow 1 is 100% idempotent.")
    
    # -------------------------------------------------------------
    # Workflow 2: Contaminated Finished Product Lot Recall
    # -------------------------------------------------------------
    print("\n--- Workflow 2: Contaminated Finished Product Lot Recall ---")
    with get_db_session() as session:
        fin_recall = session.query(RecallCase).filter(RecallCase.trigger_type == "CONTAMINATED_FINISHED_LOT").first()
        assert fin_recall is not None, "Finished product recall case not found"
        fin_recall_id = fin_recall.recall_id
        source_fin_lot = fin_recall.source_lot_id
        print(f"  Selected Case: {fin_recall_id} | Source Finished Lot: {source_fin_lot}")
        
    t0 = time.time()
    res2 = engine.process_recall(fin_recall_id)
    t_fin = time.time() - t0
    
    print(f"  Processed in {t_fin:.3f}s: Status = {res2['status']}")
    print(f"    Affected Finished Lots : {res2['metrics']['total_affected_finished_lots']}")
    print(f"    Affected Customers     : {res2['metrics']['total_affected_customers']}")
    print(f"    Recalled Quantity      : {res2['metrics']['total_recalled_quantity']}")
    print(f"    Quarantined Quantity   : {res2['metrics']['total_quarantined_quantity']}")
    print(f"    Recovered Quantity     : {res2['metrics']['total_recovered_quantity']}")
    print(f"    Notification Coverage  : {res2['metrics']['notification_coverage_pct']}%")
    print(f"    Recovery Rate          : {res2['metrics']['recovery_rate_pct']}%")
    print(f"    Recall Completion      : {res2['metrics']['recall_completion_pct']}%")
    print(f"    Actions Executed       : {res2['actions_count']}")
    
    # Test Idempotency for Workflow 2
    print("  Testing idempotency on second execution...")
    with get_db_session() as session:
        actions_count_before = session.query(RecallAction).filter(RecallAction.recall_id == fin_recall_id).count()
        notifs_count_before = session.query(CustomerNotification).filter(CustomerNotification.recall_id == fin_recall_id).count()
        
    res2_repeat = engine.process_recall(fin_recall_id)
    
    with get_db_session() as session:
        actions_count_after = session.query(RecallAction).filter(RecallAction.recall_id == fin_recall_id).count()
        notifs_count_after = session.query(CustomerNotification).filter(CustomerNotification.recall_id == fin_recall_id).count()
        
    print(f"    Actions before: {actions_count_before}, after: {actions_count_after} (Diff: {actions_count_after - actions_count_before})")
    print(f"    Notifs before : {notifs_count_before}, after: {notifs_count_after} (Diff: {notifs_count_after - notifs_count_before})")
    assert actions_count_before == actions_count_after, "Actions duplicated on rerun!"
    assert notifs_count_before == notifs_count_after, "Notifications duplicated on rerun!"
    print("    [PASS] Workflow 2 is 100% idempotent.")
    
    return {
        "raw_recall": res1,
        "raw_time": t_raw,
        "fin_recall": res2,
        "fin_time": t_fin
    }


def task4_audit_four_negative_scenarios():
    print("\n" + "=" * 80)
    print("TASK 4: FOUR NEGATIVE SCENARIOS AUDIT")
    print("=" * 80)
    
    scenarios = [
        ("A", "MISSING_INPUT_LOT", "ANOMALY_A_MISSING_INPUT_LOT"),
        ("B", "DELIVERED_EXCEEDS_PRODUCED", "ANOMALY_B_DELIVERY_EXCEEDS_PRODUCED"),
        ("C", "MISSED_CUSTOMER_NOTIFICATION", "ANOMALY_C_MISSED_CUSTOMER_NOTIFICATION"),
        ("D", "RECALLED_INVENTORY_AVAILABLE_FOR_SALE", "ANOMALY_D_RECALLED_STOCK_SALEABLE"),
    ]
    
    with get_db_session() as session:
        for letter, issue_type, label in scenarios:
            print(f"\n--- Scenario {letter}: {issue_type} ---")
            issues = session.query(ValidationIssue).filter(
                (ValidationIssue.issue_type == issue_type) |
                (ValidationIssue.ground_truth_label == label)
            ).all()
            
            print(f"  Detected instances in validation log: {len(issues)}")
            assert len(issues) > 0, f"Anomaly {issue_type} was not detected!"
            for iss in issues:
                print(f"    Entity: {iss.entity_name} ({iss.entity_id}) | Severity: {iss.severity} | Status: {iss.validation_status}")
                print(f"    Expected: {iss.expected_value}")
                print(f"    Actual  : {iss.actual_value}")
                print(f"    Ground Truth Label: {iss.ground_truth_label}")
                
    # Verify Ground Truth Isolation
    print("\n--- Ground Truth Isolation Audit ---")
    validator_code = (BASE_DIR / "src" / "validation" / "validator.py").read_text(encoding="utf-8")
    recall_code = (BASE_DIR / "src" / "recall" / "engine.py").read_text(encoding="utf-8")
    
    has_gt_leak_val = any(term in validator_code for term in ["ground_truth.json", "ground_truth.csv", "data/ground_truth", "data\\ground_truth"])
    has_gt_leak_rec = any(term in recall_code for term in ["ground_truth.json", "ground_truth.csv", "data/ground_truth", "data\\ground_truth"])
    
    print(f"  Validator opens/reads ground_truth files: {has_gt_leak_val}")
    print(f"  Recall engine opens/reads ground_truth files: {has_gt_leak_rec}")
    assert not has_gt_leak_val, "Validator reads ground truth files!"
    assert not has_gt_leak_rec, "Recall engine reads ground truth files!"
    print("  [PASS] Zero operational leakage from ground-truth data.")
    return True


def task7_audit_flask_endpoints():
    print("\n" + "=" * 80)
    print("TASK 7: FLASK API ENDPOINT VERIFICATION")
    print("=" * 80)
    
    flask_app = create_app()
    client = flask_app.test_client()
    
    endpoints = [
        ("GET", "/health", "Health / Status Check (Root)"),
        ("GET", "/api/health", "Health / Status Check (API)"),
        ("GET", "/api/dashboard/summary", "Executive Dashboard Summary"),
        ("GET", "/api/suppliers", "Master Suppliers List"),
        ("GET", "/api/material-lots", "Material Lots List"),
        ("GET", "/api/finished-lots", "Finished Lots List"),
        ("GET", "/api/production-orders", "Production Work Orders"),
        ("GET", "/api/shipments", "Outbound Shipments List"),
        ("GET", "/api/customers", "Customer Consignees List"),
        ("GET", "/api/recalls", "Recall Cases List"),
        ("GET", "/api/material-lots/RAWLOT-SUP-0001-2026-000001/genealogy", "Downstream Genealogy"),
        ("GET", "/api/finished-lots/FINLOT-2026-000001/genealogy", "Upstream Genealogy"),
        ("GET", "/api/validation/report", "Complete Validation Report"),
        ("GET", "/api/analytics/recall-performance", "Recall Performance Analytics"),
        ("GET", "/api/exports/manifest", "Export Manifest & Checksums"),
    ]
    
    all_passed = True
    for method, path, desc in endpoints:
        t0 = time.time()
        if method == "GET":
            resp = client.get(path)
        elapsed = time.time() - t0
        
        status_ok = resp.status_code == 200
        status_str = f"HTTP {resp.status_code}"
        badge = "PASS" if status_ok else "FAIL"
        print(f"  {method:<4} {path:<48} : {status_str} in {elapsed*1000:>6.1f}ms [{badge}] ({desc})")
        if not status_ok:
            all_passed = False
            
    with get_db_session() as session:
        test_raw_lot = session.query(MaterialLot).offset(5).first().lot_id

    # Test POST recall creation and processing endpoint
    print("\n  Testing POST /api/v1/recalls (Create Recall Docket)...")
    post_payload = {
        "source_lot_id": test_raw_lot,
        "title": "Audit Verification Recall: Raw Lot Chemical Purity",
        "trigger_type": "CONTAMINATED_RAW_LOT",
        "severity": "CLASS_I"
    }
    t0 = time.time()
    post_resp = client.post("/api/v1/recalls", json=post_payload)
    elapsed = time.time() - t0
    print(f"  POST /api/v1/recalls                           : HTTP {post_resp.status_code} in {elapsed*1000:.1f}ms [{'PASS' if post_resp.status_code == 201 else 'FAIL'}]")
    if post_resp.status_code == 201:
        new_recall_id = post_resp.get_json().get("recall_id")
        print(f"    Created Recall Docket: {new_recall_id}")
        
        # Test POST /api/v1/recalls/{id}/process
        t0 = time.time()
        proc_resp = client.post(f"/api/v1/recalls/{new_recall_id}/process", json={"recovery_factor": 0.88})
        elapsed = time.time() - t0
        print(f"  POST /api/v1/recalls/{new_recall_id}/process          : HTTP {proc_resp.status_code} in {elapsed*1000:.1f}ms [{'PASS' if proc_resp.status_code == 200 else 'FAIL'}]")
        print(f"    Process result: {proc_resp.get_json().get('status')}")
    else:
        all_passed = False
        
    return all_passed


if __name__ == "__main__":
    t3 = task3_audit_recalls()
    t4 = task4_audit_four_negative_scenarios()
    t7 = task7_audit_flask_endpoints()
