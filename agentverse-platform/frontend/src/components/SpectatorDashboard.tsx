import React, { useState, useEffect } from 'react';
import { SpectatorMetrics, AgentInfo } from '../types';
import { Radio, Cpu, Zap, Activity, CheckCircle2, Server, Eye, ArrowUpRight, Clock } from 'lucide-react';

interface SpectatorDashboardProps {
  metrics: SpectatorMetrics | null;
  agents?: AgentInfo[];
}

function MetricCard({
  label,
  value,
  unit,
  status,
  statusLabel,
  icon: Icon,
  color,
  glow,
}: {
  label: string;
  value: string | number;
  unit?: string;
  status: string;
  statusLabel: string;
  icon: React.FC<any>;
  color: string;
  glow: string;
}) {
  return (
    <div className={`glass-card p-5 relative overflow-hidden hover:${glow}`}>
      {/* Background gradient blob */}
      <div className={`absolute -top-6 -right-6 w-20 h-20 rounded-full opacity-10 ${color}`} style={{ filter: 'blur(20px)' }} />

      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest">{label}</span>
        <div className={`w-7 h-7 rounded-lg flex items-center justify-center border ${glow} bg-white/[0.04]`}>
          <Icon className={`w-3.5 h-3.5 ${color}`} />
        </div>
      </div>

      <div className="text-2xl font-extrabold font-mono text-white flex items-baseline gap-1 mb-3">
        {value}
        {unit && <span className="text-xs font-normal text-muted-foreground ml-1">{unit}</span>}
      </div>

      <div className="flex items-center justify-between">
        <span className={`text-[10px] font-mono font-bold px-2 py-1 rounded-lg border ${
          status === 'ONLINE'
            ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
            : status === 'DEGRADED'
            ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
            : 'bg-white/[0.06] text-muted-foreground border-white/10'
        }`}>
          {status === 'ONLINE' ? '● ONLINE' : status === 'DEGRADED' ? '⚠ DEGRADED' : '○ ' + status}
        </span>
        <span className="text-[10px] text-muted-foreground">{statusLabel}</span>
      </div>
    </div>
  );
}

export const SpectatorDashboard: React.FC<SpectatorDashboardProps> = ({ metrics, agents }) => {
  const [uptime, setUptime] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setUptime((p) => p + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  const m = metrics || {
    overall_health: 'HEALTHY',
    active_agents: 12,
    nvidia_nim_status: 'CHECKING',
    nvidia_nim_ping_ms: 0,
    cuopt_status: 'CHECKING',
    cuopt_response_time_ms: 0,
    segformer_confidence: 0,
    avg_inference_time_ms: 0,
    uptime_seconds: 0,
  };

  const totalUptime = Math.round((m.uptime_seconds || 0) + uptime);
  const uptimeStr = totalUptime < 60 ? `${totalUptime}s` : totalUptime < 3600 ? `${Math.floor(totalUptime / 60)}m ${totalUptime % 60}s` : `${Math.floor(totalUptime / 3600)}h ${Math.floor((totalUptime % 3600) / 60)}m`;

  const healthyCount = agents?.filter((a) => a.status === 'HEALTHY' || a.status === 'BUSY').length || m.active_agents;

  return (
    <div className="space-y-5 animate-slide-in">
      {/* Header Banner */}
      <div className="glass-card p-5 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-600/30 to-cyan-900/20 border border-cyan-500/30 flex items-center justify-center">
            <Radio className="w-6 h-6 text-cyan-400 animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-black text-white tracking-tight">Agent Spectator Telemetry Hub</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Real-time NVIDIA NIM latency · cuOpt routing · SegFormer vision · Sub-second pings
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden md:block">
            <p className="text-[10px] text-muted-foreground uppercase tracking-widest">Uptime</p>
            <p className="text-sm font-mono font-bold text-cyan-400">{uptimeStr}</p>
          </div>
          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" />
            SENTINEL ACTIVE
          </span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="NVIDIA NIM Status"
          value={m.nvidia_nim_ping_ms > 0 ? m.nvidia_nim_ping_ms.toFixed(0) : '—'}
          unit={m.nvidia_nim_ping_ms > 0 ? 'ms ping' : ''}
          status={m.nvidia_nim_status === 'ONLINE' ? 'ONLINE' : m.nvidia_nim_status || 'CHECKING'}
          statusLabel="NeMoTron LLM"
          icon={Server}
          color="text-violet-400"
          glow="border-violet-500/30"
        />
        <MetricCard
          label="NVIDIA cuOpt Speed"
          value={m.cuopt_response_time_ms > 0 ? m.cuopt_response_time_ms.toFixed(0) : '—'}
          unit={m.cuopt_response_time_ms > 0 ? 'ms latency' : ''}
          status={m.cuopt_status === 'ONLINE' ? 'ONLINE' : m.cuopt_status?.includes('Fallback') ? 'FALLBACK' : m.cuopt_status || 'CHECKING'}
          statusLabel="GPU Route Solver"
          icon={Zap}
          color="text-amber-400"
          glow="border-amber-500/30"
        />
        <MetricCard
          label="SegFormer AI Confidence"
          value={m.segformer_confidence > 0 ? `${Math.round(m.segformer_confidence * 100)}%` : 'N/A'}
          status={m.segformer_confidence > 0 ? 'ONLINE' : 'UNTRAINED'}
          statusLabel="Road Extraction"
          icon={Eye}
          color="text-purple-400"
          glow="border-purple-500/30"
        />
        <MetricCard
          label="Agent Pipeline"
          value={m.avg_inference_time_ms > 0 ? m.avg_inference_time_ms.toFixed(1) : '—'}
          unit={m.avg_inference_time_ms > 0 ? 'ms avg' : ''}
          status={healthyCount > 0 ? 'ONLINE' : 'DEGRADED'}
          statusLabel={`${healthyCount}/12 Agents`}
          icon={Cpu}
          color="text-cyan-400"
          glow="border-cyan-500/30"
        />
      </div>

      {/* Infrastructure Info */}
      <div className="glass-card p-5">
        <h3 className="text-xs font-bold text-white uppercase tracking-widest flex items-center gap-2 mb-4">
          <Activity className="w-4 h-4 text-violet-400" />
          KRATOS Infrastructure & Telemetry Diagnostics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              title: 'NVIDIA NIM Infrastructure',
              color: 'violet',
              body: 'NeMoTron LLM endpoints process disaster intelligence requests. Authenticated via NVIDIA Cloud API. Real-time latency measured via /models discovery endpoint.',
            },
            {
              title: 'cuOpt GPU Solver Engine',
              color: 'amber',
              body: 'CUDA-accelerated Vehicle Routing Problem (VRP) solver computes evacuation vectors under dynamic disaster conditions with GPU-accelerated optimization.',
            },
            {
              title: 'Agent Spectator Sentinel',
              color: 'cyan',
              body: 'Monitors all 12 KRATOS agents in real time: state transitions, heartbeat signals, inference latency, AI confidence scores, and cross-agent log aggregation.',
            },
          ].map((item) => (
            <div
              key={item.title}
              className={`p-4 rounded-xl border bg-white/[0.02] border-${item.color}-500/20 hover:border-${item.color}-500/40 transition-all`}
            >
              <span className={`text-xs font-bold text-${item.color}-400 block mb-2`}>{item.title}</span>
              <p className="text-[11px] text-muted-foreground leading-relaxed">{item.body}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
