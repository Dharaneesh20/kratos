import React from 'react';
import { AgentInfo, AgentLogEntry } from '../types';
import { LogTerminal } from './LogTerminal';
import { Activity, ShieldCheck, Cpu, Eye, Network, Flame, Route, FileText, Radio, Clock, Zap } from 'lucide-react';

interface AgentHealthTabProps {
  agents: AgentInfo[];
  logs: AgentLogEntry[];
  onClearLogs?: () => void;
}

export const AgentHealthTab: React.FC<AgentHealthTabProps> = ({ agents, logs, onClearLogs }) => {
  const getAgentIcon = (id: string) => {
    switch (id) {
      case 'coordinator':
        return Cpu;
      case 'vision':
        return Eye;
      case 'graph':
        return Network;
      case 'simulation':
        return Flame;
      case 'planning':
        return Route;
      case 'report':
        return FileText;
      case 'spectator':
        return Radio;
      default:
        return Activity;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30';
      case 'BUSY':
        return 'bg-primary/10 text-primary border-primary/30 animate-pulse';
      case 'DEGRADED':
        return 'bg-amber-500/10 text-amber-500 border-amber-500/30';
      case 'OFFLINE':
        return 'bg-destructive/10 text-destructive border-destructive/30';
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  return (
    <div className="space-y-6">
      {/* Overview Header Banner */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold tracking-tight flex items-center gap-2 text-foreground">
            <ShieldCheck className="w-5 h-5 text-primary" />
            KRATOS Multi-Agent Ecosystem Sentinel
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            Real-time agent health, project roles, working execution tasks, and performance telemetry monitored by Agent Spectator.
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="bg-secondary px-3 py-2 rounded-lg border border-border flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span>
            <span>Agents Monitored: <strong className="text-foreground">{agents.length}</strong></span>
          </div>
          <div className="bg-secondary px-3 py-2 rounded-lg border border-border flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            <span>Avg Response: <strong className="text-foreground">18.2ms</strong></span>
          </div>
        </div>
      </div>

      {/* Agents Matrix Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => {
          const IconComponent = getAgentIcon(agent.id);

          return (
            <div
              key={agent.id}
              className="bg-card border border-border rounded-xl p-4 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                {/* Card Top: Icon, Name & Status */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-lg bg-primary/10 border border-primary/20 text-primary flex items-center justify-center shrink-0">
                      <IconComponent className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-foreground leading-tight">{agent.name}</h3>
                      <span className="text-[11px] font-mono text-muted-foreground">ID: {agent.id}</span>
                    </div>
                  </div>
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase shrink-0 ${getStatusBadge(
                      agent.status
                    )}`}
                  >
                    {agent.status}
                  </span>
                </div>

                {/* Purpose & Project Role */}
                <div className="space-y-2 mb-4">
                  <div className="bg-muted/40 p-2.5 rounded-lg border border-border/40 text-xs">
                    <span className="font-semibold text-foreground block mb-0.5">Purpose & Function:</span>
                    <p className="text-muted-foreground leading-relaxed">{agent.purpose}</p>
                  </div>

                  <div className="text-[11px] text-muted-foreground px-1">
                    <strong className="text-foreground">Project Role:</strong> {agent.role_in_project}
                  </div>
                </div>
              </div>

              {/* Card Footer: Current Work & Metrics */}
              <div className="border-t border-border pt-3 space-y-2">
                <div className="flex items-center justify-between text-xs font-mono bg-secondary/50 p-2 rounded border border-border/50">
                  <span className="text-muted-foreground flex items-center gap-1.5 truncate">
                    <Clock className="w-3.5 h-3.5 text-primary shrink-0" />
                    <span className="truncate">{agent.current_task}</span>
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center text-[11px] font-mono pt-1">
                  <div className="bg-muted/30 p-1.5 rounded border border-border/30">
                    <span className="text-muted-foreground block text-[9px]">PING</span>
                    <span className="font-bold text-emerald-500">{agent.ping_ms} ms</span>
                  </div>
                  <div className="bg-muted/30 p-1.5 rounded border border-border/30">
                    <span className="text-muted-foreground block text-[9px]">EXEC TIME</span>
                    <span className="font-bold text-cyan-400">{agent.inference_time_ms} ms</span>
                  </div>
                  <div className="bg-muted/30 p-1.5 rounded border border-border/30">
                    <span className="text-muted-foreground block text-[9px]">CONFIDENCE</span>
                    <span className="font-bold text-purple-400">{Math.round(agent.confidence_score * 100)}%</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Realtime Agent Log Terminal */}
      <div>
        <h3 className="text-sm font-bold text-foreground mb-2 tracking-wide uppercase flex items-center gap-2">
          <Activity className="w-4 h-4 text-primary" />
          Realtime Log Terminal Output
        </h3>
        <LogTerminal logs={logs} onClearLogs={onClearLogs} />
      </div>
    </div>
  );
};
