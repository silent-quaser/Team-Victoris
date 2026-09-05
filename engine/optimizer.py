"""
GridGuard — Optimizer / Scoring Engine

Scores candidate actions using the multi-objective GridGuard objective:

    score(a) =
        W_crit  * E[critical_service_recovery(a)]
      + W_mw    * E[load_restoration_mw(a)]
      + W_risk  * risk(a)                          (negative weight)
      + W_res   * resource_cost(a)                 (negative weight)
      + W_time  * estimated_time(a)                (negative weight)
      + W_uncert* uncertainty_penalty(a)            (negative weight)

Subject to:
      electrically_feasible(a) == True
      resource_available(a)    == True

Also applies the uncertainty × impact quadrant logic:

    LOW uncertainty  + HIGH impact  → favour immediate action
    HIGH uncertainty + HIGH impact  → favour INSPECT (information acquisition)
    HIGH uncertainty + LOW impact   → act immediately (low cost of error)
    LOW uncertainty  + LOW impact   → DEFER
"""
from __future__ import annotations
from typing import List, Tuple

from config import (
    ActionType, AssetStatus,
    WEIGHT_CRITICAL_SERVICE_RECOVERY,
    WEIGHT_LOAD_RESTORATION_MW,
    WEIGHT_RISK,
    WEIGHT_RESOURCE_COST,
    WEIGHT_TIME,
    WEIGHT_UNCERTAINTY_PENALTY,
    UNCERTAINTY_HIGH_THRESHOLD,
    IMPACT_HIGH_THRESHOLD,
)
from models.action import ActionModel
from models.grid import GridStateModel
from engine.voi import calculate_voi


# ---------------------------------------------------------------------------
# Resource cost mapping (normalised [0-1])
# ---------------------------------------------------------------------------
from config import ResourceType

RESOURCE_COST: dict = {
    ResourceType.REPAIR_CREW:       0.5,
    ResourceType.INSPECTION_DRONE:  0.2,
    ResourceType.MOBILE_GENERATOR:  0.5,
}


def _resource_cost(action: ActionModel) -> float:
    return sum(RESOURCE_COST.get(r, 0.3) for r in action.required_resources)


def _uncertainty_quadrant_bonus(action: ActionModel) -> float:
    """
    Apply quadrant-aware bonus/penalty.

    HIGH uncertainty + HIGH impact → INSPECT should get a bonus
    LOW uncertainty  + HIGH impact → immediate ACT gets a bonus
    LOW everything → DEFER preferred
    """
    p_fail   = action.failure_probability
    impact   = action.expected_critical_service_score

    high_u = p_fail  >= UNCERTAINTY_HIGH_THRESHOLD
    high_i = impact  >= IMPACT_HIGH_THRESHOLD

    bonus = 0.0
    if high_u and high_i:
        # Quadrant 4: strongly favour INSPECT
        if action.action_type == ActionType.INSPECT:
            bonus = 1.5
        elif action.action_type in (ActionType.REPAIR,):
            bonus = -0.5   # penalise blind repair
    elif not high_u and high_i:
        # Quadrant 2: known critical fault → act now
        if action.action_type in (ActionType.REPAIR, ActionType.RESTORE,
                                   ActionType.RECONFIGURE):
            bonus = 0.8
    elif high_u and not high_i:
        # Quadrant 3: uncertain but low impact → act anyway (cheap error)
        if action.action_type in (ActionType.REPAIR, ActionType.RECONFIGURE):
            bonus = 0.3
    else:
        # Quadrant 1: low u, low i → defer or repair
        if action.action_type == ActionType.DEFER:
            bonus = 0.2

    return bonus


def score_action(
    action: ActionModel,
    state: GridStateModel,
    voi_value: float = 0.0,
) -> float:
    """
    Compute composite score for a single action.
    voi_value is the pre-computed VOI (if action is INSPECT, it's used as benefit).
    """
    # Base objective terms
    score = (
        WEIGHT_CRITICAL_SERVICE_RECOVERY * action.expected_critical_service_score
        + WEIGHT_LOAD_RESTORATION_MW     * action.expected_benefit_mw
        + WEIGHT_RISK                    * action.risk_score
        + WEIGHT_RESOURCE_COST           * _resource_cost(action)
        + WEIGHT_TIME                    * action.estimated_time_minutes
    )

    # Uncertainty penalty for acting without knowing
    if action.action_type != ActionType.INSPECT:
        uncertainty_pen = action.uncertainty_dependence * action.failure_probability
        score += WEIGHT_UNCERTAINTY_PENALTY * uncertainty_pen

    # VOI bonus for INSPECT actions
    if action.action_type == ActionType.INSPECT and voi_value > 0:
        score += WEIGHT_CRITICAL_SERVICE_RECOVERY * voi_value * 2.0

    # Quadrant-aware bonus
    score += _uncertainty_quadrant_bonus(action)

    return round(score, 6)


def rank_actions(
    candidates: List[ActionModel],
    state: GridStateModel,
) -> List[ActionModel]:
    """
    Score and rank all candidate actions.

    For INSPECT actions, pre-computes VOI.
    Infeasible actions are pushed to the bottom (score = -999).

    Returns candidates sorted by composite_score descending.
    """
    voi_cache: dict = {}

    for action in candidates:
        voi_val = 0.0
        if action.action_type == ActionType.INSPECT:
            if action.target_asset not in voi_cache:
                voi_result = calculate_voi(action.target_asset, state)
                voi_cache[action.target_asset] = voi_result.voi
            voi_val = voi_cache[action.target_asset]
            action.reason_codes = list(set(action.reason_codes))

        if action.electrically_feasible is False:
            action.composite_score = -999.0
        else:
            action.composite_score = score_action(action, state, voi_val)

    candidates.sort(key=lambda a: a.composite_score, reverse=True)
    return candidates
