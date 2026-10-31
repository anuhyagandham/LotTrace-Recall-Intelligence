"""
Tests for Flask REST API Endpoints.
"""

def test_api_health(flask_test_client):
    res = flask_test_client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["status"] == "HEALTHY"
    assert data["database_connected"] is True


def test_api_dashboard_summary(flask_test_client):
    res = flask_test_client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "dataset_metrics" in data
    assert "data_quality_metrics" in data
    assert "recall_metrics" in data


def test_api_suppliers(flask_test_client):
    res = flask_test_client.get("/api/suppliers?page=1&page_size=10")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["items"]) <= 10
    assert data["total_records"] > 0


def test_api_material_lots(flask_test_client):
    res = flask_test_client.get("/api/material-lots?page=1&page_size=5")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["items"]) == 5

    first_lot_id = data["items"][0]["lot_id"]
    detail_res = flask_test_client.get(f"/api/material-lots/{first_lot_id}")
    assert detail_res.status_code == 200
    assert detail_res.get_json()["material_lot"]["lot_id"] == first_lot_id

    # Genealogy
    gen_res = flask_test_client.get(f"/api/material-lots/{first_lot_id}/genealogy")
    assert gen_res.status_code == 200
    assert gen_res.get_json()["genealogy"]["found"] is True


def test_api_recalls(flask_test_client):
    res = flask_test_client.get("/api/recalls")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["total_records"] > 0

    first_recall_id = data["items"][0]["recall_id"]
    report_res = flask_test_client.get(f"/api/recalls/{first_recall_id}/report")
    assert report_res.status_code == 200
    assert report_res.get_json()["recall"]["recall_id"] == first_recall_id


def test_api_validation_report(flask_test_client):
    res = flask_test_client.get("/api/validation/report")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "summary" in data
    assert data["summary"]["passed_checks"] > 0
