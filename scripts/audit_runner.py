"""
Audit Runner for LotTrace AI.
Executes and validates all tasks required for the Strict Final Submission Audit.
"""

import sys
import time
import sqlite3
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.database.connection import get_db_session, engine
from src.models import (
    Supplier, MaterialLot, Product, BOM, BOMMaterial,
    ProductionOrder, ProductionConsumption, FinishedLot, LotGenealogy,
    Customer, Shipment, ShipmentItem, Delivery, Inventory,
    InventoryEvent, RecallCase, RecallAction, RecallEvent,
    CustomerNotification, ValidationIssue
)
from src.validation.validator import BusinessValidator
from src.recall.engine import RecallEngine
from src.genealogy.traversal import GenealogyService


def task1_verify_row_counts():
    print("=" * 80)
    print("TASK 1: DATABASE ROW COUNTS VERIFICATION")
    print("=" * 80)
    
    db_path = BASE_DIR / "data" / "lottrace.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    targets = {
        "suppliers": 500,
        "material_lots": 10000,
        "production_orders": 5000,
        "finished_lots": 8000,
        "deliveries": 20000,
    }
    
    actual_counts = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        actual_counts[table] = count
        
        target_str = f"Target: {targets[table]:,}" if table in targets else "Dependent / Bridge"
        status = "MATCH" if (table not in targets or count == targets[table]) else "MISMATCH"
        print(f"  {table:<25} : {count:>7,} rows | {target_str:<25} [{status}]")
        
    conn.close()
    return actual_counts


def task2_database_integrity():
    print("\n" + "=" * 80)
    print("TASK 2: DATABASE INTEGRITY VERIFICATION")
    print("=" * 80)
    
    db_path = BASE_DIR / "data" / "lottrace.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 1. Foreign Key Check
    cursor.execute("PRAGMA foreign_key_check")
    fk_violations = cursor.fetchall()
    print(f"  PRAGMA foreign_key_check violations: {len(fk_violations)}")
    if fk_violations:
        for v in fk_violations[:5]:
            print(f"    Violation: {v}")
            
    # 2. Primary Key Uniqueness
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    pk_duplicates = 0
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        pk_cols = [c[1] for c in columns if c[5] > 0]
        if pk_cols:
            pk_str = ", ".join(pk_cols)
            cursor.execute(f"SELECT {pk_str}, COUNT(*) FROM {table} GROUP BY {pk_str} HAVING COUNT(*) > 1")
            dups = cursor.fetchall()
            if dups:
                pk_duplicates += len(dups)
                print(f"    Duplicate PK in {table}: {len(dups)}")
    print(f"  Primary Key duplicate groups across all tables: {pk_duplicates}")
    conn.close()
    
    # 3. Business Validator Checks
    print("  Running complete BusinessValidator...")
    t0 = time.time()
    validator = BusinessValidator()
    val_report = validator.run_all_validations()
    elapsed = time.time() - t0
    
    summary = val_report["summary"]
    print(f"  Validation evaluated in {elapsed:.2f}s:")
    print(f"    Total Checks Evaluated : {summary['total_checks_evaluated']:,}")
    print(f"    Passed Checks          : {summary['passed_checks']:,}")
    print(f"    Failed Checks          : {summary['failed_checks']}")
    print(f"    Warning Checks         : {summary['warning_checks']}")
    print(f"    Validation Pass Rate   : {summary['validation_pass_rate_pct']}%")
    
    print("\n  Summary of Failed Checks (Planted Anomalies & Exceptions):")
    for iss in val_report["issues"]:
        print(f"    [{iss['severity']}] {iss['entity_name']} {iss['entity_id']}: {iss['issue_type']} (Label: {iss.get('ground_truth_label')})")
        
    return {
        "fk_violations": len(fk_violations),
        "pk_duplicates": pk_duplicates,
        "validator_summary": summary,
        "issues": val_report["issues"]
    }


if __name__ == "__main__":
    t1_counts = task1_verify_row_counts()
    t2_integrity = task2_database_integrity()
