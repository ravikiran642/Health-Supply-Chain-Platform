import React from 'react';
import { AlertOctagon, Flame, Clock, AlertTriangle } from 'lucide-react';
import { INITIAL_ALERTS } from '../../../data/mockAppData';

export const StateAlerts: React.FC = () => {
  const stateAlerts = (INITIAL_ALERTS || []).filter(
    (a) => a.state === 'Jharkhand' || a.district === 'Bokaro' || a.district === 'Ramgarh'
  );

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="state-alerts-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <AlertOctagon className="w-5 h-5 text-emerald-400" />
          State Supply Chain & Cold Chain Deviation Alerts
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Monitor district-level cold storage excursions, near-expiry drug batches, and buffer stock alerts across Jharkhand.
        </p>
      </div>

      <div className="space-y-4">
        {stateAlerts.map((alert) => (
          <div
            key={alert.id}
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 shadow-sm hover:border-slate-700"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-slate-800 border border-slate-700 text-amber-400 shrink-0">
                  <Flame className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-semibold border ${
                        alert.severity === 'CRITICAL'
                          ? 'bg-red-950/70 border-red-800 text-red-300'
                          : 'bg-amber-950/70 border-amber-800 text-amber-300'
                      }`}
                    >
                      {alert.severity}
                    </span>
                    <span className="text-xs px-2 py-0.5 bg-slate-800 text-slate-300 rounded font-mono">
                      {alert.type}
                    </span>
                    <span className="text-xs text-slate-400">
                      📍 {alert.district ? `${alert.district} District` : 'Statewide'}
                    </span>
                  </div>
                  <h2 className="text-sm font-bold text-slate-100 mt-2">{alert.title}</h2>
                  <p className="text-xs text-slate-300 mt-1 leading-relaxed">{alert.description}</p>
                </div>
              </div>
              <span className="text-xs text-slate-500 shrink-0">{alert.timestamp}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
