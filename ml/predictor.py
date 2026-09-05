"""
GridGuard — Failure Probability Predictor

Loads the trained XGBoost model and provides real-time prediction of
component failure probabilities.

This is the interface P3 calls to get P(asset is failed) for any asset
given the current environmental conditions and observations.

Usage:
    from ml.predictor import predict_failure_probability

    prob = predict_failure_probability(
        asset_id="T3_LINE",
        line_idx=2,
        env={"weather_severity": 0.75, "wind_kmh": 78, "rain_mm": 35,
             "temperature_c": 12, "load_factor": 0.82},
        observation={"scada_reading": 0.55, "sensor_health": 0.8,
                     "comm_available": True, "technician_confidence": 0.70,
                     "weather_evidence": 0.68}
    )
    # → 0.624 (T3 in demo scenario)
"""
from __future__ import annotations
import warnings
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "failure_model.json"

# Lazy-loaded model
_MODEL = None


def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found at {MODEL_PATH}. "
            "Generate data and train first:\n"
            "  python -c \"from scenario.generator import run_generation; run_generation()\"\n"
            "  python -c \"from ml.trainer import train; train()\""
        )

    try:
        import xgboost as xgb
        model = xgb.XGBClassifier()
        model.load_model(str(MODEL_PATH))
        _MODEL = model
        return _MODEL
    except Exception as e:
        raise RuntimeError(f"Failed to load XGBoost model: {e}")


def predict_failure_probability(
    asset_id: str,
    line_idx: int,
    env: Dict[str, float],
    observation: Dict[str, Any],
    loading_pct: float = 0.5,
    previous_faults: int = 0,
) -> float:
    """
    Predict P(component is failed) using the trained XGBoost model.

    Parameters
    ----------
    asset_id:        e.g. 'T3_LINE', 'L6-7', 'L12-13'
    line_idx:        pandapower line DataFrame index
    env:             Environmental conditions dict:
                         weather_severity [0,1], wind_kmh, rain_mm,
                         temperature_c, load_factor [0,1]
    observation:     Operator observations dict:
                         scada_reading [0,1], sensor_health [0,1],
                         comm_available (bool), technician_confidence [0,1],
                         weather_evidence [0,1]
    loading_pct:     Current line loading [0, 1]
    previous_faults: Historical fault count

    Returns
    -------
    float in [0.0, 1.0]: probability that this component is currently failed
    """
    from ml.features import extract_single_asset_features

    X = extract_single_asset_features(
        asset_id=asset_id,
        line_idx=line_idx,
        env=env,
        observation=observation,
        loading_pct=loading_pct,
        previous_faults=previous_faults,
    )

    try:
        model = _load_model()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            prob = float(model.predict_proba(X)[0, 1])
        return float(np.clip(prob, 0.0, 1.0))
    except FileNotFoundError:
        # Model not trained yet — fall back to physics-based estimate
        return _physics_fallback(asset_id, line_idx, env, observation, loading_pct)


def predict_all_assets(
    env: Dict[str, float],
    observations: Dict[str, Dict],
    loading: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    Predict failure probabilities for all known assets.

    Parameters
    ----------
    env:           Scenario-level environmental conditions
    observations:  Dict of asset_id → observation dict
    loading:       Dict of asset_id → loading_pct (optional)

    Returns dict of asset_id → P(failed)
    """
    from grid.ieee33 import LINE_METADATA
    from grid.grid_engine import get_net

    net = get_net()
    results = {}

    for line_idx in range(len(net.line)):
        asset_id = (net.line.at[line_idx, "asset_id"]
                    if "asset_id" in net.line.columns
                    else f"LINE_{line_idx}")
        obs = observations.get(asset_id, observations.get(str(line_idx), {}))
        load_pct = (loading or {}).get(asset_id, 0.5)

        results[asset_id] = predict_failure_probability(
            asset_id=asset_id,
            line_idx=line_idx,
            env=env,
            observation=obs,
            loading_pct=load_pct,
        )

    return results


def _physics_fallback(
    asset_id: str,
    line_idx: int,
    env: Dict,
    observation: Dict,
    loading_pct: float,
) -> float:
    """
    Physics-based failure probability estimate when ML model is not trained.
    Uses the storm profile directly (not a hardcoded constant).
    """
    from scenario.profiles import get_profile
    from grid.ieee33 import LINE_METADATA

    # Determine weather event type from severity
    severity = env.get("weather_severity", 0.3)
    if severity > 0.85:
        event_type = "HURRICANE"
    elif severity > 0.65:
        event_type = "SEVERE_STORM"
    elif severity > 0.45:
        event_type = "HIGH_WIND"
    else:
        event_type = "NORMAL"

    profile = get_profile(event_type)
    meta = LINE_METADATA.get(line_idx, {"exposed": True, "age_factor": 1.3, "dist": 0.5})

    base_prob = profile.failure_prob_line(
        loading_pct=loading_pct,
        is_exposed=meta["exposed"],
        age_factor=meta["age_factor"],
    )

    # Blend with fused observation evidence
    obs_prob = observation.get("fused_probability",
                observation.get("scada_reading", base_prob))
    blended = 0.6 * base_prob + 0.4 * float(obs_prob)
    return float(np.clip(blended, 0.0, 0.98))


def reload_model() -> None:
    """Force reload of the trained model (after retraining)."""
    global _MODEL
    _MODEL = None


def get_model_info() -> Dict[str, Any]:
    """Return info about the trained model."""
    from ml.trainer import evaluate
    info = {"model_path": str(MODEL_PATH), "model_exists": MODEL_PATH.exists()}
    if MODEL_PATH.exists():
        try:
            metrics = evaluate()
            info.update({
                "roc_auc": metrics.get("roc_auc"),
                "accuracy": metrics.get("accuracy"),
                "n_train": metrics.get("n_train"),
                "feature_importance": metrics.get("feature_importance", {}),
            })
        except Exception:
            pass
    return info
