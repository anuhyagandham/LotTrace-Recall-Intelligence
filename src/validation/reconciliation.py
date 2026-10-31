"""
Quantity Reconciliation Engine for LotTrace AI.
Provides reconciliation checks across production consumption, yields,
shipments, customer deliveries, and warehouse balances.
"""

from typing import Dict, List, Any
from sqlalchemy.orm import Session
from src.models import (
    ProductionOrder,
    FinishedLot,
    Shipment,
    ShipmentItem,
    Delivery,
    Inventory,
)


class QuantityReconciler:
    """Verifies physical and logical inventory balances across the supply chain."""

    @staticmethod
    def reconcile_production_order(order: ProductionOrder) -> Dict[str, Any]:
        """
        Reconciles: produced_quantity + scrap_quantity vs planned_quantity.
        Expected balance: produced_quantity <= planned_quantity * 1.10 (within 10% overage buffer)
        """
        total_accounted = order.produced_quantity + order.scrap_quantity
        variance = round(total_accounted - order.planned_quantity, 2)
        variance_pct = round((variance / order.planned_quantity) * 100, 2) if order.planned_quantity > 0 else 0.0

        is_reconciled = abs(variance_pct) <= 10.0
        return {
            "order_id": order.order_id,
            "planned_quantity": order.planned_quantity,
            "produced_quantity": order.produced_quantity,
            "scrap_quantity": order.scrap_quantity,
            "total_accounted": total_accounted,
            "variance": variance,
            "variance_percentage": variance_pct,
            "is_reconciled": is_reconciled,
        }

    @staticmethod
    def reconcile_delivery_vs_produced(delivery: Delivery, finished_lot: FinishedLot) -> Dict[str, Any]:
        """
        Reconciles: delivered quantity must never exceed lot produced quantity.
        """
        is_valid = delivery.quantity_delivered <= finished_lot.quantity_produced
        excess = max(0.0, round(delivery.quantity_delivered - finished_lot.quantity_produced, 2))

        return {
            "delivery_id": delivery.delivery_id,
            "finished_lot_id": finished_lot.lot_id,
            "quantity_delivered": delivery.quantity_delivered,
            "quantity_produced": finished_lot.quantity_produced,
            "excess_quantity": excess,
            "is_valid": is_valid,
        }
