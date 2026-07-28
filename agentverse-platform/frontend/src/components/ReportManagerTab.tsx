import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ReportMetadata } from '../types';
import { FileText, Download, Plus, RefreshCw, FileSpreadsheet, AlertCircle, CheckCircle2, Clock } from 'lucide-react';

export const ReportManagerTab: React.FC = () => {
  const [reports, setReports] = useState<ReportMetadata[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  const fetchReports = async () => {
    setIsLoading(true);
    try {
      const resp = await axios.get('/api/report/list');
      setReports(resp.data);
    } catch (err) {
      console.error("Failed to fetch report list:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGenerateReport = async () => {
    setIsGenerating(true);
    try {
      await axios.post('/api/report/generate', {
        hazard_type: 'FLOOD',
      });
      await fetchReports();
    } catch (err) {
      console.error("Failed to generate report:", err);
      alert("Report generation failed. Ensure backend service is active.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold tracking-tight flex items-center gap-2 text-foreground">
            <FileText className="w-5 h-5 text-primary" />
            KRATOS Report Server & Periodic Intelligence Generator
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            Automated PDF/CSV report builder powered by Report Agent. Download executive summaries, route plans, and critical node assessments.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchReports}
            className="p-2 rounded-lg border border-border bg-secondary hover:bg-muted transition-colors cursor-pointer text-xs font-medium flex items-center gap-1.5"
            title="Refresh Report List"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleGenerateReport}
            disabled={isGenerating}
            className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold text-xs shadow-md hover:bg-primary/90 transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            <span>{isGenerating ? 'Generating PDF...' : 'Generate New Report'}</span>
          </button>
        </div>
      </div>

      {/* Report Archive List */}
      <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-border bg-muted/30 flex items-center justify-between">
          <h3 className="text-sm font-bold text-foreground tracking-wide uppercase flex items-center gap-2">
            <FileText className="w-4 h-4 text-primary" />
            Report Server Archive ({reports.length})
          </h3>
          <span className="text-xs font-mono text-muted-foreground">PDF & CSV Outputs</span>
        </div>

        {reports.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground space-y-3">
            <FileText className="w-10 h-10 mx-auto opacity-30 text-primary" />
            <p className="text-sm font-medium">No reports generated yet on the server.</p>
            <p className="text-xs">Click "Generate New Report" or run a disaster workflow to generate PDF & CSV files.</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {reports.map((rep) => (
              <div
                key={rep.report_id}
                className="p-4 hover:bg-muted/20 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-foreground text-sm">
                      Disaster Resilience Report ({rep.hazard_type})
                    </span>
                    <span className="text-[10px] font-mono bg-secondary px-2 py-0.5 rounded border border-border">
                      ID: {rep.report_id}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-xs font-mono text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-primary" />
                      {rep.created_at}
                    </span>
                    <span>Resilience: <strong className="text-emerald-500">{Math.round(rep.resilience_score * 100)}%</strong></span>
                    <span>Travel Delay: <strong className="text-amber-400">+{rep.travel_delay}%</strong></span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {rep.pdf_url && (
                    <a
                      href={rep.pdf_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 rounded-lg border border-primary/40 bg-primary/10 text-primary font-medium text-xs hover:bg-primary/20 transition-colors flex items-center gap-1.5"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download PDF</span>
                    </a>
                  )}

                  {rep.csv_url && (
                    <a
                      href={rep.csv_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 rounded-lg border border-emerald-500/40 bg-emerald-500/10 text-emerald-500 font-medium text-xs hover:bg-emerald-500/20 transition-colors flex items-center gap-1.5"
                    >
                      <FileSpreadsheet className="w-3.5 h-3.5" />
                      <span>Export CSV</span>
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
