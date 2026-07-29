import React from 'react';
import { AgentInfo, AgentLogEntry } from '../types';
import { LogTerminal } from './LogTerminal';
import {
  Activity, ShieldCheck, Cpu, Eye, Network, Flame, Route,
  FileText, Radio, Clock, Zap, Bot, Layers, GitBranch, BarChart2
} from 'lucide-react';

interface AgentHealthTabProps {
  agents: AgentInfo[];
  logs: AgentLogEntry[];
  onClearLogs?: () => void;
}

const AGENT_ICONS: Record<string, React.FC<any>> = {
  coordinator: Cpu,
  dataset: Layers,
  vision: Eye,
  skeletonizer: GitBranch,
  graph: Network,
  centrality: BarChart2,
  simulation: Flame,
  planning: Route,
  repair: Zap,
  report: FileText,
  spectator: Radio,
  chatbot: Bot,
};

const AGENT_COLORS: Record<string, { text: string; bg: string; border: string }> = {
  coordinator: { text: 'text-violet-400', bg: 'bg-violet-500/10', border: 'border-violet-500/30' },
  dataset: { text: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30' },
  vision: { text: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/30' },
  skeletonizer: { text: 'text-indigo-400', bg: 'bg-indigo-500/10', border: 'border-indigo-500/30' },
  graph: { text: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/30' },
  centrality: { text: 'text-teal-400', bg: 'bg-teal-500/10', border: 'border-teal-500/30' },
  simulation: { text: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30' },
  planning: { text: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
  repair: { text: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30' },
  report: { text: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/30' },
  spectator: { text: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' },
  chatbot: { text: 'text-fuchsia-400', bg: 'bg-fuchsia-500/10', border: 'border-fuchsia-500/30' },
};

const STATUS_CONFIG = {
  HEALTHY: { dot: 'online', badge: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30', label: '● HEALTHY' },
  BUSY: { dot: 'busy', badge: 'bg-violet-500/15 text-violet-400 border-violet-500/30 animate-pulse', label: '◉ BUSY' },
  DEGRADED: { dot: 'offline', badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30', label: '⚠ DEGRADED' },
  OFFLINE: { dot: 'offline', badge: 'bg-rose-500/15 text-rose-400 border-rose-500/30', label: '○ OFFLINE' },
};

export const AgentHealthTab: React.FC<AgentHealthTabProps> = ({ agents, logs, onClearLogs }) => {
  const healthyCount = agents.filter((a) => a.status === 'HEALTHY' || a.status === 'BUSY').length;

  return (
    <div className="space-y-5 animate-slide-in">
      {/* Header */}
      <div className="glass-card p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-violet-400" />
            KRATOS Multi-Agent Ecosystem
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            12 active agents · Real-time health, inference time, and confidence monitored by Agent Spectator
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="glass px-4 py-2 rounded-xl flex items-center gap-2 text-xs">
            <span className="status-dot online" />
            <span className="text-muted-foreground">
              <strong className="text-white">{healthyCount}</strong> / {agents.length || 12} Healthy
            </span>
          </div>
          <div className="glass px-4 py-2 rounded-xl flex items-center gap-2 text-xs">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-muted-foreground">
              Avg <strong className="text-white">{agents.length > 0 ? Math.round(agents.reduce((a, b) => a + b.ping_ms, 0) / agents.length) : 0}ms</strong> ping
            </span>
          </div>
        </div>
      </div>

      {/* 12-Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {agents.map((agent, idx) => {
          const Icon = AGENT_ICONS[agent.id] || Activity;
          const colors = AGENT_COLORS[agent.id] || { text: 'text-violet-400', bg: 'bg-violet-500/10', border: 'border-violet-500/30' };
          const statusCfg = STATUS_CONFIG[agent.status] || STATUS_CONFIG.OFFLINE;

          return (
            <div
              key={agent.id}
              className="glass-card p-4 flex flex-col justify-between group animate-fade-in"
              style={{ animationDelay: `${idx * 40}ms` }}
            >
              {/* Top Row */}
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className={`w-9 h-9 rounded-xl ${colors.bg} border ${colors.border} flex items-center justify-center flex-shrink-0`}>
                      <Icon className={`w-[18px] h-[18px] ${colors.text}`} />
                    </div>
                    <div>
                      <h3 className="text-xs font-bold text-white leading-tight">{agent.name}</h3>
                      <span className="text-[9px] font-mono text-muted-foreground">ID: {agent.id}</span>
                    </div>
                  </div>
                  <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border uppercase ${statusCfg.badge}`}>
                    {statusCfg.label}
                  </span>
                </div>

                <div className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-2.5 mb-3">
                  <p className="text-[10px] text-muted-foreground leading-relaxed">{agent.purpose}</p>
                </div>
              </div>

              {/* Metrics Footer */}
              <div className="space-y-2">
                <div className="text-[10px] text-muted-foreground px-1 flex items-start gap-1">
                  <Clock className="w-3 h-3 text-violet-400 flex-shrink-0 mt-0.5" />
                  <span className="truncate">{agent.current_task}</span>
                </div>
                <div className="grid grid-cols-3 gap-1.5 text-center">
                  {[
                    { label: 'PING', value: `${agent.ping_ms}ms`, color: 'text-emerald-400' },
                    { label: 'EXEC', value: `${agent.inference_time_ms}ms`, color: 'text-cyan-400' },
                    { label: 'CONF', value: `${Math.round(agent.confidence_score * 100)}%`, color: 'text-purple-400' },
                  ].map((stat) => (
                    <div key={stat.label} className="bg-white/[0.03] border border-white/[0.05] rounded-lg py-1.5">
                      <span className="block text-[8px] text-muted-foreground uppercase tracking-wide">{stat.label}</span>
                      <span className={`block text-[11px] font-bold font-mono ${stat.color}`}>{stat.value}</span>
                    </div>
                  ))}
                </div>

                {/* Confidence bar */}
                <div className="progress-bar mt-1">
                  <div
                    className="progress-bar-fill"
                    style={{ width: `${Math.round(agent.confidence_score * 100)}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Log Terminal */}
      <div>
        <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
          <Activity className="w-4 h-4 text-violet-400" />
          Real-time Agent Log Terminal
        </h3>
        <LogTerminal logs={logs} onClearLogs={onClearLogs} />
      </div>
    </div>
  );
};
