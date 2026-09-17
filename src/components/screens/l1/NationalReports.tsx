import React from 'react';
import { FileBarChart, Download, Calendar, ArrowDownToLine, CheckCircle2 } from 'lucide-react';

export const NationalReports: React.FC = () => {
  const reports = [
    {
      id: 'rep-01',
      title: 'National Essential Drugs Consumption & Stock-Out Report',
      period: 'August - September 2026',
      size: '2.4 MB PDF',
      coverage: '36 States & UTs (16,190 Facilities)',
    },
    {
      id: 'rep-02',
      title: 'Inter-State Redistribution Impact & Cost Optimization Analysis',
      period: 'Q2 FY 2026-27',
      size: '1.8 MB PDF',
      coverage: '142 Inter-State Transfers',
    },
    {
      id: 'rep-03',
      title: 'Universal Cold Chain & Vaccine Viability Audit',
      period: 'Monthly Summary (September 2026)',
      size: '3.1 MB PDF',
      coverage: '100% Temperature Loggers',
    },
    {
      id: 'rep-04',
      title: 'Monsoon Disease Surge & Anti-Malarial Buffer Status',
      period: 'Active Epidemiological Window',
      size: '950 KB CSV Data',
      coverage: 'Eastern & Central Regional Clusters',
    },
  ];

  const handleDownload = (title: string) => {
    alert(`Generating export for: ${title}\nDownload initialized.`);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="national-reports-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <FileBarChart className="w-5 h-5 text-blue-400" />
          National Supply Chain Reports & Analytics
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Download monthly and quarterly national health supply chain audits, stock consumption trends, cold chain compliance logs, and redistribution cost savings.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {reports.map((r) => (
          <div key={r.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span className="flex items-center gap-1 font-mono">
                  <Calendar className="w-3.5 h-3.5 text-blue-400" />
                  {r.period}
                </span>
                <span className="text-slate-500">{r.size}</span>
              </div>
              <h2 className="text-sm font-bold text-slate-100 mt-1">{r.title}</h2>
              <p className="text-xs text-slate-400 mt-1">Coverage: {r.coverage}</p>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                type="button"
                onClick={() => handleDownload(r.title)}
                className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm"
              >
                <ArrowDownToLine className="w-3.5 h-3.5" />
                Download Report
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
