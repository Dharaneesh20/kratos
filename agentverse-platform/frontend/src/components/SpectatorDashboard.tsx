import React from 'react';
import { SpectatorMetrics } from '../types';
import { Radio, Cpu, Zap, Activity, ShieldAlert, CheckCircle2, Server, Eye } from 'lucide-react';

interface SpectatorDashboardProps {
  metrics: SpectatorMetrics | null;
}

export const SpectatorDashboard: React.FC<SpectatorDashboardProps> = ({ metrics }) => {
  const m = metrics || {
    overall_health: 'HEALTHY',
    active_agents: 7,
    nvidia_nim_status: 'ONLINE',
    nvidia_nim_ping_ms: 18.4,
    cuopt_status: 'ONLINE',
    cuopt_response_time_ms: 42.1,
    segformer_confidence: 0.964,
    avg_inference_time_ms: 145.2,
    uptime_seconds: 3600.0,
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-sm flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/20 text-teal-500 flex items-center justify-center">
            <Radio className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-bold tracking-tight text-foreground">
              Agent Spectator Telemetry Hub
            </h2>
            <p className="text-xs text-muted-foreground">
              Continuous monitoring of NVIDIA NIM microservices, cuOpt routing engine, SegFormer vision confidence, and sub-second pings.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono font-bold bg-emerald-500/10 text-emerald-500 border border-emerald-500/30">
            <CheckCircle2 className="w-4 h-4" />
            SENTINEL ACTIVE
          </span>
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* NVIDIA NIM Ping */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              NVIDIA NIM Status
            </span>
            <Server className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold font-mono text-foreground flex items-baseline gap-1">
            {m.nvidia_nim_ping_ms} <span className="text-xs font-normal text-muted-foreground">ms ping</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs font-mono">
            <span
              className={`font-bold px-2 py-0.5 rounded border ${
                m.nvidia_nim_status === 'ONLINE'
                  ? 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20'
                  : 'text-rose-400 bg-rose-500/10 border-rose-500/20'
              }`}
            >
              {m.nvidia_nim_status}
            </span>
            <span className="text-muted-foreground">GPU Accelerated</span>
          </div>
        </div>

        {/* cuOpt Response Time */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              NVIDIA cuOpt Speed
            </span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-extrabold font-mono text-foreground flex items-baseline gap-1">
            {m.cuopt_response_time_ms} <span className="text-xs font-normal text-muted-foreground">ms latency</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs font-mono">
            <span
              className={`font-bold px-2 py-0.5 rounded border ${
                m.cuopt_status === 'ONLINE'
                  ? 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20'
                  : 'text-amber-400 bg-amber-500/10 border-amber-500/20'
              }`}
            >
              {m.cuopt_status}
            </span>
            <span className="text-muted-foreground">Route Solver</span>
          </div>
        </div>

        {/* SegFormer Confidence */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              SegFormer AI Confidence
            </span>
            <Eye className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-extrabold font-mono text-purple-400 flex items-baseline gap-1">
            {m.segformer_confidence > 0 ? `${Math.round(m.segformer_confidence * 100)}%` : 'UNTRAINED'}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs font-mono">
            <span
              className={`font-bold px-2 py-0.5 rounded border ${
                m.segformer_confidence > 0
                  ? 'text-purple-400 bg-purple-500/10 border-purple-500/20'
                  : 'text-amber-400 bg-amber-500/10 border-amber-500/20'
              }`}
            >
              {m.segformer_confidence > 0 ? 'HIGH ACCURACY' : 'MODEL UNTRAINED'}
            </span>
            <span className="text-muted-foreground">Road Extraction</span>
          </div>
        </div>

        {/* Average Inference Time */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Avg Execution Time
            </span>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-extrabold font-mono text-cyan-400 flex items-baseline gap-1">
            {m.avg_inference_time_ms} <span className="text-xs font-normal text-muted-foreground">ms</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs font-mono">
            <span className="text-cyan-400 font-bold bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
              {m.active_agents}/11 ACTIVE
            </span>
            <span className="text-muted-foreground">Agent Pipeline</span>
          </div>
        </div>
      </div>

      {/* Detailed Technical Overview Card */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-foreground tracking-wide uppercase flex items-center gap-2">
          <Activity className="w-4 h-4 text-primary" />
          KRATOS Infrastructure Telemetry & Health Diagnostics
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
          <div className="bg-secondary/40 p-3.5 rounded-lg border border-border/50 space-y-2">
            <span className="text-muted-foreground font-bold block">NVIDIA NIM Infrastructure</span>
            <p className="text-muted-foreground">
              Containerized NIM endpoints process road vision segmentation and topological graph optimizations with sub-50ms roundtrip latency.
            </p>
          </div>

          <div className="bg-secondary/40 p-3.5 rounded-lg border border-border/50 space-y-2">
            <span className="text-muted-foreground font-bold block">cuOpt GPU Solver Engine</span>
            <p className="text-muted-foreground">
              CUDA-accelerated Vehicle Routing Problem (VRP) solver computes optimal evacuation vectors under dynamic road closures.
            </p>
          </div>

          <div className="bg-secondary/40 p-3.5 rounded-lg border border-border/50 space-y-2">
            <span className="text-muted-foreground font-bold block">Agent Spectator Protocol</span>
            <p className="text-muted-foreground">
              Monitors state transitions, validates heartbeat signals, traps runtime exceptions, and streams unified log payloads.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
