import React, { useState, useCallback, useEffect, useRef } from 'react';
import axios from 'axios';
import { AgentMonitor } from './components/AgentMonitor';
import { UploadPanel } from './components/UploadPanel';
import { MapView } from './components/MapView';
import { ResilienceGauge } from './components/ResilienceGauge';
import { RoutePanel } from './components/RoutePanel';
import { AgentHealthTab } from './components/AgentHealthTab';
import { SpectatorDashboard } from './components/SpectatorDashboard';
import { ReportManagerTab } from './components/ReportManagerTab';
import { DisasterChatbot } from './components/DisasterChatbot';
import { useWebSocket } from './hooks/useWebSocket';
import { WorkflowStatus, AgentInfo, AgentLogEntry, SpectatorMetrics } from './types';
import { Shield, Map, Activity, Radio, FileText, Bot, Zap, Wifi, WifiOff, ChevronRight } from 'lucide-react';

const TABS = [
  { id: 'overview', label: 'Disaster Map', icon: Map, color: 'text-violet-400' },
  { id: 'agents', label: 'Agent Health', icon: Activity, color: 'text-emerald-400' },
  { id: 'spectator', label: 'Telemetry', icon: Radio, color: 'text-cyan-400' },
  { id: 'reports', label: 'Reports', icon: FileText, color: 'text-purple-400' },
  { id: 'chatbot', label: 'NeMoTron AI', icon: Bot, color: 'text-emerald-400' },
] as const;

type TabId = typeof TABS[number]['id'];

