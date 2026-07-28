from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.chatbot.agent import chatbot_agent
from app.db.models import RunModel
from app.db.session import get_db

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


class ChatRequest(BaseModel):
    workflow_id: Optional[str] = None
    message: str = "Explain why this evacuation route was chosen and which bridge repair is most critical."


class ChatResponse(BaseModel):
    status: str = "success"
    agent: str = "chatbot"
    response: str


@router.post("/chat", response_model=ChatResponse)
def chat_with_nvidia_nim(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Invokes NVIDIA NeMoTron LLM Chatbot Controller Agent to explain disaster routes,
    critical node rankings, and tactical repair priorities.
    """
    run_data = {}
    if req.workflow_id:
        run = db.query(RunModel).filter(RunModel.id == req.workflow_id).first()
        if run:
            run_data = {
                "workflow_id": run.id,
                "hazard_type": run.hazard_type,
                "severity": run.severity,
                "simulation_data": run.simulation_data,
                "critical_nodes": run.critical_nodes,
                "planning_data": run.planning_data,
            }

    explanation = chatbot_agent.explain_disaster_scenario(run_data, req.message)
    return ChatResponse(
        status="success",
        agent="chatbot",
        response=explanation,
    )
