import React from 'react';
import { ReportData } from '../types';
import { FileText, Download, Table, CheckCircle2 } from 'lucide-react';

interface ReportViewerProps {
  reportData?: ReportData;
  workflowId?: string;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({ reportData, workflowId }) => {
  if (!reportData) {
    return (
      <div className="bg-card border border-border rounded-xl p-5 shadow-sm text-center py-8">
        <FileText className="w-8 h-8 text-muted-foreground mx-auto mb-2 opacity-50" />
        <h3 className="text-sm font-bold text-foreground">Disaster Intelligence Report</h3>
        <p className="text-xs text-muted-foreground mt-1">Run an analysis to generate downloadable PDF and CSV reports.</p>
      </div>
    );
  }

  const pdfUrl = reportData.pdf_url || (workflowId ? `/reports/disaster_report_${workflowId}.pdf` : '#');
  const csvUrl = reportData.csv_url || (workflowId ? `/reports/critical_nodes_${workflowId}.csv` : '#');

  return (
    <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary" />
          <h3 className="text-sm font-bold tracking-wide uppercase">ReportLab Executive Disaster Report</h3>
        </div>
        <div className="flex items-center gap-2">
          <a
            href={csvUrl}
            download
            className="px-3 py-1.5 bg-secondary text-secondary-foreground hover:bg-secondary/80 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors border border-border"
          >
            <Table className="w-3.5 h-3.5" /> CSV Data
          </a>
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 bg-primary text-primary-foreground hover:opacity-90 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-opacity"
          >
            <Download className="w-3.5 h-3.5" /> Download PDF Report
          </a>
        </div>
      </div>

      {reportData.executive_summary && (
        <div className="bg-secondary/30 border border-border p-3.5 rounded-lg text-xs text-foreground space-y-2">
          <p className="font-bold text-primary flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Executive Briefing
          </p>
          <p className="leading-relaxed" dangerouslySetInnerHTML={{ __html: reportData.executive_summary }} />
        </div>
      )}

      {reportData.recommendations && reportData.recommendations.length > 0 && (
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">Government Action Directives</h4>
          <div className="space-y-1.5 text-xs text-foreground">
            {reportData.recommendations.map((rec, i) => (
              <div key={i} className="p-2 bg-muted/40 rounded border border-border/60">
                • {rec}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
