"""
GridGuard — Pydantic models for grid state, assets, faults.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from config import AssetStatus, CriticalityLevel, ResourceType


class AssetModel(BaseModel):
    asset_id: str
    asset_type: str          # FEEDER, TRANSFORMER, LINE, BUS, SERVICE
    name: str
    status: AssetStatus
    failure_probability: float = 0.0   # 0 = certain healthy, 1 = certain failed
    load_mw: float = 0.0
    voltage_pu: Optional[float] = None
    criticality: Optional[CriticalityLevel] = None
    is_critical_service: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FaultModel(BaseModel):
    fault_id: str
    asset_id: str
    fault_type: str          # OPEN_CIRCUIT, SHORT_CIRCUIT, UNCERTAIN
    failure_probability: float
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class ResourceModel(BaseModel):
    resource_type: ResourceType
    total: int
    available: int
    in_use: int = 0


class GridStateModel(BaseModel):
    scenario_id: str
    scenario_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    assets: Dict[str, AssetModel] = Field(default_factory=dict)
    faults: Dict[str, FaultModel] = Field(default_factory=dict)
    resources: Dict[ResourceType, ResourceModel] = Field(default_factory=dict)
    topology_changes: List[str] = Field(default_factory=list)
    step: int = 0
    total_load_mw: float = 0.0
    restored_load_mw: float = 0.0
    restoration_pct: float = 0.0

    def get_active_faults(self) -> List[FaultModel]:
        return [f for f in self.faults.values() if not f.resolved]

    def get_uncertain_faults(self) -> List[FaultModel]:
        return [
            f for f in self.faults.values()
            if not f.resolved and f.fault_type == "UNCERTAIN"
        ]

    def resource_available(self, rtype: ResourceType, amount: int = 1) -> bool:
        r = self.resources.get(rtype)
        return r is not None and r.available >= amount

    def consume_resource(self, rtype: ResourceType, amount: int = 1) -> None:
        r = self.resources[rtype]
        r.available -= amount
        r.in_use += amount

    def release_resource(self, rtype: ResourceType, amount: int = 1) -> None:
        r = self.resources[rtype]
        r.available = min(r.total, r.available + amount)
        r.in_use = max(0, r.in_use - amount)
