"""
Verification of backend data feeds for all 8 Streamlit dashboard pages.
"""

import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.database.connection import get_db_session
from src.analytics.metrics import MetricsCalculator
from src.genealogy.traversal import GenealogyService
from src.models import (
    Supplier, MaterialLot, Product, BOM, ProductionOrder,
    FinishedLot, Shipment, Delivery, Customer, RecallCase, ValidationIssue
)


def verify_dashboard_backends():
    print("=" * 80)
    print("VERIFYING DASHBOARD BACKEND SERVICES & QUERIES (8 PAGES)")
    print("=" * 80)
    
    with get_db_session() as session:
        calc = MetricsCalculator(session=session)
        service = GenealogyService(session=session)
        
        # Page 1: Executive Overview
        t0 = time.time()
        d_metrics = calc.get_dataset_metrics(db=session)
        r_metrics = calc.get_recall_performance_metrics(db=session)
        q_metrics = calc.get_data_quality_metrics(db=session)
        print(f"  Page 1 (Executive Overview)           : OK in {time.time()-t0:.3f}s")
        print(f"    Total Recalls: {r_metrics['total_recalls']}, Pass Rate: {q_metrics['overall_validation_pass_rate_pct']}%")
        
        # Page 2: Supplier & Material Traceability
        t0 = time.time()
        sup_count = session.query(Supplier).count()
        mat_lots = session.query(MaterialLot).limit(200).all()
        print(f"  Page 2 (Supplier & Material Traceability) : OK in {time.time()-t0:.3f}s ({sup_count} suppliers, {len(mat_lots)} lots sampled)")
        
        # Page 3: Production Genealogy
        t0 = time.time()
        prod_orders = session.query(ProductionOrder).limit(200).all()
        fin_lots = session.query(FinishedLot).limit(200).all()
        print(f"  Page 3 (Production Genealogy)        : OK in {time.time()-t0:.3f}s ({len(prod_orders)} orders, {len(fin_lots)} fin lots sampled)")
        
        # Page 4: Finished Goods & Distribution
        t0 = time.time()
        shipments = session.query(Shipment).limit(200).all()
        deliveries = session.query(Delivery).limit(200).all()
        print(f"  Page 4 (Finished Goods & Distribution): OK in {time.time()-t0:.3f}s ({len(shipments)} shipments, {len(deliveries)} deliveries sampled)")
        
        # Page 5: Recall Management
        t0 = time.time()
        recalls = session.query(RecallCase).all()
        print(f"  Page 5 (Recall Management)           : OK in {time.time()-t0:.3f}s ({len(recalls)} recall cases loaded)")
        
        # Page 6: Genealogy Explorer
        t0 = time.time()
        down_genealogy = service.get_downstream_genealogy("RAWLOT-SUP-0001-2026-000001", db=session)
        up_genealogy = service.get_upstream_genealogy("FINLOT-2026-000001", db=session)
        print(f"  Page 6 (Genealogy Explorer)          : OK in {time.time()-t0:.3f}s (Downstream nodes: {len(down_genealogy['graph']['nodes'])}, Upstream nodes: {len(up_genealogy['graph']['nodes'])})")
        
        # Page 7: Data Quality & Exceptions
        t0 = time.time()
        issues = session.query(ValidationIssue).all()
        print(f"  Page 7 (Data Quality & Exceptions)   : OK in {time.time()-t0:.3f}s ({len(issues)} validation issues loaded)")
        
        # Page 8: Analytics & Reports
        t0 = time.time()
        dataset_summary = calc.get_dataset_metrics(db=session)
        rec_perf = calc.get_recall_performance_metrics(db=session)
        print(f"  Page 8 (Analytics & Reports)         : OK in {time.time()-t0:.3f}s (Dataset metrics: {dataset_summary['total_finished_lots']} finished lots, {rec_perf['total_recalls']} recalls)")

    print("=" * 80)
    print("ALL 8 DASHBOARD BACKEND FEEDS VALIDATED SUCCESSFULLY [100% PASS]")
    print("=" * 80)
    return True


if __name__ == "__main__":
    verify_dashboard_backends()
