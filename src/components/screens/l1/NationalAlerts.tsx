import React from 'react';
import { AlertTriangle, AlertOctagon, Flame, ShieldAlert, CheckCircle2, Globe } from 'lucide-react';
import { INITIAL_ALERTS } from '../../../data/mockAppData';

export const NationalAlerts: React.FC = () => {
  const nationalAlerts = (INITIAL_ALERTS || []).filter(
    (a) => a.state === 'National' || a.state?.includes('Bihar') || a.type === 'OUTBREAK_SIGNAL'
  );

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="national-alerts-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          National Supply Chain & Outbreak Early Warnings
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          High-priority surveillance alerts aggregated across state health clusters including epidemic spikes, national stock deficits, and emergency redistribution signals.
        </p>
      </div>

      <div className="space-y-4">
        {nationalAlerts.map((alert) => (
          <div
            key={alert.id}
            className="bg-slate-900 border border-red-900/40 rounded-xl p-6 space-y-3 relative overflow-hidden shadow-sm"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="p-2.5 rounded-lg bg-red-950/80 border border-red-800 text-red-400 shrink-0">
                  <AlertOctagon className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-red-950 text-red-300 border border-red-800">
                      {alert.severity}
                    </span>
                    <span className="text-xs px-2 py-0.5 bg-slate-800 text-slate-300 rounded font-mono">
                      {alert.type}
                    </span>
                    <span className="text-xs text-slate-400 font-medium">📍 {alert.state}</span>
                  </div>
                  <h2 className="text-base font-bold text-slate-100 mt-2">{alert.title}</h2>
                  <p className="text-sm text-slate-300 mt-1 leading-relaxed">{alert.description}</p>
                </div>
              </div>
              <span className="text-xs text-slate-500 shrink-0">{alert.timestamp}</span>
            </div>

            <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
              <div className="text-xs text-slate-400">
                Recommended Action: <span className="text-slate-200 font-medium">Dispatch inter-state vector control medicine buffers</span>
              </div>
              <button
                type="button"
                onClick={() => window.alert('Official advisory dispatched to state principal secretaries.')}
                className="px-3.5 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded text-xs font-semibold transition-colors"
              >
                Dispatch National Advisory
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
