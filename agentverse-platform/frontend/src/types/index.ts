export interface CriticalNode {
  node_id: string;
  lat: number;
  lon: number;
  criticality_score: number;
  is_bridge_adjacent: boolean;
  betweenness: number;
  closeness: number;
  degree: number;
}

export interface EvacuationRoute {
  route_id: string;
  from_node: string;
  to_node: string;
  path_nodes: string[];
  path_coords: [number, number][];
  eta_min: number;
  vehicle: string;
}

export interface RepairPriorityItem {
  node_id: string;
  priority: number;
  reason: string;
}

export interface SimulationData {
  travel_delay: number;
  resilience: number;
  affected_regions: string[];
  damaged_graph_data?: any;
  damaged_edge_ids?: string[];
}

export interface PlanningData {
  repair_priority: RepairPriorityItem[];
  evacuation_routes: EvacuationRoute[];
  recommendations: string[];
}

export interface ReportData {
  pdf_path?: string;
  csv_path?: string;
  pdf_url?: string;
  csv_url?: string;
  executive_summary?: string;
  risk_analysis?: string;
  repair_narrative?: string;
  recommendations?: string[];
}

export interface WorkflowResults {
  roads_geojson?: any;
  road_mask_png_base64?: string;
  graph_data?: any;
  critical_nodes?: CriticalNode[];
  simulation_data?: SimulationData;
  planning_data?: PlanningData;
  report_data?: ReportData;
}

export interface WorkflowStatus {
  workflow_id: string;
  state: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  current_stage: string;
  pct: number;
  hazard_type: string;
  severity: number;
  error?: string;
  results: WorkflowResults;
  logs: Array<{
    agent: string;
    stage: string;
    message: string;
    time: string;
  }>;
}

export interface AgentInfo {
  id: string;
  name: string;
  purpose: string;
  role_in_project: string;
  status: 'HEALTHY' | 'BUSY' | 'DEGRADED' | 'OFFLINE';
  ping_ms: number;
  last_heartbeat: string;
  current_task: string;
  inference_time_ms: number;
  confidence_score: number;
  processed_count: number;
}

export interface SpectatorMetrics {
  overall_health: string;
  active_agents: number;
  nvidia_nim_status: string;
  nvidia_nim_ping_ms: number;
  cuopt_status: string;
  cuopt_response_time_ms: number;
  segformer_confidence: number;
  avg_inference_time_ms: number;
  uptime_seconds: number;
}

export interface AgentLogEntry {
  id: string;
  timestamp: string;
  agent: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS';
  message: string;
  details?: Record<string, any>;
}

export interface ReportMetadata {
  report_id: string;
  workflow_id: string;
  hazard_type: string;
  created_at: string;
  pdf_url: string;
  csv_url: string;
  resilience_score: number;
  travel_delay: number;
  recommendations_count: number;
}

