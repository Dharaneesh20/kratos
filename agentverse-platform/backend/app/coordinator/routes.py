import uuid
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.coordinator.agent import execute_workflow
from app.db.models import AgentLogModel, RunModel
from app.db.session import get_db

router = APIRouter(prefix="/workflow", tags=["Workflow"])


@router.post("/run")
async def run_workflow(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    hazard_type: str = Form("FLOOD"),
    severity: float = Form(0.8),
    db: Session = Depends(get_db),
):
    workflow_id = f"wf_{uuid.uuid4().hex[:8]}"

    image_bytes = None
    if file:
        image_bytes = await file.read()

    run = RunModel(
        id=workflow_id,
        state="PENDING",
        current_stage="INIT",
        pct=0,
        hazard_type=hazard_type,
        severity=severity,
    )
    db.add(run)
    db.commit()

    background_tasks.add_task(
        execute_workflow,
        workflow_id=workflow_id,
        db=db,
        image_bytes=image_bytes,
        hazard_type=hazard_type,
        severity=severity,
    )

    return {
        "status": "success",
        "agent": "coordinator",
        "workflow_id": workflow_id,
        "poll": f"/workflow/{workflow_id}",
    }


@router.get("/{workflow_id}")
def get_workflow_status(workflow_id: str, db: Session = Depends(get_db)):
    run = db.query(RunModel).filter(RunModel.id == workflow_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")

    logs = db.query(AgentLogModel).filter(AgentLogModel.workflow_id == workflow_id).order_by(AgentLogModel.id.asc()).all()

    return {
        "workflow_id": run.id,
        "state": run.state,
        "current_stage": run.current_stage,
        "pct": run.pct,
        "hazard_type": run.hazard_type,
        "severity": run.severity,
        "error": run.error,
        "results": {
            "roads_geojson": run.roads_geojson,
            "road_mask_png_base64": run.road_mask_png_base64,
            "graph_data": run.graph_data,
            "critical_nodes": run.critical_nodes,
            "simulation_data": run.simulation_data,
            "planning_data": run.planning_data,
            "report_data": run.report_data,
        },
        "logs": [{"agent": l.agent, "stage": l.stage, "message": l.message, "time": l.created_at.isoformat()} for l in logs],
    }
