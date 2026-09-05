"""
GridGuard — Pydantic models for recommendations.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from config import ActionType, CriticalityLevel, ResourceType


class VOIResult(BaseModel):
    voi: float
    expected_gain: float
    inspection_cost: float
    decision_sensitivity: float
    p_failed: float
    p_healthy: float
    best_action_if_failed: str
    best_action_if_healthy: str
    best_action_without_info: str


class RecommendationModel(BaseModel):
    action_type: ActionType
    target_asset: str
    score: float
    voi: Optional[float] = None
    uncertainty: float
    criticality: CriticalityLevel
    expected_impact: str
    estimated_time_minutes: int
    required_resource: Optional[ResourceType] = None
    electrically_feasible: bool
    reason_codes: List[str] = Field(default_factory=list)
    explanation: str
    voi_detail: Optional[VOIResult] = None
    alternative_actions: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RiskModel(BaseModel):
    overall_risk: float
    uncertainty_risk: float
    critical_service_risk: float
    resource_risk: float
    cascade_risk: float
    risk_factors: List[str] = Field(default_factory=list)
    risk_level: str   # LOW / MEDIUM / HIGH / CRITICAL


class ImpactModel(BaseModel):
    total_load_mw: float
    lost_load_mw: float
    restoration_pct: float
    affected_critical_services: List[str]
    critical_services_down: int
    critical_services_total: int
    downstream_affected_nodes: int
    criticality_weighted_impact: float
