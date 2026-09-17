import React, { useState } from 'react';
import { ArrowLeftRight, Truck, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { INITIAL_TRANSFERS } from '../../../data/mockAppData';
import { RedistributionTransfer } from '../../../types';

export const PhcRedistribution: React.FC = () => {
  const [transfers, setTransfers] = useState<RedistributionTransfer[]>(
    (INITIAL_TRANSFERS || []).filter(
      (t) =>
        (t.sourceFacility || '').includes('Ormanjhi') ||
        (t.destinationFacility || '').includes('Ormanjhi')
    )
  );
  const [notification, setNotification] = useState<string | null>(null);

  const handleAcknowledge = (id: string) => {
    setTransfers(
      transfers.map((t) => (t.id === id ? { ...t, status: 'DELIVERED' } : t))
    );
    setNotification('Medicine transfer delivery received and taken into dispensary inventory!');
    setTimeout(() => setNotification(null), 3000);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="phc-redistribution-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <ArrowLeftRight className="w-5 h-5 text-teal-400" />
          PHC Inbound & Outbound Stock Transfers
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Acknowledge emergency incoming supplies from nearby health centres or dispatch verified surplus medicines.
        </p>
      </div>

      {notification && (
        <div className="p-4 bg-teal-950/80 border border-teal-700/60 rounded-lg text-teal-200 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-teal-400" />
          {notification}
        </div>
      )}

      <div className="space-y-4">
        {transfers.map((t) => {
          const isInbound = t.destinationFacility.includes('Ormanjhi');

          return (
            <div key={t.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-teal-400 bg-teal-950/60 border border-teal-800 px-2 py-0.5 rounded">
                    {t.transferNumber}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-semibold border ${
                      isInbound
                        ? 'bg-blue-950/60 border-blue-800 text-blue-300'
                        : 'bg-amber-950/60 border-amber-800 text-amber-300'
                    }`}
                  >
                    {isInbound ? '📥 Inbound Delivery' : '📤 Outbound Dispatch'}
                  </span>
                </div>
                <span className="text-xs text-slate-400 font-medium">Status: {t.status}</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-center bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
                <div>
                  <span className="text-slate-500">From:</span>
                  <div className="text-sm font-semibold text-slate-200 mt-0.5">{t.sourceFacility}</div>
                </div>
                <div className="flex justify-center text-slate-400">
                  <Truck className="w-4 h-4 text-teal-400" />
                </div>
                <div className="sm:text-right">
                  <span className="text-slate-500">To:</span>
                  <div className="text-sm font-semibold text-slate-200 mt-0.5">{t.destinationFacility}</div>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-1 text-xs">
                <div>
                  <span className="text-slate-400">Transferred Item: </span>
                  <strong className="text-slate-100 text-sm">{t.item}</strong> ({t.quantity} {t.unit})
                </div>

                {isInbound && t.status !== 'DELIVERED' ? (
                  <button
                    type="button"
                    onClick={() => handleAcknowledge(t.id)}
                    className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Confirm Inward Delivery & Update Stock
                  </button>
                ) : (
                  <span className="text-emerald-400 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Received into Dispensary
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
