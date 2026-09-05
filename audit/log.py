"""
GridGuard — Activity / Decision Audit Log

Persists every recommendation and state transition so the frontend
can show transparent decision reasoning.
"""
from __future__ import annotations
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional
import json


class ActivityEntry:
    def __init__(
        self,
        entry_type: str,            # "RECOMMENDATION" | "EXECUTION" | "INSPECTION" | "FAULT"
        timestamp: datetime,
        step: int,
        description: str,
        state_snapshot: Dict[str, Any],
        candidates: Optional[List[Dict]] = None,
        selected_action: Optional[Dict] = None,
        scores: Optional[Dict] = None,
        feasibility_result: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ):
        self.entry_type         = entry_type
        self.timestamp          = timestamp
        self.step               = step
        self.description        = description
        self.state_snapshot     = state_snapshot
        self.candidates         = candidates or []
        self.selected_action    = selected_action or {}
        self.scores             = scores or {}
        self.feasibility_result = feasibility_result or {}
        self.metadata           = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_type":       self.entry_type,
            "timestamp":        self.timestamp.isoformat(),
            "step":             self.step,
            "description":      self.description,
            "state_snapshot":   self.state_snapshot,
            "candidates":       self.candidates,
            "selected_action":  self.selected_action,
            "scores":           self.scores,
            "feasibility_result": self.feasibility_result,
            "metadata":         self.metadata,
        }


class ActivityLog:
    """In-memory audit log with a configurable maximum size."""

    def __init__(self, maxlen: int = 500):
        self._entries: deque[ActivityEntry] = deque(maxlen=maxlen)

    def append(self, entry: ActivityEntry) -> None:
        self._entries.append(entry)

    def log_recommendation(
        self,
        step: int,
        state_summary: Dict[str, Any],
        candidates: List[Dict],
        selected: Dict,
        scores: Dict,
        feasibility: Dict,
    ) -> None:
        self.append(ActivityEntry(
            entry_type="RECOMMENDATION",
            timestamp=datetime.utcnow(),
            step=step,
            description=f"Recommendation: {selected.get('action_type')} on {selected.get('target_asset')}",
            state_snapshot=state_summary,
            candidates=candidates,
            selected_action=selected,
            scores=scores,
            feasibility_result=feasibility,
        ))

    def log_execution(
        self,
        step: int,
        action: Dict,
        result: Dict,
        state_summary: Dict[str, Any],
    ) -> None:
        self.append(ActivityEntry(
            entry_type="EXECUTION",
            timestamp=datetime.utcnow(),
            step=step,
            description=f"Executed: {action.get('action_type')} on {action.get('target_asset')}",
            state_snapshot=state_summary,
            selected_action=action,
            metadata={"result": result},
        ))

    def log_inspection(
        self,
        step: int,
        asset_id: str,
        result: str,
        state_summary: Dict[str, Any],
    ) -> None:
        self.append(ActivityEntry(
            entry_type="INSPECTION",
            timestamp=datetime.utcnow(),
            step=step,
            description=f"Inspection result: {asset_id} = {result}",
            state_snapshot=state_summary,
            metadata={"asset_id": asset_id, "result": result},
        ))

    def log_fault(
        self,
        step: int,
        fault: Dict,
        state_summary: Dict[str, Any],
    ) -> None:
        self.append(ActivityEntry(
            entry_type="FAULT",
            timestamp=datetime.utcnow(),
            step=step,
            description=f"Fault injected: {fault.get('asset_id')} ({fault.get('fault_type')})",
            state_snapshot=state_summary,
            metadata={"fault": fault},
        ))

    def get_all(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._entries]

    def get_by_type(self, entry_type: str) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._entries if e.entry_type == entry_type]

    def get_recent(self, n: int = 20) -> List[Dict[str, Any]]:
        entries = list(self._entries)
        return [e.to_dict() for e in entries[-n:]]

    def clear(self) -> None:
        self._entries.clear()


# Singleton log
_LOG = ActivityLog()


def get_log() -> ActivityLog:
    return _LOG


def reset_log() -> None:
    _LOG.clear()
