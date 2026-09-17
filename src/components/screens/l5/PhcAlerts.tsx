import React from 'react';
import { AlertTriangle, AlertOctagon, Flame, Clock } from 'lucide-react';
import { INITIAL_ALERTS } from '../../../data/mockAppData';

export const PhcAlerts: React.FC = () => {
  const facilityAlerts = (INITIAL_ALERTS || []).filter(
    (a) => a.facility?.includes('Ormanjhi') || a.type === 'COLD_CHAIN'
  );

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-10" id="phc-alerts-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-teal-400" />
          Ormanjhi PHC Critical Alerts & Action Items
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Active stock deficits, cold storage telemetry excursions, and incoming emergency transfers requiring immediate attention.
        </p>
      </div>

      <div className="space-y-4">
        {facilityAlerts.map((alert) => (
          <div
            key={alert.id}
            className="bg-slate-900 border border-red-900/40 rounded-xl p-5 space-y-2 shadow-sm"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-950 text-red-300 border border-red-800">
                  {alert.severity}
                </span>
                <span className="text-xs px-2 py-0.5 bg-slate-800 text-slate-300 rounded font-mono">
                  {alert.type}
                </span>
              </div>
              <span className="text-xs text-slate-500 font-mono">{alert.timestamp}</span>
            </div>

            <h2 className="text-sm font-bold text-slate-100 mt-1">{alert.title}</h2>
            <p className="text-xs text-slate-300 leading-relaxed">{alert.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
