import os
from fastapi import APIRouter, HTTPException
from shared.schemas import SimulationRunRequest, SimulationRunResponse
from app.services.simulation import run_disaster_simulation

router = APIRouter(tags=["Simulation"])


@router.post("/simulation/run", response_model=SimulationRunResponse)
def run_simulation(req: SimulationRunRequest):
    """
    Simulates disaster effects on the road network (FLOOD, EARTHQUAKE, BRIDGE_FAILURE, ROAD_CLOSURE).
    Accepts graph_data dict or graph_json_path file.
    """
    if not req.graph_data and not req.graph_json_path:
        raise HTTPException(status_code=400, detail="Either graph_data dict or graph_json_path must be provided")

    if req.graph_json_path and not os.path.exists(req.graph_json_path) and not req.graph_data:
        raise HTTPException(status_code=404, detail=f"Graph JSON file not found at path: {req.graph_json_path}")

    sim_json_path = None
    if req.graph_json_path:
        cache_dir = os.path.dirname(req.graph_json_path)
        sim_json_path = os.path.join(cache_dir, "simulation.json")

    result = run_disaster_simulation(
        graph_data=req.graph_data,
        graph_json_path=req.graph_json_path,
        hazard_type=req.hazard_type,
        affected_node_ids=req.affected_node_ids,
        affected_edge_ids=req.affected_edge_ids,
        severity=req.severity,
        output_simulation_path=sim_json_path,
    )

    return SimulationRunResponse(**result)
