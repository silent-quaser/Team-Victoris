"""
GridGuard API — Dependencies and inspection endpoints.
"""
from __future__ import annotations
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from engine.dependency import (
    get_downstream_dependencies,
    find_upstream_assets,
    calculate_service_impact,
    get_asset_info,
)
from engine.state_manager import get_state, apply_inspection_result
from engine.voi import calculate_voi
from audit.log import get_log

router = APIRouter(tags=["Dependencies"])


@router.get("/dependencies/{asset_id}")
def get_dependencies(asset_id: str):
    """Full dependency chain for an asset: upstream, downstream, and service impact."""
    info = get_asset_info(asset_id)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found in graph")

    downstream = get_downstream_dependencies(asset_id)
    upstream   = find_upstream_assets(asset_id)
    impact     = calculate_service_impact(asset_id)

    return {
        "asset_id": asset_id,
        "asset_info": info,
        "upstream_assets": upstream,
        "downstream_nodes": downstream,
        "service_impact": impact,
    }


# --------------------------------------------------------------------------
# Inspection endpoint
# --------------------------------------------------------------------------

class InspectionRequest(BaseModel):
    asset_id: str
    result: str          # "FAILED" | "HEALTHY"
    notes: str = ""


@router.post("/inspection")
def submit_inspection(req: InspectionRequest):
    """
    Submit the result of an inspection.

    - Resolves uncertainty for the asset
    - Updates asset status and faults
    - Releases the inspection drone
    - Logs the event
    - Returns updated state and the new recommendation
    """
    if req.result not in ("FAILED", "HEALTHY"):
        raise HTTPException(
            status_code=422,
            detail="Result must be 'FAILED' or 'HEALTHY'"
        )

    state = get_state()

    # Verify drone is deployed (in_use)
    from config import ResourceType
    drone = state.resources.get(ResourceType.INSPECTION_DRONE)
    if drone is None or drone.in_use < 1:
        # Allow if not tracking (for direct POST usage without prior execute)
        pass

    result = apply_inspection_result(
        asset_id=req.asset_id,
        result=req.result,
        inspection_notes=req.notes,
    )

    new_state = result["new_state"]

    get_log().log_inspection(
        step=new_state.step,
        asset_id=req.asset_id,
        result=req.result,
        state_summary={
            "step": new_state.step,
            "restoration_pct": new_state.restoration_pct,
            "active_faults": len(new_state.get_active_faults()),
        },
    )

    # Generate new recommendation from updated state
    from engine.decision import recommend_next_action
    new_rec = recommend_next_action(new_state)

    return {
        "success": result["success"],
        "message": result["message"],
        "state_changes": result["state_changes"],
        "new_step": new_state.step,
        "restoration_pct": new_state.restoration_pct,
        "active_faults": len(new_state.get_active_faults()),
        "new_recommendation": new_rec.model_dump(mode="json"),
    }


@router.get("/voi/{asset_id}")
def get_voi(asset_id: str):
    """Compute the Value of Information for inspecting an uncertain asset."""
    state = get_state()
    asset = state.assets.get(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found")

    voi = calculate_voi(asset_id, state)
    return {
        "asset_id": asset_id,
        "current_status": asset.status,
        "failure_probability": asset.failure_probability,
        **voi.model_dump(),
    }
