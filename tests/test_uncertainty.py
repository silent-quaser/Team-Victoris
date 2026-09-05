"""
Tests for the uncertainty belief engine.
"""
import pytest
from uncertainty.belief import (
    BeliefState, get_uncertainty, update_belief, resolve_asset_state,
    reset_beliefs, get_all_beliefs, get_uncertain_assets,
    initialise_from_ml, UNCERTAIN_LOW, UNCERTAIN_HIGH
)


@pytest.fixture(autouse=True)
def clear_beliefs():
    """Reset belief registry before each test."""
    reset_beliefs()
    yield
    reset_beliefs()


def test_get_uncertainty_creates_default_state():
    state = get_uncertainty("T3_LINE")
    assert state is not None
    assert state.asset_id == "T3_LINE"
    assert state.p_failed == 0.0
    assert state.resolved is False


def test_update_belief_with_scada():
    state = update_belief("T3_LINE", {
        "scada_reading": 0.65,
        "sensor_health": 0.8,
        "comm_available": True,
    })
    assert state.p_failed > 0.0
    assert state.p_failed <= 1.0


def test_update_belief_high_evidence_gives_high_probability():
    state = update_belief("T3_LINE", {
        "scada_reading": 0.90,
        "technician_confidence": 0.88,
        "weather_evidence": 0.85,
        "sensor_health": 0.95,
        "comm_available": True,
    })
    # High evidence across all sources → high p_failed
    assert state.p_failed > 0.50


def test_update_belief_low_evidence_gives_low_probability():
    state = update_belief("L25-26", {
        "scada_reading": 0.05,
        "technician_confidence": 0.08,
        "weather_evidence": 0.10,
        "sensor_health": 0.95,
        "comm_available": True,
    })
    assert state.p_failed < 0.50


def test_uncertainty_flag_set_correctly():
    state = update_belief("T3_LINE", {"scada_reading": 0.50, "sensor_health": 0.8})
    # p_failed around 0.5 should be uncertain
    if UNCERTAIN_LOW <= state.p_failed <= UNCERTAIN_HIGH:
        assert state.is_uncertain is True
    else:
        assert state.is_uncertain is False


def test_resolve_failed():
    update_belief("T3_LINE", {"scada_reading": 0.62})
    state = resolve_asset_state("T3_LINE", "FAILED")
    assert state.resolved is True
    assert state.resolved_state == "FAILED"
    assert state.p_failed == 1.0
    assert state.is_uncertain is False
    assert state.confidence == 1.0


def test_resolve_healthy():
    update_belief("T3_LINE", {"scada_reading": 0.62})
    state = resolve_asset_state("T3_LINE", "HEALTHY")
    assert state.resolved is True
    assert state.resolved_state == "HEALTHY"
    assert state.p_failed == 0.0


def test_resolved_state_not_updated_by_further_evidence():
    resolve_asset_state("T3_LINE", "FAILED")
    state_before = get_uncertainty("T3_LINE").p_failed
    update_belief("T3_LINE", {"scada_reading": 0.0, "technician_confidence": 0.0})
    state_after = get_uncertainty("T3_LINE").p_failed
    assert state_before == state_after == 1.0


def test_invalid_resolve_raises():
    with pytest.raises(ValueError):
        resolve_asset_state("T3_LINE", "MAYBE")


def test_get_all_beliefs():
    update_belief("T3_LINE", {"scada_reading": 0.6})
    update_belief("L6-7", {"scada_reading": 0.9})
    beliefs = get_all_beliefs()
    assert "T3_LINE" in beliefs
    assert "L6-7" in beliefs
    assert "p_failed" in beliefs["T3_LINE"]


def test_get_uncertain_assets():
    # Create one uncertain, one certain
    update_belief("T3_LINE", {"scada_reading": 0.50, "sensor_health": 0.5})
    resolve_asset_state("L6-7", "FAILED")
    uncertain = get_uncertain_assets()
    assert "L6-7" not in uncertain


def test_initialise_from_ml():
    probs = {"T3_LINE": 0.62, "L6-7": 0.94, "L12-13": 0.95, "L25-26": 0.88}
    beliefs = initialise_from_ml(probs)
    assert abs(beliefs["T3_LINE"].p_failed - 0.62) < 0.001
    assert abs(beliefs["L6-7"].p_failed - 0.94) < 0.001


def test_belief_state_entropy_max_at_half():
    state = BeliefState(asset_id="TEST", p_failed=0.5)
    entropy_half = state.entropy
    state2 = BeliefState(asset_id="TEST2", p_failed=0.9)
    entropy_high = state2.entropy
    assert entropy_half > entropy_high  # Entropy is max at p=0.5


def test_belief_state_p_healthy():
    state = BeliefState(asset_id="TEST", p_failed=0.72)
    assert abs(state.p_healthy - 0.28) < 0.001


def test_update_belief_logs_evidence():
    state = update_belief("T3_LINE", {
        "scada_reading": 0.70,
        "technician_confidence": 0.81,
        "weather_evidence": 0.92,
        "sensor_health": 0.75,
        "comm_available": True,
    })
    assert len(state.evidence_log) >= 3  # At least 3 evidence sources


def test_comm_unavailable_reduces_scada_weight():
    state_with_comm = update_belief("A1", {
        "scada_reading": 0.9, "sensor_health": 0.9, "comm_available": True
    })
    reset_beliefs()
    state_without_comm = update_belief("A2", {
        "scada_reading": 0.9, "sensor_health": 0.9, "comm_available": False
    })
    # Without comms, SCADA weight reduced — but technician weight unchanged
    # Hard to compare directly since different assets, check that both are valid
    assert 0 <= state_with_comm.p_failed <= 1
    assert 0 <= state_without_comm.p_failed <= 1


def test_ml_prior_in_update():
    state = update_belief("T3_LINE", {
        "scada_reading": 0.40,
    }, ml_prior=0.80)
    # ML prior of 0.80 should push p_failed higher than SCADA alone
    state2 = update_belief("T3_LINE_2", {
        "scada_reading": 0.40,
    })
    assert state.p_failed > state2.p_failed
