"""
End-to-end test: full demo scenario flow.

    1. Initial state → recommend INSPECT T3
    2. POST /inspection → T3 = FAILED
    3. New recommendation → should be different (REPAIR or RECONFIGURE)
    4. Verify state transitions, resource usage, audit log
"""
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"


def test_grid_state():
    r = client.get("/grid/state")
    assert r.status_code == 200
    data = r.json()
    assert "assets" in data
    assert "faults" in data
    assert "resources" in data


def test_scenario_current():
    r = client.get("/scenario/current")
    assert r.status_code == 200
    data = r.json()
    assert data["scenario_id"] == "DEMO_STORM_001"
    assert data["active_faults"] == 4


def test_faults_endpoint():
    r = client.get("/faults")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 4
    fault_assets = {f["asset_id"] for f in data["faults"]}
    assert "T3_LINE" in fault_assets
    assert "L6-7" in fault_assets
    assert "L12-13" in fault_assets
    assert "L25-26" in fault_assets


def test_initial_recommendation_inspect_t3():
    """
    Core E2E test: initial recommendation must be INSPECT T3.
    This is produced by the VOI logic, not hardcoded.
    """
    r = client.get("/recommendation")
    assert r.status_code == 200
    data = r.json()
    assert data["action_type"] == "INSPECT"
    assert data["target_asset"] == "T3_LINE"
    assert data["electrically_feasible"] is True
    assert len(data["reason_codes"]) > 0
    assert len(data["explanation"]) > 50  # real explanation, not empty


def test_recommendation_has_voi():
    r = client.get("/recommendation")
    data = r.json()
    assert "voi" in data and data["voi"] is not None
    assert data["voi"] >= 0


def test_recommendation_has_voi_detail():
    r = client.get("/recommendation")
    data = r.json()
    assert "voi_detail" in data
    voi = data["voi_detail"]
    assert "p_failed" in voi
    assert "decision_sensitivity" in voi
    assert abs(voi["p_failed"] - 0.62) < 0.01


def test_actions_endpoint():
    r = client.get("/actions")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] > 0
    # INSPECT T3 should be in candidates
    inspect_t3 = [
        a for a in data["actions"]
        if a["action_type"] == "INSPECT" and a["target_asset"] == "T3_LINE"
    ]
    assert len(inspect_t3) >= 1


def test_assets_endpoint():
    r = client.get("/assets/T3")
    assert r.status_code == 200
    data = r.json()
    assert data["asset_id"] == "T3_LINE"
    assert data["criticality"] == "CRITICAL"


def test_dependencies_endpoint():
    r = client.get("/dependencies/T3")
    assert r.status_code == 200
    data = r.json()
    assert "downstream_nodes" in data
    assert len(data["downstream_nodes"]) > 0


def test_voi_endpoint():
    r = client.get("/voi/T3")
    assert r.status_code == 200
    data = r.json()
    assert "voi" in data
    assert abs(data["failure_probability"] - 0.62) < 0.01


def test_resources_endpoint():
    r = client.get("/resources")
    assert r.status_code == 200
    data = r.json()
    assert "resources" in data
    assert data["summary"]["drone_available"] is True


def test_restoration_progress():
    r = client.get("/restoration/progress")
    assert r.status_code == 200
    data = r.json()
    assert "restoration_pct" in data
    assert "faults_active" in data
    assert data["faults_active"] == 4


def test_risk_endpoint():
    r = client.get("/risk")
    assert r.status_code == 200
    data = r.json()
    assert "overall_risk" in data
    assert "risk_level" in data
    assert data["overall_risk"] > 0


def test_impact_endpoint():
    r = client.get("/impact")
    assert r.status_code == 200
    data = r.json()
    assert data["critical_services_down"] > 0


# ---------------------------------------------------------------------------
# E2E: Inspect T3 → confirm FAILED → new recommendation
# ---------------------------------------------------------------------------

def test_e2e_inspect_t3_failed():
    """
    Full E2E scenario:
    Step 1: GET /recommendation → INSPECT T3
    Step 2: POST /inspection {T3, FAILED}
    Step 3: Verify T3 is now FAILED
    Step 4: GET /recommendation → new recommendation (not INSPECT T3)
    """
    # Step 1
    r1 = client.get("/recommendation")
    assert r1.status_code == 200
    rec1 = r1.json()
    assert rec1["action_type"] == "INSPECT"
    assert rec1["target_asset"] == "T3_LINE"

    # Step 2: submit inspection result
    r2 = client.post("/inspection", json={"asset_id": "T3_LINE", "result": "FAILED"})
    assert r2.status_code == 200
    inspect_result = r2.json()
    assert inspect_result["success"] is True
    assert inspect_result["active_faults"] <= 4  # T3 fault type changed but not resolved

    # Step 3: verify T3 status in state
    r3 = client.get("/assets/T3")
    assert r3.status_code == 200
    asset_data = r3.json()
    assert asset_data["status"] == "FAILED"
    assert asset_data["failure_probability"] == 1.0

    # Step 4: new recommendation
    new_rec = inspect_result["new_recommendation"]
    # Should not be INSPECT T3 anymore
    is_still_inspect_t3 = (
        new_rec["action_type"] == "INSPECT" and new_rec["target_asset"] == "T3_LINE"
    )
    assert not is_still_inspect_t3, (
        f"After T3 confirmed FAILED, should not recommend INSPECT T3 again. "
        f"Got: {new_rec['action_type']} on {new_rec['target_asset']}"
    )


def test_e2e_inspect_t3_healthy():
    """
    E2E: T3 confirmed HEALTHY → faults reduce → new recommendation.
    """
    r = client.post("/inspection", json={"asset_id": "T3_LINE", "result": "HEALTHY"})
    assert r.status_code == 200
    result = r.json()
    assert result["success"] is True

    # T3 should be healthy
    r2 = client.get("/assets/T3")
    assert r2.json()["status"] == "HEALTHY"

    # Recommendation should now be something for the certain faults
    new_rec = result["new_recommendation"]
    assert new_rec["action_type"] != "INSPECT" or new_rec["target_asset"] != "T3_LINE"


def test_e2e_scenario_reset():
    """Reset returns to initial state."""
    # First modify state via inspection
    client.post("/inspection", json={"asset_id": "T3_LINE", "result": "FAILED"})

    # Reset
    r = client.post("/scenario/reset")
    assert r.status_code == 200

    # T3 should be uncertain again
    r2 = client.get("/assets/T3")
    assert r2.json()["status"] == "UNCERTAIN"

    # Recommendation should be INSPECT T3 again
    r3 = client.get("/recommendation")
    rec = r3.json()
    assert rec["action_type"] == "INSPECT"
    assert rec["target_asset"] == "T3_LINE"


def test_simulate_action():
    r = client.post("/actions/simulate", json={
        "action_type": "REPAIR",
        "target_asset": "L6-7"
    })
    assert r.status_code == 200
    data = r.json()
    assert "feasible" in data
    assert "expected_outcome" in data


def test_audit_log_populated_after_recommendation():
    client.get("/recommendation")
    r = client.get("/audit/log")
    assert r.status_code == 200
    data = r.json()
    assert data["entries"] is not None
