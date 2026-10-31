"""
Tests for SQLAlchemy Relational Models and Schema Constraints.
"""

from datetime import datetime, timedelta
from src.models import (
    Supplier,
    MaterialLot,
    Product,
    BOM,
    BOMMaterial,
    ProductionOrder,
    ProductionConsumption,
    FinishedLot,
    Shipment,
    ShipmentItem,
    Customer,
    Delivery,
    RecallCase,
    RecallAction,
)


def test_supplier_and_material_lot_relationship(db_session):
    sup = Supplier(
        supplier_id="SUP-0001",
        supplier_code="VENDOR-0001",
        name="Apex Laboratories",
        category="API",
        contact_email="quality@apex.com",
        country="USA",
    )
    db_session.add(sup)
    db_session.flush()

    raw_lot = MaterialLot(
        lot_id="RAWLOT-SUP-0001-2026-000001",
        supplier_id=sup.supplier_id,
        material_name="Acetaminophen USP",
        material_category="API",
        received_date=datetime(2026, 1, 15),
        expiry_date=datetime(2028, 1, 15),
        initial_quantity=500.0,
        current_quantity=500.0,
        unit_of_measure="KG",
        unit_cost=45.0,
    )
    db_session.add(raw_lot)
    db_session.flush()

    # Verify back-reference
    assert len(sup.material_lots) == 1
    assert sup.material_lots[0].lot_id == "RAWLOT-SUP-0001-2026-000001"
    assert raw_lot.supplier.name == "Apex Laboratories"


def test_product_bom_formulation(db_session):
    prod = Product(
        product_id="PRD-0001",
        sku="SKU-MED-0001",
        product_name="Acetaminophen 500mg Tablets",
        category="PHARMACEUTICAL",
        unit_of_measure="BOTTLES",
        shelf_life_days=730,
        standard_cost=6.50,
    )
    db_session.add(prod)
    db_session.flush()

    bom = BOM(
        bom_id="BOM-PRD-0001-V1",
        product_id=prod.product_id,
        version="v1.0",
        effective_from=datetime(2026, 1, 1),
        effective_to=datetime(2027, 1, 1),
        yield_percentage=98.5,
    )
    db_session.add(bom)
    db_session.flush()

    b_mat = BOMMaterial(
        bom_id=bom.bom_id,
        material_category="API",
        material_name="Acetaminophen USP",
        required_quantity=0.05,
        unit_of_measure="KG",
    )
    db_session.add(b_mat)
    db_session.flush()

    assert len(prod.boms) == 1
    assert len(bom.materials) == 1
    assert bom.materials[0].material_name == "Acetaminophen USP"
    assert bom.product.product_name == "Acetaminophen 500mg Tablets"
