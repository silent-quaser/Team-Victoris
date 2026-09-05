"""
GridGuard — Demo Scenario Seed Data

Severe Storm Event scenario:
    - L6-7    FAILED   (certain)
    - T3      UNCERTAIN (failure_probability = 0.62)
    - L12-13  FAILED   (certain)
    - L25-26  FAILED   (certain)

Critical services at risk:
    - Emergency Center  (via L6-7)
    - Hospital          (via T3 → BUS_10)
    - Water Plant       (via T3 → L12-13)
    - Telecom Tower     (via L25-26)
"""
from __future__ import annotations
from datetime import datetime

from config import AssetStatus, CriticalityLevel, ResourceType, INITIAL_RESOURCES
from models.grid import AssetModel, FaultModel, GridStateModel, ResourceModel
from engine.dependency import get_graph, NODE_TYPE, NODE_DESC, NODE_CRITICALITY, NODE_LOAD_MW, NODE_IS_SERVICE


DEMO_SCENARIO_ID   = "DEMO_STORM_001"
DEMO_SCENARIO_NAME = "Severe Storm Event"


def build_demo_scenario() -> GridStateModel:
    """
    Build and return the initial GridState for the demo storm scenario.
    All assets are initialised from the dependency graph; faults are injected.
    """
    G = get_graph()

    # ── Build assets from graph nodes ──────────────────────────────────────
    assets: dict = {}
    for node_id, attrs in G.nodes(data=True):
        assets[node_id] = AssetModel(
            asset_id=node_id,
            asset_type=attrs.get(NODE_TYPE, "UNKNOWN"),
            name=attrs.get(NODE_DESC, node_id),
            status=AssetStatus.HEALTHY,
            failure_probability=0.0,
            load_mw=attrs.get(NODE_LOAD_MW, 0.0),
            criticality=attrs.get(NODE_CRITICALITY, CriticalityLevel.LOW),
            is_critical_service=attrs.get(NODE_IS_SERVICE, False),
        )

    # ── Apply storm faults ─────────────────────────────────────────────────
    # L6-7: confirmed FAILED
    assets["L6-7"].status              = AssetStatus.FAILED
    assets["L6-7"].failure_probability = 1.0

    # T3_LINE: UNCERTAIN — failure_probability = 0.62
    assets["T3_LINE"].status              = AssetStatus.UNCERTAIN
    assets["T3_LINE"].failure_probability = 0.62

    # L12-13: confirmed FAILED
    assets["L12-13"].status              = AssetStatus.FAILED
    assets["L12-13"].failure_probability = 1.0

    # L25-26: confirmed FAILED
    assets["L25-26"].status              = AssetStatus.FAILED
    assets["L25-26"].failure_probability = 1.0

    # Mark downstream services as disrupted
    assets["EMERGENCY_CENTER"].status = AssetStatus.FAILED
    assets["HOSPITAL"].status         = AssetStatus.UNCERTAIN  # depends on T3
    assets["WATER_PLANT"].status      = AssetStatus.FAILED
    assets["TELECOM_TOWER"].status    = AssetStatus.FAILED

    # ── Faults ────────────────────────────────────────────────────────────
    faults = {
        "FAULT_L6-7": FaultModel(
            fault_id="FAULT_L6-7",
            asset_id="L6-7",
            fault_type="OPEN_CIRCUIT",
            failure_probability=1.0,
        ),
        "FAULT_T3_LINE": FaultModel(
            fault_id="FAULT_T3_LINE",
            asset_id="T3_LINE",
            fault_type="UNCERTAIN",
            failure_probability=0.62,
        ),
        "FAULT_L12-13": FaultModel(
            fault_id="FAULT_L12-13",
            asset_id="L12-13",
            fault_type="OPEN_CIRCUIT",
            failure_probability=1.0,
        ),
        "FAULT_L25-26": FaultModel(
            fault_id="FAULT_L25-26",
            asset_id="L25-26",
            fault_type="OPEN_CIRCUIT",
            failure_probability=1.0,
        ),
    }

    # ── Resources ─────────────────────────────────────────────────────────
    resources = {
        rtype: ResourceModel(
            resource_type=rtype,
            total=total,
            available=total,
            in_use=0,
        )
        for rtype, total in INITIAL_RESOURCES.items()
    }

    # ── Build state ───────────────────────────────────────────────────────
    state = GridStateModel(
        scenario_id=DEMO_SCENARIO_ID,
        scenario_name=DEMO_SCENARIO_NAME,
        assets=assets,
        faults=faults,
        resources=resources,
        step=0,
        total_load_mw=0.0,
        restored_load_mw=0.0,
        restoration_pct=0.0,
    )

    return state
