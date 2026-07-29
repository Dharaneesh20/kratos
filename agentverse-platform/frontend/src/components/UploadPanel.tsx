import React, { useState, useRef } from 'react';
import { Upload, ShieldAlert, Sliders, CloudLightning, Waves, GitMerge, AlertTriangle, X, File } from 'lucide-react';

interface UploadPanelProps {
  onRunWorkflow: (file: File | null, hazardType: string, severity: number) => void;
  isLoading: boolean;
}

const HAZARDS = [
  { id: 'FLOOD', label: 'Flood Inundation', icon: Waves, color: 'border-blue-500/40 bg-blue-500/10 text-blue-400', activeGlow: 'border-blue-500/70 bg-blue-500/20 ring-1 ring-blue-500/40 shadow-lg' },
  { id: 'EARTHQUAKE', label: 'Seismic Shock', icon: CloudLightning, color: 'border-amber-500/40 bg-amber-500/10 text-amber-400', activeGlow: 'border-amber-500/70 bg-amber-500/20 ring-1 ring-amber-500/40 shadow-lg' },
  { id: 'BRIDGE_FAILURE', label: 'Bridge Collapse', icon: GitMerge, color: 'border-purple-500/40 bg-purple-500/10 text-purple-400', activeGlow: 'border-purple-500/70 bg-purple-500/20 ring-1 ring-purple-500/40 shadow-lg' },
  { id: 'ROAD_CLOSURE', label: 'Arterial Closure', icon: AlertTriangle, color: 'border-rose-500/40 bg-rose-500/10 text-rose-400', activeGlow: 'border-rose-500/70 bg-rose-500/20 ring-1 ring-rose-500/40 shadow-lg' },
];

export const UploadPanel: React.FC<UploadPanelProps> = ({ onRunWorkflow, isLoading }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [hazardType, setHazardType] = useState('FLOOD');
  const [severity, setSeverity] = useState(0.8);
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (file: File | null) => {
    if (file) setSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) setSelectedFile(file);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onRunWorkflow(selectedFile, hazardType, severity);
  };

  const selectedHazard = HAZARDS.find((h) => h.id === hazardType);
  const HazardIcon = selectedHazard?.icon || ShieldAlert;

  return (
    <div className="glass-card p-5">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600/30 to-violet-900/20 border border-violet-500/30 flex items-center justify-center">
          <ShieldAlert className="w-[18px] h-[18px] text-violet-400" />
        </div>
        <div>
          <h2 className="text-sm font-bold text-white">Disaster Simulation Control</h2>
          <p className="text-[10px] text-muted-foreground">Upload satellite imagery & configure hazard parameters</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Satellite Image Upload */}
        <div>
          <label className="block text-[10px] font-semibold text-muted-foreground uppercase tracking-widest mb-2">
            Satellite Tile Input
          </label>
          <div
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onClick={() => inputRef.current?.click()}
            className={`relative border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all duration-300 ${
              isDragOver
                ? 'border-violet-500/70 bg-violet-500/10 scale-[1.01]'
                : selectedFile
                ? 'border-emerald-500/50 bg-emerald-500/8'
                : 'border-white/[0.1] hover:border-violet-500/50 hover:bg-violet-500/5'
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept="image/*,.tif,.tiff"
              onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
              className="hidden"
            />

            {selectedFile ? (
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center flex-shrink-0">
                    <File className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div className="text-left">
                    <p className="text-xs font-semibold text-white truncate max-w-[160px]">{selectedFile.name}</p>
                    <p className="text-[10px] text-emerald-400">{(selectedFile.size / 1024).toFixed(1)} KB · Ready</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                  className="w-6 h-6 rounded-lg bg-white/[0.06] hover:bg-rose-500/20 border border-white/10 flex items-center justify-center text-muted-foreground hover:text-rose-400 transition-all cursor-pointer"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ) : (
              <>
                <Upload className="w-6 h-6 mx-auto mb-2 text-muted-foreground" />
                <p className="text-xs font-medium text-foreground">Drop satellite image or click to browse</p>
                <p className="text-[10px] text-muted-foreground mt-1">PNG, JPG, GeoTIFF supported · Leave empty for synthetic tile</p>
              </>
            )}
          </div>
        </div>

        {/* Hazard Presets */}
        <div>
          <label className="block text-[10px] font-semibold text-muted-foreground uppercase tracking-widest mb-2">
            Disaster Hazard Preset
          </label>
          <div className="grid grid-cols-2 gap-2">
            {HAZARDS.map((h) => {
              const Icon = h.icon;
              const isActive = hazardType === h.id;
              return (
                <button
                  type="button"
                  key={h.id}
                  onClick={() => setHazardType(h.id)}
                  className={`p-3 rounded-xl border text-xs font-semibold text-left transition-all duration-200 cursor-pointer flex items-center gap-2 ${
                    isActive ? h.activeGlow : `${h.color} hover:opacity-80`
                  }`}
                >
                  <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                  <span>{h.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Severity Slider */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest flex items-center gap-1.5">
              <Sliders className="w-3 h-3" /> Hazard Severity
            </label>
            <span
              className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-violet-500/15 text-violet-300 border border-violet-500/30"
            >
              {Math.round(severity * 100)}%
            </span>
          </div>
          <input
            type="range"
            min="0.1"
            max="1.0"
            step="0.05"
            value={severity}
            onChange={(e) => setSeverity(parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-[9px] text-muted-foreground mt-1 font-mono">
            <span>LOW IMPACT</span>
            <span>CATASTROPHIC</span>
          </div>
        </div>

        {/* Launch Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-3.5 px-4 relative overflow-hidden rounded-xl text-sm font-bold text-white transition-all duration-300 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed group"
          style={{
            background: isLoading
              ? 'rgba(124, 58, 237, 0.3)'
              : 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 50%, #4c1d95 100%)',
            boxShadow: isLoading ? 'none' : '0 4px 24px rgba(124, 58, 237, 0.4)',
          }}
        >
          {/* shimmer animation on idle */}
          {!isLoading && (
            <span className="absolute inset-0 animate-shimmer opacity-50 group-hover:opacity-70 transition-opacity" />
          )}
          <span className="relative flex items-center justify-center gap-2">
            {isLoading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Executing Multi-Agent Pipeline...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 fill-white" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                Launch Resilience Analysis
              </>
            )}
          </span>
        </button>
      </form>
    </div>
  );
};
