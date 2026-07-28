import React from 'react';
import { PlanningData } from '../types';
import { Navigation, Wrench, Shield, CheckCircle } from 'lucide-react';

interface RoutePanelProps {
  planningData?: PlanningData;
}

export const RoutePanel: React.FC<RoutePanelProps> = ({ planningData }) => {
  const routes = planningData?.evacuation_routes || [];
  const repairs = planningData?.repair_priority || [];
  const recommendations = planningData?.recommendations || [];

  return (
    <div className="bg-card border border-border rounded-xl p-4 shadow-sm h-[260px] overflow-y-auto space-y-4">
      {/* Evacuation Routes Section */}
      <div>
        <div className="flex items-center justify-between mb-2 pb-1.5 border-b border-border">
          <div className="flex items-center gap-2">
            <Navigation className="w-4 h-4 text-primary" />
            <h3 className="text-xs font-bold tracking-wide uppercase">cuOpt Evacuation Routes ({routes.length})</h3>
          </div>
          <span className="text-[10px] font-mono text-muted-foreground">GPU Accelerated</span>
        </div>

        {routes.length === 0 ? (
          <p className="text-xs text-muted-foreground italic py-1">No active evacuation routes calculated yet. Run pipeline to compute optimal vectors.</p>
        ) : (
          <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
            {routes.map((r) => (
              <div key={r.route_id} className="p-3 bg-secondary/30 rounded-lg border border-border flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs font-mono bg-primary/20 text-primary px-2 py-0.5 rounded">
                      {r.route_id}
                    </span>
                    <span className="text-xs font-medium text-foreground">
                      Node {r.from_node} &rarr; Node {r.to_node}
                    </span>
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-1">
                    Vehicle: <span className="capitalize font-semibold text-foreground">{r.vehicle}</span> | Path length: {r.path_nodes.length} hops
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold font-mono text-emerald-500">{r.eta_min} min</span>
                  <p className="text-[10px] text-muted-foreground uppercase">Estimated ETA</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Repair Priorities Section */}
      <div>
        <div className="flex items-center gap-2 mb-2 pb-1.5 border-b border-border">
          <Wrench className="w-4 h-4 text-amber-500" />
          <h3 className="text-xs font-bold tracking-wide uppercase">Critical Node Repair Priorities</h3>
        </div>

        {repairs.length === 0 ? (
          <p className="text-xs text-muted-foreground italic py-2">No repair priorities generated.</p>
        ) : (
          <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
            {repairs.map((rp) => (
              <div key={rp.node_id} className="p-2.5 bg-secondary/30 rounded-lg border border-border flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-500 font-bold text-xs flex items-center justify-center shrink-0">
                  {rp.priority}
                </span>
                <div>
                  <p className="text-xs font-bold text-foreground">Node {rp.node_id}</p>
                  <p className="text-[11px] text-muted-foreground mt-0.5">{rp.reason}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actionable Recommendations */}
      {recommendations.length > 0 && (
        <div className="pt-3 border-t border-border">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-4 h-4 text-primary" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Strategic Recommendations</h4>
          </div>
          <ul className="space-y-1.5 text-xs text-foreground">
            {recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" />
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
