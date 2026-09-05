"""
GridGuard — Candidate Action Generator

Generates all valid candidate actions for the current grid state.
Each action is populated with:
    - expected_benefit_mw
    - expected_critical_service_score
    - risk_score
    - required_resources (checked against available)
    - estimated_time_minutes
    - uncertainty_dependence
    - reversibility
    - reason_codes
"""
from __future__ import annotations
from typing import List
import uuid

from config import (
    ActionType, AssetStatus, ResourceType,
    ACTION_TIME_MINUTES, INITIAL_RESOURCES,
    UNCERTAINTY_HIGH_THRESHOLD, IMPACT_HIGH_THRESHOLD,
)
from models.action import ActionModel
from models.grid import GridStateModel
from engine.criticality import get_criticality_score, score_criticality_impact
from engine.dependency import calculate_service_impact


def generate_candidates(state: GridStateModel) -> List[ActionModel]:
    """
    Generate all candidate actions for the current state.

    Rules:
    - INSPECT:     generated for UNCERTAIN faults if drone is available
    - REPAIR:      generated for FAILED/UNCERTAIN faults if crew available
    - RECONFIGURE: generated when a feeder or line fault can be bypassed
    - ISLAND:      generated for isolatable segments
    - RESTORE:     generated for assets that have been repaired/isolated and can be re-energised
    - DEFER:       always generated as a fallback
    """
    candidates: List[ActionModel] = []

    available_crew   = state.resources.get(ResourceType.REPAIR_CREW)
    available_drone  = state.resources.get(ResourceType.INSPECTION_DRONE)
    available_gen    = state.resources.get(ResourceType.MOBILE_GENERATOR)

    crew_ok  = available_crew  is not None and available_crew.available  >= 1
    drone_ok = available_drone is not None and available_drone.available >= 1
    gen_ok   = available_gen   is not None and available_gen.available   >= 1

    active_faults = state.get_active_faults()

    for fault in active_faults:
        asset_id   = fault.asset_id
        asset      = state.assets.get(asset_id)
        if asset is None:
            continue

        impact     = calculate_service_impact(asset_id)
        crit_score = score_criticality_impact(asset_id)
        mw         = impact["total_load_mw"]
        p_fail     = fault.failure_probability
        uncertain  = asset.status == AssetStatus.UNCERTAIN

        # ---- INSPECT -------------------------------------------------
        if uncertain and drone_ok:
            reason_codes = ["UNCERTAIN_ASSET"]
            if crit_score >= IMPACT_HIGH_THRESHOLD:
                reason_codes.append("HIGH_CRITICAL_IMPACT")
            if p_fail >= UNCERTAINTY_HIGH_THRESHOLD:
                reason_codes.append("HIGH_UNCERTAINTY")

            candidates.append(ActionModel(
                action_id=f"INSPECT_{asset_id}_{uuid.uuid4().hex[:6]}",
                action_type=ActionType.INSPECT,
                target_asset=asset_id,
                description=f"Dispatch inspection drone to {asset_id} to resolve uncertainty",
                expected_benefit_mw=mw * p_fail,       # expected MW if failed and later repaired
                expected_critical_service_score=crit_score * p_fail,
                risk_score=0.05,                        # low risk – non-destructive
                reversibility=1.0,
                required_resources=[ResourceType.INSPECTION_DRONE],
                estimated_time_minutes=ACTION_TIME_MINUTES[ActionType.INSPECT],
                uncertainty_dependence=1.0,             # outcome entirely depends on uncertainty
                failure_probability=p_fail,
                reason_codes=reason_codes,
            ))

        # ---- REPAIR --------------------------------------------------
        if crew_ok and asset.status in (AssetStatus.FAILED, AssetStatus.UNCERTAIN):
            # Risk is higher for uncertain assets (might not need repair)
            repair_risk = 0.1 if not uncertain else 0.3
            expected_mw = mw if not uncertain else mw * p_fail

            reason_codes = ["ASSET_FAULTED"]
            if crit_score >= IMPACT_HIGH_THRESHOLD:
                reason_codes.append("HIGH_CRITICAL_IMPACT")
            if uncertain:
                reason_codes.append("REPAIR_UNDER_UNCERTAINTY")

            candidates.append(ActionModel(
                action_id=f"REPAIR_{asset_id}_{uuid.uuid4().hex[:6]}",
                action_type=ActionType.REPAIR,
                target_asset=asset_id,
                description=f"Dispatch repair crew to fix {asset_id}",
                expected_benefit_mw=expected_mw,
                expected_critical_service_score=crit_score * (p_fail if uncertain else 1.0),
                risk_score=repair_risk,
                reversibility=0.8,
                required_resources=[ResourceType.REPAIR_CREW],
                estimated_time_minutes=ACTION_TIME_MINUTES[ActionType.REPAIR],
                uncertainty_dependence=0.5 if uncertain else 0.0,
                failure_probability=p_fail,
                reason_codes=reason_codes,
            ))

        # ---- RECONFIGURE (bypass) ------------------------------------
        if asset.status == AssetStatus.FAILED and asset_id.startswith("L"):
            # Line fault – try alternate path; feasibility validated separately
            reason_codes = ["LINE_FAULT_BYPASS_POSSIBLE"]
            if crit_score >= IMPACT_HIGH_THRESHOLD:
                reason_codes.append("HIGH_CRITICAL_IMPACT")

            candidates.append(ActionModel(
                action_id=f"RECONFIGURE_{asset_id}_{uuid.uuid4().hex[:6]}",
                action_type=ActionType.RECONFIGURE,
                target_asset=asset_id,
                description=f"Reconfigure network to bypass {asset_id} via alternate path",
                expected_benefit_mw=mw * 0.6,   # partial restore
                expected_critical_service_score=crit_score * 0.6,
                risk_score=0.2,
                reversibility=0.9,
                required_resources=[],           # switching – no crew needed
                estimated_time_minutes=ACTION_TIME_MINUTES[ActionType.RECONFIGURE],
                uncertainty_dependence=0.0,
                failure_probability=0.0,
                reason_codes=reason_codes,
            ))

        # ---- ISLAND --------------------------------------------------
        if asset.status == AssetStatus.FAILED and gen_ok and mw <= 2.5:
            # Only island small load segments that fit mobile generator
            reason_codes = ["MOBILE_GEN_ISLAND"]
            if crit_score >= IMPACT_HIGH_THRESHOLD:
                reason_codes.append("CRITICAL_LOAD_ISOLATION")

            candidates.append(ActionModel(
                action_id=f"ISLAND_{asset_id}_{uuid.uuid4().hex[:6]}",
                action_type=ActionType.ISLAND,
                target_asset=asset_id,
                description=f"Island downstream of {asset_id} using mobile generator",
                expected_benefit_mw=min(mw, 2.5),
                expected_critical_service_score=crit_score * 0.8,
                risk_score=0.25,
                reversibility=0.7,
                required_resources=[ResourceType.MOBILE_GENERATOR],
                estimated_time_minutes=ACTION_TIME_MINUTES[ActionType.ISLAND],
                uncertainty_dependence=0.0,
                failure_probability=0.0,
                reason_codes=reason_codes,
            ))

    # ---- DEFER (always available as fallback) -----------------------
    candidates.append(ActionModel(
        action_id=f"DEFER_{uuid.uuid4().hex[:6]}",
        action_type=ActionType.DEFER,
        target_asset="ALL",
        description="Defer all actions – gather more information before committing",
        expected_benefit_mw=0.0,
        expected_critical_service_score=0.0,
        risk_score=0.0,
        reversibility=1.0,
        required_resources=[],
        estimated_time_minutes=0,
        uncertainty_dependence=0.0,
        failure_probability=0.0,
        reason_codes=["DEFER_FALLBACK"],
    ))

    return candidates
