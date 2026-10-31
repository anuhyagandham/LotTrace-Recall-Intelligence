"""
Genealogy Traversal Engine for LotTrace AI.
Implements complete, recursive upstream and downstream traceability graphs
with loop detection and node-level enrichment.
"""

from typing import Dict, List, Set, Optional, Any
from sqlalchemy.orm import Session
from src.database.connection import get_db_session
from src.models import (
    MaterialLot,
    Supplier,
    Product,
    ProductionOrder,
    ProductionConsumption,
    FinishedLot,
    LotGenealogy,
    Shipment,
    ShipmentItem,
    Customer,
    Delivery,
)
from src.genealogy.graph import GraphNode, GraphEdge, TraceabilityGraph
from src.utils.logging_config import logger


class GenealogyService:
    """Enterprise Supply Chain Traceability and Genealogy Traversal Service."""

    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    def _get_session(self):
        if self._external_session:
            return self._external_session
        return get_db_session()

    def get_upstream_genealogy(self, finished_lot_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        UPSTREAM TRACEABILITY:
        Finished Lot -> Production Order -> Consumed Material Lots -> Suppliers.
        """
        logger.info(f"Traversing upstream genealogy for finished lot: {finished_lot_id}")
        session_cm = None
        if db is not None:
            session = db
        elif self._external_session:
            session = self._external_session
        else:
            session_cm = get_db_session()
            session = session_cm.__enter__()

        try:
            fin_lot = session.query(FinishedLot).filter(FinishedLot.lot_id == finished_lot_id).first()
            if not fin_lot:
                return {"error": f"Finished lot '{finished_lot_id}' not found", "found": False}

            graph = TraceabilityGraph(root_id=finished_lot_id, direction="UPSTREAM")

            # Root Node: Finished Lot
            graph.add_node(GraphNode(
                id=fin_lot.lot_id,
                label=f"Finished Lot: {fin_lot.lot_id}",
                node_type="FINISHED_LOT",
                is_contaminated=fin_lot.is_contaminated,
                attributes={
                    "product_id": fin_lot.product_id,
                    "product_name": fin_lot.product.product_name if fin_lot.product else "Unknown",
                    "quantity_produced": fin_lot.quantity_produced,
                    "quantity_available": fin_lot.quantity_available,
                    "unit_of_measure": fin_lot.unit_of_measure,
                    "quality_status": fin_lot.quality_status,
                    "manufactured_date": fin_lot.manufactured_date.isoformat(),
                    "expiry_date": fin_lot.expiry_date.isoformat(),
                }
            ))

            order = fin_lot.production_order
            consumed_materials_summary = []
            suppliers_summary = []

            if order:
                # Node: Production Order
                order_node = GraphNode(
                    id=order.order_id,
                    label=f"Work Order: {order.order_id}",
                    node_type="WORK_ORDER",
                    attributes={
                        "bom_id": order.bom_id,
                        "planned_quantity": order.planned_quantity,
                        "produced_quantity": order.produced_quantity,
                        "yield_percentage": round((order.produced_quantity / order.planned_quantity) * 100, 2) if order.planned_quantity > 0 else 0.0,
                        "status": order.status,
                        "order_date": order.order_date.isoformat(),
                    }
                )
                graph.add_node(order_node)
                graph.add_edge(GraphEdge(
                    source=order.order_id,
                    target=fin_lot.lot_id,
                    relationship="PRODUCES",
                    quantity=fin_lot.quantity_produced,
                    uom=fin_lot.unit_of_measure,
                ))

                # Traverse Consumptions
                for consumption in order.consumptions:
                    raw_lot = consumption.material_lot
                    if not raw_lot:
                        continue

                    # Node: Material Lot
                    raw_node = GraphNode(
                        id=raw_lot.lot_id,
                        label=f"Raw Lot: {raw_lot.lot_id}",
                        node_type="RAW_LOT",
                        is_contaminated=raw_lot.is_contaminated,
                        attributes={
                            "material_name": raw_lot.material_name,
                            "material_category": raw_lot.material_category,
                            "supplier_id": raw_lot.supplier_id,
                            "initial_quantity": raw_lot.initial_quantity,
                            "current_quantity": raw_lot.current_quantity,
                            "unit_of_measure": raw_lot.unit_of_measure,
                            "quality_status": raw_lot.quality_status,
                            "received_date": raw_lot.received_date.isoformat(),
                        }
                    )
                    graph.add_node(raw_node)
                    graph.add_edge(GraphEdge(
                        source=raw_lot.lot_id,
                        target=order.order_id,
                        relationship="CONSUMED_IN",
                        quantity=consumption.quantity_consumed,
                        uom=consumption.unit_of_measure,
                    ))

                    consumed_materials_summary.append({
                        "raw_lot_id": raw_lot.lot_id,
                        "material_name": raw_lot.material_name,
                        "category": raw_lot.material_category,
                        "quantity_consumed": consumption.quantity_consumed,
                        "uom": consumption.unit_of_measure,
                        "is_contaminated": raw_lot.is_contaminated,
                        "supplier_id": raw_lot.supplier_id,
                    })

                    # Traverse Supplier
                    supplier = raw_lot.supplier
                    if supplier:
                        sup_node = GraphNode(
                            id=supplier.supplier_id,
                            label=f"Supplier: {supplier.name}",
                            node_type="SUPPLIER",
                            attributes={
                                "supplier_code": supplier.supplier_code,
                                "category": supplier.category,
                                "country": supplier.country,
                                "contact_email": supplier.contact_email,
                            }
                        )
                        graph.add_node(sup_node)
                        graph.add_edge(GraphEdge(
                            source=supplier.supplier_id,
                            target=raw_lot.lot_id,
                            relationship="SUPPLIES",
                            quantity=raw_lot.initial_quantity,
                            uom=raw_lot.unit_of_measure,
                        ))

                        suppliers_summary.append({
                            "supplier_id": supplier.supplier_id,
                            "supplier_name": supplier.name,
                            "supplier_code": supplier.supplier_code,
                            "category": supplier.category,
                            "country": supplier.country,
                        })

            # Deduplicate suppliers in summary
            unique_suppliers = {s["supplier_id"]: s for s in suppliers_summary}.values()

            return {
                "found": True,
                "finished_lot_id": finished_lot_id,
                "product_name": fin_lot.product.product_name if fin_lot.product else "Unknown",
                "production_order_id": order.order_id if order else None,
                "total_consumed_raw_lots": len(consumed_materials_summary),
                "total_suppliers": len(unique_suppliers),
                "consumed_materials": consumed_materials_summary,
                "suppliers": list(unique_suppliers),
                "graph": graph.to_dict(),
            }
        finally:
            if session_cm:
                session_cm.__exit__(None, None, None)

    def get_downstream_genealogy(
        self,
        source_lot_id: str,
        lot_type: str = "AUTO",
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        DOWNSTREAM TRACEABILITY:
        Source Lot (Raw or Finished) -> Production Orders -> Finished Lots -> Shipments -> Deliveries -> Customers.
        """
        logger.info(f"Traversing downstream genealogy for source lot: {source_lot_id}")
        session_cm = None
        if db is not None:
            session = db
        elif self._external_session:
            session = self._external_session
        else:
            session_cm = get_db_session()
            session = session_cm.__enter__()

        try:
            # Auto-detect lot type if needed
            is_raw = False
            raw_lot = session.query(MaterialLot).filter(MaterialLot.lot_id == source_lot_id).first()
            if raw_lot:
                is_raw = True
            else:
                fin_lot = session.query(FinishedLot).filter(FinishedLot.lot_id == source_lot_id).first()
                if not fin_lot:
                    return {"error": f"Lot '{source_lot_id}' not found in raw or finished lots", "found": False}

            graph = TraceabilityGraph(root_id=source_lot_id, direction="DOWNSTREAM")

            visited_lots: Set[str] = set()
            visited_orders: Set[str] = set()
            visited_shipments: Set[str] = set()
            visited_deliveries: Set[str] = set()
            visited_customers: Set[str] = set()

            affected_finished_lots: List[Dict[str, Any]] = []
            affected_shipments: List[Dict[str, Any]] = []
            affected_deliveries: List[Dict[str, Any]] = []
            affected_customers: List[Dict[str, Any]] = []

            total_recalled_qty = 0.0

            if is_raw:
                # Add Raw Lot Node
                graph.add_node(GraphNode(
                    id=raw_lot.lot_id,
                    label=f"Raw Lot: {raw_lot.lot_id}",
                    node_type="RAW_LOT",
                    is_contaminated=raw_lot.is_contaminated,
                    attributes={
                        "material_name": raw_lot.material_name,
                        "material_category": raw_lot.material_category,
                        "supplier_id": raw_lot.supplier_id,
                        "quality_status": raw_lot.quality_status,
                    }
                ))

                # Trace all work orders consuming this raw lot
                consumptions = session.query(ProductionConsumption).filter(
                    ProductionConsumption.material_lot_id == source_lot_id
                ).all()

                for cons in consumptions:
                    order = cons.production_order
                    if not order or order.order_id in visited_orders:
                        continue
                    visited_orders.add(order.order_id)

                    graph.add_node(GraphNode(
                        id=order.order_id,
                        label=f"Work Order: {order.order_id}",
                        node_type="WORK_ORDER",
                        attributes={
                            "product_id": order.product_id,
                            "produced_quantity": order.produced_quantity,
                            "status": order.status,
                        }
                    ))
                    graph.add_edge(GraphEdge(
                        source=source_lot_id,
                        target=order.order_id,
                        relationship="CONSUMED_IN",
                        quantity=cons.quantity_consumed,
                        uom=cons.unit_of_measure,
                    ))

                    # Trace finished lots produced by this order
                    for f_lot in order.finished_lots:
                        self._trace_downstream_finished_lot(
                            session, f_lot, order.order_id, graph,
                            visited_lots, visited_shipments, visited_deliveries, visited_customers,
                            affected_finished_lots, affected_shipments, affected_deliveries, affected_customers
                        )
            else:
                # Starting directly from a finished lot
                self._trace_downstream_finished_lot(
                    session, fin_lot, None, graph,
                    visited_lots, visited_shipments, visited_deliveries, visited_customers,
                    affected_finished_lots, affected_shipments, affected_deliveries, affected_customers
                )

            # Sum total delivered quantity across affected deliveries
            for d in affected_deliveries:
                total_recalled_qty += d["quantity_delivered"]

            return {
                "found": True,
                "source_lot_id": source_lot_id,
                "source_lot_type": "RAW" if is_raw else "FINISHED",
                "total_affected_production_orders": len(visited_orders),
                "total_affected_finished_lots": len(affected_finished_lots),
                "total_affected_shipments": len(affected_shipments),
                "total_affected_deliveries": len(affected_deliveries),
                "total_affected_customers": len(affected_customers),
                "total_delivered_quantity": round(total_recalled_qty, 2),
                "affected_finished_lots": affected_finished_lots,
                "affected_shipments": affected_shipments,
                "affected_deliveries": affected_deliveries,
                "affected_customers": affected_customers,
                "graph": graph.to_dict(),
            }
        finally:
            if session_cm:
                session_cm.__exit__(None, None, None)

    def _trace_downstream_finished_lot(
        self,
        session: Session,
        f_lot: FinishedLot,
        parent_order_id: Optional[str],
        graph: TraceabilityGraph,
        visited_lots: Set[str],
        visited_shipments: Set[str],
        visited_deliveries: Set[str],
        visited_customers: Set[str],
        affected_finished_lots: List[Dict[str, Any]],
        affected_shipments: List[Dict[str, Any]],
        affected_deliveries: List[Dict[str, Any]],
        affected_customers: List[Dict[str, Any]],
    ):
        """Helper to trace finished lot into shipments, deliveries, and customers."""
        if f_lot.lot_id not in visited_lots:
            visited_lots.add(f_lot.lot_id)
            graph.add_node(GraphNode(
                id=f_lot.lot_id,
                label=f"Finished Lot: {f_lot.lot_id}",
                node_type="FINISHED_LOT",
                is_contaminated=f_lot.is_contaminated,
                is_affected=True,
                attributes={
                    "product_id": f_lot.product_id,
                    "product_name": f_lot.product.product_name if f_lot.product else "Unknown",
                    "quantity_produced": f_lot.quantity_produced,
                    "quantity_available": f_lot.quantity_available,
                    "unit_of_measure": f_lot.unit_of_measure,
                    "quality_status": f_lot.quality_status,
                }
            ))

            if parent_order_id:
                graph.add_edge(GraphEdge(
                    source=parent_order_id,
                    target=f_lot.lot_id,
                    relationship="PRODUCES",
                    quantity=f_lot.quantity_produced,
                    uom=f_lot.unit_of_measure,
                ))

            affected_finished_lots.append({
                "finished_lot_id": f_lot.lot_id,
                "product_id": f_lot.product_id,
                "product_name": f_lot.product.product_name if f_lot.product else "Unknown",
                "quantity_produced": f_lot.quantity_produced,
                "quantity_available": f_lot.quantity_available,
                "unit_of_measure": f_lot.unit_of_measure,
                "quality_status": f_lot.quality_status,
            })

        # Trace outbound shipments carrying this finished lot
        for s_item in f_lot.shipment_items:
            shipment = s_item.shipment
            if not shipment:
                continue

            if shipment.shipment_id not in visited_shipments:
                visited_shipments.add(shipment.shipment_id)
                graph.add_node(GraphNode(
                    id=shipment.shipment_id,
                    label=f"Shipment: {shipment.shipment_id}",
                    node_type="SHIPMENT",
                    attributes={
                        "tracking_number": shipment.tracking_number,
                        "carrier": shipment.carrier,
                        "ship_date": shipment.ship_date.isoformat(),
                        "status": shipment.status,
                    }
                ))

                affected_shipments.append({
                    "shipment_id": shipment.shipment_id,
                    "tracking_number": shipment.tracking_number,
                    "carrier": shipment.carrier,
                    "ship_date": shipment.ship_date.isoformat(),
                    "status": shipment.status,
                })

            graph.add_edge(GraphEdge(
                source=f_lot.lot_id,
                target=shipment.shipment_id,
                relationship="SHIPPED_IN",
                quantity=s_item.quantity_shipped,
                uom=s_item.unit_of_measure,
            ))

            # Trace deliveries of this shipment
            for delivery in shipment.deliveries:
                if delivery.delivery_id not in visited_deliveries:
                    visited_deliveries.add(delivery.delivery_id)
                    affected_deliveries.append({
                        "delivery_id": delivery.delivery_id,
                        "shipment_id": shipment.shipment_id,
                        "customer_id": delivery.customer_id,
                        "customer_name": delivery.customer.customer_name if delivery.customer else "Unknown",
                        "delivery_date": delivery.delivery_date.isoformat(),
                        "quantity_delivered": delivery.quantity_delivered,
                        "status": delivery.status,
                    })

                customer = delivery.customer
                if customer and customer.customer_id not in visited_customers:
                    visited_customers.add(customer.customer_id)
                    graph.add_node(GraphNode(
                        id=customer.customer_id,
                        label=f"Customer: {customer.customer_name}",
                        node_type="CUSTOMER",
                        is_affected=True,
                        attributes={
                            "customer_type": customer.customer_type,
                            "contact_email": customer.contact_email,
                            "city": customer.city,
                            "state": customer.state,
                            "risk_tier": customer.risk_tier,
                        }
                    ))

                    affected_customers.append({
                        "customer_id": customer.customer_id,
                        "customer_name": customer.customer_name,
                        "customer_type": customer.customer_type,
                        "contact_email": customer.contact_email,
                        "contact_phone": customer.contact_phone,
                        "city": customer.city,
                        "state": customer.state,
                        "risk_tier": customer.risk_tier,
                    })

                if customer:
                    graph.add_edge(GraphEdge(
                        source=shipment.shipment_id,
                        target=customer.customer_id,
                        relationship="DELIVERED_TO",
                        quantity=delivery.quantity_delivered,
                    ))
