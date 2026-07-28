import React from 'react';
import { WorkflowStatus } from '../types';
import { CheckCircle2, Loader2, AlertCircle, Eye, Network, Flame, Route, FileText, Database } from 'lucide-react';

interface AgentMonitorProps {
  status: WorkflowStatus | null;
  isConnected: boolean;
}

const STAGES = [
  { id: 'DATASET', label: 'Dataset Ingestion', icon: Database, agent: 'coordinator' },
  { id: 'VISION', label: 'Vision SegFormer', icon: Eye, agent: 'vision' },
  { id: 'GRAPH', label: 'Graph Intelligence', icon: Network, agent: 'graph' },
  { id: 'SIMULATION', label: 'Disaster Stress', icon: Flame, agent: 'simulation' },
  { id: 'PLANNING', label: 'cuOpt Routing', icon: Route, agent: 'planning' },
  { id: 'REPORT', label: 'Report Generator', icon: FileText, agent: 'report' },
];

export const AgentMonitor: React.FC<AgentMonitorProps> = ({ status, isConnected }) => {
  const currentStage = status?.current_stage || 'INIT';
  const isFailed = status?.state === 'FAILED';

  const getStageStatus = (stageId: string) => {
    if (!status) return 'idle';
    if (isFailed) return currentStage === stageId ? 'failed' : 'idle';
    if (currentStage === 'DONE') return 'completed';

    const stageIndex = STAGES.findIndex((s) => s.id === stageId);
    const currentIndex = STAGES.findIndex((s) => s.id === currentStage);

    if (stageIndex < currentIndex) return 'completed';
    if (stageIndex === currentIndex) return 'running';
    return 'pending';
  };

  return (
    <div className="bg-card border border-border rounded-xl p-4 shadow-sm mb-6">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="relative flex h-3 w-3">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full ${
                isConnected ? 'bg-emerald-400' : 'bg-amber-400'
              } opacity-75`}
            ></span>
            <span
              className={`relative inline-flex rounded-full h-3 w-3 ${
                isConnected ? 'bg-emerald-500' : 'bg-amber-500'
              }`}
            ></span>
          </span>
          <h2 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">
            Multi-Agent Workflow Orchestrator
          </h2>
        </div>
        <div className="text-xs font-mono text-muted-foreground">
          {status?.workflow_id ? (
            <span className="bg-secondary px-2.5 py-1 rounded-md border border-border">
              ID: {status.workflow_id}
            </span>
          ) : (
            <span>Ready for Analysis</span>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {status && (
        <div className="w-full bg-muted h-2 rounded-full overflow-hidden mb-4">
          <div
            className={`h-full transition-all duration-500 ${
              isFailed ? 'bg-destructive' : 'bg-primary'
            }`}
            style={{ width: `${status.pct}%` }}
          />
        </div>
      )}

      {/* Stage Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
        {STAGES.map((s) => {
          const state = getStageStatus(s.id);
          const Icon = s.icon;

          return (
            <div
              key={s.id}
              className={`flex flex-col p-3 rounded-lg border text-xs transition-all ${
                state === 'running'
                  ? 'border-primary bg-primary/10 shadow-sm'
                  : state === 'completed'
                  ? 'border-emerald-500/30 bg-emerald-500/5'
                  : state === 'failed'
                  ? 'border-destructive bg-destructive/10'
                  : 'border-border/60 bg-muted/20 opacity-60'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <Icon
                  className={`w-4 h-4 ${
                    state === 'running'
                      ? 'text-primary'
                      : state === 'completed'
                      ? 'text-emerald-500'
                      : state === 'failed'
                      ? 'text-destructive'
                      : 'text-muted-foreground'
                  }`}
                />
                {state === 'running' && <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />}
                {state === 'completed' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />}
                {state === 'failed' && <AlertCircle className="w-3.5 h-3.5 text-destructive" />}
              </div>
              <span className="font-medium text-foreground truncate">{s.label}</span>
              <span className="text-[10px] text-muted-foreground capitalize mt-0.5">{state}</span>
            </div>
          );
        })}
      </div>

      {/* Live Log Footer */}
      {status?.logs && status.logs.length > 0 && (
        <div className="mt-3 pt-3 border-t border-border/40 text-xs font-mono text-muted-foreground flex items-center gap-2">
          <span className="text-primary font-bold">&gt;</span>
          <span className="truncate">{status.logs[status.logs.length - 1].message}</span>
        </div>
      )}
    </div>
  );
};
