"""
GridGuard API — Recommendation, risk, and impact endpoints.
"""
from __future__ import annotations
from fastapi import APIRouter

from engine.state_manager import get_state
from engine.decision import recommend_next_action
from engine.dependency import calculate_service_impact, get_all_critical_services
from engine.criticality import get_criticality, score_criticality_impact
from audit.log import get_log
from models.recommendation import RiskModel, ImpactModel
from config import AssetStatus, CriticalityLevel

router = APIRouter(tags=["Recommendation"])


@router.get("/recommendation")
def get_recommendation():
    """
    Compute and return the recommended next action.
    Decision is driven by VOI, criticality, uncertainty, and feasibility.
    Logs the recommendation to the activity log.
    """
    state   = get_state()
    rec     = recommend_next_action(state)

    # Log the recommendation
    from engine.candidate_generator import generate_candidates
    from engine.optimizer import rank_actions
    from engine.feasibility import validate_action

    candidates = generate_candidates(state)
    for c in candidates:
        feasible, reason = validate_action(c, state)
        c.electrically_feasible = feasible

    ranked = rank_actions(candidates, state)
    scores = {a.action_id: a.composite_score for a in ranked[:10]}

    get_log().log_recommendation(
        step=state.step,
        state_summary={
            "step": state.step,
            "restoration_pct": state.restoration_pct,
            "active_faults": len(state.get_active_faults()),
        },
        candidates=[{
            "action_id": a.action_id,
            "action_type": a.action_type,
            "target_asset": a.target_asset,
            "score": a.composite_score,
        } for a in ranked[:10]],
        selected=rec.model_dump(mode="json"),
        scores=scores,
        feasibility={"electrically_feasible": rec.electrically_feasible},
    )

    return rec.model_dump(mode="json")


@router.get("/impact")
def get_impact():
    """System-wide impact summary: load, critical services, restoration."""
    state    = get_state()
    svc_ids  = get_all_critical_services()

    # Which services are currently down?
    down_svcs = []
    for svc in svc_ids:
        asset = state.assets.get(svc)
        if asset and asset.status in (AssetStatus.FAILED, AssetStatus.UNCERTAIN):
            down_svcs.append(svc)

    # Downstream affected nodes from all active faults
    affected_nodes = set()
    from engine.dependency import get_downstream_dependencies
    for fault in state.get_active_faults():
        for dep in get_downstream_dependencies(fault.asset_id):
            affected_nodes.add(dep["node_id"])

    # Criticality-weighted impact
    crit_weighted = sum(
        score_criticality_impact(f.asset_id)
        for f in state.get_active_faults()
    )

    lost_mw = state.total_load_mw - state.restored_load_mw

    return ImpactModel(
        total_load_mw=state.total_load_mw,
        lost_load_mw=round(lost_mw, 3),
        restoration_pct=state.restoration_pct,
        affected_critical_services=[s.replace("_", " ").title() for s in down_svcs],
        critical_services_down=len(down_svcs),
        critical_services_total=len(svc_ids),
        downstream_affected_nodes=len(affected_nodes),
        criticality_weighted_impact=round(min(crit_weighted, 1.0), 4),
    ).model_dump()


@router.get("/risk")
def get_risk():
    """Current risk assessment based on uncertainty, criticality, and resources."""
    state = get_state()
    faults = state.get_active_faults()
    uncertain = state.get_uncertain_faults()

    # Uncertainty risk: mean failure prob of uncertain faults
    u_risk = (
        sum(f.failure_probability for f in uncertain) / len(uncertain)
        if uncertain else 0.0
    )

    # Critical service risk: fraction of critical services affected
    svc_ids = get_all_critical_services()
    down_svcs = [
        s for s in svc_ids
        if state.assets.get(s) and
           state.assets[s].status in (AssetStatus.FAILED, AssetStatus.UNCERTAIN)
    ]
    cs_risk = len(down_svcs) / max(len(svc_ids), 1)

    # Resource risk: fraction of resources depleted
    from config import ResourceType
    total_res = sum(r.total for r in state.resources.values())
    used_res  = sum(r.in_use for r in state.resources.values())
    res_risk  = used_res / max(total_res, 1)

    # Cascade risk: assets with uncertain + high criticality
    cascade_risk = sum(
        score_criticality_impact(f.asset_id)
        for f in uncertain
    ) / max(len(faults), 1)

    overall = (u_risk * 0.3 + cs_risk * 0.4 + cascade_risk * 0.3)

    risk_factors = []
    if u_risk > 0.5:    risk_factors.append("HIGH_UNCERTAINTY_FAULTS")
    if cs_risk > 0.5:   risk_factors.append("CRITICAL_SERVICES_AT_RISK")
    if res_risk > 0.6:  risk_factors.append("RESOURCE_DEPLETION")
    if cascade_risk > 0.4: risk_factors.append("CASCADE_RISK")

    if overall >= 0.75:   risk_level = "CRITICAL"
    elif overall >= 0.5:  risk_level = "HIGH"
    elif overall >= 0.25: risk_level = "MEDIUM"
    else:                 risk_level = "LOW"

    return RiskModel(
        overall_risk=round(overall, 4),
        uncertainty_risk=round(u_risk, 4),
        critical_service_risk=round(cs_risk, 4),
        resource_risk=round(res_risk, 4),
        cascade_risk=round(cascade_risk, 4),
        risk_factors=risk_factors,
        risk_level=risk_level,
    ).model_dump()
