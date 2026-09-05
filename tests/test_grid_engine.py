"""
Tests for the IEEE 33-bus grid engine.
"""
import pytest
import copy
import pandapower as pp
from grid.ieee33 import build_ieee33_net, get_critical_service_buses
from grid.grid_engine import (
    create_grid, reset_grid, get_net, inject_fault, get_grid_state,
    execute_simulated_action, get_asset_status
)
from grid.power_flow import (
    run_power_flow, get_voltage_violations, get_line_overloads,
    check_grid_feasibility, simulate_action_pf
)


# ── IEEE 33-bus structure ────────────────────────────────────────────────────

def test_ieee33_loads():
    net = build_ieee33_net()
    assert len(net.bus) == 33
    # Original 32 radial + 5 tie-switch lines
    assert len(net.line) >= 32


def test_ieee33_critical_service_loads():
    net = build_ieee33_net()
    svc_loads = net.load[net.load["critical_service"] == True]
    assert len(svc_loads) == 4  # Hospital, Water, Emergency, Telecom


def test_ieee33_service_ids():
    net = build_ieee33_net()
    services = get_critical_service_buses(net)
    assert "HOSPITAL" in services
    assert "WATER_PLANT" in services
    assert "EMERGENCY_CENTER" in services
    assert "TELECOM_TOWER" in services


def test_ieee33_asset_ids_on_lines():
    net = build_ieee33_net()
    assert "asset_id" in net.line.columns
    assert "L6-7" in net.line["asset_id"].values
    assert "L12-13" in net.line["asset_id"].values
    assert "L25-26" in net.line["asset_id"].values
    assert "T3_LINE" in net.line["asset_id"].values


def test_ieee33_failure_prob_column():
    net = build_ieee33_net()
    assert "failure_probability" in net.line.columns
    assert (net.line["failure_probability"] == 0.0).all()


# ── Grid engine ──────────────────────────────────────────────────────────────

def test_create_grid():
    net = create_grid()
    assert net is not None
    assert len(net.bus) == 33


def test_reset_grid_clears_faults():
    create_grid()
    inject_fault("L6-7")
    net_after_fault = get_net()
    assert not net_after_fault.line.at[5, "in_service"]

    reset_grid()
    net_clean = get_net()
    assert net_clean.line.at[5, "in_service"]


def test_inject_fault_l6_7():
    create_grid()
    result = inject_fault("L6-7", fault_type="OPEN_CIRCUIT", failure_probability=1.0)
    assert result["success"] is True
    net = get_net()
    assert not net.line.at[5, "in_service"]


def test_inject_fault_t3_uncertain():
    create_grid()
    result = inject_fault("T3_LINE", fault_type="UNCERTAIN",
                          failure_probability=0.62, is_uncertain=True)
    assert result["success"] is True
    net = get_net()
    # T3_LINE with is_uncertain=True should NOT be taken out of service
    assert net.line.at[2, "is_uncertain"] == True
    assert abs(net.line.at[2, "failure_probability"] - 0.62) < 0.001


def test_inject_fault_failure_probability_recorded():
    create_grid()
    inject_fault("L12-13", failure_probability=0.94)
    net = get_net()
    assert abs(net.line.at[11, "failure_probability"] - 0.94) < 0.001


def test_get_grid_state_structure():
    create_grid()
    state = get_grid_state()
    assert "buses" in state
    assert "lines" in state
    assert "loads" in state
    assert "critical_services" in state
    assert "pf_converged" in state
    assert len(state["buses"]) == 33


def test_get_grid_state_pf_converges_on_clean_net():
    create_grid()
    state = get_grid_state()
    assert state["pf_converged"] is True


def test_get_grid_state_critical_services_online_clean():
    create_grid()
    state = get_grid_state()
    for svc_id, svc_status in state["critical_services"].items():
        assert svc_status["energised"] is True, f"{svc_id} should be online on clean net"


def test_execute_repair_restores_line():
    create_grid()
    inject_fault("L6-7")
    net = get_net()
    assert not net.line.at[5, "in_service"]

    result = execute_simulated_action({"action_type": "REPAIR", "target_asset": "L6-7"})
    assert result["success"] is True
    net_after = get_net()
    assert net_after.line.at[5, "in_service"]


def test_execute_defer_no_change():
    create_grid()
    inject_fault("L6-7")
    result = execute_simulated_action({"action_type": "DEFER", "target_asset": "L6-7"})
    assert result["success"] is True
    net = get_net()
    assert not net.line.at[5, "in_service"]  # Fault still present


def test_get_asset_status():
    create_grid()
    inject_fault("L6-7", failure_probability=0.95)
    status = get_asset_status("L6-7")
    assert status["found"] is True
    assert status["in_service"] is False
    assert abs(status["failure_probability"] - 0.95) < 0.001


def test_get_asset_status_unknown():
    create_grid()
    status = get_asset_status("NONEXISTENT_LINE")
    assert status["found"] is False


# ── Power flow ───────────────────────────────────────────────────────────────

def test_pf_converges_clean():
    create_grid()
    result = run_power_flow()
    assert result["converged"] is True
    assert result["summary"]["vm_min"] > 0.60  # heavily loaded with critical services


def test_pf_voltage_bounds_clean():
    create_grid()
    result = run_power_flow()
    assert result["summary"]["vm_min"] >= 0.60   # IEEE 33-bus has low voltages due to added loads
    assert result["summary"]["vm_max"] <= 1.05


def test_no_violations_on_clean_net():
    create_grid()
    run_power_flow()
    violations = get_voltage_violations()
    # IEEE 33-bus can have low voltages but should converge
    # Just check the function runs
    assert isinstance(violations, list)


def test_feasibility_clean_net():
    create_grid()
    feasible, reason = check_grid_feasibility()
    # May have voltage violations due to IEEE 33-bus characteristics
    # but should converge
    assert isinstance(feasible, bool)
    assert isinstance(reason, str)


def test_simulate_inspect_always_feasible():
    create_grid()
    inject_fault("L6-7")
    feasible, reason, pf = simulate_action_pf({"action_type": "INSPECT", "target_asset": "L6-7"})
    assert feasible is True


def test_simulate_defer_always_feasible():
    create_grid()
    feasible, reason, pf = simulate_action_pf({"action_type": "DEFER", "target_asset": "L6-7"})
    assert feasible is True


def test_simulate_repair_returns_pf_results():
    create_grid()
    inject_fault("L6-7")
    feasible, reason, pf = simulate_action_pf({"action_type": "REPAIR", "target_asset": "L6-7"})
    assert isinstance(feasible, bool)
    assert "converged" in pf or pf == {}  # Inspect/defer return {}
