import React from 'react';
import { SimulationData } from '../types';
import { Activity, Clock, ShieldCheck, MapPin } from 'lucide-react';

interface ResilienceGaugeProps {
  simulationData?: SimulationData;
}

export const ResilienceGauge: React.FC<ResilienceGaugeProps> = ({ simulationData }) => {
  const resilience = simulationData?.resilience ?? 1.0;
  const travelDelay = simulationData?.travel_delay ?? 0.0;
  const affectedRegions = simulationData?.affected_regions || [];

  const pct = Math.round(resilience * 100);
  const strokeDashoffset = 283 - (283 * pct) / 100;

  return (
    <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
      <div className="flex items-center gap-2 mb-4 pb-2 border-b border-border">
        <Activity className="w-5 h-5 text-primary" />
        <h3 className="text-sm font-bold tracking-wide uppercase">Resilience Index & Impact</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
        {/* SVG Radial Gauge */}
        <div className="flex flex-col items-center justify-center relative py-2">
          <svg className="w-32 h-32 transform -rotate-90">
            <circle
              cx="64"
              cy="64"
              r="45"
              className="stroke-muted"
              strokeWidth="10"
              fill="transparent"
            />
            <circle
              cx="64"
              cy="64"
              r="45"
              className="stroke-primary transition-all duration-1000 ease-out"
              strokeWidth="10"
              strokeDasharray="283"
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
            />
          </svg>
          <div className="absolute flex flex-col items-center justify-center">
            <span className="text-2xl font-extrabold font-mono text-foreground">{pct}%</span>
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">Resilience</span>
          </div>
        </div>

        {/* Impact Cards */}
        <div className="space-y-3">
          <div className="bg-secondary/40 border border-border rounded-lg p-3 flex items-center gap-3">
            <div className="p-2 rounded-md bg-destructive/10 text-destructive">
              <Clock className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[11px] font-semibold text-muted-foreground uppercase">Travel Delay Penalty</p>
              <p className="text-base font-bold font-mono text-destructive">+{travelDelay}%</p>
            </div>
          </div>

          <div className="bg-secondary/40 border border-border rounded-lg p-3 flex items-center gap-3">
            <div className="p-2 rounded-md bg-emerald-500/10 text-emerald-500">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[11px] font-semibold text-muted-foreground uppercase">System Status</p>
              <p className="text-xs font-bold text-foreground">
                {pct >= 80 ? 'HIGH OPERATIONAL' : pct >= 50 ? 'MODERATE DEGRADATION' : 'CRITICAL RESILIENCE FAILURE'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Affected Regions */}
      {affectedRegions.length > 0 && (
        <div className="mt-4 pt-3 border-t border-border">
          <p className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 text-primary" /> Damaged / Disconnected Sectors ({affectedRegions.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {affectedRegions.map((region, idx) => (
              <span key={idx} className="bg-muted text-muted-foreground text-[11px] px-2 py-0.5 rounded border border-border">
                {region}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
