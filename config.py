"""
GridGuard — Configuration Constants
"""
from enum import Enum
from typing import Dict


# ---------------------------------------------------------------------------
# Criticality levels
# ---------------------------------------------------------------------------
class CriticalityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


CRITICALITY_WEIGHTS: Dict[CriticalityLevel, float] = {
    CriticalityLevel.CRITICAL: 1.0,
    CriticalityLevel.HIGH: 0.75,
    CriticalityLevel.MEDIUM: 0.40,
    CriticalityLevel.LOW: 0.15,
}

# ---------------------------------------------------------------------------
# Action types
# ---------------------------------------------------------------------------
class ActionType(str, Enum):
    REPAIR = "REPAIR"
    INSPECT = "INSPECT"
    RECONFIGURE = "RECONFIGURE"
    ISLAND = "ISLAND"
    RESTORE = "RESTORE"
    DEFER = "DEFER"


# ---------------------------------------------------------------------------
# Asset / fault status
# ---------------------------------------------------------------------------
class AssetStatus(str, Enum):
    HEALTHY = "HEALTHY"
    FAILED = "FAILED"
    UNCERTAIN = "UNCERTAIN"
    DEGRADED = "DEGRADED"
    ISOLATED = "ISOLATED"
    RESTORED = "RESTORED"


# ---------------------------------------------------------------------------
# Resource types
# ---------------------------------------------------------------------------
class ResourceType(str, Enum):
    REPAIR_CREW = "REPAIR_CREW"
    INSPECTION_DRONE = "INSPECTION_DRONE"
    MOBILE_GENERATOR = "MOBILE_GENERATOR"


# ---------------------------------------------------------------------------
# Initial resource pool
# ---------------------------------------------------------------------------
INITIAL_RESOURCES: Dict[ResourceType, int] = {
    ResourceType.REPAIR_CREW: 2,
    ResourceType.INSPECTION_DRONE: 1,
    ResourceType.MOBILE_GENERATOR: 1,
}

MOBILE_GENERATOR_CAPACITY_MW = 2.5

# ---------------------------------------------------------------------------
# Electrical limits
# ---------------------------------------------------------------------------
VOLTAGE_UPPER_PU = 1.05
VOLTAGE_LOWER_PU = 0.95
LINE_LOADING_MAX_PCT = 100.0
TRANSFORMER_LOADING_MAX_PCT = 100.0

# ---------------------------------------------------------------------------
# Action time estimates (minutes)
# ---------------------------------------------------------------------------
ACTION_TIME_MINUTES: Dict[ActionType, int] = {
    ActionType.REPAIR: 90,
    ActionType.INSPECT: 18,
    ActionType.RECONFIGURE: 15,
    ActionType.ISLAND: 20,
    ActionType.RESTORE: 10,
    ActionType.DEFER: 0,
}

# ---------------------------------------------------------------------------
# Scoring weights for the decision engine
# ---------------------------------------------------------------------------
WEIGHT_CRITICAL_SERVICE_RECOVERY = 3.0
WEIGHT_LOAD_RESTORATION_MW       = 0.5
WEIGHT_RISK                      = -2.0
WEIGHT_RESOURCE_COST             = -0.3
WEIGHT_TIME                      = -0.01   # per minute
WEIGHT_UNCERTAINTY_PENALTY       = -1.5

# VOI / inspection cost (normalised resource unit)
INSPECTION_RESOURCE_COST = 0.20   # fraction of drone capacity consumed

# Uncertainty thresholds for quadrant classification
UNCERTAINTY_HIGH_THRESHOLD = 0.40
IMPACT_HIGH_THRESHOLD       = 0.50
