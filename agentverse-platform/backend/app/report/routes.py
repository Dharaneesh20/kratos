from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.report.agent import report_agent
from shared.schemas import ReportMetadata

router = APIRouter(prefix="/report", tags=["Report Agent"])


class GenerateReportRequest(BaseModel):
    workflow_id: Optional[str] = None
    hazard_type: str = "FLOOD"
    run_data: Optional[Dict[str, Any]] = None


@router.get("/list", response_model=List[ReportMetadata])
def list_reports():
    """Lists all generated disaster reports stored on the report server."""
    return report_agent.list_reports()


@router.get("/latest", response_model=Optional[ReportMetadata])
def get_latest_report():
    """Gets the most recently generated report metadata."""
    reports = report_agent.list_reports()
    if not reports:
        return None
    return reports[0]


@router.post("/generate")
def generate_report(req: GenerateReportRequest):
    """Triggers generation of a disaster report PDF and CSV via Report Agent."""
    run_data = req.run_data or {}
    if req.workflow_id:
        run_data["workflow_id"] = req.workflow_id
    run_data["hazard_type"] = req.hazard_type

    res = report_agent.generate_periodic_report(run_data)
    return {
        "status": "success",
        "agent": "report",
        "message": "Disaster intelligence report generated successfully.",
        "report": res,
    }
