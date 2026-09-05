"""
GridGuard — Decision Engine

Implements recommend_next_action(state) by:
1. Generating candidate actions
2. Validating electrical feasibility of each
3. Computing VOI for uncertain assets
4. Scoring / ranking via the optimizer
5. Building a structured RecommendationModel with explanation

The recommendation is driven entirely by calculated values —
no action is hardcoded as "the answer".
"""
from __future__ import annotations
from typing import List, Optional

from config import (
    ActionType, CriticalityLevel, AssetStatus,
    UNCERTAINTY_HIGH_THRESHOLD, IMPACT_HIGH_THRESHOLD,
)
from models.action import ActionModel
from models.grid import GridStateModel
from models.recommendation import RecommendationModel, VOIResult
from engine.candidate_generator import generate_candidates
from engine.feasibility import validate_action
from engine.optimizer import rank_actions, score_action
from engine.voi import calculate_voi
from engine.criticality import get_criticality, score_criticality_impact
from engine.dependency import calculate_service_impact


def recommend_next_action(state: GridStateModel) -> RecommendationModel:
    """
    Core decision function.

    Returns the top-ranked feasible action with a full explanation
    derived from computed values.
    """
    # Step 1: generate candidates
    candidates = generate_candidates(state)

    # Step 2: validate electrical feasibility
    for action in candidates:
        feasible, reason = validate_action(action, state)
        action.electrically_feasible = feasible
        action.feasibility_reason = reason

    # Step 3: pre-compute VOI for uncertain assets
    voi_results: dict[str, VOIResult] = {}
    for action in candidates:
        if action.action_type == ActionType.INSPECT:
            if action.target_asset not in voi_results:
                voi_results[action.target_asset] = calculate_voi(
                    action.target_asset, state
                )

    # Step 4: rank
    ranked = rank_actions(candidates, state)

    # Step 5: pick best feasible action
    best: Optional[ActionModel] = None
    for action in ranked:
        if action.electrically_feasible is not False:
            best = action
            break

    if best is None:
        # Fallback: DEFER
        best = ActionModel(
            action_id="DEFER_FALLBACK",
            action_type=ActionType.DEFER,
            target_asset="ALL",
            description="No feasible actions available",
            composite_score=-1.0,
            electrically_feasible=True,
            failure_probability=0.0,
            expected_critical_service_score=0.0,
        )

    # Step 6: build explanation from values
    voi_detail = voi_results.get(best.target_asset) if best.action_type == ActionType.INSPECT else None
    criticality = get_criticality(best.target_asset)
    impact      = calculate_service_impact(best.target_asset)
    crit_score  = score_criticality_impact(best.target_asset)

    reason_codes = list(set(best.reason_codes))
    explanation  = _build_explanation(best, voi_detail, crit_score, state)

    # Alternatives (next 3 feasible)
    alternatives = []
    for a in ranked:
        if a.action_id == best.action_id:
            continue
        if a.electrically_feasible is False:
            continue
        alternatives.append({
            "action_type":   a.action_type,
            "target_asset":  a.target_asset,
            "score":         round(a.composite_score, 4),
            "description":   a.description,
        })
        if len(alternatives) >= 3:
            break

    return RecommendationModel(
        action_type=best.action_type,
        target_asset=best.target_asset,
        score=round(best.composite_score, 4),
        voi=round(voi_detail.voi, 4) if voi_detail else None,
        uncertainty=round(best.failure_probability, 4),
        criticality=criticality,
        expected_impact=_format_impact(impact),
        estimated_time_minutes=best.estimated_time_minutes,
        required_resource=best.required_resources[0] if best.required_resources else None,
        electrically_feasible=bool(best.electrically_feasible),
        reason_codes=reason_codes,
        explanation=explanation,
        voi_detail=voi_detail,
        alternative_actions=alternatives,
    )


# ---------------------------------------------------------------------------
# Explanation generator (values-driven, not templated)
# ---------------------------------------------------------------------------

def _build_explanation(
    action: ActionModel,
    voi: Optional[VOIResult],
    crit_score: float,
    state: GridStateModel,
) -> str:
    parts: List[str] = []
    asset = action.target_asset
    atype = action.action_type

    # Header
    parts.append(
        f"Recommended action: {atype.value} on {asset} "
        f"(composite score: {action.composite_score:.3f})."
    )

    if atype == ActionType.INSPECT and voi:
        parts.append(
            f"Current failure probability of {asset} is {voi.p_failed:.0%}. "
            f"Inspection VOI = {voi.voi:.3f} (expected gain {voi.expected_gain:.3f}, "
            f"cost {voi.inspection_cost:.3f})."
        )
        parts.append(
            f"Decision sensitivity is {voi.decision_sensitivity:.3f}: "
            f"if {asset} is FAILED the best action is {voi.best_action_if_failed}, "
            f"if HEALTHY the best action is {voi.best_action_if_healthy}. "
            f"Without inspection, the system would choose {voi.best_action_without_info}."
        )
        parts.append(
            f"Criticality-weighted impact score of {asset}: {crit_score:.3f}. "
            f"High uncertainty ({voi.p_failed:.0%}) combined with high critical-service impact "
            f"places this in the HIGH-UNCERTAINTY × HIGH-IMPACT quadrant, "
            f"strongly favouring information acquisition before committing resources."
        )

    elif atype == ActionType.REPAIR:
        parts.append(
            f"{asset} is confirmed {'FAILED' if action.failure_probability >= 1.0 else 'FAULTED'}. "
            f"Expected load restoration: {action.expected_benefit_mw:.2f} MW. "
            f"Critical service impact score: {crit_score:.3f}."
        )
        parts.append(
            f"Risk score: {action.risk_score:.2f}. "
            f"Estimated repair time: {action.estimated_time_minutes} minutes."
        )

    elif atype == ActionType.RECONFIGURE:
        parts.append(
            f"Network reconfiguration to bypass {asset} can restore "
            f"approximately {action.expected_benefit_mw:.2f} MW ({60:.0f}% of downstream load)."
        )
        parts.append(f"No crew resource required. Estimated time: {action.estimated_time_minutes} min.")

    elif atype == ActionType.ISLAND:
        parts.append(
            f"Islanding downstream of {asset} with mobile generator "
            f"can restore {action.expected_benefit_mw:.2f} MW critical load."
        )

    elif atype == ActionType.DEFER:
        parts.append(
            "All other actions are infeasible or carry unacceptable risk/cost. "
            "Deferring is recommended pending additional information."
        )

    # Resource situation
    active_faults = state.get_active_faults()
    uncertain_count = len(state.get_uncertain_faults())
    parts.append(
        f"System context: {len(active_faults)} active fault(s), "
        f"{uncertain_count} uncertain. "
        f"Step {state.step} of sequential recovery."
    )

    return " ".join(parts)


def _format_impact(impact: dict) -> str:
    services = impact.get("affected_services", [])
    mw = impact.get("total_load_mw", 0.0)
    if services:
        svc_names = ", ".join(s.replace("_", " ").title() for s in services)
        return f"{mw:.1f} MW at risk; affected critical services: {svc_names}"
    return f"{mw:.1f} MW at risk; no critical services directly affected"
