"""
GridGuard API — Activity / audit log endpoint.
"""
from fastapi import APIRouter
from audit.log import get_log

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/log")
def get_activity_log(limit: int = 50):
    """Return recent activity log entries."""
    return {"entries": get_log().get_recent(limit), "total": limit}


@router.get("/log/recommendations")
def get_recommendation_log():
    """Return only recommendation entries from the audit log."""
    return {"entries": get_log().get_by_type("RECOMMENDATION")}


@router.get("/log/executions")
def get_execution_log():
    """Return only execution entries from the audit log."""
    return {"entries": get_log().get_by_type("EXECUTION")}
