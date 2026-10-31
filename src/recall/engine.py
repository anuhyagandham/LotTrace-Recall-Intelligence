"""
Intelligent Product Recall Management Engine for LotTrace AI.
Orchestrates end-to-end recall initiation, downstream scope traversal,
idempotent operational action dispatch, containment, and metric calculations.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from src.database.connection import get_db_session
from src.models import (
    RecallCase,
    RecallAction,
    RecallEvent,
    CustomerNotification,
    MaterialLot,
    FinishedLot,
    Inventory,
    InventoryEvent,
    Customer,
    Delivery,
    RecallStatus,
    RecallActionType,
    RecallActionStatus,
    NotificationChannel,
    NotificationStatus,
    InventoryEventType,
    QualityStatus,
)
from src.genealogy.traversal import GenealogyService
from src.generator.id_generator import (
    generate_recall_case_id,
    generate_recall_action_id,
    generate_recall_event_id,
    generate_customer_notification_id,
    generate_inventory_event_id,
)
from src.utils.logging_config import logger


class RecallEngine:
    """Enterprise Supply Chain Product Recall Management and Containment Engine."""

    def __init__(self, session: Optional[Session] = None):
        self._external_session = session
        self.genealogy_service = GenealogyService(session=session)

    def create_recall(
        self,
        source_lot_id: str,
        title: str,
        trigger_type: str = "CONTAMINATED_RAW_LOT",
        severity: str = "CLASS_I",
        target_days: int = 30,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Creates a new product recall docket, flags source contamination,
        and records initial audit events.
        """
        logger.info(f"Initiating recall docket for lot: {source_lot_id}")
        session_cm = None
        if db is not None:
            session = db
        elif self._external_session:
            session = self._external_session
        else:
            session_cm = get_db_session()
            session = session_cm.__enter__()

        try:
            # Determine source lot type
            raw_lot = session.query(MaterialLot).filter(MaterialLot.lot_id == source_lot_id).first()
            fin_lot = session.query(FinishedLot).filter(FinishedLot.lot_id == source_lot_id).first()

            if not raw_lot and not fin_lot:
                raise ValueError(f"Lot '{source_lot_id}' does not exist in master records")

            source_type = "RAW" if raw_lot else "FINISHED"

            # Count existing recall cases to generate next deterministic ID
            existing_count = session.query(RecallCase).count()
            recall_id = generate_recall_case_id(existing_count + 1)

            # Mark source lot contaminated
            if raw_lot:
                raw_lot.is_contaminated = True
                raw_lot.quality_status = QualityStatus.CONTAMINATED.value
            if fin_lot:
                fin_lot.is_contaminated = True
                fin_lot.quality_status = QualityStatus.CONTAMINATED.value

            init_date = datetime.utcnow()
            target_date = init_date + timedelta(days=target_days)

            # Pre-calculate scope via genealogy
            scope = self.genealogy_service.get_downstream_genealogy(source_lot_id, db=session)

            total_affected_lots = scope.get("total_affected_finished_lots", 0)
            total_affected_dels = scope.get("total_affected_deliveries", 0)
            total_affected_custs = scope.get("total_affected_customers", 0)
            total_recalled_qty = scope.get("total_delivered_quantity", 0.0)

            recall = RecallCase(
                recall_id=recall_id,
                title=title,
                trigger_type=trigger_type,
                source_lot_id=source_lot_id,
                source_lot_type=source_type,
                severity=severity,
                initiated_date=init_date,
                target_completion_date=target_date,
                status=RecallStatus.OPEN.value,
                closure_date=None,
                total_affected_finished_lots=total_affected_lots,
                total_affected_deliveries=total_affected_dels,
                total_affected_customers=total_affected_custs,
                total_recalled_quantity=total_recalled_qty,
                total_quarantined_quantity=0.0,
                total_recovered_quantity=0.0,
                notification_coverage_pct=0.0,
                recovery_rate_pct=0.0,
                recall_completion_pct=0.0,
                created_at=init_date,
                updated_at=init_date,
            )
            session.add(recall)

            # Audit Event
            event = RecallEvent(
                event_id=generate_recall_event_id(session.query(RecallEvent).count() + 1),
                recall_id=recall_id,
                previous_status="NONE",
                new_status=RecallStatus.OPEN.value,
                reason=f"Recall initiated for {source_type} lot {source_lot_id}. Scope: {total_affected_lots} finished lots, {total_affected_custs} customers.",
                trigger_source="RECALL_ENGINE",
                created_at=init_date,
            )
            session.add(event)
            session.flush()

            logger.info(f"Recall {recall_id} created successfully with {total_affected_lots} affected lots.")
            return {
                "success": True,
                "recall_id": recall_id,
                "scope": scope,
                "recall": recall.to_dict(),
            }
        finally:
            if session_cm:
                session_cm.__exit__(None, None, None)

    def process_recall(
        self,
        recall_id: str,
        recovery_factor: float = 0.85,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Executes idempotent end-to-end recall lifecycle:
        1. Quarantine affected warehouse inventory.
        2. Dispatches notifications to affected customers.
        3. Simulates product recovery and returns.
        4. Calculates final completion, coverage, and recovery metrics.
        """
        logger.info(f"Processing recall actions for {recall_id} (idempotent)")
        session_cm = None
        if db is not None:
            session = db
        elif self._external_session:
            session = self._external_session
        else:
            session_cm = get_db_session()
            session = session_cm.__enter__()

        try:
            recall = session.query(RecallCase).filter(RecallCase.recall_id == recall_id).first()
            if not recall:
                raise ValueError(f"Recall case '{recall_id}' not found")

            now = datetime.utcnow()

            # Step 1: Transition to INVESTIGATING if currently OPEN
            if recall.status == RecallStatus.OPEN.value:
                self._record_transition(session, recall, RecallStatus.INVESTIGATING.value, "Downstream genealogy scope analysis started")

            # Step 2: Get downstream scope
            scope = self.genealogy_service.get_downstream_genealogy(recall.source_lot_id, db=session)
            affected_fin_lots = scope.get("affected_finished_lots", [])
            affected_custs = scope.get("affected_customers", [])
            affected_dels = scope.get("affected_deliveries", [])

            # Update recall scope metrics
            recall.total_affected_finished_lots = len(affected_fin_lots)
            recall.total_affected_customers = len(affected_custs)
            recall.total_affected_deliveries = len(affected_dels)
            recall.total_recalled_quantity = scope.get("total_delivered_quantity", 0.0)

            # Step 3: Transition to CONTAINMENT_IN_PROGRESS
            if recall.status in [RecallStatus.OPEN.value, RecallStatus.INVESTIGATING.value]:
                self._record_transition(session, recall, RecallStatus.CONTAINMENT_IN_PROGRESS.value, "Initiating warehouse stock quarantine and hold")

            # Step 4: Quarantine Warehouse Inventories (Idempotent)
            all_affected_lot_ids = [recall.source_lot_id] + [f["finished_lot_id"] for f in affected_fin_lots]
            quarantined_total = 0.0

            action_seq = session.query(RecallAction).count()
            inv_evt_seq = session.query(InventoryEvent).count()

            for lot_id in all_affected_lot_ids:
                inventories = session.query(Inventory).filter(Inventory.lot_id == lot_id).all()
                for inv in inventories:
                    if inv.status != "QUARANTINED":
                        qty_to_quarantine = inv.quantity_on_hand
                        inv.quantity_quarantined += qty_to_quarantine
                        inv.quantity_on_hand = 0.0
                        inv.status = "QUARANTINED"
                        quarantined_total += qty_to_quarantine

                        # Record Quarantine Inventory Event
                        inv_evt_seq += 1
                        q_event = InventoryEvent(
                            event_id=generate_inventory_event_id(inv_evt_seq),
                            inventory_id=inv.inventory_id,
                            lot_id=lot_id,
                            event_type=InventoryEventType.QUARANTINE.value,
                            quantity_change=-qty_to_quarantine,
                            resulting_balance=0.0,
                            reference_type="RECALL_HOLD",
                            reference_id=recall_id,
                            event_date=now,
                            notes=f"Warehouse stock quarantined under recall {recall_id}",
                            created_at=now,
                        )
                        session.add(q_event)

                    # Check if action already exists
                    existing_action = session.query(RecallAction).filter(
                        RecallAction.recall_id == recall_id,
                        RecallAction.action_type == RecallActionType.QUARANTINE_INVENTORY.value,
                        RecallAction.target_entity_id == inv.inventory_id,
                    ).first()

                    if not existing_action:
                        action_seq += 1
                        q_action = RecallAction(
                            action_id=generate_recall_action_id(action_seq),
                            recall_id=recall_id,
                            action_type=RecallActionType.QUARANTINE_INVENTORY.value,
                            target_entity_type="INVENTORY",
                            target_entity_id=inv.inventory_id,
                            status=RecallActionStatus.COMPLETED.value,
                            assigned_to="Quality Assurance / Warehouse Operations",
                            scheduled_date=now,
                            completed_date=now,
                            notes=f"Locked bin {inv.location_bin} at {inv.warehouse_id} for lot {lot_id}",
                            created_at=now,
                            updated_at=now,
                        )
                        session.add(q_action)

            recall.total_quarantined_quantity = quarantined_total

            # Step 5: Customer Notifications (Idempotent)
            if recall.status == RecallStatus.CONTAINMENT_IN_PROGRESS.value:
                self._record_transition(session, recall, RecallStatus.CUSTOMERS_NOTIFIED.value, "Dispatching urgent customer safety notices")

            notif_seq = session.query(CustomerNotification).count()
            successful_notifs = 0

            for cust_info in affected_custs:
                cust_id = cust_info["customer_id"]
                # Check if notification already logged
                existing_notif = session.query(CustomerNotification).filter(
                    CustomerNotification.recall_id == recall_id,
                    CustomerNotification.customer_id == cust_id,
                ).first()

                if not existing_notif:
                    notif_seq += 1
                    notification = CustomerNotification(
                        notification_id=generate_customer_notification_id(notif_seq),
                        recall_id=recall_id,
                        customer_id=cust_id,
                        delivery_id=None,
                        finished_lot_id=affected_fin_lots[0]["finished_lot_id"] if affected_fin_lots else None,
                        notification_channel=NotificationChannel.REGISTERED_MAIL.value if cust_info.get("risk_tier") == "CRITICAL_HEALTHCARE" else NotificationChannel.EMAIL.value,
                        notification_status=NotificationStatus.ACKNOWLEDGED.value,
                        sent_at=now,
                        acknowledged_at=now + timedelta(hours=4),
                        response_notes=f"Customer safety contact {cust_info['contact_email']} confirmed stock quarantine at facility.",
                        created_at=now,
                    )
                    session.add(notification)
                    successful_notifs += 1
                else:
                    if existing_notif.notification_status in [NotificationStatus.ACKNOWLEDGED.value, NotificationStatus.SENT.value]:
                        successful_notifs += 1

                # Customer Notification Action
                existing_cust_action = session.query(RecallAction).filter(
                    RecallAction.recall_id == recall_id,
                    RecallAction.action_type == RecallActionType.CUSTOMER_NOTIFICATION.value,
                    RecallAction.target_entity_id == cust_id,
                ).first()

                if not existing_cust_action:
                    action_seq += 1
                    c_action = RecallAction(
                        action_id=generate_recall_action_id(action_seq),
                        recall_id=recall_id,
                        action_type=RecallActionType.CUSTOMER_NOTIFICATION.value,
                        target_entity_type="CUSTOMER",
                        target_entity_id=cust_id,
                        status=RecallActionStatus.COMPLETED.value,
                        assigned_to="Regulatory Affairs & Customer Care",
                        scheduled_date=now,
                        completed_date=now,
                        notes=f"Dispatched official recall notice to {cust_info['customer_name']}",
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(c_action)

            # Step 6: Recovery in Progress
            if recall.status == RecallStatus.CUSTOMERS_NOTIFIED.value:
                self._record_transition(session, recall, RecallStatus.RECOVERY_IN_PROGRESS.value, "Simulating product returns and field recovery")

            recovered_qty = round(recall.total_recalled_quantity * recovery_factor, 2)
            recall.total_recovered_quantity = recovered_qty

            existing_rec_action = session.query(RecallAction).filter(
                RecallAction.recall_id == recall_id,
                RecallAction.action_type == RecallActionType.PRODUCT_RECOVERY.value,
            ).first()

            if not existing_rec_action:
                action_seq += 1
                rec_action = RecallAction(
                    action_id=generate_recall_action_id(action_seq),
                    recall_id=recall_id,
                    action_type=RecallActionType.PRODUCT_RECOVERY.value,
                    target_entity_type="FINISHED_LOT",
                    target_entity_id=recall.source_lot_id,
                    status=RecallActionStatus.COMPLETED.value,
                    assigned_to="Reverse Logistics Team",
                    scheduled_date=now,
                    completed_date=now,
                    notes=f"Received {recovered_qty} units returned from field consignees.",
                    created_at=now,
                    updated_at=now,
                )
                session.add(rec_action)

            # Step 7: Calculate Evaluation Metrics
            # Notification Coverage: Notified Affected / Total Affected * 100
            total_cust = len(affected_custs)
            recall.notification_coverage_pct = round((successful_notifs / total_cust) * 100, 2) if total_cust > 0 else 100.0

            # Recovery Rate: Recovered Quantity / Total Recall-Eligible Quantity * 100
            total_eligible = recall.total_recalled_quantity
            recall.recovery_rate_pct = round((recovered_qty / total_eligible) * 100, 2) if total_eligible > 0 else 100.0

            # Recall Completion: Completed Actions / Total Actions * 100
            session.flush()
            all_actions = session.query(RecallAction).filter(RecallAction.recall_id == recall_id).all()
            completed_actions = [a for a in all_actions if a.status == RecallActionStatus.COMPLETED.value]
            recall.recall_completion_pct = round((len(completed_actions) / len(all_actions)) * 100, 2) if all_actions else 100.0

            # Step 8: Close recall if completion >= 90%
            if recall.recall_completion_pct >= 90.0:
                self._record_transition(session, recall, RecallStatus.COMPLETED.value, "All mandatory containment, notification, and recovery milestones satisfied")
                recall.closure_date = now

            recall.updated_at = now
            session.flush()

            logger.info(f"Recall {recall_id} processed. Coverage: {recall.notification_coverage_pct}%, Recovery: {recall.recovery_rate_pct}%, Completion: {recall.recall_completion_pct}%")

            return {
                "success": True,
                "recall_id": recall_id,
                "status": recall.status,
                "metrics": {
                    "total_affected_finished_lots": recall.total_affected_finished_lots,
                    "total_affected_customers": recall.total_affected_customers,
                    "total_recalled_quantity": recall.total_recalled_quantity,
                    "total_quarantined_quantity": recall.total_quarantined_quantity,
                    "total_recovered_quantity": recall.total_recovered_quantity,
                    "notification_coverage_pct": recall.notification_coverage_pct,
                    "recovery_rate_pct": recall.recovery_rate_pct,
                    "recall_completion_pct": recall.recall_completion_pct,
                },
                "actions_count": len(all_actions),
            }
        finally:
            if session_cm:
                session_cm.__exit__(None, None, None)

    def _record_transition(self, session: Session, recall: RecallCase, new_status: str, reason: str):
        """Records an immutable RecallEvent transition in the audit ledger."""
        prev = recall.status
        recall.status = new_status
        evt_count = session.query(RecallEvent).count()
        event = RecallEvent(
            event_id=generate_recall_event_id(evt_count + 1),
            recall_id=recall.recall_id,
            previous_status=prev,
            new_status=new_status,
            reason=reason,
            trigger_source="RECALL_ENGINE",
            created_at=datetime.utcnow(),
        )
        session.add(event)
        session.flush()

    def get_recall_report(self, recall_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """Returns comprehensive recall investigation and containment dossier."""
        session_cm = None
        if db is not None:
            session = db
        elif self._external_session:
            session = self._external_session
        else:
            session_cm = get_db_session()
            session = session_cm.__enter__()

        try:
            recall = session.query(RecallCase).filter(RecallCase.recall_id == recall_id).first()
            if not recall:
                return {"error": f"Recall '{recall_id}' not found"}

            actions = session.query(RecallAction).filter(RecallAction.recall_id == recall_id).all()
            events = session.query(RecallEvent).filter(RecallEvent.recall_id == recall_id).order_by(RecallEvent.created_at).all()
            notifications = session.query(CustomerNotification).filter(CustomerNotification.recall_id == recall_id).all()

            scope = self.genealogy_service.get_downstream_genealogy(recall.source_lot_id, db=session)

            return {
                "recall": recall.to_dict(),
                "scope": scope,
                "actions": [a.to_dict() for a in actions],
                "event_history": [e.to_dict() for e in events],
                "notifications": [n.to_dict() for n in notifications],
            }
        finally:
            if session_cm:
                session_cm.__exit__(None, None, None)
