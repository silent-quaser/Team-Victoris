"""
GridGuard — Synthetic Scenario Generator

Generates reproducible synthetic grid scenarios from the IEEE 33-bus model
driven by calibrated storm profiles from real outage data.

Each scenario contains:
    TRUE STATE    — ground truth (what actually happened in the simulator)
    OBSERVED STATE — imperfect observations (what the operator/SCADA sees)

This separation is the core GridGuard concept: decisions must be made
under uncertainty because the operator cannot directly observe true state.

Output files (written to data/synthetic/):
    scenarios.csv           — scenario metadata + environment
    component_states.csv    — true component failure states
    observations.csv        — imperfect observed states
    powerflow_results.csv   — PF results per scenario
    critical_impacts.csv    — MW loss and critical service impacts

Usage:
    gen = ScenarioGenerator(seed=42)
    gen.generate(n=2000)
    # → writes 5 CSVs to data/synthetic/
"""
from __future__ import annotations
import copy
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pandapower as pp

from grid.ieee33 import build_ieee33_net, CRITICAL_SERVICE_LOADS, LINE_ASSET_MAP
from scenario.profiles import get_profile, list_profiles, StormProfile

BASE_DIR = Path(__file__).parent.parent
SYNTHETIC_DIR = BASE_DIR / "data" / "synthetic"

# ---------------------------------------------------------------------------
# Asset metadata for 37 lines in case33bw (+ 5 tie switches)
# ---------------------------------------------------------------------------
# exposed_to_weather: True for overhead lines
# age_factor: 1.0 = new, 2.0 = old
# distance_from_sub: 0 = at substation, 1 = end of feeder
LINE_METADATA = {
    0:  {"exposed": True,  "age_factor": 1.2, "dist": 0.05},
    1:  {"exposed": True,  "age_factor": 1.4, "dist": 0.10},
    2:  {"exposed": True,  "age_factor": 1.8, "dist": 0.15},  # T3_LINE (transformer zone)
    3:  {"exposed": True,  "age_factor": 1.1, "dist": 0.20},
    4:  {"exposed": True,  "age_factor": 1.3, "dist": 0.25},
    5:  {"exposed": True,  "age_factor": 1.5, "dist": 0.30},  # L6-7
    6:  {"exposed": True,  "age_factor": 1.2, "dist": 0.35},
    7:  {"exposed": False, "age_factor": 1.0, "dist": 0.40},
    8:  {"exposed": True,  "age_factor": 1.6, "dist": 0.45},
    9:  {"exposed": True,  "age_factor": 1.4, "dist": 0.50},
    10: {"exposed": True,  "age_factor": 1.1, "dist": 0.30},
    11: {"exposed": True,  "age_factor": 1.7, "dist": 0.35},  # L12-13
    12: {"exposed": True,  "age_factor": 1.3, "dist": 0.40},
    13: {"exposed": False, "age_factor": 1.0, "dist": 0.45},
    14: {"exposed": True,  "age_factor": 1.2, "dist": 0.50},
    15: {"exposed": True,  "age_factor": 1.5, "dist": 0.55},
    16: {"exposed": True,  "age_factor": 1.4, "dist": 0.60},
    17: {"exposed": True,  "age_factor": 1.6, "dist": 0.65},
    18: {"exposed": True,  "age_factor": 1.3, "dist": 0.55},
    19: {"exposed": False, "age_factor": 1.1, "dist": 0.60},
    20: {"exposed": True,  "age_factor": 1.4, "dist": 0.65},
    21: {"exposed": True,  "age_factor": 1.2, "dist": 0.70},
    22: {"exposed": True,  "age_factor": 1.5, "dist": 0.75},
    23: {"exposed": True,  "age_factor": 1.3, "dist": 0.80},
    24: {"exposed": True,  "age_factor": 1.8, "dist": 0.85},  # L25-26
    25: {"exposed": True,  "age_factor": 1.6, "dist": 0.90},
    26: {"exposed": True,  "age_factor": 1.4, "dist": 0.60},
    27: {"exposed": True,  "age_factor": 1.2, "dist": 0.65},
    28: {"exposed": False, "age_factor": 1.0, "dist": 0.70},
    29: {"exposed": True,  "age_factor": 1.5, "dist": 0.75},
    30: {"exposed": True,  "age_factor": 1.7, "dist": 0.80},
    31: {"exposed": True,  "age_factor": 1.3, "dist": 0.50},
    32: {"exposed": True,  "age_factor": 1.1, "dist": 0.55},
    33: {"exposed": True,  "age_factor": 1.4, "dist": 0.60},
    34: {"exposed": False, "age_factor": 1.0, "dist": 0.65},
    35: {"exposed": True,  "age_factor": 1.2, "dist": 0.70},
    36: {"exposed": True,  "age_factor": 1.5, "dist": 0.75},
}

