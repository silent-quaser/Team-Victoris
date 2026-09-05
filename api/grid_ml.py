"""
GridGuard API — ML, Grid Simulation, and Uncertainty endpoints.

Exposes the new Grid + ML + Uncertainty layer to the frontend / P3 engine.

Endpoints:
    GET  /grid-ml/network-state          IEEE 33-bus state (PF + faults)
    GET  /grid-ml/impact                 Current grid impact assessment
    POST /grid-ml/inject-fault           Inject fault into IEEE 33-bus
    POST /grid-ml/execute-action         Apply action to simulation
    POST /grid-ml/predict-failure        P(failed) for a single asset
    GET  /grid-ml/predict-all            P(failed) for all assets
    POST /grid-ml/update-belief          Update Bayesian belief state
    GET  /grid-ml/beliefs                All current belief states
    POST /grid-ml/resolve-asset          Resolve asset to FAILED/HEALTHY
    POST /grid-ml/reset-ieee33           Reset IEEE 33-bus simulation
    GET  /grid-ml/model-info             Trained ML model metadata
    GET  /grid-ml/storm-profiles         Available storm profiles
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/grid-ml", tags=["Grid ML"])


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class FaultRequest(BaseModel):
    asset_id: str = Field(..., description="Asset identifier, e.g. 'T3_LINE', 'L6-7'")
    fault_type: str = Field("OPEN_CIRCUIT", description="OPEN_CIRCUIT | UNCERTAIN")
    failure_probability: float = Field(1.0, ge=0.0, le=1.0)
    is_uncertain: bool = False


class ActionRequest(BaseModel):
    action_type: str = Field(..., description="REPAIR | INSPECT | RECONFIGURE | DEFER")
    target_asset: str = Field(..., description="Asset ID to apply action to")


class FailurePredictRequest(BaseModel):
    asset_id: str
    line_idx: int = Field(..., ge=0, le=36)
    env: Dict[str, float] = Field(default_factory=dict)
    observation: Dict[str, Any] = Field(default_factory=dict)
    loading_pct: float = Field(0.5, ge=0.0, le=1.0)
    previous_faults: int = Field(0, ge=0)


class UpdateBeliefRequest(BaseModel):
    asset_id: str
    observations: Dict[str, Any]
    ml_prior: Optional[float] = Field(None, ge=0.0, le=1.0)


class ResolveRequest(BaseModel):
    asset_id: str
    result: str = Field(..., description="FAILED or HEALTHY")


class PredictAllRequest(BaseModel):
    env: Dict[str, float]
    observations: Dict[str, Dict] = Field(default_factory=dict)
    loading: Dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Grid simulation endpoints
# ---------------------------------------------------------------------------

@router.get("/network-state")
def ieee33_network_state():
    """Return full IEEE 33-bus network state including power flow results."""
    from grid.grid_engine import get_grid_state, get_net
    try:
        get_net()  # Ensure network exists
        return get_grid_state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grid state error: {e}")


@router.post("/reset-ieee33")
def reset_ieee33():
    """Reset the IEEE 33-bus simulation to base state (no faults)."""
    from grid.grid_engine import reset_grid, get_grid_state
    from uncertainty.belief import reset_beliefs
    reset_grid()
    reset_beliefs()
    state = get_grid_state()
    return {
        "message": "IEEE 33-bus simulation reset",
        "pf_converged": state["pf_converged"],
        "total_load_mw": state["total_load_mw"],
        "critical_services": state["critical_services"],
    }


@router.post("/inject-fault")
def inject_ieee33_fault(req: FaultRequest):
    """
    Inject a fault into the IEEE 33-bus simulation.

    - OPEN_CIRCUIT + failure_probability=1.0 → line taken out of service immediately
    - UNCERTAIN + failure_probability=0.62 → line stays in service, uncertainty flagged
    """
    from grid.grid_engine import inject_fault, get_grid_state
    try:
        result = inject_fault(
            asset_id=req.asset_id,
            fault_type=req.fault_type,
            failure_probability=req.failure_probability,
            is_uncertain=req.is_uncertain,
        )
        state_update = get_grid_state()
        return {
            "fault_result": result,
            "critical_services": state_update["critical_services"],
            "pf_converged": state_update["pf_converged"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/execute-action")
def execute_ieee33_action(req: ActionRequest):
    """
    Apply a recovery action to the IEEE 33-bus simulation.

    Supported: REPAIR, INSPECT, RECONFIGURE, ISLAND, RESTORE, DEFER.
    Returns updated grid state and power flow results.
    """
    from grid.grid_engine import execute_simulated_action
    try:
        return execute_simulated_action(req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/impact")
def grid_impact():
    """
    Current grid impact assessment.

    Returns MW unavailable, critical service status, buses affected,
    impact score, and restoration percentage.
    """
    from impact.calculator import calculate_grid_impact
    from grid.grid_engine import get_net
    try:
        net = get_net()
        return calculate_grid_impact(net, run_pf=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Impact calculation error: {e}")


# ---------------------------------------------------------------------------
# ML prediction endpoints
# ---------------------------------------------------------------------------

@router.post("/predict-failure")
def predict_failure_probability(req: FailurePredictRequest):
    """
    Predict P(component is failed) using trained XGBoost model.

    Falls back to physics-based estimate if model not yet trained.
    """
    from ml.predictor import predict_failure_probability as _predict, get_model_info
    try:
        prob = _predict(
            asset_id=req.asset_id,
            line_idx=req.line_idx,
            env=req.env,
            observation=req.observation,
            loading_pct=req.loading_pct,
            previous_faults=req.previous_faults,
        )
        return {
            "asset_id": req.asset_id,
            "p_failed": round(prob, 4),
            "is_uncertain": 0.25 <= prob <= 0.75,
            "model_info": get_model_info(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")


@router.post("/predict-all")
def predict_all_assets(req: PredictAllRequest):
    """Predict failure probabilities for all assets in the current grid."""
    from ml.predictor import predict_all_assets as _predict_all
    try:
        probs = _predict_all(
            env=req.env,
            observations=req.observations,
            loading=req.loading,
        )
        return {
            "predictions": probs,
            "uncertain_assets": [a for a, p in probs.items() if 0.25 <= p <= 0.75],
            "likely_failed": [a for a, p in probs.items() if p > 0.75],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")


@router.get("/model-info")
def model_info():
    """Return metadata about the trained XGBoost model."""
    from ml.predictor import get_model_info
    return get_model_info()


# ---------------------------------------------------------------------------
# Uncertainty / belief endpoints
# ---------------------------------------------------------------------------

@router.post("/update-belief")
def update_asset_belief(req: UpdateBeliefRequest):
    """
    Update Bayesian belief state for an asset with new evidence.

    Fuses: SCADA reading + technician report + weather evidence + ML prior.
    """
    from uncertainty.belief import update_belief
    try:
        state = update_belief(
            asset_id=req.asset_id,
            observations=req.observations,
            ml_prior=req.ml_prior,
        )
        return state.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/beliefs")
def all_beliefs():
    """Return current Bayesian belief states for all known assets."""
    from uncertainty.belief import get_all_beliefs, get_uncertain_assets
    all_b = get_all_beliefs()
    uncertain = list(get_uncertain_assets().keys())
    return {
        "beliefs": all_b,
        "uncertain_assets": uncertain,
        "n_uncertain": len(uncertain),
    }


@router.post("/resolve-asset")
def resolve_asset(req: ResolveRequest):
    """
    Resolve an asset state after physical inspection or confirmed repair.

    Once resolved, further evidence updates are blocked.
    result must be 'FAILED' or 'HEALTHY'.
    """
    from uncertainty.belief import resolve_asset_state
    try:
        state = resolve_asset_state(req.asset_id, req.result)
        return state.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Utility endpoints
# ---------------------------------------------------------------------------

@router.get("/storm-profiles")
def storm_profiles():
    """Return available storm profiles and their parameters."""
    from scenario.profiles import list_profiles, _registry
    names = list_profiles()
    registry = _registry()
    result = {}
    for etype, desc in names.items():
        p = registry[etype]
        result[etype] = {
            "description": desc,
            "weather_severity": p.weather_severity,
            "line_failure_prob_base": p.line_failure_prob_base,
            "mean_duration_hours": p.mean_duration_hours,
            "data_source": p.data_source,
        }
    return result


@router.get("/simulate-action-pf")
def simulate_action_feasibility(action_type: str, target_asset: str):
    """
    Pre-validate an action electrically without modifying simulation state.
    Used by P3 to gate candidate actions.
    """
    from grid.power_flow import simulate_action_pf
    action = {"action_type": action_type, "target_asset": target_asset}
    feasible, reason, pf = simulate_action_pf(action)
    return {
        "feasible": feasible,
        "reason": reason,
        "action": action,
        "pf_summary": pf.get("summary") if pf else None,
    }