export function App() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [agentsList, setAgentsList] = useState<AgentInfo[]>([]);
  const [spectatorLogs, setSpectatorLogs] = useState<AgentLogEntry[]>([]);
  const [spectatorMetrics, setSpectatorMetrics] = useState<SpectatorMetrics | null>(null);

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
      console.error('Telemetry fetch error:', e);
    }
  }, []);

  useEffect(() => {
    fetchSpectatorData();
    const interval = setInterval(fetchSpectatorData, 4000);
    return () => clearInterval(interval);
  }, [fetchSpectatorData]);

  const handleWSMessage = useCallback(
    (data: any) => {
      if (data.workflow_id) {
        setWorkflowStatus((prev) => ({
          workflow_id: data.workflow_id,
          state: data.status === 'completed' ? 'COMPLETED' : data.status === 'failed' ? 'FAILED' : 'RUNNING',
          current_stage: data.stage,
          pct: data.pct,
          hazard_type: prev?.hazard_type || 'FLOOD',
          severity: prev?.severity || 0.8,
          error: data.error,
          results: { ...prev?.results, ...data.results },
          logs: [
            ...(prev?.logs || []),
            { agent: data.agent, stage: data.stage, message: data.message, time: new Date().toISOString() },
          ],
        }));
        if (data.stage === 'DONE' || data.status === 'failed') setIsLoading(false);
        fetchSpectatorData();
      }
    },
    [fetchSpectatorData]
  );

  const { isConnected } = useWebSocket(handleWSMessage);

  const handleRunWorkflow = async (file: File | null, hazardType: string, severity: number) => {
    setIsLoading(true);
    const formData = new FormData();
    if (file) formData.append('file', file);
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

      const pollInterval = setInterval(async () => {
        try {
          const statusResp = await axios.get(`/api/workflow/${workflow_id}`);
          const data = statusResp.data;
          setWorkflowStatus(data);
          if (data.state === 'COMPLETED' || data.state === 'FAILED') {
            setIsLoading(false);
            clearInterval(pollInterval);
          }
        } catch (e) {}
      }, 2000);
    } catch (err) {
      setIsLoading(false);
      alert('Failed to start workflow. Ensure backend service is active.');
    }
  };

  const nimOnline = spectatorMetrics?.nvidia_nim_status === 'ONLINE';
  const cuoptOnline = spectatorMetrics?.cuopt_status === 'ONLINE';

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* ── GLASSMORPHISM HEADER ── */}
      <header className="glass-nav sticky top-0 z-50 px-6 py-0">
        <div className="max-w-[1600px] mx-auto flex items-center justify-between h-[60px]">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 to-violet-900 flex items-center justify-center shadow-lg glow-violet">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-black tracking-widest text-gradient-violet uppercase">KRATOS</h1>
              <p className="text-[10px] text-muted-foreground font-medium tracking-wider hidden sm:block">
                Multi-Agent Disaster Intelligence Platform
              </p>
            </div>
          </div>

          {/* Center Nav Tabs */}
          <nav className="hidden md:flex items-center gap-1 bg-white/[0.03] border border-white/[0.06] rounded-xl p-1 backdrop-blur-xl">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`relative px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all duration-200 cursor-pointer ${
                    isActive
                      ? 'bg-violet-600/20 text-white border border-violet-500/30 shadow-lg'
                      : 'text-muted-foreground hover:text-foreground hover:bg-white/[0.04]'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-violet-400' : tab.color}`} />
                  {tab.label}
                  {isActive && (
                    <span className="absolute inset-x-0 -bottom-[1px] h-[2px] bg-gradient-to-r from-violet-500 to-cyan-500 rounded-full" />
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right Status Bar */}
          <div className="flex items-center gap-2">
            {/* NIM Status Pill */}
            <div
              className={`hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-bold border backdrop-blur ${
                nimOnline
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : 'bg-white/[0.04] border-white/10 text-muted-foreground'
              }`}
            >
              <span className={`status-dot ${nimOnline ? 'online' : 'offline'} w-1.5 h-1.5`} />
              NIM
            </div>

            {/* cuOpt Status Pill */}
            <div
              className={`hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-bold border backdrop-blur ${
                cuoptOnline
                  ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
                  : 'bg-white/[0.04] border-white/10 text-muted-foreground'
              }`}
            >
              <Zap className="w-2.5 h-2.5" />
              cuOpt
            </div>

            {/* WebSocket indicator */}
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-bold border ${
                isConnected
                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                  : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
              }`}
            >
              {isConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
              <span className="hidden sm:inline">{isConnected ? 'LIVE' : 'OFFLINE'}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile nav */}
      <div className="md:hidden flex items-center overflow-x-auto gap-0.5 glass-nav px-3 py-2 border-t border-white/[0.04]">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-[10px] font-semibold transition-all cursor-pointer ${
                activeTab === tab.id
                  ? 'bg-violet-600/20 text-white border border-violet-500/30'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="w-3 h-3" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* ── WORKFLOW PIPELINE BANNER ── */}
      <div className="max-w-[1600px] mx-auto px-4 pt-5">
        <AgentMonitor status={workflowStatus} isConnected={isConnected} />
      </div>

      {/* ── MAIN CONTENT ── */}
      <main className="max-w-[1600px] mx-auto px-4 pb-8">

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 animate-slide-in">
            {/* Left Column */}
            <div className="xl:col-span-4 space-y-5">
              <UploadPanel onRunWorkflow={handleRunWorkflow} isLoading={isLoading} />
              <ResilienceGauge simulationData={workflowStatus?.results?.simulation_data} />
              <RoutePanel planningData={workflowStatus?.results?.planning_data} />
            </div>

            {/* Right Column */}
            <div className="xl:col-span-8 space-y-5">
              <MapView
                roadsGeoJSON={workflowStatus?.results?.roads_geojson}
                roadMaskBase64={workflowStatus?.results?.road_mask_png_base64}
                criticalNodes={workflowStatus?.results?.critical_nodes}
                evacuationRoutes={workflowStatus?.results?.planning_data?.evacuation_routes}
              />
              <DisasterChatbot
                workflowId={workflowStatus?.workflow_id}
                spectatorMetrics={spectatorMetrics}
              />
            </div>
          </div>
        )}

        {/* Agents Tab */}
        {activeTab === 'agents' && (
          <div className="animate-slide-in">
            <AgentHealthTab agents={agentsList} logs={spectatorLogs} onClearLogs={() => setSpectatorLogs([])} />
          </div>
        )}

        {/* Spectator Tab */}
        {activeTab === 'spectator' && (
          <div className="animate-slide-in">
            <SpectatorDashboard metrics={spectatorMetrics} agents={agentsList} />
          </div>
        )}

        {/* Reports Tab */}
        {activeTab === 'reports' && (
          <div className="animate-slide-in">
            <ReportManagerTab />
          </div>
        )}

        {/* Chatbot Full Tab */}
        {activeTab === 'chatbot' && (
          <div className="animate-slide-in">
            <DisasterChatbot
              workflowId={workflowStatus?.workflow_id}
              spectatorMetrics={spectatorMetrics}
              fullScreen
            />
          </div>
        )}
      </main>
    </div>
  );
}
