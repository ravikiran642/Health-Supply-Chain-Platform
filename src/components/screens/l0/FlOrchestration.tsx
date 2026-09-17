import React, { useState } from 'react';
import { Cpu, Play, Square, RefreshCw, CheckCircle2, TrendingUp, AlertCircle, Layers } from 'lucide-react';
import { INITIAL_FL_ROUNDS } from '../../../data/mockAppData';
import { FlRound } from '../../../types';

export const FlOrchestration: React.FC = () => {
  const [rounds, setRounds] = useState<FlRound[]>(INITIAL_FL_ROUNDS);
  const [isRunning, setIsRunning] = useState(true);
  const [activeTab, setActiveTab] = useState<'ROUNDS' | 'NODES' | 'HYPERPARAMS'>('ROUNDS');

  const currentRound = rounds[0];

  const handleToggleRound = () => {
    if (isRunning) {
      setIsRunning(false);
    } else {
      setIsRunning(true);
      // increment progress
      setRounds((prev) => [
        {
          ...prev[0],
          convergenceProgress: Math.min(prev[0].convergenceProgress + 8, 100),
          globalAccuracy: +(prev[0].globalAccuracy + 0.2).toFixed(2),
        },
        ...prev.slice(1),
      ]);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10" id="fl-orchestration-screen">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-950 text-purple-300 border border-purple-800">
              FedAvg Orchestration Engine
            </span>
            <span className="text-xs text-slate-400">Differential Privacy (ε=1.2, δ=1e-5)</span>
          </div>
          <h1 className="text-xl font-bold text-slate-100 mt-2 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-purple-400" />
            Federated Learning Training & Aggregation
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Decentralized demand forecasting and stock-out risk model trained collaboratively across edge hospital nodes without raw patient data leaving facilities.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleToggleRound}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm ${
              isRunning
                ? 'bg-amber-600 hover:bg-amber-500 text-white'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white'
            }`}
          >
            {isRunning ? (
              <>
                <Square className="w-3.5 h-3.5 fill-current" /> Pause Round #14
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" /> Resume Training
              </>
            )}
          </button>
        </div>
      </div>

      {/* Round 14 Highlight Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Current Round Status</div>
          <div className="text-xl font-bold text-slate-100 mt-1 flex items-center gap-2">
            Round #{currentRound.roundNumber}
            <span className="text-xs px-2 py-0.5 rounded bg-purple-950 text-purple-400 border border-purple-800 font-normal">
              {isRunning ? 'IN_PROGRESS' : 'PAUSED'}
            </span>
          </div>
          <div className="text-xs text-slate-500 mt-2">Started: {currentRound.startTime}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Global Model Accuracy</div>
          <div className="text-xl font-bold text-emerald-400 mt-1">{currentRound.globalAccuracy}%</div>
          <div className="text-xs text-emerald-500 mt-2">Target benchmark: &gt;90% (Passed)</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Categorical Cross-Entropy Loss</div>
          <div className="text-xl font-bold text-slate-100 mt-1 font-mono">{currentRound.loss}</div>
          <div className="text-xs text-slate-400 mt-2">Downward trajectory</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Node Participation</div>
          <div className="text-xl font-bold text-slate-100 mt-1">
            {currentRound.participatingNodes} / {currentRound.totalNodes} Nodes
          </div>
          <div className="text-xs text-slate-400 mt-2">87.5% quorum reached</div>
        </div>
      </div>

      {/* Progress & Convergence bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-200">Current Round Aggregation Convergence</h2>
            <p className="text-xs text-slate-400 mt-0.5">Gradient weight vector verification and secure multi-party computation check</p>
          </div>
          <span className="text-sm font-bold text-purple-400 font-mono">{currentRound.convergenceProgress}%</span>
        </div>
        <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
          <div
            className="h-full bg-gradient-to-r from-purple-600 to-emerald-500 transition-all duration-500"
            style={{ width: `${currentRound.convergenceProgress}%` }}
          ></div>
        </div>
      </div>

      {/* Round History Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Layers className="w-4 h-4 text-purple-400" />
          Federated Round History & Model Checkpoints
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Round</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Global Accuracy</th>
                <th className="py-3 px-4">Loss</th>
                <th className="py-3 px-4">Participating Nodes</th>
                <th className="py-3 px-4">Start Time</th>
                <th className="py-3 px-4">Completed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {rounds.map((r) => (
                <tr key={r.roundNumber} className="hover:bg-slate-800/40">
                  <td className="py-3 px-4 font-bold text-slate-100">Round #{r.roundNumber}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
                        r.status === 'COMPLETED'
                          ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800'
                          : 'bg-purple-950/60 text-purple-300 border-purple-800'
                      }`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono font-bold text-emerald-400">{r.globalAccuracy}%</td>
                  <td className="py-3 px-4 font-mono text-slate-300">{r.loss}</td>
                  <td className="py-3 px-4 text-slate-300">
                    {r.participatingNodes} / {r.totalNodes}
                  </td>
                  <td className="py-3 px-4 text-slate-400">{r.startTime}</td>
                  <td className="py-3 px-4 text-slate-400">{r.completedTime || 'Ongoing...'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
