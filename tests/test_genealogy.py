"""
Tests for Upstream and Downstream Genealogy Traversal.
"""

from src.database.connection import get_db_session
from src.genealogy.traversal import GenealogyService
from src.models import FinishedLot, MaterialLot


def test_upstream_genealogy_traversal():
    """Tests tracing from a finished lot back to work orders, raw ingredients, and suppliers."""
    with get_db_session() as session:
        service = GenealogyService(session=session)
        fin_lot = session.query(FinishedLot).first()
        assert fin_lot is not None, "Starter dataset should have finished lots"

        upstream = service.get_upstream_genealogy(fin_lot.lot_id, db=session)
        assert upstream["found"] is True
        assert upstream["finished_lot_id"] == fin_lot.lot_id
        assert upstream["total_consumed_raw_lots"] > 0
        assert upstream["total_suppliers"] > 0
        assert "graph" in upstream
        assert len(upstream["graph"]["nodes"]) >= 3


def test_downstream_genealogy_traversal():
    """Tests tracing from a raw material lot downstream through to finished lots and customers."""
    with get_db_session() as session:
        service = GenealogyService(session=session)
        raw_lot = session.query(MaterialLot).first()
        assert raw_lot is not None, "Starter dataset should have raw material lots"

        downstream = service.get_downstream_genealogy(raw_lot.lot_id, db=session)
        assert downstream["found"] is True
        assert downstream["source_lot_id"] == raw_lot.lot_id
        assert downstream["source_lot_type"] == "RAW"
        assert downstream["total_affected_finished_lots"] > 0
        assert downstream["total_affected_customers"] > 0
        assert downstream["total_delivered_quantity"] > 0
