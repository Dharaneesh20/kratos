import React, { useState } from 'react';
import { Upload, Play, ShieldAlert, Sliders } from 'lucide-react';

interface UploadPanelProps {
  onRunWorkflow: (file: File | null, hazardType: str, severity: number) => void;
  isLoading: boolean;
}

const HAZARDS = [
  { id: 'FLOOD', label: 'Flood Inundation', color: 'border-blue-500/50 bg-blue-500/5' },
  { id: 'EARTHQUAKE', label: 'Seismic Shock', color: 'border-amber-500/50 bg-amber-500/5' },
  { id: 'BRIDGE_FAILURE', label: 'Bridge Collapse', color: 'border-purple-500/50 bg-purple-500/5' },
  { id: 'ROAD_CLOSURE', label: 'Arterial Closure', color: 'border-red-500/50 bg-red-500/5' },
];

export const UploadPanel: React.FC<UploadPanelProps> = ({ onRunWorkflow, isLoading }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [hazardType, setHazardType] = useState<string>('FLOOD');
  const [severity, setSeverity] = useState<number>(0.8);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onRunWorkflow(selectedFile, hazardType, severity);
  };

  return (
    <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-border">
        <ShieldAlert className="w-5 h-5 text-primary" />
        <h2 className="text-base font-bold">Disaster Simulation & Extraction Control</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Upload Satellite Image File */}
        <div>
          <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
            Satellite Tile Input (Optional)
          </label>
          <div className="border-2 border-dashed border-border hover:border-primary/50 rounded-lg p-4 text-center cursor-pointer transition-colors relative">
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
            />
            <Upload className="w-6 h-6 mx-auto mb-1.5 text-muted-foreground" />
            <p className="text-xs font-medium text-foreground">
              {selectedFile ? selectedFile.name : 'Click or drop satellite image tile (.png, .jpg, .tif)'}
            </p>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              {selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB` : 'Leave empty to run on high-resolution synthetic road network tile'}
            </p>
          </div>
        </div>

        {/* Hazard Selector */}
        <div>
          <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
            Select Disaster Hazard Preset
          </label>
          <div className="grid grid-cols-2 gap-2">
            {HAZARDS.map((h) => (
              <button
                type="button"
                key={h.id}
                onClick={() => setHazardType(h.id)}
                className={`p-2.5 rounded-lg border text-xs font-medium text-left transition-all ${
                  hazardType === h.id
                    ? 'border-primary ring-2 ring-primary/20 bg-primary/10 font-bold'
                    : 'border-border hover:bg-muted/40'
                }`}
              >
                {h.label}
              </button>
            ))}
          </div>
        </div>

        {/* Severity Slider */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-primary" /> Hazard Severity
            </label>
            <span className="text-xs font-mono font-bold text-primary">{Math.round(severity * 100)}%</span>
          </div>
          <input
            type="range"
            min="0.1"
            max="1.0"
            step="0.05"
            value={severity}
            onChange={(e) => setSeverity(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-3 px-4 bg-primary text-primary-foreground font-semibold rounded-lg shadow hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2 transition-all cursor-pointer text-sm"
        >
          {isLoading ? (
            <span>Executing Pipeline...</span>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>Run Multi-Agent Resilience Analysis</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};
