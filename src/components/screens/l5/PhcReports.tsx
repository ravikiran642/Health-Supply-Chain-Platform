import React from 'react';
import { FileText, Download, Calendar, ArrowDownToLine } from 'lucide-react';

export const PhcReports: React.FC = () => {
  const reports = [
    {
      id: 'r1',
      title: 'Monthly Medicine Consumption & Wastage Register',
      period: 'August 2026',
      format: 'PDF (1.2 MB)',
    },
    {
      id: 'r2',
      title: 'Cold Chain Vaccine Temperature Logger (ILR-01)',
      period: 'Past 30 Days',
      format: 'CSV (320 KB)',
    },
    {
      id: 'r3',
      title: 'Inpatient Bed Occupancy & Length of Stay Summary',
      period: 'Past 14 Days',
      format: 'PDF (840 KB)',
    },
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-10" id="phc-reports-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <FileText className="w-5 h-5 text-teal-400" />
          PHC Registers & Compliance Reports
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Export facility-level inventory logs, cold chain temperature compliance records, and patient admission registers.
        </p>
      </div>

      <div className="space-y-3">
        {reports.map((r) => (
          <div
            key={r.id}
            className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between shadow-sm"
          >
            <div>
              <h2 className="text-sm font-bold text-slate-200">{r.title}</h2>
              <div className="text-xs text-slate-500 mt-0.5">
                Period: {r.period} • {r.format}
              </div>
            </div>
            <button
              type="button"
              onClick={() => alert(`Downloading ${r.title}`)}
              className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-teal-300 rounded text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-colors"
            >
              <ArrowDownToLine className="w-3.5 h-3.5 text-teal-400" />
              Download
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
