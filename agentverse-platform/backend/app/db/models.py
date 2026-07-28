import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class RunModel(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True, index=True)
    state = Column(String, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    current_stage = Column(String, default="INIT")
    pct = Column(Integer, default=0)
    hazard_type = Column(String, default="FLOOD")
    severity = Column(Float, default=0.8)
    error = Column(Text, nullable=True)

    # Stored artifact JSONs
    roads_geojson = Column(JSON, nullable=True)
    road_mask_png_base64 = Column(Text, nullable=True)
    graph_data = Column(JSON, nullable=True)
    critical_nodes = Column(JSON, nullable=True)
    simulation_data = Column(JSON, nullable=True)
    planning_data = Column(JSON, nullable=True)
    report_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class AgentLogModel(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String, index=True)
    agent = Column(String)
    stage = Column(String)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
