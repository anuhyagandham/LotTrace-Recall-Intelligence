"""
Tests for Product Recall Engine and Containment Lifecycle.
"""

from src.database.connection import get_db_session
from src.recall.engine import RecallEngine
from src.models import RecallCase, RecallAction, CustomerNotification, RecallEvent, MaterialLot, FinishedLot


def test_recall_initiation_and_scope_calculation():
    with get_db_session() as session:
        engine = RecallEngine(session=session)
        raw_lot = session.query(MaterialLot).first()

        res = engine.create_recall(
            source_lot_id=raw_lot.lot_id,
            title=f"Test Quality Recall for {raw_lot.lot_id}",
            trigger_type="CONTAMINATED_RAW_LOT",
            severity="CLASS_I",
            db=session,
        )

        assert res["success"] is True
        assert res["recall_id"].startswith("REC-2026-")
        assert res["recall"]["total_affected_finished_lots"] > 0
        assert res["recall"]["status"] == "OPEN"

        # Verify lot contamination flag
        lot_in_db = session.query(MaterialLot).filter(MaterialLot.lot_id == raw_lot.lot_id).first()
        assert lot_in_db.is_contaminated is True


def test_idempotent_recall_processing():
    with get_db_session() as session:
        engine = RecallEngine(session=session)
        recall = session.query(RecallCase).first()

        # First run
        run1 = engine.process_recall(recall.recall_id, recovery_factor=0.85, db=session)
        assert run1["success"] is True
        initial_actions = run1["actions_count"]

        # Second run (Idempotency test)
        run2 = engine.process_recall(recall.recall_id, recovery_factor=0.85, db=session)
        assert run2["success"] is True
        assert run2["actions_count"] == initial_actions, "Idempotent execution must not duplicate actions"

        # Verify metrics
        assert run2["metrics"]["notification_coverage_pct"] > 0
        assert run2["metrics"]["recovery_rate_pct"] > 0
        assert run2["metrics"]["recall_completion_pct"] >= 90.0
