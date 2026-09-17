import React, { useState } from 'react';
import { ArrowLeftRight, CheckCircle2, XCircle, Truck, MapPin } from 'lucide-react';
import { INITIAL_TRANSFERS } from '../../../data/mockAppData';
import { RedistributionTransfer } from '../../../types';

export const StateRedistribution: React.FC = () => {
  const [transfers, setTransfers] = useState<RedistributionTransfer[]>(
    (INITIAL_TRANSFERS || []).filter((t) => t.tier === 'INTRA_STATE')
  );
  const [msg, setMsg] = useState<string | null>(null);

  const handleApprove = (id: string) => {
    setTransfers(
      transfers.map((t) =>
        t.id === id ? { ...t, status: 'APPROVED', approvedBy: 'Jharkhand State Approver' } : t
      )
    );
    setMsg('Transfer approved! Inter-district logistics order issued to civil surgeon.');
    setTimeout(() => setMsg(null), 3000);
  };

  const handleReject = (id: string) => {
    setTransfers(transfers.map((t) => (t.id === id ? { ...t, status: 'REJECTED' } : t)));
    setMsg('Transfer proposal rejected.');
    setTimeout(() => setMsg(null), 3000);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10" id="state-redistribution-screen">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <ArrowLeftRight className="w-5 h-5 text-emerald-400" />
            Intra-State (District-to-District) Redistribution Queue
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Review and authorize district-level medicine reallocations across Jharkhand districts (e.g. Dhanbad surplus to Ranchi deficit).
          </p>
        </div>
      </div>

      {msg && (
        <div className="p-4 bg-emerald-950/80 border border-emerald-700/60 rounded-lg text-emerald-300 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          {msg}
        </div>
      )}

      <div className="space-y-4">
        {transfers.map((t) => (
          <div key={t.id} className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2.5 py-1 rounded">
                  {t.transferNumber}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-semibold border ${
                    t.urgency === 'EMERGENCY'
                      ? 'bg-red-950/70 border-red-800 text-red-300'
                      : 'bg-amber-950/70 border-amber-800 text-amber-300'
                  }`}
                >
                  {t.urgency}
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="text-slate-400">Initiated: {t.createdAt}</span>
                <span className="px-2 py-0.5 rounded font-medium bg-slate-800 border border-slate-700 text-slate-200">
                  {t.status.replace('_', ' ')}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center bg-slate-950/80 p-4 rounded-lg border border-slate-800">
              <div>
                <div className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Origin District Facility</div>
                <div className="text-sm font-semibold text-slate-200 mt-1">{t.sourceFacility}</div>
              </div>

              <div className="flex flex-col items-center justify-center text-center">
                <div className="text-xs font-medium text-slate-400 mb-1">
                  {t.distanceKm} km • Savings: <strong className="text-emerald-400">{t.costSavingsEst}</strong>
                </div>
                <div className="flex items-center gap-2 text-emerald-400">
                  <span className="w-10 h-0.5 bg-emerald-700"></span>
                  <Truck className="w-5 h-5" />
                  <span className="w-10 h-0.5 bg-emerald-700"></span>
                </div>
              </div>

              <div className="md:text-right">
                <div className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Destination District Store</div>
                <div className="text-sm font-semibold text-slate-200 mt-1">{t.destinationFacility}</div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
              <div>
                <div className="text-xs text-slate-400">Medicine & Reallocation Units:</div>
                <div className="text-base font-bold text-slate-100 mt-0.5">
                  {t.item} — <span className="text-emerald-400">{t.quantity.toLocaleString()} {t.unit}</span>
                </div>
              </div>

              {t.status === 'PENDING_APPROVAL' ? (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleReject(t.id)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg border border-slate-700 transition-colors"
                  >
                    Reject
                  </button>
                  <button
                    type="button"
                    onClick={() => handleApprove(t.id)}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 shadow-sm"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Approve Transfer
                  </button>
                </div>
              ) : (
                <div className="text-xs text-slate-400">
                  Status: <strong className="text-slate-200">{t.approvedBy || t.status}</strong>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
