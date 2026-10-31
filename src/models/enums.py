"""
Enumeration types for domain entities and lifecycle states in LotTrace AI.
"""

from enum import Enum


class SupplierStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class MaterialCategory(str, Enum):
    API = "API"  # Active Pharmaceutical / Chemical Ingredient
    EXCIPIENT = "EXCIPIENT"
    PACKAGING = "PACKAGING"
    SOLVENT = "SOLVENT"
    FLAVORING = "FLAVORING"
    PRESERVATIVE = "PRESERVATIVE"


class ProductCategory(str, Enum):
    PHARMACEUTICAL = "PHARMACEUTICAL"
    FOOD_BEVERAGE = "FOOD_BEVERAGE"
    CHEMICAL = "CHEMICAL"
    NUTRACEUTICAL = "NUTRACEUTICAL"


class QualityStatus(str, Enum):
    RELEASED = "RELEASED"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"
    CONTAMINATED = "CONTAMINATED"
    UNDER_TEST = "UNDER_TEST"


class ProductionOrderStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ShipmentStatus(str, Enum):
    CREATED = "CREATED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    RETURNED = "RETURNED"
    RECALLED = "RECALLED"


class DeliveryStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    DELIVERED = "DELIVERED"
    REJECTED = "REJECTED"
    RETURNED = "RETURNED"


class RecallTriggerType(str, Enum):
    CONTAMINATED_RAW_LOT = "CONTAMINATED_RAW_LOT"
    CONTAMINATED_FINISHED_LOT = "CONTAMINATED_FINISHED_LOT"
    QUALITY_AUDIT_FAILURE = "QUALITY_AUDIT_FAILURE"
    CUSTOMER_COMPLAINT = "CUSTOMER_COMPLAINT"


class RecallSeverity(str, Enum):
    CLASS_I = "CLASS_I"      # Dangerous / defective products that could cause serious health problems
    CLASS_II = "CLASS_II"    # Products that might cause temporary health problems
    CLASS_III = "CLASS_III"  # Products unlikely to cause adverse health consequences


class RecallStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    CONTAINMENT_IN_PROGRESS = "CONTAINMENT_IN_PROGRESS"
    CUSTOMERS_NOTIFIED = "CUSTOMERS_NOTIFIED"
    RECOVERY_IN_PROGRESS = "RECOVERY_IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"


class RecallActionType(str, Enum):
    QUARANTINE_INVENTORY = "QUARANTINE_INVENTORY"
    CUSTOMER_NOTIFICATION = "CUSTOMER_NOTIFICATION"
    SHIPMENT_STOP = "SHIPMENT_STOP"
    CARRIER_INTERCEPT = "CARRIER_INTERCEPT"
    PRODUCT_RECOVERY = "PRODUCT_RECOVERY"
    DISPOSAL = "DISPOSAL"
    ROOT_CAUSE_INVESTIGATION = "ROOT_CAUSE_INVESTIGATION"


class RecallActionStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class NotificationChannel(str, Enum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    REGISTERED_MAIL = "REGISTERED_MAIL"
    EDI = "EDI"
    PORTAL = "PORTAL"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    FAILED = "FAILED"


class InventoryEventType(str, Enum):
    RECEIPT = "RECEIPT"
    PRODUCTION_CONSUMPTION = "PRODUCTION_CONSUMPTION"
    PRODUCTION_OUTPUT = "PRODUCTION_OUTPUT"
    SHIPMENT_DISPATCH = "SHIPMENT_DISPATCH"
    CUSTOMER_RETURN = "CUSTOMER_RETURN"
    QUARANTINE = "QUARANTINE"
    RECOVERY = "RECOVERY"
    SCRAP = "SCRAP"
    AUDIT_ADJUSTMENT = "AUDIT_ADJUSTMENT"


class ValidationSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    WARNING = "WARNING"


class ValidationStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
