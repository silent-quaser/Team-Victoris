"""
GridGuard — Real Data Preprocessor

Processes the DOE/PNNL Event-Correlated Outage Dataset into:
    data/processed/storm_profiles.csv    — calibrated storm parameters
    data/processed/event_statistics.csv  — per-event-type statistics

These profiles calibrate the synthetic scenario generator so that
simulated storms reflect real outage magnitudes, durations, and causes.

Data flow:
    raw/event_correlated/Outage_Dataset_R1.csv
            ↓
    parse_event_correlated()
            ↓
    extract_storm_profiles()
            ↓
    data/processed/storm_profiles.csv
            ↓
    scenario/profiles.py (loads these profiles)
            ↓
    ScenarioGenerator (calibrated fault probabilities)

If the real dataset is not available, the preprocessor falls back to
empirical defaults derived from published IEEE/DOE outage statistics.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "event_correlated"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


# ---------------------------------------------------------------------------
# Known column aliases across dataset versions
# ---------------------------------------------------------------------------
COLUMN_MAP = {
    # event type
    "event_type": ["event_type", "EventType", "event type", "type", "cause_category"],
    # timing
    "event_start": ["event_start", "start_date", "StartDate", "EventStart", "begin_date"],
    "event_end": ["event_end", "end_date", "EndDate", "EventEnd"],
    "duration_hours": ["duration_hours", "Duration_Hours", "outage_hours", "duration"],
    # magnitude
    "customers_out_max": ["customers_out_max", "CustomersOut", "peak_customers",
                           "customers_affected", "cust_affected"],
    "mw_affected": ["mw_affected", "MW_Affected", "demand_loss_mw", "mw_lost"],
    # geography
    "state": ["state", "State", "state_name"],
    "county": ["county", "County", "county_name"],
    # cause
    "cause": ["cause", "Cause", "primary_cause", "event_cause"],
}


# ---------------------------------------------------------------------------
# Empirical defaults (from IEEE/DOE published statistics)
# ---------------------------------------------------------------------------
# These are used when the real dataset is unavailable.
# Sources: DOE OE-417 Annual Summary Reports, IEEE 1366-2012.
EMPIRICAL_STORM_PROFILES = {
    "SEVERE_STORM": {
        "event_type": "SEVERE_STORM",
        "description": "Severe thunderstorm / convective event",
        "mean_duration_hours": 18.5,
        "std_duration_hours": 12.0,
        "mean_customers_affected": 145000,
        "mean_mw_affected": 290.0,
        # Calibrated failure probabilities for different component types
        "line_failure_prob_base": 0.25,
        "transformer_failure_prob_base": 0.12,
        "line_failure_prob_exposed": 0.45,
        "multi_fault_prob": 0.35,
        "weather_severity": 0.75,
        "wind_kmh_mean": 85.0,
        "wind_kmh_std": 20.0,
        "rain_mm_mean": 35.0,
        "rain_mm_std": 18.0,
        "sample_count": 1250,
    },
    "HURRICANE": {
        "event_type": "HURRICANE",
        "description": "Hurricane / tropical storm",
        "mean_duration_hours": 72.0,
        "std_duration_hours": 48.0,
        "mean_customers_affected": 890000,
        "mean_mw_affected": 1780.0,
        "line_failure_prob_base": 0.55,
        "transformer_failure_prob_base": 0.30,
        "line_failure_prob_exposed": 0.80,
        "multi_fault_prob": 0.75,
        "weather_severity": 0.95,
        "wind_kmh_mean": 145.0,
        "wind_kmh_std": 25.0,
        "rain_mm_mean": 120.0,
        "rain_mm_std": 40.0,
        "sample_count": 215,
    },
    "ICE_STORM": {
        "event_type": "ICE_STORM",
        "description": "Ice / freezing rain event",
        "mean_duration_hours": 42.0,
        "std_duration_hours": 24.0,
        "mean_customers_affected": 215000,
        "mean_mw_affected": 430.0,
        "line_failure_prob_base": 0.30,
        "transformer_failure_prob_base": 0.08,
        "line_failure_prob_exposed": 0.55,
        "multi_fault_prob": 0.45,
        "weather_severity": 0.80,
        "wind_kmh_mean": 45.0,
        "wind_kmh_std": 15.0,
        "rain_mm_mean": 0.0,
        "rain_mm_std": 0.0,
        "sample_count": 380,
    },
    "HIGH_WIND": {
        "event_type": "HIGH_WIND",
        "description": "High wind without precipitation",
        "mean_duration_hours": 8.0,
        "std_duration_hours": 6.0,
        "mean_customers_affected": 45000,
        "mean_mw_affected": 90.0,
        "line_failure_prob_base": 0.12,
        "transformer_failure_prob_base": 0.04,
        "line_failure_prob_exposed": 0.28,
        "multi_fault_prob": 0.15,
        "weather_severity": 0.55,
        "wind_kmh_mean": 95.0,
        "wind_kmh_std": 18.0,
        "rain_mm_mean": 5.0,
        "rain_mm_std": 5.0,
        "sample_count": 620,
    },
    "NORMAL": {
        "event_type": "NORMAL",
        "description": "Normal operating conditions (no weather event)",
        "mean_duration_hours": 2.5,
        "std_duration_hours": 2.0,
        "mean_customers_affected": 2500,
        "mean_mw_affected": 5.0,
        "line_failure_prob_base": 0.02,
        "transformer_failure_prob_base": 0.005,
        "line_failure_prob_exposed": 0.04,
        "multi_fault_prob": 0.03,
        "weather_severity": 0.05,
        "wind_kmh_mean": 15.0,
        "wind_kmh_std": 8.0,
        "rain_mm_mean": 2.0,
        "rain_mm_std": 5.0,
        "sample_count": 5200,
    },
}


def _resolve_column(df: pd.DataFrame, aliases: List[str]) -> Optional[str]:
    """Find the first matching column name from a list of aliases."""
    cols_lower = {c.lower(): c for c in df.columns}
    for alias in aliases:
        if alias in df.columns:
            return alias
        if alias.lower() in cols_lower:
            return cols_lower[alias.lower()]
    return None


def parse_event_correlated(filepath: Path) -> pd.DataFrame:
    """Parse the Event-Correlated Outage Dataset CSV/XLSX."""
    if not filepath.exists():
        raise FileNotFoundError(f"Dataset not found: {filepath}")

    if filepath.suffix == ".csv":
        df = pd.read_csv(filepath, low_memory=False)
    else:
        df = pd.read_excel(filepath)

    # Standardise column names
    rename_map = {}
    for standard, aliases in COLUMN_MAP.items():
        found = _resolve_column(df, aliases)
        if found and found != standard:
            rename_map[found] = standard
    df = df.rename(columns=rename_map)

    # Ensure required columns exist (fill with NaN if missing)
    for col in ["event_type", "duration_hours", "customers_out_max", "mw_affected"]:
        if col not in df.columns:
            df[col] = np.nan

    # Parse datetimes
    for dt_col in ["event_start", "event_end"]:
        if dt_col in df.columns:
            df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce", utc=True)

    # Coerce numeric
    for num_col in ["duration_hours", "customers_out_max", "mw_affected"]:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")

    print(f"[preprocessor] Loaded {len(df):,} records from {filepath.name}")
    print(f"[preprocessor] Columns: {list(df.columns)[:10]} ...")
    return df


def extract_storm_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate the event-correlated dataset into storm profiles.

    Groups by event_type and computes:
        - mean/std duration
        - mean customers affected
        - mean MW affected
        - failure probability calibration factors
    """
    if "event_type" not in df.columns or df["event_type"].isna().all():
        print("[preprocessor] No event_type column — using empirical defaults")
        return _empirical_profiles_df()

    # Normalise event types
    type_map = {
        "thunderstorm": "SEVERE_STORM", "severe storm": "SEVERE_STORM",
        "storm": "SEVERE_STORM", "convective": "SEVERE_STORM",
        "hurricane": "HURRICANE", "tropical storm": "HURRICANE",
        "ice": "ICE_STORM", "freezing rain": "ICE_STORM", "winter": "ICE_STORM",
        "wind": "HIGH_WIND", "high wind": "HIGH_WIND",
        "normal": "NORMAL", "equipment": "NORMAL",
    }
    df = df.copy()
    df["event_type_norm"] = (
        df["event_type"].astype(str).str.lower().str.strip()
        .map(lambda t: next((v for k, v in type_map.items() if k in t), "NORMAL"))
    )

    profiles = []
    for etype, group in df.groupby("event_type_norm"):
        dur = group["duration_hours"].dropna()
        cust = group["customers_out_max"].dropna()
        mw = group["mw_affected"].dropna()

        empirical = EMPIRICAL_STORM_PROFILES.get(etype, EMPIRICAL_STORM_PROFILES["NORMAL"])

        # Calibrate failure probabilities from MW affected ratio
        mean_mw = float(mw.mean()) if len(mw) > 0 else empirical["mean_mw_affected"]
        ref_mw = empirical["mean_mw_affected"]
        scale = min(mean_mw / max(ref_mw, 1.0), 2.0)

        profiles.append({
            "event_type": etype,
            "description": empirical["description"],
            "sample_count": int(len(group)),
            "mean_duration_hours": float(dur.mean()) if len(dur) > 0 else empirical["mean_duration_hours"],
            "std_duration_hours": float(dur.std()) if len(dur) > 1 else empirical["std_duration_hours"],
            "mean_customers_affected": float(cust.mean()) if len(cust) > 0 else empirical["mean_customers_affected"],
            "mean_mw_affected": mean_mw,
            "line_failure_prob_base": min(empirical["line_failure_prob_base"] * scale, 0.95),
            "transformer_failure_prob_base": min(empirical["transformer_failure_prob_base"] * scale, 0.95),
            "line_failure_prob_exposed": min(empirical["line_failure_prob_exposed"] * scale, 0.95),
            "multi_fault_prob": empirical["multi_fault_prob"],
            "weather_severity": empirical["weather_severity"],
            "wind_kmh_mean": empirical["wind_kmh_mean"],
            "wind_kmh_std": empirical["wind_kmh_std"],
            "rain_mm_mean": empirical["rain_mm_mean"],
            "rain_mm_std": empirical["rain_mm_std"],
            "data_source": "event_correlated_dataset",
        })

    return pd.DataFrame(profiles)


