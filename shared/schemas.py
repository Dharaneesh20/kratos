from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    version: str = "0.1.0"


class CriticalNode(BaseModel):
    node_id: str
    lat: float
    lon: float
    criticality_score: float
    is_bridge_adjacent: bool = False
    betweenness: float = 0.0
    closeness: float = 0.0
    degree: float = 0.0


class GraphBuildRequest(BaseModel):
    roads_geojson: Dict[str, Any]
    snap_tolerance_m: float = 5.0


class GraphBuildResponse(BaseModel):
    status: str = "success"
    agent: str = "graph"
    nodes: int
    edges: int
    graph_data: Dict[str, Any]
    critical_nodes: List[CriticalNode]


class SimulationRunRequest(BaseModel):
    graph_data: Dict[str, Any]
    hazard_type: str = "FLOOD"
    affected_node_ids: List[str] = Field(default_factory=list)
    affected_edge_ids: List[str] = Field(default_factory=list)
    severity: float = 0.8


class SimulationRunResponse(BaseModel):
    status: str = "success"
    agent: str = "simulation"
    travel_delay: float
    resilience: float
    affected_regions: List[str] = Field(default_factory=list)
    damaged_graph_data: Dict[str, Any] = Field(default_factory=dict)
    damaged_edge_ids: List[str] = Field(default_factory=list)


class SafeZone(BaseModel):
    node_id: str
    label: str


class PlanningRequest(BaseModel):
    graph_data: Dict[str, Any]
    critical_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    simulation_data: Dict[str, Any] = Field(default_factory=dict)
    hazard_type: str = "FLOOD"
    safe_zones: List[SafeZone] = Field(default_factory=list)


class EvacuationRoute(BaseModel):
    route_id: str
    from_node: str
    to_node: str
    path_nodes: List[str]
    path_coords: List[List[float]]
    eta_min: float
    vehicle: str = "ambulance"


class RepairPriorityItem(BaseModel):
    node_id: str
    priority: int
    reason: str


class PlanningResponse(BaseModel):
    status: str = "success"
    agent: str = "planning"
    repair_priority: List[RepairPriorityItem] = Field(default_factory=list)
    evacuation_routes: List[EvacuationRoute] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class ReportRequest(BaseModel):
    workflow_id: str
    roads_geojson: Optional[Dict[str, Any]] = None
    graph_data: Optional[Dict[str, Any]] = None
    critical_nodes: Optional[List[Dict[str, Any]]] = None
    simulation_data: Optional[Dict[str, Any]] = None
    planning_data: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    status: str = "success"
    agent: str = "report"
    executive_summary: str
    risk_analysis: str
    repair_narrative: str
    recommendations: List[str]
    pdf_path: str
    csv_path: str
    summary_json: Dict[str, Any]


class WorkflowRunRequest(BaseModel):
    hazard_type: str = "FLOOD"
    severity: float = 0.8


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    state: str
    current_stage: str
    pct: int
    error: Optional[str] = None
    results: Dict[str, Any] = Field(default_factory=dict)
    logs: List[Dict[str, Any]] = Field(default_factory=list)


class AgentInfo(BaseModel):
    id: str
    name: str
    purpose: str
    role_in_project: str
    status: str = "HEALTHY"  # HEALTHY, BUSY, DEGRADED, OFFLINE
    ping_ms: float = 12.5
    last_heartbeat: str
    current_task: str = "Idle / Monitoring"
    inference_time_ms: float = 0.0
    confidence_score: float = 0.95
    processed_count: int = 0


class SpectatorMetrics(BaseModel):
    overall_health: str = "HEALTHY"
    active_agents: int = 7
    nvidia_nim_status: str = "ONLINE"
    nvidia_nim_ping_ms: float = 18.4
    cuopt_status: str = "ONLINE"
    cuopt_response_time_ms: float = 42.1
    segformer_confidence: float = 0.964
    avg_inference_time_ms: float = 145.2
    uptime_seconds: float = 3600.0


class AgentLogEntry(BaseModel):
    id: str
    timestamp: str
    agent: str
    level: str = "INFO"  # INFO, WARNING, ERROR, SUCCESS
    message: str
    details: Optional[Dict[str, Any]] = None


class ReportMetadata(BaseModel):
    report_id: str
    workflow_id: str
    hazard_type: str
    created_at: str
    pdf_url: str
    csv_url: str
    resilience_score: float
    travel_delay: float
    recommendations_count: int

