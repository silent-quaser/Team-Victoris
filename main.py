"""
GridGuard — FastAPI Application Entry Point

Initialises:
    - Demo storm scenario state
    - All API routers
    - CORS (open for local dev)
    - OpenAPI metadata

Run:
    uvicorn main:app --reload --port 8000
"""
from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from engine.state_manager import init_state, _update_restoration_progress
from engine.dependency import reset_graph
from scenario.demo import build_demo_scenario
from audit.log import reset_log

from api.grid         import router as grid_router
from api.assets       import router as assets_router
from api.scenario     import router as scenario_router
from api.actions      import router as actions_router
from api.recommendation import router as rec_router
from api.resources    import router as resources_router
from api.dependencies import router as deps_router
from api.audit        import router as audit_router
from api.grid_ml      import router as grid_ml_router


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise demo scenario and IEEE 33-bus simulation on startup."""
    reset_graph()
    state = build_demo_scenario()
    init_state(state)
    reset_log()
    _update_restoration_progress(state)
    print(f"[GridGuard] Demo scenario loaded: {state.scenario_name}")
    print(f"[GridGuard] Active faults: {len(state.get_active_faults())}")
    # Initialise IEEE 33-bus simulation
    try:
        from grid.grid_engine import create_grid
        create_grid()
        print("[GridGuard] IEEE 33-bus simulation ready.")
    except Exception as e:
        print(f"[GridGuard] Warning: IEEE 33-bus init failed: {e}")
    yield
    print("[GridGuard] Shutting down.")


# ---------------------------------------------------------------------------
# App definition
# ---------------------------------------------------------------------------

app = FastAPI(
    title="GridGuard API",
    description=(
        "Impact-Aware Grid Recovery Under Uncertainty. "
        "Decision engine with VOI, criticality analysis, and pandapower feasibility."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(grid_router)
app.include_router(assets_router)
app.include_router(scenario_router)
app.include_router(actions_router)
app.include_router(rec_router)
app.include_router(resources_router)
app.include_router(deps_router)
app.include_router(audit_router)
app.include_router(grid_ml_router)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
def health():
    """Health check."""
    from engine.state_manager import get_state
    state = get_state()
    return {
        "status": "ok",
        "scenario": state.scenario_name,
        "step": state.step,
        "restoration_pct": state.restoration_pct,
    }
