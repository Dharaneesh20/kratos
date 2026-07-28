import React, { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import { AgentMonitor } from './components/AgentMonitor';
import { UploadPanel } from './components/UploadPanel';
import { MapView } from './components/MapView';
import { ResilienceGauge } from './components/ResilienceGauge';
import { RoutePanel } from './components/RoutePanel';
import { ReportViewer } from './components/ReportViewer';
import { AgentHealthTab } from './components/AgentHealthTab';
import { SpectatorDashboard } from './components/SpectatorDashboard';
import { ReportManagerTab } from './components/ReportManagerTab';
import { useWebSocket } from './hooks/useWebSocket';
import { WorkflowStatus, AgentInfo, AgentLogEntry, SpectatorMetrics } from './types';
import { Shield, Moon, Sun, Layers, Map, Activity, Radio, FileText } from 'lucide-react';

export function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'agents' | 'spectator' | 'reports'>('overview');
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Spectator Telemetry State
  const [agentsList, setAgentsList] = useState<AgentInfo[]>([]);
  const [spectatorLogs, setSpectatorLogs] = useState<AgentLogEntry[]>([]);
  const [spectatorMetrics, setSpectatorMetrics] = useState<SpectatorMetrics | null>(null);

  // Fetch Spectator telemetry and agent health periodically
  const fetchSpectatorData = useCallback(async () => {
    try {
      const [agentsRes, logsRes, metricsRes] = await Promise.all([
        axios.get('/api/spectator/agents').catch(() => null),
        axios.get('/api/spectator/logs').catch(() => null),
        axios.get('/api/spectator/metrics').catch(() => null),
      ]);

      if (agentsRes?.data) setAgentsList(agentsRes.data);
      if (logsRes?.data) setSpectatorLogs(logsRes.data);
      if (metricsRes?.data) setSpectatorMetrics(metricsRes.data);
    } catch (e) {
      console.error("Telemetry fetch error:", e);
    }
  }, []);

  useEffect(() => {
    fetchSpectatorData();
    const interval = setInterval(fetchSpectatorData, 3000);
    return () => clearInterval(interval);
  }, [fetchSpectatorData]);

  // WebSocket live updates handler
  const handleWSMessage = useCallback(
    (data: any) => {
      if (data.workflow_id) {
        setWorkflowStatus((prev) => {
          if (!prev || prev.workflow_id === data.workflow_id) {
            return {
              workflow_id: data.workflow_id,
              state: data.status === 'completed' ? 'COMPLETED' : data.status === 'failed' ? 'FAILED' : 'RUNNING',
              current_stage: data.stage,
              pct: data.pct,
              hazard_type: prev?.hazard_type || 'FLOOD',
              severity: prev?.severity || 0.8,
              error: data.error,
              results: {
                ...prev?.results,
                ...data.results,
              },
              logs: [
                ...(prev?.logs || []),
                {
                  agent: data.agent,
                  stage: data.stage,
                  message: data.message,
                  time: new Date().toISOString(),
                },
              ],
            };
          }
          return prev;
        });

        if (data.stage === 'DONE' || data.status === 'failed') {
          setIsLoading(false);
        }

        // Trigger telemetry update on WS broadcast
        fetchSpectatorData();
      }
    },
    [fetchSpectatorData]
  );

  const { isConnected } = useWebSocket(handleWSMessage);

  const handleRunWorkflow = async (file: File | null, hazardType: string, severity: number) => {
    setIsLoading(true);

    const formData = new FormData();
    if (file) {
      formData.append('file', file);
    }
    formData.append('hazard_type', hazardType);
    formData.append('severity', severity.toString());

    try {
      const resp = await axios.post('/api/workflow/run', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const { workflow_id } = resp.data;

      setWorkflowStatus({
        workflow_id,
        state: 'RUNNING',
        current_stage: 'INIT',
        pct: 5,
        hazard_type: hazardType,
        severity,
        results: {},
        logs: [{ agent: 'coordinator', stage: 'INIT', message: 'Workflow initiated', time: new Date().toISOString() }],
      });

      // Poll as a fallback if WS misses events
      const pollInterval = setInterval(async () => {
        try {
          const statusResp = await axios.get(`/api/workflow/${workflow_id}`);
          const data = statusResp.data;
          setWorkflowStatus(data);

          if (data.state === 'COMPLETED' || data.state === 'FAILED') {
            setIsLoading(false);
            clearInterval(pollInterval);
          }
        } catch (e) {
          console.error("Polling error:", e);
        }
      }, 2000);
    } catch (err: any) {
      console.error("Failed to run workflow:", err);
      setIsLoading(false);
      alert("Failed to start workflow run. Ensure backend service is active.");
    }
  };

  const handleClearLogs = () => {
    setSpectatorLogs([]);
  };

  return (
    <div className={`min-h-screen ${darkMode ? 'dark bg-background text-foreground' : 'bg-background text-foreground'}`}>
      {/* KRATOS Header */}
      <header className="border-b border-border bg-card/80 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-primary text-primary-foreground flex items-center justify-center shadow-md">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-extrabold tracking-tight flex items-center gap-2 text-foreground">
              KRATOS <span className="text-xs font-normal text-muted-foreground bg-muted px-2 py-0.5 rounded border border-border">v0.1.0</span>
            </h1>
            <p className="text-[11px] text-muted-foreground font-medium">
              Knowledge-driven Road Analysis for Terrain Occlusion & Security
            </p>
          </div>
        </div>

        {/* Header Center Navigation Tabs */}
        <div className="hidden md:flex items-center gap-1 bg-secondary/80 p-1 rounded-xl border border-border/60">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === 'overview'
                ? 'bg-card text-foreground shadow-sm border border-border/80'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Map className="w-3.5 h-3.5 text-primary" />
            <span>Disaster Map</span>
          </button>

          <button
            onClick={() => setActiveTab('agents')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === 'agents'
                ? 'bg-card text-foreground shadow-sm border border-border/80'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Activity className="w-3.5 h-3.5 text-emerald-500" />
            <span>Agents & Health</span>
          </button>

          <button
            onClick={() => setActiveTab('spectator')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === 'spectator'
                ? 'bg-card text-foreground shadow-sm border border-border/80'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Radio className="w-3.5 h-3.5 text-teal-400" />
            <span>Spectator Telemetry</span>
          </button>

          <button
            onClick={() => setActiveTab('reports')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              activeTab === 'reports'
                ? 'bg-card text-foreground shadow-sm border border-border/80'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <FileText className="w-3.5 h-3.5 text-purple-400" />
            <span>Report Server</span>
          </button>
        </div>

        {/* Right Action Icons */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 text-xs text-muted-foreground font-mono bg-secondary px-3 py-1.5 rounded-lg border border-border">
            <Layers className="w-3.5 h-3.5 text-primary" />
            <span>NVIDIA cuOpt + SegFormer AI</span>
          </div>

          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-lg border border-border hover:bg-muted transition-colors cursor-pointer"
            title="Toggle theme"
          >
            {darkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-700" />}
          </button>
        </div>
      </header>

      {/* Mobile Tab Navigation Bar */}
      <div className="md:hidden flex items-center justify-around bg-card border-b border-border p-2 font-mono text-xs">
        <button
          onClick={() => setActiveTab('overview')}
          className={`p-2 rounded-lg ${activeTab === 'overview' ? 'bg-primary text-primary-foreground font-bold' : 'text-muted-foreground'}`}
        >
          Map
        </button>
        <button
          onClick={() => setActiveTab('agents')}
          className={`p-2 rounded-lg ${activeTab === 'agents' ? 'bg-primary text-primary-foreground font-bold' : 'text-muted-foreground'}`}
        >
          Agents
        </button>
        <button
          onClick={() => setActiveTab('spectator')}
          className={`p-2 rounded-lg ${activeTab === 'spectator' ? 'bg-primary text-primary-foreground font-bold' : 'text-muted-foreground'}`}
        >
          Spectator
        </button>
        <button
          onClick={() => setActiveTab('reports')}
          className={`p-2 rounded-lg ${activeTab === 'reports' ? 'bg-primary text-primary-foreground font-bold' : 'text-muted-foreground'}`}
        >
          Reports
        </button>
      </div>

      {/* Dashboard Body */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Top Workflow Agent Monitor */}
        <AgentMonitor status={workflowStatus} isConnected={isConnected} />

        {/* Tab 1: Disaster Overview & Map */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column */}
            <div className="lg:col-span-5 space-y-6">
              <UploadPanel onRunWorkflow={handleRunWorkflow} isLoading={isLoading} />
              <ResilienceGauge simulationData={workflowStatus?.results?.simulation_data} />
              <ReportViewer reportData={workflowStatus?.results?.report_data} workflowId={workflowStatus?.workflow_id} />
            </div>

            {/* Right Column */}
            <div className="lg:col-span-7 space-y-6">
              <MapView
                roadsGeoJSON={workflowStatus?.results?.roads_geojson}
                roadMaskBase64={workflowStatus?.results?.road_mask_png_base64}
                criticalNodes={workflowStatus?.results?.critical_nodes}
                evacuationRoutes={workflowStatus?.results?.planning_data?.evacuation_routes}
              />
              <RoutePanel planningData={workflowStatus?.results?.planning_data} />
            </div>
          </div>
        )}

        {/* Tab 2: Agents & Health Matrix */}
        {activeTab === 'agents' && (
          <AgentHealthTab agents={agentsList} logs={spectatorLogs} onClearLogs={handleClearLogs} />
        )}

        {/* Tab 3: Spectator Telemetry */}
        {activeTab === 'spectator' && (
          <SpectatorDashboard metrics={spectatorMetrics} />
        )}

        {/* Tab 4: Report Server */}
        {activeTab === 'reports' && (
          <ReportManagerTab />
        )}
      </main>
    </div>
  );
}
