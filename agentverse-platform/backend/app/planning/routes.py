from fastapi import APIRouter, HTTPException
from shared.schemas import PlanningRequest, PlanningResponse
from app.planning.agent import run_planning_agent

router = APIRouter(prefix="/planning", tags=["Planning Agent"])


@router.post("/generate", response_model=PlanningResponse)
def generate_plan(req: PlanningRequest):
    """
    Planning Agent endpoint: uses NVIDIA cuOpt / NetworkX for routing,
    computes repair priority rankings, and invokes NVIDIA NIM for reasoning.
    """
    if not req.graph_data:
        raise HTTPException(status_code=400, detail="graph_data is required for planning")

    safe_zones = [sz.model_dump() for sz in req.safe_zones] if req.safe_zones else []

    res = run_planning_agent(
        graph_data=req.graph_data,
        critical_nodes=req.critical_nodes,
        simulation_data=req.simulation_data,
        hazard_type=req.hazard_type,
        safe_zones=safe_zones,
    )

    return res
