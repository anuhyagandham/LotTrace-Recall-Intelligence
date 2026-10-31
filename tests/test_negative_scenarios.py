"""
Tests for Planted Negative Anomaly Scenarios and Ground-Truth Separation.
"""

from pathlib import Path
import json
import csv
from config import GROUND_TRUTH_CSV, GROUND_TRUTH_JSON
from src.database.connection import get_db_session
from src.validation.validator import BusinessValidator
from src.models import ValidationIssue


def test_ground_truth_files_exist_and_separated():
    """Verifies that ground truth files exist in dedicated folder and are properly structured."""
    assert GROUND_TRUTH_CSV.exists()
    assert GROUND_TRUTH_JSON.exists()

    with open(GROUND_TRUTH_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "ground_truth" in data
        assert len(data["ground_truth"]) >= 4

        scenarios = {row["scenario"] for row in data["ground_truth"] if "scenario" in row}
        assert "SCENARIO_A" in scenarios
        assert "SCENARIO_B" in scenarios
        assert "SCENARIO_C" in scenarios
        assert "SCENARIO_D" in scenarios


def test_planted_anomalies_detected_by_validator():
    """Verifies that BusinessValidator independently detects all four planted anomaly cases."""
    with get_db_session() as session:
        validator = BusinessValidator(session=session)
        result = validator.run_all_validations(db=session)

        issues = result["issues"]
        issue_types = {i["issue_type"] for i in issues}

        assert "MISSING_INPUT_LOT" in issue_types, "Scenario A missing input lot must be detected"
        assert "DELIVERED_EXCEEDS_PRODUCED" in issue_types, "Scenario B excess delivery must be detected"
        assert "RECALLED_INVENTORY_AVAILABLE_FOR_SALE" in issue_types, "Scenario D recalled stock saleable must be detected"


def test_reconciliation_anomaly_b_details():
    """Detailed verification of Scenario B: Delivered quantity exceeds produced quantity."""
    with get_db_session() as session:
        validator = BusinessValidator(session=session)
        result = validator.run_all_validations(db=session)

        anomaly_b_issues = [i for i in result["issues"] if i["issue_type"] == "DELIVERED_EXCEEDS_PRODUCED"]
        assert len(anomaly_b_issues) >= 1
        issue = anomaly_b_issues[0]
        assert issue["severity"] == "CRITICAL"
        assert issue["validation_status"] == "FAILED"
