import sys
from pathlib import Path

# Add project root to sys.path so `shared` can be imported
root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from fastapi import FastAPI, HTTPException
from shared.schemas import (
    GraphBuildRequest,
    GraphBuildResponse,
    HealthResponse,
    SimulationRunRequest,
    SimulationRunResponse,
)
from app.centrality import compute_critical_nodes
from app.graph_builder import build_graph_from_geojson
from app.simulation import run_disaster_simulation

app = FastAPI(title="graph-service", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(service="graph-service")


@app.post("/graph/build", response_model=GraphBuildResponse)
def build_graph(req: GraphBuildRequest):
    """
    Consumes roads_geojson LineStrings from vision-service, builds NetworkX road graph,
    snaps coordinates, detects bridges, and computes centrality/critical nodes.
    """
    if not req.roads_geojson or "features" not in req.roads_geojson:
        raise HTTPException(status_code=400, detail="Invalid GeoJSON object provided")

    G, graph_data = build_graph_from_geojson(req.roads_geojson, snap_tolerance_m=req.snap_tolerance_m)
    critical_nodes = compute_critical_nodes(G)

    return GraphBuildResponse(
        nodes=G.number_of_nodes(),
        edges=G.number_of_edges(),
        graph_data=graph_data,
        critical_nodes=critical_nodes,
    )


@app.post("/simulation/run", response_model=SimulationRunResponse)
def run_simulation(req: SimulationRunRequest):
    """
    Simulates disaster effects on the road network (FLOOD, EARTHQUAKE, BRIDGE_FAILURE, ROAD_CLOSURE).
    """
    if not req.graph_data:
        raise HTTPException(status_code=400, detail="graph_data is required for simulation")

    result = run_disaster_simulation(
        graph_data=req.graph_data,
        hazard_type=req.hazard_type,
        affected_node_ids=req.affected_node_ids,
        affected_edge_ids=req.affected_edge_ids,
        severity=req.severity,
    )

    return SimulationRunResponse(**result)
