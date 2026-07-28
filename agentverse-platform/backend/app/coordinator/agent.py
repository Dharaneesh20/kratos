import asyncio
import io
import uuid
from typing import Dict, Any, Optional
import httpx
from PIL import Image, ImageDraw
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import RunModel, AgentLogModel
from app.planning.agent import run_planning_agent
from app.report.pdf_builder import generate_report_files
from app.spectator.agent import spectator_agent
from app.websocket.manager import manager


def generate_synthetic_satellite_image_tile() -> bytes:
    """
    Generates a realistic test satellite tile (512x512 with clear road patterns)
    when no custom image file is provided by the user.
    """
    img = Image.new("RGB", (512, 512), color=(40, 60, 45))
    draw = ImageDraw.Draw(img)

    # Draw agricultural fields/terrain
    draw.rectangle([10, 10, 200, 240], fill=(65, 95, 55))
    draw.rectangle([220, 10, 500, 180], fill=(50, 80, 60))
    draw.rectangle([10, 260, 240, 500], fill=(55, 85, 50))
    draw.rectangle([260, 200, 500, 500], fill=(60, 90, 55))

    # Draw clear road grid network (asphalt color)
    road_color = (130, 130, 130)
    # Main horizontal arterials
    draw.line([(0, 150), (512, 150)], fill=road_color, width=12)
    draw.line([(0, 350), (512, 350)], fill=road_color, width=12)
    # Main vertical arterials
    draw.line([(150, 0), (150, 512)], fill=road_color, width=12)
    draw.line([(350, 0), (350, 512)], fill=road_color, width=12)

    # Secondary diagonal connectors
    draw.line([(0, 0), (512, 512)], fill=road_color, width=8)
    draw.line([(150, 350), (350, 150)], fill=road_color, width=8)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def execute_workflow(workflow_id: str, db: Session, image_bytes: Optional[bytes] = None, hazard_type: str = "FLOOD", severity: float = 0.8):
    run = db.query(RunModel).filter(RunModel.id == workflow_id).first()
    if not run:
        return

    async def log_and_broadcast(agent: str, stage: str, pct: int, msg: str, results: Dict[str, Any] = None):
        run.current_stage = stage
        run.pct = pct
        db.commit()

        log_entry = AgentLogModel(workflow_id=workflow_id, agent=agent, stage=stage, message=msg)
        db.add(log_entry)
        db.commit()

        # Update Spectator Agent state & telemetry log
        spectator_agent.log_event(agent_id=agent, level="INFO", message=msg, details={"workflow_id": workflow_id, "stage": stage})
        spectator_agent.update_agent_state(agent_id=agent, current_task=f"Executing {stage}", status="BUSY" if pct < 100 else "HEALTHY")

        event = {
            "workflow_id": workflow_id,
            "agent": agent,
            "stage": stage,
            "pct": pct,
            "status": "running" if pct < 100 else "completed",
            "message": msg,
            "results": results or {},
        }
        await manager.broadcast(event)


    try:
        # Stage 1: DATASET
        run.state = "RUNNING"
        db.commit()
        await log_and_broadcast("coordinator", "DATASET", 10, "Initializing dataset and satellite tile input...")

        if not image_bytes:
            image_bytes = generate_synthetic_satellite_image_tile()

        # Stage 2: VISION
        await log_and_broadcast("vision", "VISION", 25, "Running SegFormer road extraction AI model...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": ("sat_tile.png", image_bytes, "image/png")}
            resp = await client.post(f"{settings.VISION_SERVICE_URL}/vision/process", files=files)
            if resp.status_code != 200:
                raise Exception(f"Vision service error ({resp.status_code}): {resp.text}")

            vision_data = resp.json()
            run.roads_geojson = vision_data.get("roads_geojson")
            run.road_mask_png_base64 = vision_data.get("road_mask_png_base64")
            db.commit()

        # Stage 3: GRAPH
        await log_and_broadcast("graph", "GRAPH", 45, "Constructing topological road network graph...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            graph_req = {"roads_geojson": run.roads_geojson, "snap_tolerance_m": 5.0}
            resp = await client.post(f"{settings.GRAPH_SERVICE_URL}/graph/build", json=graph_req)
            if resp.status_code != 200:
                raise Exception(f"Graph service error ({resp.status_code}): {resp.text}")

            graph_res = resp.json()
            run.graph_data = graph_res.get("graph_data")
            run.critical_nodes = graph_res.get("critical_nodes")
            db.commit()

        # Stage 4: SIMULATION
        await log_and_broadcast("simulation", "SIMULATION", 65, f"Running disaster stress simulation for {hazard_type} (severity {severity})...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            sim_req = {
                "graph_data": run.graph_data,
                "hazard_type": hazard_type,
                "severity": severity,
            }
            resp = await client.post(f"{settings.GRAPH_SERVICE_URL}/simulation/run", json=sim_req)
            if resp.status_code != 200:
                raise Exception(f"Simulation service error ({resp.status_code}): {resp.text}")

            sim_res = resp.json()
            run.simulation_data = sim_res
            db.commit()

        # Stage 5: PLANNING
        await log_and_broadcast("planning", "PLANNING", 80, "Calculating cuOpt/Dijkstra evacuation routes and repair priorities...")
        planning_res = run_planning_agent(
            graph_data=run.graph_data,
            critical_nodes=run.critical_nodes or [],
            simulation_data=run.simulation_data or {},
            hazard_type=hazard_type,
        )
        run.planning_data = planning_res.model_dump()
        db.commit()

        # Stage 6: REPORT
        await log_and_broadcast("report", "REPORT", 95, "Generating ReportLab PDF & CSV disaster intelligence report...")
        report_res = generate_report_files(workflow_id, {
            "hazard_type": hazard_type,
            "simulation_data": run.simulation_data,
            "critical_nodes": run.critical_nodes,
            "planning_data": run.planning_data,
        })
        run.report_data = report_res
        run.state = "COMPLETED"
        run.current_stage = "DONE"
        run.pct = 100
        db.commit()

        final_results = {
            "roads_geojson": run.roads_geojson,
            "road_mask_png_base64": run.road_mask_png_base64,
            "graph_data": run.graph_data,
            "critical_nodes": run.critical_nodes,
            "simulation_data": run.simulation_data,
            "planning_data": run.planning_data,
            "report_data": run.report_data,
        }
        await log_and_broadcast("coordinator", "DONE", 100, "Workflow executed successfully!", results=final_results)

    except Exception as e:
        run.state = "FAILED"
        run.error = str(e)
        db.commit()
        await manager.broadcast({
            "workflow_id": workflow_id,
            "agent": "coordinator",
            "stage": "FAILED",
            "pct": run.pct,
            "status": "failed",
            "message": f"Workflow failed: {str(e)}",
            "error": str(e),
        })
