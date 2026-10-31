"""
Flask REST API for LotTrace AI.
Provides complete enterprise endpoints for supply chain traceability,
genealogy graphs, recall management, validation audits, and operational analytics.
"""

import os
from datetime import datetime
from flask import Flask, request, jsonify
from sqlalchemy.orm import Session
from config import API_HOST, API_PORT
from src.database.connection import get_db_session
from src.models import (
    Supplier,
    MaterialLot,
    Product,
    BOM,
    ProductionOrder,
    FinishedLot,
    Shipment,
    Delivery,
    Customer,
    RecallCase,
    RecallAction,
    RecallEvent,
    CustomerNotification,
    ValidationIssue,
)
from src.genealogy.traversal import GenealogyService
from src.recall.engine import RecallEngine
from src.validation.validator import BusinessValidator
from src.analytics.metrics import MetricsCalculator
from src.utils.logging_config import setup_logger

logger = setup_logger("lottrace_api")


def create_app() -> Flask:
    """Application factory for LotTrace AI REST API."""
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    def paginate_query(query, page: int = 1, page_size: int = 50):
        """Helper to paginate SQLAlchemy queries cleanly."""
        total = query.count()
        page = max(1, page)
        page_size = min(max(1, page_size), 500)
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        return {
            "page": page,
            "page_size": page_size,
            "total_records": total,
            "total_pages": total_pages,
            "items": [item.to_dict() for item in items if hasattr(item, "to_dict")],
        }

    # ------------------------------------------------------------------------
    # Error Handlers
    # ------------------------------------------------------------------------
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": "Bad Request", "message": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "Not Found", "message": str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.exception(f"Internal server error: {error}")
        return jsonify({"success": False, "error": "Internal Server Error", "message": "An unexpected error occurred"}), 500

    # ------------------------------------------------------------------------
    # Health & System Status
    # ------------------------------------------------------------------------
    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint verifying DB connectivity."""
        try:
            with get_db_session() as session:
                sup_count = session.query(Supplier).count()
            return jsonify({
                "success": True,
                "status": "HEALTHY",
                "service": "LotTrace AI REST API",
                "database_connected": True,
                "suppliers_in_db": sup_count,
                "timestamp": datetime.utcnow().isoformat(),
            }), 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                "success": False,
                "status": "UNHEALTHY",
                "database_connected": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }), 503

    # ------------------------------------------------------------------------
    # Executive Dashboard Summary
    # ------------------------------------------------------------------------
    @app.route("/api/dashboard/summary", methods=["GET"])
    def dashboard_summary():
        """Returns consolidated dataset counts, quality scores, and recall metrics."""
        with get_db_session() as session:
            calc = MetricsCalculator(session=session)
            dataset_metrics = calc.get_dataset_metrics()
            quality_metrics = calc.get_data_quality_metrics()
            recall_metrics = calc.get_recall_performance_metrics()

        return jsonify({
            "success": True,
            "dataset_metrics": dataset_metrics,
            "data_quality_metrics": quality_metrics,
            "recall_metrics": recall_metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }), 200

    # ------------------------------------------------------------------------
    # Master Suppliers
    # ------------------------------------------------------------------------
    @app.route("/api/suppliers", methods=["GET"])
    def get_suppliers():
        """Lists approved suppliers with optional search and category filters."""
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 50, type=int)
        category = request.args.get("category")
        status = request.args.get("status")
        query_str = request.args.get("q")

        with get_db_session() as session:
            q = session.query(Supplier)
            if category:
                q = q.filter(Supplier.category == category)
            if status:
                q = q.filter(Supplier.status == status)
            if query_str:
                q = q.filter(Supplier.name.ilike(f"%{query_str}%") | Supplier.supplier_code.ilike(f"%{query_str}%"))

            res = paginate_query(q, page=page, page_size=page_size)
            return jsonify({"success": True, **res}), 200

    # ------------------------------------------------------------------------
    # Raw Material Lots
    # ------------------------------------------------------------------------
    @app.route("/api/material-lots", methods=["GET"])
    def get_material_lots():
        """Lists raw material lots with pagination and contamination filters."""
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 50, type=int)
        is_contaminated = request.args.get("is_contaminated")
        supplier_id = request.args.get("supplier_id")
        category = request.args.get("category")

        with get_db_session() as session:
            q = session.query(MaterialLot)
            if is_contaminated is not None:
                is_contam_bool = is_contaminated.lower() in ["true", "1", "yes"]
                q = q.filter(MaterialLot.is_contaminated == is_contam_bool)
            if supplier_id:
                q = q.filter(MaterialLot.supplier_id == supplier_id)
            if category:
                q = q.filter(MaterialLot.material_category == category)

            res = paginate_query(q, page=page, page_size=page_size)
            return jsonify({"success": True, **res}), 200

    @app.route("/api/material-lots/<lot_id>", methods=["GET"])
    def get_material_lot_detail(lot_id: str):
        """Returns detailed master record of a single raw material lot."""
        with get_db_session() as session:
            lot = session.query(MaterialLot).filter(MaterialLot.lot_id == lot_id).first()
            if not lot:
                return jsonify({"success": False, "error": f"Material lot '{lot_id}' not found"}), 404
            return jsonify({"success": True, "material_lot": lot.to_dict()}), 200

    @app.route("/api/material-lots/<lot_id>/genealogy", methods=["GET"])
    def get_material_lot_genealogy(lot_id: str):
        """Downstream genealogy tracing from raw lot to finished lots, shipments, and customers."""
        with get_db_session() as session:
            service = GenealogyService(session=session)
            genealogy = service.get_downstream_genealogy(lot_id, db=session)
            if not genealogy.get("found"):
                return jsonify({"success": False, "error": genealogy.get("error")}), 404
            return jsonify({"success": True, "genealogy": genealogy}), 200

    # ------------------------------------------------------------------------
    # Finished Goods Lots
    # ------------------------------------------------------------------------
    @app.route("/api/finished-lots", methods=["GET"])
    def get_finished_lots():
        """Lists manufactured finished lots with pagination."""
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 50, type=int)
        is_contaminated = request.args.get("is_contaminated")
        product_id = request.args.get("product_id")

        with get_db_session() as session:
            q = session.query(FinishedLot)
            if is_contaminated is not None:
                is_contam_bool = is_contaminated.lower() in ["true", "1", "yes"]
                q = q.filter(FinishedLot.is_contaminated == is_contam_bool)
            if product_id:
                q = q.filter(FinishedLot.product_id == product_id)

            res = paginate_query(q, page=page, page_size=page_size)
            return jsonify({"success": True, **res}), 200

    @app.route("/api/finished-lots/<lot_id>/genealogy", methods=["GET"])
    def get_finished_lot_genealogy(lot_id: str):
        """Upstream genealogy tracing from finished lot to raw ingredients and suppliers."""
        with get_db_session() as session:
            service = GenealogyService(session=session)
            genealogy = service.get_upstream_genealogy(lot_id, db=session)
            if not genealogy.get("found"):
                return jsonify({"success": False, "error": genealogy.get("error")}), 404
            return jsonify({"success": True, "genealogy": genealogy}), 200

    # ------------------------------------------------------------------------
    # Production Work Orders
    # ------------------------------------------------------------------------
    @app.route("/api/production-orders", methods=["GET"])
    def get_production_orders():
        """Lists manufacturing production orders and consumption yields."""
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 50, type=int)
        status = request.args.get("status")

        with get_db_session() as session:
            q = session.query(ProductionOrder)
            if status:
                q = q.filter(ProductionOrder.status == status)

            res = paginate_query(q, page=page, page_size=page_size)
            return jsonify({"success": True, **res}), 200

    # ------------------------------------------------------------------------
    # Outbound Logistics & Distribution
    # ------------------------------------------------------------------------
    @app.route("/api/shipments", methods=["GET"])
    def get_shipments():
        """Lists freight shipments."""
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 50, type=int)
        carrier = request.args.get("carrier")

        with get_db_session() as session:
            q = session.query(Shipment)
            if carrier:
                q = q.filter(Shipment.carrier == carrier)

            res = paginate_query(q, page=page, page_size=page_size)
            return jsonify({"success": True, **res}), 200

    @app.route("/api/customers", methods=["GET"])
    def get_customers():
        """Lists healthcare institutions and customer consignees."""
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 50, type=int)
        risk_tier = request.args.get("risk_tier")

        with get_db_session() as session:
            q = session.query(Customer)
            if risk_tier:
                q = q.filter(Customer.risk_tier == risk_tier)

            res = paginate_query(q, page=page, page_size=page_size)
            return jsonify({"success": True, **res}), 200

    # ------------------------------------------------------------------------
    # Recall Management Endpoints
    # ------------------------------------------------------------------------
    @app.route("/api/recalls", methods=["GET"])
    def get_recalls():
        """Lists product recall cases with status and severity filters."""
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 50, type=int)
        status = request.args.get("status")
        severity = request.args.get("severity")

        with get_db_session() as session:
            q = session.query(RecallCase)
            if status:
                q = q.filter(RecallCase.status == status)
            if severity:
                q = q.filter(RecallCase.severity == severity)

            res = paginate_query(q, page=page, page_size=page_size)
            return jsonify({"success": True, **res}), 200

    @app.route("/api/recalls/<recall_id>", methods=["GET"])
    def get_recall_detail(recall_id: str):
        """Returns single recall dossier with metrics and status."""
        with get_db_session() as session:
            recall = session.query(RecallCase).filter(RecallCase.recall_id == recall_id).first()
            if not recall:
                return jsonify({"success": False, "error": f"Recall case '{recall_id}' not found"}), 404
            return jsonify({"success": True, "recall": recall.to_dict()}), 200

    @app.route("/api/recalls", methods=["POST"])
    def create_recall():
        """Initiates a new product recall docket for a contaminated raw or finished lot."""
        data = request.get_json() or {}
        source_lot_id = data.get("source_lot_id")
        title = data.get("title", f"Recall Investigation for {source_lot_id}")
        trigger_type = data.get("trigger_type", "CONTAMINATED_RAW_LOT")
        severity = data.get("severity", "CLASS_I")
        target_days = data.get("target_days", 30)

        if not source_lot_id:
            return jsonify({"success": False, "error": "Field 'source_lot_id' is required"}), 400

        try:
            with get_db_session() as session:
                engine = RecallEngine(session=session)
                res = engine.create_recall(
                    source_lot_id=source_lot_id,
                    title=title,
                    trigger_type=trigger_type,
                    severity=severity,
                    target_days=target_days,
                    db=session,
                )
                return jsonify(res), 201
        except Exception as e:
            logger.error(f"Failed to create recall: {e}")
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/recalls/<recall_id>/process", methods=["POST"])
    def process_recall(recall_id: str):
        """Executes idempotent containment, quarantine, customer notifications, and recovery."""
        data = request.get_json() or {}
        recovery_factor = float(data.get("recovery_factor", 0.85))

        try:
            with get_db_session() as session:
                engine = RecallEngine(session=session)
                res = engine.process_recall(
                    recall_id=recall_id,
                    recovery_factor=recovery_factor,
                    db=session,
                )
                return jsonify(res), 200
        except Exception as e:
            logger.error(f"Failed to process recall {recall_id}: {e}")
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/recalls/<recall_id>/actions", methods=["POST"])
    def add_recall_action(recall_id: str):
        """Manually appends an operational containment task to a recall case."""
        data = request.get_json() or {}
        action_type = data.get("action_type")
        target_entity_type = data.get("target_entity_type", "LOT")
        target_entity_id = data.get("target_entity_id")
        assigned_to = data.get("assigned_to", "Field Safety Inspector")
        notes = data.get("notes", "Manual containment action registered")

        if not action_type or not target_entity_id:
            return jsonify({"success": False, "error": "'action_type' and 'target_entity_id' are required"}), 400

        with get_db_session() as session:
            recall = session.query(RecallCase).filter(RecallCase.recall_id == recall_id).first()
            if not recall:
                return jsonify({"success": False, "error": f"Recall case '{recall_id}' not found"}), 404

            from src.generator.id_generator import generate_recall_action_id
            act_count = session.query(RecallAction).count()
            action = RecallAction(
                action_id=generate_recall_action_id(act_count + 1),
                recall_id=recall_id,
                action_type=action_type,
                target_entity_type=target_entity_type,
                target_entity_id=target_entity_id,
                status="PENDING",
                assigned_to=assigned_to,
                scheduled_date=datetime.utcnow(),
                notes=notes,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(action)
            session.flush()
            return jsonify({"success": True, "action": action.to_dict()}), 201

    @app.route("/api/recalls/<recall_id>/report", methods=["GET"])
    def get_recall_report(recall_id: str):
        """Returns full audit dossier, event history, actions, and downstream scope for a recall."""
        with get_db_session() as session:
            engine = RecallEngine(session=session)
            report = engine.get_recall_report(recall_id, db=session)
            if "error" in report:
                return jsonify({"success": False, "error": report["error"]}), 404
            return jsonify({"success": True, **report}), 200

    # ------------------------------------------------------------------------
    # Data Quality & Validation Report
    # ------------------------------------------------------------------------
    @app.route("/api/validation/report", methods=["GET"])
    def get_validation_report():
        """Runs and returns comprehensive data quality and business rule validation audit."""
        with get_db_session() as session:
            validator = BusinessValidator(session=session)
            report = validator.run_all_validations(db=session)
            return jsonify({"success": True, **report}), 200

    # ------------------------------------------------------------------------
    # Analytics & Recall Performance
    # ------------------------------------------------------------------------
    @app.route("/api/analytics/recall-performance", methods=["GET"])
    def get_recall_performance():
        """Returns consolidated recall containment metrics: coverage, recovery, completion."""
        with get_db_session() as session:
            calc = MetricsCalculator(session=session)
            perf = calc.get_recall_performance_metrics(db=session)
            return jsonify({"success": True, "performance": perf}), 200

    return app


app = create_app()

if __name__ == "__main__":
    logger.info(f"Starting LotTrace AI REST API server on http://{API_HOST}:{API_PORT}")
    app.run(host=API_HOST, port=API_PORT, debug=True)
