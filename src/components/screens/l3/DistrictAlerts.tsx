import React from 'react';
import { Bell, AlertTriangle, Flame, Clock } from 'lucide-react';
import { INITIAL_ALERTS } from '../../../data/mockAppData';

export const DistrictAlerts: React.FC = () => {
  const districtAlerts = (INITIAL_ALERTS || []).filter((a) => a.district === 'Ranchi');

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="district-alerts-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Bell className="w-5 h-5 text-amber-400" />
          Ranchi District PHC Incident & Stock Alerts
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Stock-outs, cold chain deviations, and staff absences requiring district health office intervention.
        </p>
      </div>

      <div className="space-y-4">
        {districtAlerts.map((alert) => (
          <div key={alert.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2 shadow-sm">
            <div className="flex items-start justify-between">
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
                <span className="text-xs text-amber-400 font-medium">📍 {alert.facility}</span>
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