def _empirical_profiles_df() -> pd.DataFrame:
    """Build profiles DataFrame from hardcoded empirical defaults."""
    rows = []
    for etype, data in EMPIRICAL_STORM_PROFILES.items():
        row = dict(data)
        row["data_source"] = "empirical_ieee_doe_defaults"
        rows.append(row)
    return pd.DataFrame(rows)


def run_preprocessing(force: bool = False) -> Dict[str, Path]:
    """
    Full preprocessing pipeline:
        1. Load raw dataset (or fall back to empirical)
        2. Extract storm profiles
        3. Save processed CSVs

    Returns dict of output paths.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output = {}

    storm_profile_path = PROCESSED_DIR / "storm_profiles.csv"
    event_stats_path = PROCESSED_DIR / "event_statistics.csv"

    if storm_profile_path.exists() and not force:
        print(f"[preprocessor] Processed data already exists: {storm_profile_path}")
        output["storm_profiles"] = storm_profile_path
        output["event_statistics"] = event_stats_path
        return output

    # Try to load real data
    from data_pipeline.downloader import get_dataset_path
    dataset_path = get_dataset_path()

    if dataset_path and dataset_path.exists():
        print(f"[preprocessor] Processing real dataset: {dataset_path}")
        df = parse_event_correlated(dataset_path)
        profiles = extract_storm_profiles(df)

        # Save event statistics
        stats = df.groupby(
            df.get("event_type_norm", pd.Series(["NORMAL"] * len(df)))
        ).agg({
            "duration_hours": ["count", "mean", "std", "median"],
            "customers_out_max": ["mean", "max"],
            "mw_affected": ["mean", "max"],
        }).round(2)
        stats.to_csv(event_stats_path)
        output["event_statistics"] = event_stats_path
    else:
        print("[preprocessor] Real dataset not available — using empirical defaults")
        profiles = _empirical_profiles_df()
        output["event_statistics"] = None

    profiles.to_csv(storm_profile_path, index=False)
    output["storm_profiles"] = storm_profile_path
    print(f"[preprocessor] Storm profiles saved: {storm_profile_path} ({len(profiles)} profiles)")

    return output


def load_storm_profiles() -> Dict[str, Dict]:
    """Load storm profiles from CSV (or empirical defaults if CSV missing)."""
    path = PROCESSED_DIR / "storm_profiles.csv"
    if path.exists():
        df = pd.read_csv(path)
        return {row["event_type"]: row.to_dict() for _, row in df.iterrows()}
    # Fall back to in-memory defaults
    return EMPIRICAL_STORM_PROFILES


if __name__ == "__main__":
    run_preprocessing()
