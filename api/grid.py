"""
GridGuard API — Grid state, assets, and faults endpoints.
"""
from __future__ import annotations
from typing import List

from fastapi import APIRouter, HTTPException

from engine.state_manager import get_state
from engine.feasibility import get_network_status

router = APIRouter(prefix="/grid", tags=["Grid"])


@router.get("/state")
def grid_state():
    """Full grid state including all assets, faults, and resources."""
    state = get_state()
    return state.model_dump()


@router.get("/network")
def network_status():
    """Run pandapower AC power flow and return electrical metrics."""
    state = get_state()
    return get_network_status(state)
