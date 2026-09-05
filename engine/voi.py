"""
GridGuard — Value of Information (VOI) Engine

Implements the VOI calculation:

    VOI(x) = E[best outcome | observing x] − best outcome without observing x − cost(x)

For a binary uncertain asset (FAILED / HEALTHY), this expands to:

    VOI(x) = [p(F) * score(best_action | FAILED) + p(H) * score(best_action | HEALTHY)]
             − score(best_action_without_info)
             − inspection_cost

Key function:
    calculate_voi(target_asset, state) → VOIResult
"""
from __future__ import annotations
from typing import Dict, Any, Tuple

from config import (
    INSPECTION_RESOURCE_COST,
    WEIGHT_CRITICAL_SERVICE_RECOVERY,
    WEIGHT_LOAD_RESTORATION_MW,
    WEIGHT_RISK,
    WEIGHT_RESOURCE_COST,
    WEIGHT_TIME,
    ActionType, ResourceType, AssetStatus,
)
from models.grid import GridStateModel
from models.recommendation import VOIResult
from engine.dependency import calculate_service_impact
from engine.criticality import score_criticality_impact


def _action_outcome_score(
    action_type: ActionType,
    asset_id: str,
    state: GridStateModel,
    assume_failed: bool,
    assume_healthy: bool,
) -> float:
    """
    Compute the expected outcome score if we take `action_type` on `asset_id`,
    given assumed asset state (failed or healthy).

    Uses the same objective as the decision engine:
        W_crit * crit_score + W_mw * mw − W_risk * risk − W_time * time − W_resource * resource_cost
    """
    impact = calculate_service_impact(asset_id)
    crit   = score_criticality_impact(asset_id)
    mw     = impact["total_load_mw"]

    if action_type == ActionType.INSPECT:
        # Inspection itself doesn't restore power; value comes from information
        benefit_mw   = 0.0
        benefit_crit = 0.0
        risk         = 0.05
        time_min     = 18
        res_cost     = INSPECTION_RESOURCE_COST

    elif action_type == ActionType.REPAIR:
        if assume_failed:
            benefit_mw   = mw
            benefit_crit = crit
        else:
            # Asset is healthy → repair is wasted
            benefit_mw   = 0.0
            benefit_crit = 0.0
        risk     = 0.1
        time_min = 90
        res_cost = 0.5   # crew cost unit

    elif action_type == ActionType.RECONFIGURE:
        benefit_mw   = mw * 0.6 if assume_failed else 0.0
        benefit_crit = crit * 0.6 if assume_failed else 0.0
        risk         = 0.2
        time_min     = 15
        res_cost     = 0.0

    elif action_type == ActionType.ISLAND:
        benefit_mw   = min(mw, 2.5) if assume_failed else 0.0
        benefit_crit = crit * 0.8   if assume_failed else 0.0
        risk         = 0.25
        time_min     = 20
        res_cost     = 0.5

    elif action_type == ActionType.DEFER:
        benefit_mw   = 0.0
        benefit_crit = 0.0
        risk         = 0.0
        time_min     = 0
        res_cost     = 0.0
    else:
        benefit_mw   = 0.0
        benefit_crit = 0.0
        risk         = 0.0
        time_min     = 0
        res_cost     = 0.0

    score = (
        WEIGHT_CRITICAL_SERVICE_RECOVERY * benefit_crit
        + WEIGHT_LOAD_RESTORATION_MW     * benefit_mw
        + WEIGHT_RISK                    * risk
        + WEIGHT_RESOURCE_COST           * res_cost
        + WEIGHT_TIME                    * time_min
    )
    return score


def _best_action_given_state(
    asset_id: str,
    state: GridStateModel,
    assume_failed: bool,
    assume_healthy: bool,
    available_actions: Tuple[ActionType, ...] = (
        ActionType.REPAIR, ActionType.RECONFIGURE,
        ActionType.ISLAND, ActionType.DEFER,
    )
) -> Tuple[ActionType, float]:
    """
    Find the best action and its score given an assumed asset state.
    Returns (best_action_type, score).
    """
    best_score  = float("-inf")
    best_action = ActionType.DEFER

    for act in available_actions:
        # Check resource feasibility
        if act == ActionType.REPAIR:
            from config import ResourceType
            r = state.resources.get(ResourceType.REPAIR_CREW)
            if r is None or r.available < 1:
                continue
        elif act == ActionType.ISLAND:
            r = state.resources.get(ResourceType.MOBILE_GENERATOR)
            if r is None or r.available < 1:
                continue

        s = _action_outcome_score(act, asset_id, state, assume_failed, assume_healthy)
        if s > best_score:
            best_score  = s
            best_action = act

    return best_action, best_score


