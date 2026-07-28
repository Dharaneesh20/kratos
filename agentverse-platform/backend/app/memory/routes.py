from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.models import RunModel
from app.db.session import get_db

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("/runs")
def list_past_runs(db: Session = Depends(get_db)):
    runs = db.query(RunModel).order_by(RunModel.created_at.desc()).all()
    return [
        {
            "workflow_id": r.id,
            "state": r.state,
            "current_stage": r.current_stage,
            "hazard_type": r.hazard_type,
            "severity": r.severity,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "resilience": r.simulation_data.get("resilience") if r.simulation_data else None,
            "nodes_count": len(r.critical_nodes) if r.critical_nodes else 0,
        }
        for r in runs
    ]


@router.get("/runs/{workflow_id}")
def get_past_run_detail(workflow_id: str, db: Session = Depends(get_db)):
    run = db.query(RunModel).filter(RunModel.id == workflow_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "workflow_id": run.id,
        "state": run.state,
        "hazard_type": run.hazard_type,
        "severity": run.severity,
        "results": {
            "roads_geojson": run.roads_geojson,
            "road_mask_png_base64": run.road_mask_png_base64,
            "graph_data": run.graph_data,
            "critical_nodes": run.critical_nodes,
            "simulation_data": run.simulation_data,
            "planning_data": run.planning_data,
            "report_data": run.report_data,
        },
    }
