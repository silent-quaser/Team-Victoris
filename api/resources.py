"""
GridGuard API — Resources and restoration progress endpoints.
"""
from __future__ import annotations
from fastapi import APIRouter

from engine.state_manager import get_state
from config import ResourceType

router = APIRouter(tags=["Resources"])


@router.get("/resources")
def get_resources():
    """Current availability of all recovery resources."""
    state = get_state()
    resources = [r.model_dump() for r in state.resources.values()]
    return {
        "resources": resources,
        "summary": {
            "repair_crews_available": state.resources.get(
                ResourceType.REPAIR_CREW, None
            ).available if ResourceType.REPAIR_CREW in state.resources else 0,
            "drone_available": state.resources.get(
                ResourceType.INSPECTION_DRONE, None
            ).available > 0 if ResourceType.INSPECTION_DRONE in state.resources else False,
            "mobile_generator_available": state.resources.get(
                ResourceType.MOBILE_GENERATOR, None
            ).available > 0 if ResourceType.MOBILE_GENERATOR in state.resources else False,
        }
    }


@router.get("/restoration/progress")
def get_restoration_progress():
    """Current restoration progress: load, critical services, steps."""
    state = get_state()
    from engine.dependency import get_all_critical_services
    from config import AssetStatus
    svc_ids = get_all_critical_services()
    restored_svcs = [
        s for s in svc_ids
        if state.assets.get(s) and
           state.assets[s].status in (AssetStatus.HEALTHY, AssetStatus.RESTORED)
    ]
    down_svcs = [
        s for s in svc_ids
        if state.assets.get(s) and
           state.assets[s].status in (AssetStatus.FAILED, AssetStatus.UNCERTAIN)
    ]

    active_faults = state.get_active_faults()
    resolved_faults = [f for f in state.faults.values() if f.resolved]

    return {
        "step": state.step,
        "total_load_mw": state.total_load_mw,
        "restored_load_mw": state.restored_load_mw,
        "lost_load_mw": round(state.total_load_mw - state.restored_load_mw, 3),
        "restoration_pct": state.restoration_pct,
        "critical_services_total": len(svc_ids),
        "critical_services_restored": len(restored_svcs),
        "critical_services_down": len(down_svcs),
        "critical_services_restored_list": [s.replace("_", " ").title() for s in restored_svcs],
        "critical_services_down_list": [s.replace("_", " ").title() for s in down_svcs],
        "faults_total": len(state.faults),
        "faults_active": len(active_faults),
        "faults_resolved": len(resolved_faults),
        "topology_changes": state.topology_changes,
    }
