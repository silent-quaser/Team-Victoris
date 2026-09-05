"""
Tests for the scenario generator.
"""
import pytest
from pathlib import Path
import tempfile
import pandas as pd
import numpy as np
from scenario.generator import ScenarioGenerator, SCENARIO_TYPE_WEIGHTS
from scenario.profiles import get_profile, list_profiles, StormProfile, reset_registry


def test_scenario_generator_creates_instance():
    gen = ScenarioGenerator(seed=42)
    assert gen is not None


def test_scenario_generator_deterministic():
    """Same seed produces identical scenarios."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        gen1 = ScenarioGenerator(seed=123)
        gen2 = ScenarioGenerator(seed=123)
        dfs1 = gen1.generate(n=10, output_dir=tmp / "r1", verbose=False)
        dfs2 = gen2.generate(n=10, output_dir=tmp / "r2", verbose=False)
        pd.testing.assert_frame_equal(
            dfs1["scenarios"].reset_index(drop=True),
            dfs2["scenarios"].reset_index(drop=True),
        )


def test_scenario_generator_different_seeds():
    """Different seeds produce different scenarios."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        gen1 = ScenarioGenerator(seed=1)
        gen2 = ScenarioGenerator(seed=2)
        dfs1 = gen1.generate(n=20, output_dir=tmp / "r1", verbose=False)
        dfs2 = gen2.generate(n=20, output_dir=tmp / "r2", verbose=False)
        # Should NOT be identical
        assert not dfs1["scenarios"]["weather_severity"].equals(
            dfs2["scenarios"]["weather_severity"]
        )


def test_scenario_generates_correct_count():
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = ScenarioGenerator(seed=42)
        dfs = gen.generate(n=50, output_dir=Path(tmpdir), verbose=False)
        assert len(dfs["scenarios"]) == 50


def test_component_states_has_all_lines():
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = ScenarioGenerator(seed=42)
        dfs = gen.generate(n=5, output_dir=Path(tmpdir), verbose=False)
        comp = dfs["component_states"]
        # Each scenario should have entries for all 37 lines
        n_per_scenario = comp.groupby("scenario_id").size()
        assert (n_per_scenario == 37).all()


def test_observations_match_component_states():
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = ScenarioGenerator(seed=42)
        dfs = gen.generate(n=5, output_dir=Path(tmpdir), verbose=False)
        assert len(dfs["observations"]) == len(dfs["component_states"])


def test_failure_probability_in_bounds():
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = ScenarioGenerator(seed=42)
        dfs = gen.generate(n=20, output_dir=Path(tmpdir), verbose=False)
        comp = dfs["component_states"]
        assert (comp["failure_probability"] >= 0.0).all()
        assert (comp["failure_probability"] <= 1.0).all()


def test_true_failed_is_binary():
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = ScenarioGenerator(seed=42)
        dfs = gen.generate(n=20, output_dir=Path(tmpdir), verbose=False)
        comp = dfs["component_states"]
        assert comp["true_failed"].isin([0, 1]).all()


def test_fused_probability_in_bounds():
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = ScenarioGenerator(seed=42)
        dfs = gen.generate(n=20, output_dir=Path(tmpdir), verbose=False)
        obs = dfs["observations"]
        assert (obs["fused_probability"] >= 0.0).all()
        assert (obs["fused_probability"] <= 1.0).all()


def test_severe_storm_higher_failure_rate():
    """SEVERE_STORM scenarios should have more failures than NORMAL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        gen = ScenarioGenerator(seed=42)
        dfs = gen.generate(n=200, output_dir=tmp, verbose=False)
        comp = dfs["component_states"]
        scen = dfs["scenarios"]
        merged = comp.merge(scen[["scenario_id", "event_type"]], on="scenario_id")
        storm_rate = merged[merged["event_type"] == "SEVERE_STORM"]["true_failed"].mean()
        normal_rate = merged[merged["event_type"] == "NORMAL"]["true_failed"].mean()
        assert storm_rate > normal_rate, f"Storm rate {storm_rate:.3f} should exceed normal {normal_rate:.3f}"


def test_critical_impacts_columns():
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = ScenarioGenerator(seed=42)
        dfs = gen.generate(n=5, output_dir=Path(tmpdir), verbose=False)
        impact = dfs["critical_impacts"]
        assert "mw_unavailable" in impact.columns
        assert "hospital_offline" in impact.columns
        assert "water_plant_offline" in impact.columns
        assert "critical_services_down" in impact.columns
        assert "n_faulted_lines" in impact.columns


def test_powerflow_results_columns():
    with tempfile.TemporaryDirectory() as tmpdir:
        gen = ScenarioGenerator(seed=42)
        dfs = gen.generate(n=5, output_dir=Path(tmpdir), verbose=False)
        pf = dfs["powerflow_results"]
        assert "pf_converged" in pf.columns
        assert "scenario_id" in pf.columns


# ── Storm profiles ────────────────────────────────────────────────────────────

def test_list_profiles_returns_all_types():
    reset_registry()
    profiles = list_profiles()
    assert "SEVERE_STORM" in profiles
    assert "NORMAL" in profiles
    assert "HURRICANE" in profiles


def test_get_profile_severe_storm():
    profile = get_profile("SEVERE_STORM")
    assert isinstance(profile, StormProfile)
    assert profile.line_failure_prob_base > 0
    assert profile.weather_severity > 0.5


def test_severe_storm_higher_prob_than_normal():
    storm = get_profile("SEVERE_STORM")
    normal = get_profile("NORMAL")
    assert storm.line_failure_prob_base > normal.line_failure_prob_base
    assert storm.weather_severity > normal.weather_severity


def test_failure_prob_increases_with_loading():
    profile = get_profile("SEVERE_STORM")
    prob_low = profile.failure_prob_line(loading_pct=0.2)
    prob_high = profile.failure_prob_line(loading_pct=0.9)
    assert prob_high > prob_low


def test_exposed_higher_failure_prob():
    profile = get_profile("SEVERE_STORM")
    prob_exposed = profile.failure_prob_line(loading_pct=0.5, is_exposed=True)
    prob_sheltered = profile.failure_prob_line(loading_pct=0.5, is_exposed=False)
    assert prob_exposed > prob_sheltered


def test_hurricane_profile_highest_severity():
    hurricane = get_profile("HURRICANE")
    normal = get_profile("NORMAL")
    assert hurricane.weather_severity > normal.weather_severity
    assert hurricane.line_failure_prob_base > normal.line_failure_prob_base
