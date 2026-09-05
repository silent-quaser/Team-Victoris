"""
GridGuard — Pydantic models for candidate actions.
"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field

from config import ActionType, ResourceType, CriticalityLevel


class ActionModel(BaseModel):
    action_id: str
    action_type: ActionType
    target_asset: str
    description: str

    # Benefit / risk
    expected_benefit_mw: float = 0.0           # expected load restoration
    expected_critical_service_score: float = 0.0
    risk_score: float = 0.0                    # 0-1
    reversibility: float = 1.0                 # 0=irreversible, 1=fully reversible

    # Resources
    required_resources: List[ResourceType] = Field(default_factory=list)
    estimated_time_minutes: int = 0

    # Uncertainty
    uncertainty_dependence: float = 0.0        # how much outcome changes with uncertainty
    failure_probability: float = 0.0           # current fault probability

    # Feasibility
    electrically_feasible: Optional[bool] = None
    feasibility_reason: Optional[str] = None

    # Score (set by optimizer)
    composite_score: float = 0.0

    # Reason codes
    reason_codes: List[str] = Field(default_factory=list)
