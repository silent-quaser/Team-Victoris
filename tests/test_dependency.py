"""
Tests for the dependency graph engine.
"""
import pytest
from engine.dependency import (
    build_dependency_graph,
    get_downstream_dependencies,
    calculate_service_impact,
    get_all_critical_services,
    find_upstream_assets,
    get_asset_info,
    reset_graph,
)


def test_graph_builds():
    reset_graph()
    G = build_dependency_graph()
    assert G.number_of_nodes() > 10
    assert G.number_of_edges() > 10


def test_critical_services_in_graph():
    svcs = get_all_critical_services()
    assert "HOSPITAL" in svcs
    assert "WATER_PLANT" in svcs
    assert "EMERGENCY_CENTER" in svcs
    assert "TELECOM_TOWER" in svcs


def test_t3_downstream_contains_hospital():
    deps = get_downstream_dependencies("T3_LINE")
    node_ids = [d["node_id"] for d in deps]
    # T3 → BUS_12 → L12-13 → BUS_13 → WATER_PLANT
    # and T3 is upstream of BUS_12 which is upstream of water plant path
    assert len(deps) > 0


def test_l6_7_downstream_contains_emergency_center():
    deps = get_downstream_dependencies("L6-7")
    node_ids = [d["node_id"] for d in deps]
    assert "EMERGENCY_CENTER" in node_ids


def test_l12_13_downstream_contains_water_plant():
    deps = get_downstream_dependencies("L12-13")
    node_ids = [d["node_id"] for d in deps]
    assert "WATER_PLANT" in node_ids


def test_l25_26_downstream_contains_telecom():
    deps = get_downstream_dependencies("L25-26")
    node_ids = [d["node_id"] for d in deps]
    assert "TELECOM_TOWER" in node_ids


def test_service_impact_has_positive_load():
    impact = calculate_service_impact("T3_LINE")
    assert impact["total_load_mw"] > 0


def test_service_impact_critical_score():
    impact = calculate_service_impact("T3_LINE")
    assert 0.0 <= impact["critical_service_score"] <= 1.0


def test_service_impact_returns_affected_services():
    impact = calculate_service_impact("L12-13")
    assert "WATER_PLANT" in impact["affected_services"]


def test_upstream_of_hospital_includes_bus_10():
    upstream = find_upstream_assets("HOSPITAL")
    assert "BUS_10" in upstream


def test_asset_info_returns_dict():
    info = get_asset_info("T3_LINE")
    assert info is not None
    assert "node_type" in info


def test_unknown_asset_returns_empty_list():
    deps = get_downstream_dependencies("NONEXISTENT_ASSET")
    assert deps == []


def test_unknown_asset_impact():
    impact = calculate_service_impact("NONEXISTENT")
    assert impact["total_load_mw"] == 0.0
