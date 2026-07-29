import sys
from pathlib import Path

# Add project root to sys.path so `shared` can be imported
root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.schemas import HealthResponse
from app.config import settings
from app.routers import graph, simulation

app = FastAPI(
    title="graph-service",
    description="Route Resilience AI - Graph Intelligence & Disaster Simulation Service",
    version="0.1.0",
)

# Mount routers
app.include_router(graph.router)
app.include_router(simulation.router)


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(service=settings.SERVICE_NAME)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "agent": "graph",
            "message": str(exc),
            "code": "GRAPH_001",
        },
    )