# Scenario type weights (probability of each event type being selected)
SCENARIO_TYPE_WEIGHTS = {
    "NORMAL":        0.40,
    "SEVERE_STORM":  0.30,
    "HIGH_WIND":     0.15,
    "ICE_STORM":     0.10,
    "HURRICANE":     0.05,
}

# Observation noise model (how uncertain SCADA/sensors are under different conditions)
SCADA_NOISE_BY_SEVERITY = {
    "NORMAL":       0.05,   # Very reliable under normal conditions
    "SEVERE_STORM": 0.20,   # Moderate noise
    "HIGH_WIND":    0.15,
    "ICE_STORM":    0.25,   # Ice can disrupt sensors
    "HURRICANE":    0.35,   # Highest uncertainty
}


class ScenarioGenerator:
    """
    Generates synthetic IEEE 33-bus fault scenarios.

    Each scenario:
        1. Selects an event type (NORMAL, SEVERE_STORM, HURRICANE, etc.)
        2. Samples environmental conditions from the calibrated storm profile
        3. Computes failure probabilities for every line based on environment,
           loading, age, and prior faults
        4. Samples TRUE states (binary: failed/healthy) from those probabilities
        5. Generates OBSERVED states with realistic sensor noise
        6. Runs pandapower power flow on the faulted network
        7. Computes MW loss and critical service impacts
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self._base_net = build_ieee33_net()

    def generate(
        self,
        n: int = 2000,
        output_dir: Optional[Path] = None,
        verbose: bool = True,
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate n scenarios and write to data/synthetic/.

        Returns dict of DataFrames.
        """
        output_dir = output_dir or SYNTHETIC_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        scenarios_rows = []
        component_rows = []
        observation_rows = []
        pf_rows = []
        impact_rows = []

        event_types = list(SCENARIO_TYPE_WEIGHTS.keys())
        weights = [SCENARIO_TYPE_WEIGHTS[et] for et in event_types]

        for i in range(n):
            if verbose and (i % 200 == 0):
                print(f"  [generator] Scenario {i}/{n} ...")

            scenario_id = f"SCN_{i:05d}"

            # 1. Sample event type
            event_type = str(self.rng.choice(event_types, p=weights))
            profile = get_profile(event_type)

            # 2. Sample environment
            env = self._sample_environment(profile)

            # 3. Compute failure probabilities and sample true states
            true_states, failure_probs = self._sample_true_states(profile, env)

            # 4. Generate observations
            observations = self._generate_observations(true_states, failure_probs, profile, env)

            # 5. Run power flow on faulted network
            pf_result = self._run_faulted_pf(true_states)

            # 6. Compute impacts
            impact = self._compute_impact(pf_result, true_states)

            # Assemble rows
            scenario_row = {
                "scenario_id": scenario_id,
                "event_type": event_type,
                "weather_severity": round(env["weather_severity"], 3),
                "wind_kmh": round(env["wind_kmh"], 1),
                "rain_mm": round(env["rain_mm"], 1),
                "temperature_c": round(env["temperature_c"], 1),
                "load_factor": round(env["load_factor"], 3),
                "n_true_failures": int(sum(v["true_failed"] for v in true_states.values())),
                "n_uncertain": int(sum(1 for v in observations.values() if v["is_uncertain"])),
                "seed": self.seed,
                "scenario_index": i,
            }
            scenarios_rows.append(scenario_row)

            for line_idx, state in true_states.items():
                component_rows.append({
                    "scenario_id": scenario_id,
                    "line_idx": int(line_idx),
                    "asset_id": state["asset_id"],
                    "true_failed": int(state["true_failed"]),
                    "failure_probability": round(state["failure_probability"], 4),
                    "loading_pct": round(state["loading_pct"], 3),
                    "is_exposed": int(state["is_exposed"]),
                    "age_factor": round(state["age_factor"], 2),
                    "previous_faults": int(state["previous_faults"]),
                })

            for line_idx, obs in observations.items():
                observation_rows.append({
                    "scenario_id": scenario_id,
                    "line_idx": int(line_idx),
                    "asset_id": obs["asset_id"],
                    "scada_reading": round(obs["scada_reading"], 4),
                    "technician_confidence": round(obs["technician_confidence"], 4),
                    "weather_evidence": round(obs["weather_evidence"], 4),
                    "sensor_health": round(obs["sensor_health"], 4),
                    "comm_available": int(obs["comm_available"]),
                    "fused_probability": round(obs["fused_probability"], 4),
                    "is_uncertain": int(obs["is_uncertain"]),
                })

            pf_rows.append({
                "scenario_id": scenario_id,
                **pf_result,
            })

            impact_rows.append({
                "scenario_id": scenario_id,
                **impact,
            })

        # Build DataFrames
        dfs = {
            "scenarios": pd.DataFrame(scenarios_rows),
            "component_states": pd.DataFrame(component_rows),
            "observations": pd.DataFrame(observation_rows),
            "powerflow_results": pd.DataFrame(pf_rows),
            "critical_impacts": pd.DataFrame(impact_rows),
        }

        # Save
        for name, df in dfs.items():
            path = output_dir / f"{name}.csv"
            df.to_csv(path, index=False)
            if verbose:
                print(f"  [generator] Saved {len(df):,} rows -> {path.name}")

        return dfs

    # ── Internal methods ───────────────────────────────────────────────────

    def _sample_environment(self, profile: StormProfile) -> Dict[str, float]:
        """Sample environmental conditions from profile distributions."""
        wind = profile.sample_wind(self.rng)
        rain = profile.sample_rain(self.rng)
        temp = float(self.rng.uniform(-5, 35))
        load_factor = float(np.clip(self.rng.normal(0.75, 0.15), 0.3, 1.0))
        severity = float(min(profile.weather_severity * (1 + 0.2 * self.rng.standard_normal()), 1.0))
        return {
            "weather_severity": severity,
            "wind_kmh": wind,
            "rain_mm": rain,
            "temperature_c": temp,
            "load_factor": load_factor,
        }

    def _sample_true_states(
        self, profile: StormProfile, env: Dict
    ) -> Tuple[Dict[int, Dict], Dict[int, float]]:
        """Compute failure probabilities and sample binary true states."""
        net = self._base_net
        true_states: Dict[int, Dict] = {}
        failure_probs: Dict[int, float] = {}

        # Sample previous fault history (Poisson, mean 1)
        prev_faults = self.rng.poisson(1.0, size=len(net.line))

        for line_idx in range(len(net.line)):
            meta = LINE_METADATA.get(line_idx, {"exposed": True, "age_factor": 1.3, "dist": 0.5})
            row = net.line.iloc[line_idx]

            # Loading = base loading × load_factor × some variance
            base_loading = float(min(
                (row.get("max_i_ka", 0.4) * env["load_factor"] * self.rng.uniform(0.3, 0.9)),
                0.98
            ))
            loading_pct = float(np.clip(base_loading, 0.0, 0.98))

            # Failure probability from profile (calibrated from real data)
            if line_idx == 2:  # T3_LINE — transformer zone, higher base prob
                prob = profile.failure_prob_transformer(loading_pct, meta["age_factor"])
            else:
                prob = profile.failure_prob_line(
                    loading_pct=loading_pct,
                    is_exposed=meta["exposed"],
                    age_factor=meta["age_factor"],
                    previous_faults=int(prev_faults[line_idx]),
                )

            # Weather severity modifier
            prob = float(min(prob * (1 + 0.5 * env["weather_severity"]), 0.98))

            # Sample true state
            true_failed = bool(self.rng.random() < prob)

            asset_id = (net.line.at[line_idx, "asset_id"]
                        if "asset_id" in net.line.columns
                        else f"LINE_{line_idx}")

            true_states[line_idx] = {
                "asset_id": asset_id,
                "true_failed": true_failed,
                "failure_probability": prob,
                "loading_pct": loading_pct,
                "is_exposed": meta["exposed"],
                "age_factor": meta["age_factor"],
                "previous_faults": int(prev_faults[line_idx]),
            }
            failure_probs[line_idx] = prob

        return true_states, failure_probs

    def _generate_observations(
        self,
        true_states: Dict[int, Dict],
        failure_probs: Dict[int, float],
        profile: StormProfile,
        env: Dict,
    ) -> Dict[int, Dict]:
        """Generate imperfect observed states (what the operator sees)."""
        noise_level = SCADA_NOISE_BY_SEVERITY.get(profile.event_type, 0.15)
        observations: Dict[int, Dict] = {}

        for line_idx, state in true_states.items():
            true_state = float(state["true_failed"])
            prob = state["failure_probability"]

            # SCADA reading: noisy sensor
            scada_base = true_state + self.rng.normal(0, noise_level)
            scada = float(np.clip(scada_base, 0, 1))

            # Technician confidence: correlates with true state but with delay/error
            tech_noise = self.rng.normal(0, noise_level * 1.5)
            tech_conf = float(np.clip(true_state + tech_noise, 0, 1))

            # Weather evidence: correlates with failure probability (not true state)
            weather_evidence = float(np.clip(
                env["weather_severity"] * (0.5 + 0.5 * prob) + self.rng.normal(0, 0.05),
                0, 1
            ))

            # Sensor health (can be degraded in severe storms)
            sensor_health = float(np.clip(
                1.0 - 0.5 * env["weather_severity"] + self.rng.normal(0, 0.05),
                0.1, 1.0
            ))

            # Communication availability
            comm_available = bool(self.rng.random() > 0.2 * env["weather_severity"])

            # Bayesian fusion (simplified) — see uncertainty/belief.py for full version
            w_scada = sensor_health * (1.0 if comm_available else 0.3)
            w_tech = 0.6
            w_weather = 0.4
            total_w = w_scada + w_tech + w_weather
            fused = (w_scada * scada + w_tech * tech_conf + w_weather * weather_evidence) / total_w
            fused = float(np.clip(fused, 0, 1))

            # Uncertain if fused probability is in [0.3, 0.7]
            is_uncertain = 0.25 <= fused <= 0.75

            observations[line_idx] = {
                "asset_id": state["asset_id"],
                "scada_reading": scada,
                "technician_confidence": tech_conf,
                "weather_evidence": weather_evidence,
                "sensor_health": sensor_health,
                "comm_available": comm_available,
                "fused_probability": fused,
                "is_uncertain": is_uncertain,
            }

        return observations

    def _run_faulted_pf(self, true_states: Dict[int, Dict]) -> Dict[str, Any]:
        """Run power flow on a copy of the network with faults applied."""
        net = copy.deepcopy(self._base_net)

        for line_idx, state in true_states.items():
            if state["true_failed"] and line_idx < len(net.line):
                net.line.at[line_idx, "in_service"] = False

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pp.runpp(net, numba=False, verbose=False)
            vm_min = float(net.res_bus["vm_pu"].min())
            vm_max = float(net.res_bus["vm_pu"].max())
            loading_max = float(net.res_line["loading_percent"].max())
            total_loss = float(net.res_line["pl_mw"].sum())
            converged = True
        except Exception:
            vm_min, vm_max, loading_max, total_loss = None, None, None, None
            converged = False

        return {
            "pf_converged": converged,
            "vm_pu_min": round(vm_min, 4) if vm_min is not None else None,
            "vm_pu_max": round(vm_max, 4) if vm_max is not None else None,
            "loading_max_pct": round(loading_max, 2) if loading_max is not None else None,
            "total_loss_mw": round(total_loss, 4) if total_loss is not None else None,
            "_net": net,   # Keep for impact calculation
        }

    def _compute_impact(
        self,
        pf_result: Dict[str, Any],
        true_states: Dict[int, Dict],
    ) -> Dict[str, Any]:
        """Compute MW loss and critical service impacts."""
        net: pp.pandapowerNet = pf_result.pop("_net")

        n_faulted_lines = sum(1 for s in true_states.values() if s["true_failed"])

        # MW unavailable: sum loads on disconnected buses
        mw_unavailable = 0.0
        buses_affected = set()

        if pf_result.get("pf_converged"):
            for idx, row in net.res_bus.iterrows():
                if np.isnan(row["vm_pu"]) or row["vm_pu"] < 0.5:
                    buses_affected.add(int(idx))
                    # Add loads at this bus
                    bus_loads = net.load[net.load["bus"] == idx]
                    mw_unavailable += float(bus_loads["p_mw"].sum())

        # Critical services
        services = {}
        total_critical_mw_lost = 0.0
        for bus_idx, name, p_mw, _, svc_id in CRITICAL_SERVICE_LOADS:
            svc_offline = bus_idx in buses_affected
            services[svc_id] = int(svc_offline)
            if svc_offline:
                total_critical_mw_lost += p_mw

        return {
            "n_faulted_lines": n_faulted_lines,
            "mw_unavailable": round(mw_unavailable, 3),
            "buses_affected": len(buses_affected),
            "hospital_offline": services.get("HOSPITAL", 0),
            "water_plant_offline": services.get("WATER_PLANT", 0),
            "telecom_offline": services.get("TELECOM_TOWER", 0),
            "emergency_offline": services.get("EMERGENCY_CENTER", 0),
            "critical_mw_lost": round(total_critical_mw_lost, 3),
            "critical_services_down": int(sum(services.values())),
        }


def run_generation(n: int = 2000, seed: int = 42) -> Dict[str, pd.DataFrame]:
    """Entry point: generate n scenarios with reproducible seed."""
    print(f"[generator] Generating {n} synthetic scenarios (seed={seed}) ...")
    from data_pipeline.preprocessor import run_preprocessing
    run_preprocessing()  # Ensure storm profiles are available

    gen = ScenarioGenerator(seed=seed)
    return gen.generate(n=n, verbose=True)


if __name__ == "__main__":
    run_generation()
