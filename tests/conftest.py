# conftest.py — shared pytest fixtures for GridGuard tests
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from engine.dependency import reset_graph
from engine.state_manager import init_state, _update_restoration_progress
from scenario.demo import build_demo_scenario
from audit.log import reset_log


@pytest.fixture(autouse=True)
def fresh_state():
    """Reset to demo scenario before every test."""
    reset_graph()
    state = build_demo_scenario()
    init_state(state)
    _update_restoration_progress(state)
    reset_log()
    yield
    reset_graph()
