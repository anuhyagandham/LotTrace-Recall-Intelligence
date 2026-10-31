"""
Tests for Deterministic Identification System.
"""

from src.generator.id_generator import (
    generate_supplier_id,
    generate_raw_lot_id,
    generate_production_order_id,
    generate_finished_lot_id,
    generate_shipment_id,
    generate_delivery_id,
    generate_recall_case_id,
    generate_customer_id,
)


def test_supplier_id_format():
    assert generate_supplier_id(1) == "SUP-0001"
    assert generate_supplier_id(42) == "SUP-0042"
    assert generate_supplier_id(500) == "SUP-0500"


def test_raw_lot_id_format():
    sup_id = "SUP-0001"
    lot_id = generate_raw_lot_id(sup_id, 1, 2026)
    assert lot_id == "RAWLOT-SUP-0001-2026-000001"
    assert lot_id.startswith("RAWLOT-SUP-0001-2026-")
    assert len(lot_id.split("-")[-1]) == 6


def test_production_order_id_format():
    wo_id = generate_production_order_id(1, 2026)
    assert wo_id == "WO-2026-000001"
    assert generate_production_order_id(5000, 2026) == "WO-2026-005000"


def test_finished_lot_id_format():
    fin_id = generate_finished_lot_id(1, 2026)
    assert fin_id == "FINLOT-2026-000001"
    assert generate_finished_lot_id(8000, 2026) == "FINLOT-2026-008000"


def test_shipment_and_delivery_ids():
    assert generate_shipment_id(1, 2026) == "SHP-2026-000001"
    assert generate_delivery_id(1, 2026) == "DEL-2026-000001"
    assert generate_customer_id(1) == "CUST-0001"


def test_recall_case_id_format():
    assert generate_recall_case_id(1, 2026) == "REC-2026-000001"
    assert generate_recall_case_id(10, 2026) == "REC-2026-000010"
