import React from 'react';
import { BrainCircuit, Activity, Globe, CheckCircle2, TrendingUp, Layers } from 'lucide-react';
import { INITIAL_FL_ROUNDS } from '../../../data/mockAppData';

export const FlGlobalOverview: React.FC = () => {
  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="fl-global-overview-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <BrainCircuit className="w-5 h-5 text-blue-400" />
          Global Federated Model Status & Accuracy
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          National overview of AI demand prediction model accuracy, privacy-preserving federated aggregation rounds, and participating states.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Global Forecast Accuracy</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">93.4%</div>
          <div className="text-xs text-emerald-500 mt-1">±1.8% RMSE error margin</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Active Aggregation Round</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">Round #14</div>
          <div className="text-xs text-slate-400 mt-1">FedAvg with secure DP-SGD</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Participating State Clusters</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">28 / 32 Nodes</div>
          <div className="text-xs text-slate-400 mt-1">87.5% consensus reached</div>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-sm font-semibold text-slate-200">Global Model Checkpoints</h2>
        <div className="divide-y divide-slate-800">
          {INITIAL_FL_ROUNDS.map((r) => (
            <div key={r.roundNumber} className="py-3 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <span className="font-bold text-slate-100">Round #{r.roundNumber}</span>
                <span className="px-2 py-0.5 rounded text-[11px] bg-emerald-950/60 text-emerald-400 border border-emerald-800">
                  {r.status}
                </span>
                <span className="text-slate-400">Nodes: {r.participatingNodes}</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="font-mono font-bold text-emerald-400">{r.globalAccuracy}% accuracy</span>
                <span className="text-slate-500">{r.startTime}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