def calculate_voi(target_asset: str, state: GridStateModel) -> VOIResult:
    """
    Compute the Value of Information for inspecting target_asset.

    Algorithm:
    1. Determine p(FAILED) from current fault belief
    2. Enumerate two possible observations: FAILED, HEALTHY
    3. For each observation, find the best action and its outcome score
    4. Expected value WITH information:
           E_info = p(F) * score(best|F) + p(H) * score(best|H)
    5. Best action WITHOUT information (acting on current belief):
           pick action that maximises E[outcome] = p(F)*score(act|F) + p(H)*score(act|H)
    6. VOI = E_info − score_without_info − inspection_cost
    7. decision_sensitivity = |score(best|F) − score(best|H)|
    """
    # Step 1: failure probability
    p_fail = 0.5  # default if uncertain
    
    from uncertainty.belief import get_uncertainty
    belief = get_uncertainty(target_asset)
    if belief is not None:
        p_fail = belief.p_failed
    else:
        for fault in state.faults.values():
            if fault.asset_id == target_asset and not fault.resolved:
                p_fail = fault.failure_probability
                break

    p_healthy = 1.0 - p_fail

    inspection_cost = INSPECTION_RESOURCE_COST   # normalised cost [0-1 scale]

    # Step 2-3: best action under each observation
    best_if_failed,  score_if_failed  = _best_action_given_state(
        target_asset, state, assume_failed=True,  assume_healthy=False
    )
    best_if_healthy, score_if_healthy = _best_action_given_state(
        target_asset, state, assume_failed=False, assume_healthy=True
    )

    # Step 4: expected value WITH information
    e_with_info = p_fail * score_if_failed + p_healthy * score_if_healthy

    # Step 5: best action WITHOUT information
    available_actions = (
        ActionType.REPAIR, ActionType.RECONFIGURE,
        ActionType.ISLAND, ActionType.DEFER,
    )
    best_without_score = float("-inf")
    best_without_action = ActionType.DEFER

    for act in available_actions:
        # Check resource feasibility
        if act == ActionType.REPAIR:
            r = state.resources.get(ResourceType.REPAIR_CREW)
            if r is None or r.available < 1:
                continue
        elif act == ActionType.ISLAND:
            r = state.resources.get(ResourceType.MOBILE_GENERATOR)
            if r is None or r.available < 1:
                continue

        # Expected outcome of this action without knowing state
        s_fail    = _action_outcome_score(act, target_asset, state, assume_failed=True,  assume_healthy=False)
        s_healthy = _action_outcome_score(act, target_asset, state, assume_failed=False, assume_healthy=True)
        expected  = p_fail * s_fail + p_healthy * s_healthy
        if expected > best_without_score:
            best_without_score  = expected
            best_without_action = act

    # Step 6: VOI
    raw_voi         = e_with_info - best_without_score - inspection_cost
    expected_gain   = e_with_info - best_without_score  # gain before cost

    # Normalise VOI to [0, 1] for comparability
    # Use 10.0 as a plausible max raw score range
    SCORE_RANGE = 10.0
    voi_normalised = max(0.0, min(raw_voi / SCORE_RANGE, 1.0))

    # Step 7: decision sensitivity
    decision_sensitivity = abs(score_if_failed - score_if_healthy) / SCORE_RANGE
    decision_sensitivity = min(decision_sensitivity, 1.0)

    return VOIResult(
        voi=round(voi_normalised, 4),
        expected_gain=round(expected_gain, 4),
        inspection_cost=round(inspection_cost, 4),
        decision_sensitivity=round(decision_sensitivity, 4),
        p_failed=round(p_fail, 4),
        p_healthy=round(p_healthy, 4),
        best_action_if_failed=best_if_failed.value,
        best_action_if_healthy=best_if_healthy.value,
        best_action_without_info=best_without_action.value,
    )
