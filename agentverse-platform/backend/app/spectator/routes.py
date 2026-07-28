from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.spectator.agent import spectator_agent
from shared.schemas import AgentInfo, SpectatorMetrics, AgentLogEntry

router = APIRouter(prefix="/spectator", tags=["Spectator Agent"])


class TelemetryPayload(BaseModel):
    agent_id: str
    level: str = "INFO"
    message: str
    current_task: Optional[str] = None
    status: Optional[str] = None
    execution_time_ms: Optional[float] = 0.0
    confidence_score: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


@router.get("/health")
def get_spectator_health():
    """Returns general Spectator Agent sentinel status."""
    metrics = spectator_agent.get_metrics()
    return {
        "status": "active",
        "agent": "spectator",
        "overall_health": metrics.overall_health,
        "active_agents": metrics.active_agents,
        "uptime_seconds": metrics.uptime_seconds,
    }


@router.get("/agents", response_model=List[AgentInfo])
def list_agents():
    """Returns detailed status, purpose, and health ping for every agent in KRATOS."""
    return spectator_agent.get_agent_list()


@router.get("/metrics", response_model=SpectatorMetrics)
def get_metrics():
    """Returns real-time telemetry metrics (NVIDIA NIM latency, cuOpt response time, AI confidence)."""
    return spectator_agent.get_metrics()


@router.get("/logs", response_model=List[AgentLogEntry])
def get_logs(agent: Optional[str] = Query(None), limit: int = Query(100, le=500)):
    """Returns unified real-time logs collected across all agents directly from SQLite DB and live memory."""
    return spectator_agent.get_logs_from_db(agent, limit)


@router.post("/telemetry")
def record_telemetry(payload: TelemetryPayload):
    """Allows agents to report telemetry, heartbeats, and logs to Spectator Agent."""
    if payload.current_task or payload.status:
        spectator_agent.update_agent_state(
            agent_id=payload.agent_id,
            current_task=payload.current_task or "Processing",
            status=payload.status or "BUSY",
            execution_time_ms=payload.execution_time_ms or 0.0,
            confidence=payload.confidence_score,
        )

    log_entry = spectator_agent.log_event(
        agent_id=payload.agent_id,
        level=payload.level,
        message=payload.message,
        details=payload.details,
    )
    return {"status": "recorded", "log": log_entry}
