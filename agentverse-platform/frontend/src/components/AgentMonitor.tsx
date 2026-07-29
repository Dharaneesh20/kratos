import React from 'react';
import { WorkflowStatus } from '../types';
import {
  CheckCircle2, Loader2, AlertCircle, Eye, Network, Flame, Route,
  FileText, Database, GitCommit, BarChart3, Wrench, Radio, ChevronRight
} from 'lucide-react';

interface AgentMonitorProps {
  status: WorkflowStatus | null;
  isConnected: boolean;
}

const STAGES = [
  { id: 'DATASET', label: 'Dataset', icon: Database },
  { id: 'VISION', label: 'Vision', icon: Eye },
  { id: 'SKELETON', label: 'Skeleton', icon: GitCommit },
  { id: 'GRAPH', label: 'Graph', icon: Network },
  { id: 'CENTRALITY', label: 'Centrality', icon: BarChart3 },
  { id: 'SIMULATION', label: 'Simulation', icon: Flame },
  { id: 'PLANNING', label: 'Planning', icon: Route },
  { id: 'REPAIR', label: 'Repair', icon: Wrench },
  { id: 'REPORT', label: 'Report', icon: FileText },
  { id: 'SPECTATOR', label: 'Spectator', icon: Radio },
];

export const AgentMonitor: React.FC<AgentMonitorProps> = ({ status, isConnected }) => {
  const currentStage = status?.current_stage || 'INIT';
  const isFailed = status?.state === 'FAILED';

  const getStageStatus = (stageId: string) => {
    if (!status) return 'idle';
    if (isFailed && currentStage === stageId) return 'failed';
    if (currentStage === 'DONE') return 'completed';
    const si = STAGES.findIndex((s) => s.id === stageId);
    const ci = STAGES.findIndex((s) => s.id === currentStage);
    if (si < ci) return 'completed';
    if (si === ci) return 'running';
    return 'pending';
  };

  const pct = status?.pct || 0;

  return (
    <div className="glass-card p-4 mb-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isConnected ? 'bg-emerald-400' : 'bg-rose-400'}`} />
            <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isConnected ? 'bg-emerald-500' : 'bg-rose-500'}`} />
          </span>
          <h2 className="text-xs font-bold tracking-widest text-muted-foreground uppercase">
            KRATOS Multi-Agent Workflow Pipeline
          </h2>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono">
          {status?.state === 'COMPLETED' && (
            <span className="flex items-center gap-1 text-emerald-400 font-bold">
              <CheckCircle2 className="w-3 h-3" /> COMPLETED
            </span>
          )}
          {status?.state === 'FAILED' && (
            <span className="flex items-center gap-1 text-rose-400 font-bold">
              <AlertCircle className="w-3 h-3" /> FAILED
            </span>
          )}
          {status?.workflow_id && (
            <span className="text-muted-foreground bg-white/[0.04] border border-white/[0.08] px-2 py-0.5 rounded-lg">
              #{status.workflow_id.slice(-8)}
            </span>
          )}
          {!status && (
            <span className="text-muted-foreground">Ready for analysis</span>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="progress-bar mb-4">
        <div
          className="progress-bar-fill"
          style={{
            width: `${pct}%`,
            background: isFailed
              ? 'linear-gradient(90deg, #f43f5e, #be123c)'
              : 'linear-gradient(90deg, #7c3aed, #06b6d4)',
          }}
        />
      </div>

      {/* Stage Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {STAGES.map((s, idx) => {
          const state = getStageStatus(s.id);
          const Icon = s.icon;
          return (
            <React.Fragment key={s.id}>
              <div
                className={`flex-shrink-0 flex flex-col items-center gap-1 px-2.5 py-2 rounded-xl border text-[10px] font-medium transition-all duration-300 ${
                  state === 'running'
                    ? 'border-violet-500/70 bg-violet-500/15 text-violet-300 shadow-lg'
                    : state === 'completed'
                    ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400'
                    : state === 'failed'
                    ? 'border-rose-500/40 bg-rose-500/10 text-rose-400'
                    : 'border-white/[0.06] bg-white/[0.02] text-muted-foreground opacity-60'
                }`}
              >
                <div className="flex items-center gap-1">
                  <Icon className="w-3 h-3" />
                  {state === 'running' && <Loader2 className="w-2.5 h-2.5 animate-spin" />}
                  {state === 'completed' && <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />}
                  {state === 'failed' && <AlertCircle className="w-2.5 h-2.5 text-rose-400" />}
                </div>
                <span>{s.label}</span>
              </div>
              {idx < STAGES.length - 1 && (
                <ChevronRight className="w-3 h-3 text-muted-foreground/40 flex-shrink-0" />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Last log message */}
      {status?.logs && status.logs.length > 0 && (
        <div className="mt-3 pt-3 border-t border-white/[0.05] text-[10px] font-mono text-muted-foreground flex items-center gap-2">
          <span className="text-violet-400 font-bold">›</span>
          <span className="truncate">{status.logs[status.logs.length - 1].message}</span>
        </div>
      )}
    </div>
  );
};
