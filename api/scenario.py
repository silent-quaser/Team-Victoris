"""
GridGuard API — Scenario management endpoints.
"""
from __future__ import annotations
from pydantic import BaseModel
from typing import Optional

from fastapi import APIRouter

from engine.state_manager import init_state, get_state, inject_fault
from engine.dependency import reset_graph
from scenario.demo import build_demo_scenario
from audit.log import get_log, reset_log

router = APIRouter(prefix="/scenario", tags=["Scenario"])


class FaultRequest(BaseModel):
    asset_id: str
    fault_type: str = "OPEN_CIRCUIT"       # OPEN_CIRCUIT | SHORT_CIRCUIT | UNCERTAIN
    failure_probability: float = 1.0
    fault_id: Optional[str] = None


@router.get("/current")
def current_scenario():
    """Metadata about the current scenario."""
    state = get_state()
    return {
        "scenario_id":   state.scenario_id,
        "scenario_name": state.scenario_name,
        "step":          state.step,
        "timestamp":     state.timestamp.isoformat(),
        "active_faults": len(state.get_active_faults()),
        "uncertain_faults": len(state.get_uncertain_faults()),
        "restoration_pct": state.restoration_pct,
    }


@router.post("/reset")
def reset_scenario():
    """Reset the system to the initial demo storm scenario."""
    reset_graph()
    state = build_demo_scenario()
    init_state(state)
    reset_log()
    # Recalculate restoration progress
    from engine.state_manager import _update_restoration_progress
    _update_restoration_progress(get_state())
    return {"message": "Scenario reset to demo storm event", "scenario_id": state.scenario_id}


@router.post("/fault")
def inject_fault_endpoint(req: FaultRequest):
    """Inject a new fault into the current grid state."""
    fault = inject_fault(
        asset_id=req.asset_id,
        fault_type=req.fault_type,
        failure_probability=req.failure_probability,
        fault_id=req.fault_id,
    )
    state = get_state()
    from audit.log import get_log
    get_log().log_fault(
        step=state.step,
        fault=fault.model_dump(),
        state_summary=_state_summary(state),
    )
    return {"message": f"Fault injected on {req.asset_id}", "fault": fault.model_dump()}


def _state_summary(state) -> dict:
    return {
        "step": state.step,
        "scenario_id": state.scenario_id,
        "restoration_pct": state.restoration_pct,
        "active_faults": len(state.get_active_faults()),
    }
