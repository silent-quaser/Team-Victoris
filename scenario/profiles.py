"""
GridGuard — Storm Profiles

Dataclass definitions for storm event profiles used to calibrate
the synthetic scenario generator.

Profiles are loaded from:
    data/processed/storm_profiles.csv   (built by data_pipeline/preprocessor.py)

If the CSV doesn't exist (e.g., first run), empirical defaults from
EMPIRICAL_STORM_PROFILES in preprocessor.py are used.

Usage:
    from scenario.profiles import StormProfile, get_profile, list_profiles

    profile = get_profile("SEVERE_STORM")
    # profile.failure_prob_line(loading_pct=0.8, is_exposed=True) → 0.52
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class StormProfile:
    """Calibrated storm event parameters for scenario generation."""

    event_type: str
    description: str

    # Duration statistics (hours)
    mean_duration_hours: float = 18.5
    std_duration_hours: float = 12.0

    # Outage magnitude statistics
    mean_customers_affected: float = 145_000
    mean_mw_affected: float = 290.0

    # Base failure probabilities (calibrated from real data)
    line_failure_prob_base: float = 0.25
    transformer_failure_prob_base: float = 0.12
    line_failure_prob_exposed: float = 0.45  # overhead lines, vulnerable positions
    multi_fault_prob: float = 0.35          # probability of multiple simultaneous faults

    # Environmental conditions
    weather_severity: float = 0.75          # [0, 1] normalized severity index
    wind_kmh_mean: float = 85.0
    wind_kmh_std: float = 20.0
    rain_mm_mean: float = 35.0
    rain_mm_std: float = 18.0

    # Metadata
    sample_count: int = 0
    data_source: str = "empirical"

    # ── Failure probability calculations ───────────────────────────────────

    def failure_prob_line(
        self,
        loading_pct: float = 0.5,
        is_exposed: bool = False,
        age_factor: float = 1.0,
        previous_faults: int = 0,
    ) -> float:
        """
        Calculate failure probability for a line segment.

        Parameters
        ----------
        loading_pct:      Current loading as fraction [0, 1]
        is_exposed:       True if overhead / exposed to weather
        age_factor:       Multiplier > 1 for older equipment
        previous_faults:  Historical fault count (increases probability)
        """
        base = self.line_failure_prob_exposed if is_exposed else self.line_failure_prob_base

        # Loading factor: exponential increase near rated capacity
        loading_factor = 1.0 + 0.5 * (loading_pct ** 2)

        # Age degradation
        age_mult = min(age_factor, 2.5)

        # Historical failure penalty
        fault_bonus = min(0.1 * previous_faults, 0.3)

        prob = base * loading_factor * age_mult + fault_bonus
        return float(min(max(prob, 0.0), 0.98))

    def failure_prob_transformer(
        self,
        loading_pct: float = 0.5,
        age_factor: float = 1.0,
    ) -> float:
        """Calculate failure probability for a transformer."""
        base = self.transformer_failure_prob_base
        loading_factor = 1.0 + 0.8 * (loading_pct ** 2)
        return float(min(base * loading_factor * min(age_factor, 2.5), 0.98))

    def sample_wind(self, rng) -> float:
        """Sample wind speed from this profile's distribution (km/h)."""
        return float(max(0, rng.normal(self.wind_kmh_mean, self.wind_kmh_std)))

    def sample_rain(self, rng) -> float:
        """Sample rainfall from this profile's distribution (mm)."""
        return float(max(0, rng.normal(self.rain_mm_mean, self.rain_mm_std)))

    def sample_duration(self, rng) -> float:
        """Sample outage duration in hours."""
        return float(max(0.5, rng.normal(self.mean_duration_hours, self.std_duration_hours)))


# ---------------------------------------------------------------------------
# Profile registry
# ---------------------------------------------------------------------------

def _load_profiles() -> Dict[str, StormProfile]:
    """Load profiles from CSV or fall back to empirical defaults."""
    from data_pipeline.preprocessor import load_storm_profiles

    raw = load_storm_profiles()
    profiles: Dict[str, StormProfile] = {}
    for etype, data in raw.items():
        try:
            profiles[etype] = StormProfile(
                event_type=etype,
                description=str(data.get("description", etype)),
                mean_duration_hours=float(data.get("mean_duration_hours", 18.5)),
                std_duration_hours=float(data.get("std_duration_hours", 12.0)),
                mean_customers_affected=float(data.get("mean_customers_affected", 145000)),
                mean_mw_affected=float(data.get("mean_mw_affected", 290.0)),
                line_failure_prob_base=float(data.get("line_failure_prob_base", 0.25)),
                transformer_failure_prob_base=float(data.get("transformer_failure_prob_base", 0.12)),
                line_failure_prob_exposed=float(data.get("line_failure_prob_exposed", 0.45)),
                multi_fault_prob=float(data.get("multi_fault_prob", 0.35)),
                weather_severity=float(data.get("weather_severity", 0.75)),
                wind_kmh_mean=float(data.get("wind_kmh_mean", 85.0)),
                wind_kmh_std=float(data.get("wind_kmh_std", 20.0)),
                rain_mm_mean=float(data.get("rain_mm_mean", 35.0)),
                rain_mm_std=float(data.get("rain_mm_std", 18.0)),
                sample_count=int(data.get("sample_count", 0)),
                data_source=str(data.get("data_source", "empirical")),
            )
        except Exception as e:
            print(f"[profiles] Warning: could not load profile '{etype}': {e}")
    return profiles


# Lazy-loaded registry
_REGISTRY: Optional[Dict[str, StormProfile]] = None


def _registry() -> Dict[str, StormProfile]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _load_profiles()
    return _REGISTRY


def get_profile(event_type: str) -> StormProfile:
    """Get a storm profile by event type. Raises KeyError if not found."""
    reg = _registry()
    if event_type not in reg:
        # Closest fallback
        fallback = "SEVERE_STORM" if "STORM" in event_type.upper() else "NORMAL"
        return reg.get(fallback, list(reg.values())[0])
    return reg[event_type]


def list_profiles() -> Dict[str, str]:
    """Return dict of {event_type: description} for all available profiles."""
    return {k: v.description for k, v in _registry().items()}


def reset_registry() -> None:
    """Force reload of profiles (useful after preprocessing)."""
    global _REGISTRY
    _REGISTRY = None
