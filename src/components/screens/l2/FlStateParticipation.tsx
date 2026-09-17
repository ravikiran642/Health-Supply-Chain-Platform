import React from 'react';
import { Layers, Activity, CheckCircle2, ShieldCheck } from 'lucide-react';

export const FlStateParticipation: React.FC = () => {
  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="fl-state-participation-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Layers className="w-5 h-5 text-emerald-400" />
          Jharkhand State FL Cluster Contribution
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Telemetry of the Jharkhand State Federated Learning edge aggregator, local gradient submissions, and privacy validation.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Local State Model Accuracy</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">93.8%</div>
          <div className="text-xs text-slate-400 mt-1">Evaluated on 42,000 local test rows</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Connected District Nodes</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">4 / 4 Online</div>
          <div className="text-xs text-emerald-400 mt-1">100% active district participation</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Next Scheduled Round</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">Round #15</div>
          <div className="text-xs text-slate-400 mt-1">Tomorrow, 06:00 AM IST</div>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-xs text-slate-400 space-y-2">
        <div className="flex items-center gap-2 text-slate-200 font-semibold text-sm">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Differential Privacy Guarantee
        </div>
        <p>
          Model updates sent from Jharkhand district nodes undergo local Gaussian noise addition (epsilon = 1.2) before leaving the state boundary. Raw patient prescriptions and PHC facility records remain completely decentralized within the district.
        </p>
      </div>
    </div>
  );
};
