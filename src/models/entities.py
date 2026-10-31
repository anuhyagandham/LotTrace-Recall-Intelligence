"""
SQLAlchemy ORM Entity Definitions for LotTrace AI.
Defines all 20 normalized relational models: 11 core entities, 9 bridge/event tables.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    Text,
)
from sqlalchemy.orm import relationship
from src.database.connection import Base


# ============================================================================
# 1. Supplier Entity
# ============================================================================
class Supplier(Base):
    """Represents an approved raw material vendor/supplier."""
    __tablename__ = "suppliers"

    supplier_id = Column(String(50), primary_key=True, index=True)
    supplier_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    country = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    material_lots = relationship("MaterialLot", back_populates="supplier", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "supplier_id": self.supplier_id,
            "supplier_code": self.supplier_code,
            "name": self.name,
            "category": self.category,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "address": self.address,
            "country": self.country,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# 2. MaterialLot Entity
# ============================================================================
class MaterialLot(Base):
    """Represents a specific received lot/batch of raw material from a supplier."""
    __tablename__ = "material_lots"

    lot_id = Column(String(100), primary_key=True, index=True)
    supplier_id = Column(String(50), ForeignKey("suppliers.supplier_id"), nullable=False, index=True)
    material_name = Column(String(255), nullable=False)
    material_category = Column(String(100), nullable=False)
    received_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    initial_quantity = Column(Float, nullable=False)
    current_quantity = Column(Float, nullable=False)
    unit_of_measure = Column(String(20), nullable=False)
    unit_cost = Column(Float, nullable=False)
    quality_status = Column(String(50), nullable=False, default="RELEASED")
    is_contaminated = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    supplier = relationship("Supplier", back_populates="material_lots")
    consumptions = relationship("ProductionConsumption", back_populates="material_lot")
    genealogies = relationship("LotGenealogy", back_populates="raw_lot")

    __table_args__ = (
        Index("idx_material_lot_supplier_status", "supplier_id", "quality_status"),
        Index("idx_material_lot_contamination", "is_contaminated"),
    )

    def to_dict(self):
        return {
            "lot_id": self.lot_id,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier.name if self.supplier else None,
            "material_name": self.material_name,
            "material_category": self.material_category,
            "received_date": self.received_date.isoformat() if self.received_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "initial_quantity": self.initial_quantity,
            "current_quantity": self.current_quantity,
            "unit_of_measure": self.unit_of_measure,
            "unit_cost": self.unit_cost,
            "quality_status": self.quality_status,
            "is_contaminated": self.is_contaminated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# 3. Product Entity
# ============================================================================
class Product(Base):
    """Finished product specification catalog."""
    __tablename__ = "products"

    product_id = Column(String(50), primary_key=True, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    unit_of_measure = Column(String(20), nullable=False)
    shelf_life_days = Column(Integer, nullable=False)
    standard_cost = Column(Float, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    boms = relationship("BOM", back_populates="product", cascade="all, delete-orphan")
    production_orders = relationship("ProductionOrder", back_populates="product")
    finished_lots = relationship("FinishedLot", back_populates="product")

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "sku": self.sku,
            "product_name": self.product_name,
            "category": self.category,
            "unit_of_measure": self.unit_of_measure,
            "shelf_life_days": self.shelf_life_days,
            "standard_cost": self.standard_cost,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# 4. BOM (Bill of Materials) Entity
# ============================================================================
class BOM(Base):
    """Bill of Materials version defining component formulation and validity window."""
    __tablename__ = "boms"

    bom_id = Column(String(50), primary_key=True, index=True)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    yield_percentage = Column(Float, nullable=False, default=100.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="boms")
    materials = relationship("BOMMaterial", back_populates="bom", cascade="all, delete-orphan")
    production_orders = relationship("ProductionOrder", back_populates="bom")

    __table_args__ = (
        UniqueConstraint("product_id", "version", name="uq_bom_product_version"),
    )

    def to_dict(self):
        return {
            "bom_id": self.bom_id,
            "product_id": self.product_id,
            "version": self.version,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "is_active": self.is_active,
            "yield_percentage": self.yield_percentage,
            "materials_count": len(self.materials) if self.materials else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# 5. BOMMaterial (Bridge Table)
# ============================================================================
class BOMMaterial(Base):
    """Specific raw material component requirement within a BOM."""
    __tablename__ = "bom_materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bom_id = Column(String(50), ForeignKey("boms.bom_id"), nullable=False, index=True)
    material_category = Column(String(100), nullable=False)
    material_name = Column(String(255), nullable=False)
    required_quantity = Column(Float, nullable=False)
    unit_of_measure = Column(String(20), nullable=False)
    is_mandatory = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    bom = relationship("BOM", back_populates="materials")

    def to_dict(self):
        return {
            "id": self.id,
            "bom_id": self.bom_id,
            "material_category": self.material_category,
            "material_name": self.material_name,
            "required_quantity": self.required_quantity,
            "unit_of_measure": self.unit_of_measure,
            "is_mandatory": self.is_mandatory,
        }


# ============================================================================
# 6. ProductionOrder Entity
# ============================================================================
class ProductionOrder(Base):
    """Manufacturing work order executing product formulation."""
    __tablename__ = "production_orders"

    order_id = Column(String(50), primary_key=True, index=True)
    bom_id = Column(String(50), ForeignKey("boms.bom_id"), nullable=False, index=True)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False, index=True)
    order_date = Column(DateTime, nullable=False)
    start_date = Column(DateTime, nullable=False)
    completion_date = Column(DateTime, nullable=False)
    planned_quantity = Column(Float, nullable=False)
    produced_quantity = Column(Float, nullable=False)
    scrap_quantity = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="COMPLETED")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    bom = relationship("BOM", back_populates="production_orders")
    product = relationship("Product", back_populates="production_orders")
    consumptions = relationship("ProductionConsumption", back_populates="production_order", cascade="all, delete-orphan")
    finished_lots = relationship("FinishedLot", back_populates="production_order")
    lot_genealogies = relationship("LotGenealogy", back_populates="production_order")

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "bom_id": self.bom_id,
            "product_id": self.product_id,
            "product_name": self.product.product_name if self.product else None,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "planned_quantity": self.planned_quantity,
            "produced_quantity": self.produced_quantity,
            "scrap_quantity": self.scrap_quantity,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# 7. ProductionConsumption (Bridge Table)
# ============================================================================
class ProductionConsumption(Base):
    """Actual consumption record of a raw material lot into a production order."""
    __tablename__ = "production_consumptions"

    consumption_id = Column(String(50), primary_key=True, index=True)
    production_order_id = Column(String(50), ForeignKey("production_orders.order_id"), nullable=False, index=True)
    material_lot_id = Column(String(100), ForeignKey("material_lots.lot_id"), nullable=False, index=True)
    quantity_consumed = Column(Float, nullable=False)
    unit_of_measure = Column(String(20), nullable=False)
    consumption_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    production_order = relationship("ProductionOrder", back_populates="consumptions")
    material_lot = relationship("MaterialLot", back_populates="consumptions")

    def to_dict(self):
        return {
            "consumption_id": self.consumption_id,
            "production_order_id": self.production_order_id,
            "material_lot_id": self.material_lot_id,
            "quantity_consumed": self.quantity_consumed,
            "unit_of_measure": self.unit_of_measure,
            "consumption_date": self.consumption_date.isoformat() if self.consumption_date else None,
        }


# ============================================================================
# 8. FinishedLot Entity
# ============================================================================
class FinishedLot(Base):
    """Manufactured lot of finished product released for distribution."""
    __tablename__ = "finished_lots"

    lot_id = Column(String(100), primary_key=True, index=True)
    production_order_id = Column(String(50), ForeignKey("production_orders.order_id"), nullable=False, index=True)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False, index=True)
    manufactured_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    quantity_produced = Column(Float, nullable=False)
    quantity_available = Column(Float, nullable=False)
    unit_of_measure = Column(String(20), nullable=False)
    quality_status = Column(String(50), nullable=False, default="RELEASED")
    is_contaminated = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    production_order = relationship("ProductionOrder", back_populates="finished_lots")
    product = relationship("Product", back_populates="finished_lots")
    shipment_items = relationship("ShipmentItem", back_populates="finished_lot")
    genealogies = relationship("LotGenealogy", back_populates="finished_lot")

    __table_args__ = (
        Index("idx_finished_lot_contamination", "is_contaminated"),
        Index("idx_finished_lot_quality", "quality_status"),
    )

    def to_dict(self):
        return {
            "lot_id": self.lot_id,
            "production_order_id": self.production_order_id,
            "product_id": self.product_id,
            "product_name": self.product.product_name if self.product else None,
            "manufactured_date": self.manufactured_date.isoformat() if self.manufactured_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "quantity_produced": self.quantity_produced,
            "quantity_available": self.quantity_available,
            "unit_of_measure": self.unit_of_measure,
            "quality_status": self.quality_status,
            "is_contaminated": self.is_contaminated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# 9. LotGenealogy (Traceability Bridge Table)
# ============================================================================
class LotGenealogy(Base):
    """Direct genealogical mapping connecting raw lots to finished lots via orders."""
    __tablename__ = "lot_genealogies"

    genealogy_id = Column(String(50), primary_key=True, index=True)
    raw_lot_id = Column(String(100), ForeignKey("material_lots.lot_id"), nullable=False, index=True)
    finished_lot_id = Column(String(100), ForeignKey("finished_lots.lot_id"), nullable=False, index=True)
    production_order_id = Column(String(50), ForeignKey("production_orders.order_id"), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False, default="DIRECT_CONSUMPTION")
    depth_level = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    raw_lot = relationship("MaterialLot", back_populates="genealogies")
    finished_lot = relationship("FinishedLot", back_populates="genealogies")
    production_order = relationship("ProductionOrder", back_populates="lot_genealogies")

    __table_args__ = (
        UniqueConstraint("raw_lot_id", "finished_lot_id", "production_order_id", name="uq_genealogy_link"),
    )

    def to_dict(self):
        return {
            "genealogy_id": self.genealogy_id,
            "raw_lot_id": self.raw_lot_id,
            "finished_lot_id": self.finished_lot_id,
            "production_order_id": self.production_order_id,
            "relationship_type": self.relationship_type,
            "depth_level": self.depth_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# 10. Shipment Entity
# ============================================================================
class Shipment(Base):
    """Outbound logistics freight movement carrying finished goods."""
    __tablename__ = "shipments"

    shipment_id = Column(String(50), primary_key=True, index=True)
    tracking_number = Column(String(100), unique=True, nullable=False, index=True)
    ship_date = Column(DateTime, nullable=False)
    carrier = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="DELIVERED")
    origin_warehouse = Column(String(100), nullable=False)
    destination_region = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    items = relationship("ShipmentItem", back_populates="shipment", cascade="all, delete-orphan")
    deliveries = relationship("Delivery", back_populates="shipment", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "shipment_id": self.shipment_id,
            "tracking_number": self.tracking_number,
            "ship_date": self.ship_date.isoformat() if self.ship_date else None,
            "carrier": self.carrier,
            "status": self.status,
            "origin_warehouse": self.origin_warehouse,
            "destination_region": self.destination_region,
            "items_count": len(self.items) if self.items else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# 11. ShipmentItem (Bridge Table)
# ============================================================================
class ShipmentItem(Base):
    """Line item detailing specific finished lot allocated to a shipment."""
    __tablename__ = "shipment_items"

    item_id = Column(String(50), primary_key=True, index=True)
    shipment_id = Column(String(50), ForeignKey("shipments.shipment_id"), nullable=False, index=True)
    finished_lot_id = Column(String(100), ForeignKey("finished_lots.lot_id"), nullable=False, index=True)
    quantity_shipped = Column(Float, nullable=False)
    unit_of_measure = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    shipment = relationship("Shipment", back_populates="items")
    finished_lot = relationship("FinishedLot", back_populates="shipment_items")

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "shipment_id": self.shipment_id,
            "finished_lot_id": self.finished_lot_id,
            "quantity_shipped": self.quantity_shipped,
            "unit_of_measure": self.unit_of_measure,
        }


# ============================================================================
# 12. Customer Entity
# ============================================================================
class Customer(Base):
    """Downstream customer organization receiving product consignments."""
    __tablename__ = "customers"

    customer_id = Column(String(50), primary_key=True, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_type = Column(String(100), nullable=False)  # HOSPITAL, CLINIC, PHARMACY_CHAIN, DISTRIBUTOR, RETAILER
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    risk_tier = Column(String(50), nullable=False, default="STANDARD")  # CRITICAL_HEALTHCARE, HIGH_VOLUME, STANDARD
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    deliveries = relationship("Delivery", back_populates="customer")
    notifications = relationship("CustomerNotification", back_populates="customer")

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_type": self.customer_type,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "risk_tier": self.risk_tier,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# 13. Delivery Entity
# ============================================================================
class Delivery(Base):
    """Physical handover of shipment contents to a customer destination."""
    __tablename__ = "deliveries"

    delivery_id = Column(String(50), primary_key=True, index=True)
    shipment_id = Column(String(50), ForeignKey("shipments.shipment_id"), nullable=False, index=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False, index=True)
    delivery_date = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default="DELIVERED")
    received_by = Column(String(255), nullable=False)
    quantity_delivered = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    shipment = relationship("Shipment", back_populates="deliveries")
    customer = relationship("Customer", back_populates="deliveries")

    def to_dict(self):
        return {
            "delivery_id": self.delivery_id,
            "shipment_id": self.shipment_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer.customer_name if self.customer else None,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "status": self.status,
            "received_by": self.received_by,
            "quantity_delivered": self.quantity_delivered,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# 14. Inventory Entity
# ============================================================================
class Inventory(Base):
    """Warehouse balance position for raw materials and finished goods."""
    __tablename__ = "inventories"

    inventory_id = Column(String(50), primary_key=True, index=True)
    lot_id = Column(String(100), nullable=False, index=True)
    lot_type = Column(String(50), nullable=False)  # RAW or FINISHED
    warehouse_id = Column(String(50), nullable=False)
    location_bin = Column(String(50), nullable=False)
    quantity_on_hand = Column(Float, nullable=False)
    quantity_reserved = Column(Float, nullable=False, default=0.0)
    quantity_quarantined = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="AVAILABLE")  # AVAILABLE, QUARANTINED, BLOCKED, CONSUMED
    last_audit_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    events = relationship("InventoryEvent", back_populates="inventory", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_inventory_lot_status", "lot_id", "status"),
    )

    def to_dict(self):
        return {
            "inventory_id": self.inventory_id,
            "lot_id": self.lot_id,
            "lot_type": self.lot_type,
            "warehouse_id": self.warehouse_id,
            "location_bin": self.location_bin,
            "quantity_on_hand": self.quantity_on_hand,
            "quantity_reserved": self.quantity_reserved,
            "quantity_quarantined": self.quantity_quarantined,
            "status": self.status,
            "last_audit_date": self.last_audit_date.isoformat() if self.last_audit_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# 15. InventoryEvent (Event-History Table)
# ============================================================================
class InventoryEvent(Base):
    """Immutable ledger of inventory transactions, receipts, deductions, and quarantines."""
    __tablename__ = "inventory_events"

    event_id = Column(String(50), primary_key=True, index=True)
    inventory_id = Column(String(50), ForeignKey("inventories.inventory_id"), nullable=False, index=True)
    lot_id = Column(String(100), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    quantity_change = Column(Float, nullable=False)
    resulting_balance = Column(Float, nullable=False)
    reference_type = Column(String(50), nullable=False)
    reference_id = Column(String(50), nullable=False)
    event_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    inventory = relationship("Inventory", back_populates="events")

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "inventory_id": self.inventory_id,
            "lot_id": self.lot_id,
            "event_type": self.event_type,
            "quantity_change": self.quantity_change,
            "resulting_balance": self.resulting_balance,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "notes": self.notes,
        }


# ============================================================================
# 16. RecallCase Entity
# ============================================================================
class RecallCase(Base):
    """Core product safety recall investigation and containment docket."""
    __tablename__ = "recall_cases"

    recall_id = Column(String(50), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    trigger_type = Column(String(50), nullable=False)  # CONTAMINATED_RAW_LOT, CONTAMINATED_FINISHED_LOT
    source_lot_id = Column(String(100), nullable=False, index=True)
    source_lot_type = Column(String(20), nullable=False)  # RAW or FINISHED
    severity = Column(String(20), nullable=False)  # CLASS_I, CLASS_II, CLASS_III
    initiated_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    target_completion_date = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default="OPEN")
    closure_date = Column(DateTime, nullable=True)
    total_affected_finished_lots = Column(Integer, nullable=False, default=0)
    total_affected_deliveries = Column(Integer, nullable=False, default=0)
    total_affected_customers = Column(Integer, nullable=False, default=0)
    total_recalled_quantity = Column(Float, nullable=False, default=0.0)
    total_quarantined_quantity = Column(Float, nullable=False, default=0.0)
    total_recovered_quantity = Column(Float, nullable=False, default=0.0)
    notification_coverage_pct = Column(Float, nullable=False, default=0.0)
    recovery_rate_pct = Column(Float, nullable=False, default=0.0)
    recall_completion_pct = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    actions = relationship("RecallAction", back_populates="recall_case", cascade="all, delete-orphan")
    events = relationship("RecallEvent", back_populates="recall_case", cascade="all, delete-orphan")
    notifications = relationship("CustomerNotification", back_populates="recall_case", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "recall_id": self.recall_id,
            "title": self.title,
            "trigger_type": self.trigger_type,
            "source_lot_id": self.source_lot_id,
            "source_lot_type": self.source_lot_type,
            "severity": self.severity,
            "initiated_date": self.initiated_date.isoformat() if self.initiated_date else None,
            "target_completion_date": self.target_completion_date.isoformat() if self.target_completion_date else None,
            "status": self.status,
            "closure_date": self.closure_date.isoformat() if self.closure_date else None,
            "total_affected_finished_lots": self.total_affected_finished_lots,
            "total_affected_deliveries": self.total_affected_deliveries,
            "total_affected_customers": self.total_affected_customers,
            "total_recalled_quantity": self.total_recalled_quantity,
            "total_quarantined_quantity": self.total_quarantined_quantity,
            "total_recovered_quantity": self.total_recovered_quantity,
            "notification_coverage_pct": self.notification_coverage_pct,
            "recovery_rate_pct": self.recovery_rate_pct,
            "recall_completion_pct": self.recall_completion_pct,
            "actions_count": len(self.actions) if self.actions else 0,
            "notifications_count": len(self.notifications) if self.notifications else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# 17. RecallAction Entity
# ============================================================================
class RecallAction(Base):
    """Specific operational task mandated during recall execution."""
    __tablename__ = "recall_actions"

    action_id = Column(String(50), primary_key=True, index=True)
    recall_id = Column(String(50), ForeignKey("recall_cases.recall_id"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)
    target_entity_type = Column(String(50), nullable=False)
    target_entity_id = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")
    assigned_to = Column(String(100), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    completed_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    recall_case = relationship("RecallCase", back_populates="actions")

    def to_dict(self):
        return {
            "action_id": self.action_id,
            "recall_id": self.recall_id,
            "action_type": self.action_type,
            "target_entity_type": self.target_entity_type,
            "target_entity_id": self.target_entity_id,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "completed_date": self.completed_date.isoformat() if self.completed_date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# 18. RecallEvent (Event-History Table)
# ============================================================================
class RecallEvent(Base):
    """Audit ledger capturing every lifecycle state transition for a recall."""
    __tablename__ = "recall_events"

    event_id = Column(String(50), primary_key=True, index=True)
    recall_id = Column(String(50), ForeignKey("recall_cases.recall_id"), nullable=False, index=True)
    previous_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    reason = Column(String(500), nullable=False)
    trigger_source = Column(String(100), nullable=False, default="RECALL_ENGINE")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    recall_case = relationship("RecallCase", back_populates="events")

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "recall_id": self.recall_id,
            "previous_status": self.previous_status,
            "new_status": self.new_status,
            "reason": self.reason,
            "trigger_source": self.trigger_source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# 19. CustomerNotification Entity
# ============================================================================
class CustomerNotification(Base):
    """Notice dispatched to an affected customer regarding a product recall."""
    __tablename__ = "customer_notifications"

    notification_id = Column(String(50), primary_key=True, index=True)
    recall_id = Column(String(50), ForeignKey("recall_cases.recall_id"), nullable=False, index=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False, index=True)
    delivery_id = Column(String(50), nullable=True)
    finished_lot_id = Column(String(100), nullable=True)
    notification_channel = Column(String(50), nullable=False)
    notification_status = Column(String(50), nullable=False, default="PENDING")
    sent_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    response_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    recall_case = relationship("RecallCase", back_populates="notifications")
    customer = relationship("Customer", back_populates="notifications")

    def to_dict(self):
        return {
            "notification_id": self.notification_id,
            "recall_id": self.recall_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer.customer_name if self.customer else None,
            "delivery_id": self.delivery_id,
            "finished_lot_id": self.finished_lot_id,
            "notification_channel": self.notification_channel,
            "notification_status": self.notification_status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "response_notes": self.response_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# 20. ValidationIssue Entity
# ============================================================================
class ValidationIssue(Base):
    """Quality, reconciliation, or referential anomaly discovered during data auditing."""
    __tablename__ = "validation_issues"

    validation_id = Column(String(50), primary_key=True, index=True)
    entity_name = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    issue_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW, WARNING
    expected_value = Column(String(255), nullable=True)
    actual_value = Column(String(255), nullable=True)
    validation_status = Column(String(20), nullable=False, default="FAILED")
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ground_truth_label = Column(String(100), nullable=True)

    def to_dict(self):
        return {
            "validation_id": self.validation_id,
            "entity_name": self.entity_name,
            "entity_id": self.entity_id,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "validation_status": self.validation_status,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "ground_truth_label": self.ground_truth_label,
        }
