import React, { useState } from 'react';
import { ArrowRightLeft, CheckCircle2, Truck, Sparkles, X } from 'lucide-react';
import { INITIAL_TRANSFERS } from '../../../data/mockAppData';
import { RedistributionTransfer } from '../../../types';

export const RedistributionRecommendations: React.FC = () => {
  const [transfers, setTransfers] = useState<RedistributionTransfer[]>(
    (INITIAL_TRANSFERS || []).filter((t) => t.tier === 'INTER_PHC')
  );
  const [feedback, setFeedback] = useState<string | null>(null);

  const handleApprove = (id: string) => {
    setTransfers(
      transfers.map((t) => (t.id === id ? { ...t, status: 'APPROVED', approvedBy: 'Ranchi District Approver' } : t))
    );
    setFeedback('PHC Redistribution Transfer authorized! Pickup dispatched.');
    setTimeout(() => setFeedback(null), 3000);
  };

  const handleReject = (id: string) => {
    setTransfers(transfers.map((t) => (t.id === id ? { ...t, status: 'REJECTED' } : t)));
    setFeedback('Transfer recommendation declined.');
    setTimeout(() => setFeedback(null), 3000);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="redistribution-recommendations-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5" /> AI Optimal Logistics Matching
          </span>
        </div>
        <h1 className="text-xl font-bold text-slate-100 mt-2 flex items-center gap-2">
          <ArrowRightLeft className="w-5 h-5 text-amber-400" />
          Inter-PHC Redistribution Recommendations
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Algorithmic redistribution between Ranchi district PHCs to resolve zero-stock emergencies without placing new procurement orders.
        </p>
      </div>

      {feedback && (
        <div className="p-4 bg-emerald-950/80 border border-emerald-700/60 rounded-lg text-emerald-300 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          {feedback}
        </div>
      )}

      <div className="space-y-4">
        {transfers.map((t) => (
          <div key={t.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 rounded">
                  {t.transferNumber}
                </span>
                <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-950/70 border border-red-800 text-red-300">
                  {t.urgency}
                </span>
              </div>
              <span className="text-xs text-slate-400 font-mono">Distance: {t.distanceKm} km transit</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-center bg-slate-950 p-4 rounded-lg border border-slate-800 text-xs">
              <div>
                <span className="text-slate-500 font-semibold">Surplus Facility:</span>
                <div className="text-sm font-bold text-emerald-400 mt-0.5">{t.sourceFacility}</div>
              </div>
              <div className="flex justify-center text-slate-400">
                <div className="flex items-center gap-1.5 font-medium">
                  <span>Transfer {t.quantity} {t.unit}</span>
                  <Truck className="w-4 h-4 text-amber-400" />
                </div>
              </div>
              <div className="sm:text-right">
                <span className="text-slate-500 font-semibold">Deficit Facility:</span>
                <div className="text-sm font-bold text-red-400 mt-0.5">{t.destinationFacility}</div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-1">
              <div>
                <span className="text-xs text-slate-400">Medicine: </span>
                <span className="text-sm font-bold text-slate-100">{t.item}</span>
                <div className="text-xs text-emerald-400 mt-0.5">Est. Savings: {t.costSavingsEst}</div>
              </div>

              {t.status === 'RECOMMENDED' || t.status === 'PENDING_APPROVAL' ? (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleReject(t.id)}
                    className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded border border-slate-700 transition-colors"
                  >
                    Reject
                  </button>
                  <button
                    type="button"
                    onClick={() => handleApprove(t.id)}
                    className="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded transition-colors flex items-center gap-1.5 shadow-sm"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Approve Transfer
                  </button>
                </div>
              ) : (
                <div className="text-xs text-slate-400">
                  Approved By: <strong className="text-emerald-400">{t.approvedBy || t.status}</strong>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
