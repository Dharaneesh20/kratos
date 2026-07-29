import React from 'react';
import { PlanningData } from '../types';
import { Navigation, Wrench, Shield, CheckCircle2, Clock, ArrowRight } from 'lucide-react';

interface RoutePanelProps {
  planningData?: PlanningData;
}

const ROUTE_COLORS = ['text-emerald-400', 'text-cyan-400', 'text-blue-400', 'text-rose-400', 'text-purple-400'];

export const RoutePanel: React.FC<RoutePanelProps> = ({ planningData }) => {
  const routes = planningData?.evacuation_routes || [];
  const repairs = planningData?.repair_priority || [];
  const recommendations = planningData?.recommendations || [];

  return (
    <div className="glass-card p-5 space-y-5 max-h-[300px] overflow-y-auto">
      {/* Evacuation Routes */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Navigation className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Evacuation Routes <span className="text-muted-foreground font-normal">({routes.length})</span>
            </h3>
          </div>
          <span className="text-[9px] font-mono text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-1.5 py-0.5 rounded">
            cuOpt Optimized
          </span>
        </div>

        {routes.length === 0 ? (
          <p className="text-[11px] text-muted-foreground italic py-2">
            No routes calculated. Run the pipeline to compute optimal evacuation vectors.
          </p>
        ) : (
          <div className="space-y-2">
            {routes.map((r, idx) => (
              <div key={r.route_id} className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/[0.07] hover:border-emerald-500/30 transition-all">
                <div className="flex items-center gap-2.5">
                  <div className="w-6 h-6 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center flex-shrink-0">
                    <Navigation className={`w-3 h-3 ${ROUTE_COLORS[idx % ROUTE_COLORS.length]}`} />
                  </div>
                  <div>
                    <span className={`text-[10px] font-mono font-bold ${ROUTE_COLORS[idx % ROUTE_COLORS.length]}`}>
                      {r.route_id}
                    </span>
                    <p className="text-[10px] text-muted-foreground">
                      {r.from_node} <ArrowRight className="w-2.5 h-2.5 inline" /> {r.to_node} · {r.path_nodes.length} hops
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold font-mono text-emerald-400">{r.eta_min}m</span>
                  <p className="text-[9px] text-muted-foreground uppercase">ETA</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Repair Priorities */}
      {repairs.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Wrench className="w-4 h-4 text-amber-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Repair Priorities <span className="text-muted-foreground font-normal">({repairs.length})</span>
            </h3>
          </div>
          <div className="space-y-2">
            {repairs.slice(0, 5).map((rp) => (
              <div key={rp.node_id} className="flex items-start gap-2.5 p-2.5 rounded-xl bg-amber-500/5 border border-amber-500/15 hover:border-amber-500/30 transition-all">
                <span className="w-5 h-5 rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-400 font-bold text-[9px] flex items-center justify-center flex-shrink-0 mt-0.5">
                  {rp.priority}
                </span>
                <div>
                  <p className="text-[11px] font-bold text-white">Node {rp.node_id}</p>
                  <p className="text-[10px] text-muted-foreground">{rp.reason}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="pt-3 border-t border-white/[0.06]">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-3.5 h-3.5 text-violet-400" />
            <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Strategic Recommendations</h4>
          </div>
          <ul className="space-y-1.5">
            {recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-1.5 text-[11px] text-foreground">
                <CheckCircle2 className="w-3 h-3 text-emerald-400 mt-0.5 flex-shrink-0" />
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
