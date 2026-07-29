import React, { useState, useEffect, useRef } from 'react';
import { AgentLogEntry } from '../types';
import { Terminal, Filter, RefreshCw, Trash2, ArrowDownCircle, Search } from 'lucide-react';

interface LogTerminalProps {
  logs: AgentLogEntry[];
  onClearLogs?: () => void;
}

export const LogTerminal: React.FC<LogTerminalProps> = ({ logs, onClearLogs }) => {
  const [selectedAgent, setSelectedAgent] = useState<string>('all');
  const [selectedLevel, setSelectedLevel] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  const filteredLogs = logs.filter((log) => {
    const matchesAgent = selectedAgent === 'all' || log.agent === selectedAgent;
    const matchesLevel = selectedLevel === 'all' || log.level === selectedLevel;
    const matchesSearch =
      !searchQuery ||
      log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.agent.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesAgent && matchesLevel && matchesSearch;
  });

  useEffect(() => {
    if (autoScroll && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'text-rose-400 bg-rose-950/50 border-rose-800/40';
      case 'WARNING':
        return 'text-amber-300 bg-amber-950/50 border-amber-800/40';
      case 'SUCCESS':
        return 'text-emerald-400 bg-emerald-950/50 border-emerald-800/40';
      default:
        return 'text-cyan-400 bg-cyan-950/40 border-cyan-800/30';
    }
  };

  const getAgentBadgeColor = (agent: string) => {
    switch (agent) {
      case 'coordinator':
        return 'text-indigo-300 bg-indigo-950/60 border-indigo-700/50';
      case 'vision':
        return 'text-purple-300 bg-purple-950/60 border-purple-700/50';
      case 'graph':
        return 'text-blue-300 bg-blue-950/60 border-blue-700/50';
      case 'simulation':
        return 'text-amber-300 bg-amber-950/60 border-amber-700/50';
      case 'planning':
        return 'text-emerald-300 bg-emerald-950/60 border-emerald-700/50';
      case 'report':
        return 'text-pink-300 bg-pink-950/60 border-pink-700/50';
      case 'spectator':
        return 'text-teal-300 bg-teal-950/60 border-teal-700/50';
      default:
        return 'text-slate-300 bg-slate-800 border-slate-700';
    }
  };

  return (
    <div className="glass-card overflow-hidden flex flex-col h-[480px]">
      {/* Terminal Header Bar */}
      <div className="px-4 py-3 border-b border-white/[0.06] bg-white/[0.02] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
            KRATOS Spectator Live Log Stream
          </span>
          <span className="text-[9px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 px-2 py-0.5 rounded-full flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            LIVE ({filteredLogs.length})
          </span>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Search box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-2.5 top-1.5" />
            <input
              type="text"
              placeholder="Search logs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-white/[0.03] border border-white/[0.08] text-foreground text-xs rounded-lg pl-8 pr-2.5 py-1.5 font-mono focus:outline-none focus:border-violet-500/50 w-36 sm:w-44"
            />
          </div>

          {/* Agent Filter */}
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="bg-white/[0.03] border border-white/[0.08] text-foreground text-xs rounded-lg px-2 py-1.5 font-mono focus:outline-none focus:border-violet-500/50 cursor-pointer"
          >
            <option value="all">All Agents</option>
            <option value="coordinator">Coordinator</option>
            <option value="dataset">Dataset Ingestion</option>
            <option value="vision">Vision SegFormer</option>
            <option value="skeletonizer">Skeletonizer</option>
            <option value="graph">Graph Intel</option>
            <option value="centrality">Centrality Matrix</option>
            <option value="simulation">Disaster Stress</option>
            <option value="planning">cuOpt Planner</option>
            <option value="repair">Repair Ranker</option>
            <option value="report">Report Agent</option>
            <option value="spectator">Spectator Agent</option>
          </select>

          {/* Auto-scroll toggle */}
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`p-1.5 rounded-lg border text-xs font-mono flex items-center gap-1 transition-colors cursor-pointer ${
              autoScroll
                ? 'bg-violet-500/15 border-violet-500/30 text-violet-400'
                : 'bg-white/[0.03] border-white/[0.08] text-muted-foreground hover:text-foreground'
            }`}
            title="Toggle Auto Scroll"
          >
            <ArrowDownCircle className="w-3.5 h-3.5" />
          </button>

          {/* Clear button */}
          {onClearLogs && (
            <button
              onClick={onClearLogs}
              className="p-1.5 rounded-lg border border-white/[0.08] bg-white/[0.03] text-muted-foreground hover:text-rose-400 hover:border-rose-500/30 transition-colors cursor-pointer"
              title="Clear Logs"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Terminal Content Stream */}
      <div className="flex-1 p-4 font-mono text-xs overflow-y-auto space-y-1.5 bg-white/[0.01] selection:bg-violet-900 selection:text-white">
        {filteredLogs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-muted-foreground text-center py-12">
            <Terminal className="w-8 h-8 mb-2 opacity-30" />
            <p>No log messages matching current filter criteria.</p>
          </div>
        ) : (
          filteredLogs.map((log) => (
            <div
              key={log.id}
              className="flex flex-col sm:flex-row sm:items-start gap-1.5 sm:gap-3 p-1.5 rounded-lg hover:bg-white/[0.03] transition-colors border border-transparent hover:border-white/[0.05]"
            >
              {/* Time & Badge */}
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-[11px] text-muted-foreground">{log.timestamp}</span>
                <span
                  className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded border ${getAgentBadgeColor(
                    log.agent
                  )}`}
                >
                  {log.agent}
                </span>
                <span
                  className={`text-[9px] uppercase font-semibold px-1 py-0.5 rounded border ${getLevelColor(
                    log.level
                  )}`}
                >
                  {log.level}
                </span>
              </div>

              {/* Message */}
              <div className="text-foreground/90 leading-relaxed break-all">
                <span className="text-violet-400 font-bold mr-1.5">›</span>
                {log.message}
              </div>
            </div>
          ))
        )}
        <div ref={terminalEndRef} />
      </div>
    </div>
  );
};
