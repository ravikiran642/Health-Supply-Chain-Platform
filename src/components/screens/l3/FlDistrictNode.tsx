import React from 'react';
import { Activity, Server, ShieldCheck, CheckCircle2 } from 'lucide-react';

export const FlDistrictNode: React.FC = () => {
  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="fl-district-node-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Activity className="w-5 h-5 text-amber-400" />
          Ranchi District Federated Edge Node Telemetry
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Telemetry, training loss, and gradient aggregation status for the district edge hardware node.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Node Status</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            ONLINE
          </div>
          <div className="text-xs text-slate-400 mt-1 font-mono">Heartbeat: 8s ago</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Local Validation Accuracy</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">92.4%</div>
          <div className="text-xs text-emerald-400 mt-1">+0.8% in Round #14</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Edge Hardware Load</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">18% CPU</div>
          <div className="text-xs text-slate-400 mt-1">RAM: 2.1 GB / 8.0 GB</div>
        </div>
      </div>
    </div>
  );
};
