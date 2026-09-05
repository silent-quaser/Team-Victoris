"""
GridGuard — ML Feature Extraction

Extracts feature vectors from synthetic scenario data for XGBoost training.
Every feature is derived from the IEEE 33-bus simulation; no raw dataset
column is used as a direct training label.

Feature vector per component instance:
    # Asset properties
    asset_type_encoded     — 0=line, 1=transformer_zone
    is_exposed             — 1 if overhead/exposed to weather
    age_factor             — [1.0, 2.5] proxy for equipment age
    distance_from_sub      — [0, 1] normalised distance from substation
    previous_faults        — integer count of prior faults

    # Electrical state
    loading_pct            — current loading as fraction [0, 1]
    voltage_pu             — bus voltage (if available from PF)

    # Environmental
    weather_severity       — [0, 1] storm severity index
    wind_kmh               — wind speed (km/h)
    rain_mm                — rainfall (mm)
    temperature_c          — ambient temperature (°C)
    load_factor            — grid-wide load level [0, 1]

    # Observation quality (what the operator sees)
    scada_reading          — SCADA failure indicator [0, 1]
    sensor_health          — sensor reliability [0.1, 1]
    comm_available         — communication link up (0/1)
    technician_confidence  — tech report confidence [0, 1]
    weather_evidence       — weather-based failure evidence [0, 1]

Target:
    true_failed            — binary (0/1) ground truth from simulator
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from scenario.generator import LINE_METADATA

BASE_DIR = Path(__file__).parent.parent
SYNTHETIC_DIR = BASE_DIR / "data" / "synthetic"


FEATURE_COLUMNS = [
    # Asset properties
    "asset_type_encoded",
    "is_exposed",
    "age_factor",
    "distance_from_sub",
    "previous_faults",
    # Electrical
    "loading_pct",
    # Environmental
    "weather_severity",
    "wind_kmh",
    "rain_mm",
    "temperature_c",
    "load_factor",
    # Observation quality
    "scada_reading",
    "sensor_health",
    "comm_available",
    "technician_confidence",
    "weather_evidence",
]

TARGET_COLUMN = "true_failed"


def load_synthetic_data(synthetic_dir: Optional[Path] = None) -> Optional[pd.DataFrame]:
    """
    Load and join synthetic scenario data into a single feature DataFrame.

    Returns None if synthetic data has not been generated yet.
    """
    synth = synthetic_dir or SYNTHETIC_DIR
    comp_path = synth / "component_states.csv"
    obs_path = synth / "observations.csv"
    scen_path = synth / "scenarios.csv"

    if not comp_path.exists() or not obs_path.exists() or not scen_path.exists():
        return None

    comp = pd.read_csv(comp_path)
    obs = pd.read_csv(obs_path)
    scen = pd.read_csv(scen_path)

    # Merge component states + observations
    merge_keys = ["scenario_id", "line_idx"]
    df = comp.merge(obs, on=merge_keys, suffixes=("", "_obs"))

    # Merge scenario-level environmental data
    df = df.merge(
        scen[["scenario_id", "weather_severity", "wind_kmh", "rain_mm",
              "temperature_c", "load_factor"]],
        on="scenario_id",
    )

    return df


def build_feature_matrix(
    df: pd.DataFrame,
    line_metadata: Optional[Dict] = None,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Build feature matrix X and target vector y from the raw joined DataFrame.

    Parameters
    ----------
    df:            Merged DataFrame from load_synthetic_data()
    line_metadata: Override for LINE_METADATA (defaults to grid.ieee33.LINE_METADATA)

    Returns (X, y) where X is features, y is binary target.
    """
    meta = line_metadata or LINE_METADATA
    df = df.copy()

    # Asset type encoding (T3_LINE = transformer zone → type 1)
    df["asset_type_encoded"] = df["asset_id"].apply(
        lambda a: 1 if "T3" in str(a) or a == "LINE_2" else 0
    )

    # Fill in metadata from LINE_METADATA
    df["distance_from_sub"] = df["line_idx"].apply(
        lambda idx: meta.get(int(idx), {}).get("dist", 0.5)
    )

    # Ensure column alignment
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0

    # Coerce types
    for col in FEATURE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN], errors="coerce").fillna(0).astype(int)

    X = df[FEATURE_COLUMNS].astype(float)
    y = df[TARGET_COLUMN]

    return X, y


def extract_single_asset_features(
    asset_id: str,
    line_idx: int,
    env: Dict,
    observation: Dict,
    loading_pct: float = 0.5,
    previous_faults: int = 0,
) -> pd.DataFrame:
    """
    Build a single-row feature DataFrame for real-time prediction.

    Used by predictor.py to get P(failure) for a live asset.

    Parameters
    ----------
    asset_id:       e.g. 'T3_LINE', 'L6-7'
    line_idx:       line DataFrame index
    env:            dict with weather_severity, wind_kmh, rain_mm, temperature_c, load_factor
    observation:    dict with scada_reading, sensor_health, comm_available,
                    technician_confidence, weather_evidence
    loading_pct:    current loading [0, 1]
    previous_faults:historical fault count
    """
    meta = LINE_METADATA.get(line_idx, {"exposed": True, "age_factor": 1.3, "dist": 0.5})
    features = {
        "asset_type_encoded": 1 if "T3" in asset_id else 0,
        "is_exposed": int(meta["exposed"]),
        "age_factor": meta["age_factor"],
        "distance_from_sub": meta["dist"],
        "previous_faults": previous_faults,
        "loading_pct": loading_pct,
        "weather_severity": env.get("weather_severity", 0.5),
        "wind_kmh": env.get("wind_kmh", 30.0),
        "rain_mm": env.get("rain_mm", 10.0),
        "temperature_c": env.get("temperature_c", 15.0),
        "load_factor": env.get("load_factor", 0.75),
        "scada_reading": observation.get("scada_reading", 0.5),
        "sensor_health": observation.get("sensor_health", 0.8),
        "comm_available": int(observation.get("comm_available", True)),
        "technician_confidence": observation.get("technician_confidence", 0.5),
        "weather_evidence": observation.get("weather_evidence", 0.5),
    }
    return pd.DataFrame([features])[FEATURE_COLUMNS]
