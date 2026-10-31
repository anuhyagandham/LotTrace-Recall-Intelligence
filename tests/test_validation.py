"""
Tests for Automated Business Validation Engine and Metrics.
"""

from src.database.connection import get_db_session
from src.validation.validator import BusinessValidator
from src.analytics.metrics import MetricsCalculator


def test_business_validation_suite_structure():
    with get_db_session() as session:
        validator = BusinessValidator(session=session)
        result = validator.run_all_validations(db=session)

        assert "summary" in result
        assert "issues" in result
        summary = result["summary"]

        assert summary["total_checks_evaluated"] > 1000
        assert summary["passed_checks"] > 0
        assert summary["failed_checks"] >= 4
        assert summary["validation_pass_rate_pct"] > 95.0


def test_metrics_calculator_outputs():
    with get_db_session() as session:
        calc = MetricsCalculator(session=session)
        dataset_metrics = calc.get_dataset_metrics(db=session)
        quality_metrics = calc.get_data_quality_metrics(db=session)
        recall_metrics = calc.get_recall_performance_metrics(db=session)

        assert dataset_metrics["total_suppliers"] > 0
        assert dataset_metrics["total_material_lots"] > 0
        assert dataset_metrics["total_finished_lots"] > 0

        assert quality_metrics["primary_key_integrity_pct"] == 100.0
        assert quality_metrics["overall_validation_pass_rate_pct"] > 95.0

        assert recall_metrics["total_recalls"] > 0
        assert "average_notification_coverage_pct" in recall_metrics
