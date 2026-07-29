import React from 'react';
import { SimulationData } from '../types';
import { Activity, Clock, ShieldCheck, MapPin, TrendingDown } from 'lucide-react';

interface ResilienceGaugeProps {
  simulationData?: SimulationData;
}

export const ResilienceGauge: React.FC<ResilienceGaugeProps> = ({ simulationData }) => {
  const resilience = simulationData?.resilience ?? null;
  const travelDelay = simulationData?.travel_delay ?? null;
  const affectedRegions = simulationData?.affected_regions || [];

  const pct = resilience !== null ? Math.round(resilience * 100) : 0;
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = resilience !== null
    ? circumference - (circumference * pct) / 100
    : circumference;

  const gaugeColor =
    resilience === null
      ? '#374151'
      : pct >= 80
      ? '#10b981'
      : pct >= 50
      ? '#f59e0b'
      : '#f43f5e';

  const statusLabel =
    resilience === null
      ? 'Awaiting Analysis'
      : pct >= 80
      ? 'HIGH OPERATIONAL'
      : pct >= 50
      ? 'MODERATE DEGRADATION'
      : 'CRITICAL FAILURE';

  return (
    <div className="glass-card p-5">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-4">
        <div className="w-8 h-8 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
          <Activity className="w-4 h-4 text-cyan-400" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white">Resilience Index</h3>
          <p className="text-[10px] text-muted-foreground">Disaster impact & network survivability</p>
        </div>
      </div>

      <div className="flex items-center gap-5">
        {/* SVG Radial Gauge */}
        <div className="relative flex-shrink-0" style={{ width: 110, height: 110 }}>
          <svg width="110" height="110" className="transform -rotate-90">
            <circle
              cx="55" cy="55" r="45"
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="10"
              fill="transparent"
            />
            <circle
              cx="55" cy="55" r="45"
              stroke={gaugeColor}
              strokeWidth="10"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              style={{ transition: 'stroke-dashoffset 1s ease, stroke 0.5s ease' }}
            />
          </svg>
          {/* Glow effect */}
          <div
            className="absolute inset-0 rounded-full"
            style={{
              boxShadow: resilience !== null ? `0 0 20px ${gaugeColor}40` : 'none',
              borderRadius: '50%',
            }}
          />
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-xl font-extrabold font-mono text-white">
              {resilience !== null ? `${pct}%` : '—'}
            </span>
            <span className="text-[9px] uppercase tracking-widest text-muted-foreground">Resilience</span>
          </div>
        </div>

        {/* Stats */}
        <div className="flex-1 space-y-2">
          {travelDelay !== null && (
            <div className="flex items-center gap-2.5 bg-rose-500/8 border border-rose-500/20 rounded-xl p-2.5">
              <TrendingDown className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
              <div>
                <p className="text-[9px] text-muted-foreground uppercase tracking-wide">Travel Delay</p>
                <p className="text-sm font-bold font-mono text-rose-400">+{travelDelay.toFixed(1)}%</p>
              </div>
            </div>
          )}

          <div
            className="flex items-center gap-2.5 rounded-xl p-2.5 border"
            style={{
              borderColor: `${gaugeColor}30`,
              background: `${gaugeColor}08`,
            }}
          >
            <ShieldCheck className="w-3.5 h-3.5 flex-shrink-0" style={{ color: gaugeColor }} />
            <div>
              <p className="text-[9px] text-muted-foreground uppercase tracking-wide">System Status</p>
              <p className="text-xs font-bold" style={{ color: gaugeColor }}>{statusLabel}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Affected Regions */}
      {affectedRegions.length > 0 && (
        <div className="mt-4 pt-3 border-t border-white/[0.06]">
          <p className="text-[10px] font-semibold text-muted-foreground mb-2 flex items-center gap-1.5">
            <MapPin className="w-3 h-3 text-rose-400" />
            Affected Sectors ({affectedRegions.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {affectedRegions.map((region, idx) => (
              <span
                key={idx}
                className="text-[9px] px-2 py-1 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/20"
              >
                {region}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
