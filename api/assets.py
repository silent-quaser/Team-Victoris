"""
GridGuard API — Asset and fault detail endpoints.
"""
from __future__ import annotations
from typing import List

from fastapi import APIRouter, HTTPException

from engine.state_manager import get_state, inject_fault
from engine.criticality import get_criticality, score_criticality_impact, get_affected_critical_services
from engine.dependency import calculate_service_impact, get_downstream_dependencies, get_asset_info

router = APIRouter(tags=["Assets"])


@router.get("/assets/{asset_id}")
def get_asset(asset_id: str):
    """Detail for a single asset including criticality and impact."""
    state = get_state()
    asset = state.assets.get(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found")

    info = get_asset_info(asset_id) or {}
    impact = calculate_service_impact(asset_id)

    return {
        **asset.model_dump(),
        "criticality": get_criticality(asset_id),
        "criticality_score": score_criticality_impact(asset_id),
        "affected_critical_services": get_affected_critical_services(asset_id),
        "impact_summary": impact,
        "graph_info": info,
    }


@router.get("/faults")
def list_faults():
    """All active (unresolved) faults."""
    state = get_state()
    faults = [f.model_dump() for f in state.get_active_faults()]
    for f in faults:
        f["criticality"] = get_criticality(f["asset_id"])
        f["critical_services"] = get_affected_critical_services(f["asset_id"])
    return {"faults": faults, "total": len(faults)}
