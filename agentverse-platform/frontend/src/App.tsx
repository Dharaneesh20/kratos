import React, { useState, useCallback } from 'react';
import axios from 'axios';
import { AgentMonitor } from './components/AgentMonitor';
import { UploadPanel } from './components/UploadPanel';
import { MapView } from './components/MapView';
import { ResilienceGauge } from './components/ResilienceGauge';
import { RoutePanel } from './components/RoutePanel';
import { ReportViewer } from './components/ReportViewer';
import { useWebSocket } from './hooks/useWebSocket';
import { WorkflowStatus } from './types';
import { Network, Moon, Sun, Layers } from 'lucide-react';

export function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // WebSocket live updates handler
  const handleWSMessage = useCallback((data: any) => {
    if (data.workflow_id) {
      setWorkflowStatus((prev) => {
        // Merge or update status
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
    }
  }, []);

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
        hazard_type,
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

  return (
    <div className={`min-h-screen ${darkMode ? 'dark bg-background text-foreground' : 'bg-background text-foreground'}`}>
      {/* Header */}
      <header className="border-b border-border bg-card/80 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-primary text-primary-foreground flex items-center justify-center shadow-md">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-extrabold tracking-tight flex items-center gap-2">
              AgentVerse <span className="text-xs font-normal text-muted-foreground bg-muted px-2 py-0.5 rounded border border-border">v0.1.0</span>
            </h1>
            <p className="text-[11px] text-muted-foreground font-medium">Occlusion-Robust Road AI & Criticality Platform</p>
          </div>
        </div>

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

      {/* Dashboard Body */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Top Workflow Agent Monitor */}
        <AgentMonitor status={workflowStatus} isConnected={isConnected} />

        {/* 2-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column (Control & Gauges) */}
          <div className="lg:col-span-5 space-y-6">
            <UploadPanel onRunWorkflow={handleRunWorkflow} isLoading={isLoading} />
            <ResilienceGauge simulationData={workflowStatus?.results?.simulation_data} />
            <ReportViewer reportData={workflowStatus?.results?.report_data} workflowId={workflowStatus?.workflow_id} />
          </div>

          {/* Right Column (Map & Routes) */}
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
      </main>
    </div>
  );
}
