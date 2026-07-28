import os
import sys
from pathlib import Path

# Add project root to sys.path so `shared` can be imported
root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth.routes import router as auth_router
from app.config import settings
from app.coordinator.routes import router as coordinator_router
from app.db.session import init_db
from app.memory.routes import router as memory_router
from app.websocket.manager import manager
from shared.schemas import HealthResponse

init_db()

app = FastAPI(title="agentverse-backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(coordinator_router)
app.include_router(memory_router)
app.include_router(auth_router)

os.makedirs(settings.REPORTS_DIR, exist_ok=True)
app.mount("/reports", StaticFiles(directory=settings.REPORTS_DIR), name="reports")


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(service="agentverse-backend")


@app.websocket("/ws")
@app.websocket("/ws/workflow")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
