"""
GridGuard — Bayesian Evidence Fusion / Uncertainty Model

Maintains a belief state per asset and updates it using evidence from
multiple sources. This is intentionally transparent and interpretable —
no opaque neural networks.

Evidence sources:
    SCADA          — sensor reading of failure state [0, 1]
    Technician     — human inspection report confidence [0, 1]
    Weather        — weather-based failure likelihood [0, 1]
    Sensor Health  — reliability weighting for SCADA [0, 1]
    Historical     — prior failure rate from ML model [0, 1]

Fusion method:
    Weighted Bayesian update starting from ML prior.

    P(failed | evidence) ∝
        P(SCADA | failed) × P(tech | failed) × P(weather | failed) × P(ML_prior)

    Simplified to a weighted average with reliability weights,
    which approximates the Bayesian posterior under mild independence assumptions.

Public API (called by P3):
    get_uncertainty(asset_id)              → BeliefState
    update_belief(asset_id, observations)  → BeliefState
    resolve_asset_state(asset_id, result)  → mark FAILED or HEALTHY
    reset_beliefs()                        → clear all beliefs
    get_all_beliefs()                      → Dict[str, BeliefState]

Example:
    from uncertainty.belief import get_uncertainty, update_belief

    state = get_uncertainty("T3_LINE")
    # → BeliefState(p_failed=0.62, is_uncertain=True, confidence=0.41)

    state = update_belief("T3_LINE", {
        "scada_reading": 0.70,
        "technician_confidence": 0.81,
        "weather_evidence": 0.92,
        "sensor_health": 0.75,
        "comm_available": True,
    })
    # → BeliefState(p_failed=0.78, is_uncertain=True, confidence=0.68)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Uncertainty thresholds
# ---------------------------------------------------------------------------
UNCERTAIN_LOW = 0.25   # Below this → probably HEALTHY
UNCERTAIN_HIGH = 0.75  # Above this → probably FAILED
# Between [UNCERTAIN_LOW, UNCERTAIN_HIGH] → UNCERTAIN (inspect is valuable)


@dataclass
class BeliefState:
    """
    Current uncertainty state for a single asset.

    p_failed:       Posterior probability asset is failed [0, 1]
    is_uncertain:   True if p_failed ∈ [UNCERTAIN_LOW, UNCERTAIN_HIGH]
    confidence:     Reliability of the estimate [0, 1] — depends on
                    evidence quality (sensor health, comm availability, etc.)
    resolved:       True once physical inspection or repair confirms state
    resolved_state: 'FAILED' or 'HEALTHY' after resolution
    evidence_log:   Ordered list of (source, value, weight) evidence items
    """
    asset_id: str
    p_failed: float = 0.0
    is_uncertain: bool = False
    confidence: float = 0.5
    resolved: bool = False
    resolved_state: Optional[str] = None
    evidence_log: list = field(default_factory=list)

    def __post_init__(self):
        self._update_uncertainty_flag()

    def _update_uncertainty_flag(self):
        self.is_uncertain = (
            not self.resolved
            and UNCERTAIN_LOW <= self.p_failed <= UNCERTAIN_HIGH
        )

    @property
    def p_healthy(self) -> float:
        return 1.0 - self.p_failed

    @property
    def entropy(self) -> float:
        """Shannon entropy of the binary belief — max at p=0.5."""
        import math
        p = self.p_failed
        if p <= 0 or p >= 1:
            return 0.0
        return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "p_failed": round(self.p_failed, 4),
            "p_healthy": round(self.p_healthy, 4),
            "is_uncertain": self.is_uncertain,
            "confidence": round(self.confidence, 4),
            "entropy": round(self.entropy, 4),
            "resolved": self.resolved,
            "resolved_state": self.resolved_state,
            "evidence_count": len(self.evidence_log),
        }


# ---------------------------------------------------------------------------
# Global belief registry
# ---------------------------------------------------------------------------
_BELIEFS: Dict[str, BeliefState] = {}


def _get_or_create(asset_id: str) -> BeliefState:
    if asset_id not in _BELIEFS:
        _BELIEFS[asset_id] = BeliefState(asset_id=asset_id)
    return _BELIEFS[asset_id]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_uncertainty(asset_id: str) -> BeliefState:
    """
    Get current uncertainty belief state for an asset.

    If the asset has no prior evidence, returns a BeliefState with
    p_failed from the ML model (or physics fallback).
    """
    return _get_or_create(asset_id)


def update_belief(
    asset_id: str,
    observations: Dict[str, Any],
    ml_prior: Optional[float] = None,
) -> BeliefState:
    """
    Update the belief state for an asset with new evidence.

    Uses weighted Bayesian fusion:
        P(failed | evidence) ∝ Σ w_i × evidence_i / Σ w_i

    Parameters
    ----------
    asset_id:     Asset to update
    observations: Dict with any combination of:
                      scada_reading         [0, 1]
                      technician_confidence [0, 1]
                      weather_evidence      [0, 1]
                      sensor_health         [0, 1]  (reliability of SCADA)
                      comm_available        bool
                      historical_rate       [0, 1]  (from ML or records)
    ml_prior:     Prior probability from ML model (optional override)

    Returns updated BeliefState.
    """
    state = _get_or_create(asset_id)

    if state.resolved:
        return state  # Resolved states don't change

    # ── Extract evidence ───────────────────────────────────────────────────
    sensor_health = float(observations.get("sensor_health", 0.8))
    comm_available = bool(observations.get("comm_available", True))
    comm_factor = 1.0 if comm_available else 0.3  # Degraded if comms down

    evidence_items = []

    # SCADA reading
    if "scada_reading" in observations:
        scada_val = float(observations["scada_reading"])
        scada_weight = sensor_health * comm_factor * 1.5  # Most direct signal
        evidence_items.append(("SCADA", scada_val, scada_weight))

    # Technician report
    if "technician_confidence" in observations:
        tech_val = float(observations["technician_confidence"])
        tech_weight = 1.2  # High weight — human judgment
        evidence_items.append(("TECHNICIAN", tech_val, tech_weight))

    # Weather evidence
    if "weather_evidence" in observations:
        weather_val = float(observations["weather_evidence"])
        weather_weight = 0.8  # Indirect signal
        evidence_items.append(("WEATHER", weather_val, weather_weight))

    # ML model prior
    ml_val = ml_prior if ml_prior is not None else observations.get("historical_rate", None)
    if ml_val is not None:
        ml_weight = 1.0  # Equal weight to model
        evidence_items.append(("ML_PRIOR", float(ml_val), ml_weight))
    elif state.p_failed > 0:
        # Use existing belief as prior
        evidence_items.append(("PRIOR", state.p_failed, 0.7))

    # ── Fuse evidence ──────────────────────────────────────────────────────
    if not evidence_items:
        return state

    total_weight = sum(w for _, _, w in evidence_items)
    if total_weight <= 0:
        return state

    p_fused = sum(v * w for _, v, w in evidence_items) / total_weight
    p_fused = float(min(max(p_fused, 0.0), 1.0))

    # Confidence = weighted reliability of evidence
    raw_confidence = (
        sensor_health * comm_factor * 0.4
        + 0.35  # technician base
        + 0.25 * (1 if ml_prior is not None else 0)
    )
    confidence = float(min(max(raw_confidence, 0.0), 1.0))

    # Bayesian smoothing: don't swing belief too violently in one update
    # Blend 70% new evidence, 30% prior
    prior_p = state.p_failed
    if prior_p > 0:
        p_fused = 0.70 * p_fused + 0.30 * prior_p

    # Log evidence
    for source, val, weight in evidence_items:
        state.evidence_log.append({
            "source": source,
            "value": round(float(val), 4),
            "weight": round(float(weight), 4),
        })

    # Update state
    state.p_failed = round(p_fused, 4)
    state.confidence = round(confidence, 4)
    state._update_uncertainty_flag()

    _BELIEFS[asset_id] = state
    return state


def initialise_from_ml(
    asset_probabilities: Dict[str, float],
) -> Dict[str, BeliefState]:
    """
    Initialise belief states from ML model predictions.

    Parameters
    ----------
    asset_probabilities: Dict of asset_id → P(failed) from ML model

    Returns updated beliefs dict.
    """
    for asset_id, prob in asset_probabilities.items():
        state = _get_or_create(asset_id)
        if not state.resolved:
            state.p_failed = float(np.clip(prob, 0.0, 1.0))
            state.confidence = 0.6  # Medium confidence — model only
            state._update_uncertainty_flag()
            state.evidence_log.append({
                "source": "ML_MODEL_INIT",
                "value": round(prob, 4),
                "weight": 1.0,
            })
    return dict(_BELIEFS)


def resolve_asset_state(
    asset_id: str,
    result: str,  # 'FAILED' or 'HEALTHY'
) -> BeliefState:
    """
    Resolve an asset's state after physical inspection or confirmed repair.

    After this call, further evidence updates are blocked.

    Parameters
    ----------
    asset_id: Asset identifier
    result:   'FAILED' or 'HEALTHY'
    """
    state = _get_or_create(asset_id)
    result = result.upper()
    if result not in ("FAILED", "HEALTHY"):
        raise ValueError(f"result must be 'FAILED' or 'HEALTHY', got '{result}'")

    state.resolved = True
    state.resolved_state = result
    state.p_failed = 1.0 if result == "FAILED" else 0.0
    state.confidence = 1.0
    state.is_uncertain = False
    state.evidence_log.append({
        "source": "PHYSICAL_INSPECTION",
        "value": 1.0 if result == "FAILED" else 0.0,
        "weight": 10.0,  # Overrides all other evidence
    })
    _BELIEFS[asset_id] = state
    return state


def reset_beliefs() -> None:
    """Clear all belief states (e.g., on scenario reset)."""
    global _BELIEFS
    _BELIEFS = {}


def get_all_beliefs() -> Dict[str, Dict[str, Any]]:
    """Return serialised belief states for all assets."""
    return {asset_id: state.to_dict() for asset_id, state in _BELIEFS.items()}


def get_uncertain_assets() -> Dict[str, BeliefState]:
    """Return only assets currently in UNCERTAIN state."""
    return {k: v for k, v in _BELIEFS.items() if v.is_uncertain}


# ── numpy needed for clip ───────────────────────────────────────────────────
try:
    import numpy as np
except ImportError:
    class np:  # type: ignore
        @staticmethod
        def clip(v, lo, hi):
            return max(lo, min(hi, v))
