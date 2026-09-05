"""
GridGuard API — Actions endpoints (simulate, execute).
"""
from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List

from fastapi import APIRouter, HTTPException

from config import ActionType, ResourceType
from engine.state_manager import get_state, execute_action as _execute
from engine.candidate_generator import generate_candidates
from engine.feasibility import validate_action
from engine.optimizer import rank_actions
from audit.log import get_log

router = APIRouter(prefix="/actions", tags=["Actions"])


class SimulateRequest(BaseModel):
    action_type: ActionType
    target_asset: str


class ExecuteRequest(BaseModel):
    action_id: str   # must match a candidate action_id; or synthesize below


@router.get("")
def list_actions():
    """All candidate actions for the current state, scored and ranked."""
    state = get_state()
    candidates = generate_candidates(state)
    for c in candidates:
        feasible, reason = validate_action(c, state)
        c.electrically_feasible = feasible
        c.feasibility_reason = reason
    ranked = rank_actions(candidates, state)
    return {
        "actions": [a.model_dump() for a in ranked],
        "total": len(ranked),
    }


@router.post("/simulate")
def simulate_action(req: SimulateRequest):
    """
    Dry-run: return expected outcome and feasibility of an action
    without modifying state.
    """
    from models.action import ActionModel
    from config import ACTION_TIME_MINUTES
    from engine.dependency import calculate_service_impact
    from engine.criticality import score_criticality_impact
    import uuid

    state = get_state()
    impact = calculate_service_impact(req.target_asset)
    crit   = score_criticality_impact(req.target_asset)

    action = ActionModel(
        action_id=f"SIM_{req.action_type}_{req.target_asset}_{uuid.uuid4().hex[:6]}",
        action_type=req.action_type,
        target_asset=req.target_asset,
        description=f"Simulated {req.action_type} on {req.target_asset}",
        expected_benefit_mw=impact["total_load_mw"],
        expected_critical_service_score=crit,
        estimated_time_minutes=ACTION_TIME_MINUTES.get(req.action_type, 0),
        failure_probability=0.5,
    )

    feasible, reason = validate_action(action, state)
    action.electrically_feasible = feasible
    action.feasibility_reason = reason

    from engine.optimizer import score_action
    action.composite_score = score_action(action, state)

    return {
        "action": action.model_dump(),
        "feasible": feasible,
        "feasibility_reason": reason,
        "expected_outcome": {
            "benefit_mw": impact["total_load_mw"],
            "critical_service_score": crit,
            "affected_services": impact["affected_services"],
        }
    }


@router.post("/execute")
def execute_action_endpoint(req: ExecuteRequest):
    """
    Execute a candidate action by its action_id.
    Generates fresh candidates and finds the matching one.
    """
    state = get_state()
    candidates = generate_candidates(state)

    # Find the matching candidate
    target = None
    for c in candidates:
        if c.action_id == req.action_id:
            target = c
            break

    if target is None:
        raise HTTPException(
            status_code=404,
            detail=f"Action '{req.action_id}' not found in current candidates. "
                   "Refresh /actions to get current action IDs."
        )

    # Validate feasibility
    feasible, reason = validate_action(target, state)
    if not feasible:
        raise HTTPException(
            status_code=422,
            detail=f"Action rejected: electrically infeasible — {reason}"
        )

    result = _execute(target)
    new_state = result["new_state"]

    get_log().log_execution(
        step=new_state.step,
        action=target.model_dump(),
        result={"success": result["success"], "changes": result["state_changes"]},
        state_summary={
            "step": new_state.step,
            "restoration_pct": new_state.restoration_pct,
            "active_faults": len(new_state.get_active_faults()),
        },
    )

    return {
        "success": result["success"],
        "message": result["message"],
        "state_changes": result["state_changes"],
        "new_step": new_state.step,
        "restoration_pct": new_state.restoration_pct,
    }
