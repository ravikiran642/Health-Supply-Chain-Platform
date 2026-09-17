import React, { useState } from 'react';
import { FileCheck, CheckCircle2, XCircle, Clock, AlertTriangle, Send } from 'lucide-react';
import { INITIAL_INDENTS } from '../../../data/mockAppData';
import { IndentRequest } from '../../../types';

export const IndentApprovals: React.FC = () => {
  const [indents, setIndents] = useState<IndentRequest[]>(INITIAL_INDENTS);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const handleApprove = (id: string, qty: number) => {
    setIndents(
      indents.map((i) =>
        i.id === id ? { ...i, status: 'APPROVED', approvedQty: qty } : i
      )
    );
    setActionMsg(`Indent ${id} approved for ${qty} units. District warehouse dispatch initiated.`);
    setTimeout(() => setActionMsg(null), 3000);
  };

  const handleReject = (id: string) => {
    setIndents(indents.map((i) => (i.id === id ? { ...i, status: 'REJECTED' } : i)));
    setActionMsg(`Indent ${id} rejected.`);
    setTimeout(() => setActionMsg(null), 3000);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="indent-approvals-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <FileCheck className="w-5 h-5 text-amber-400" />
          PHC Stock Indent Requisitions & Approvals
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Review stock requisitions submitted by PHC Medical Officers. Compare requested quantities with AI-recommended buffers and authorize district warehouse dispatches.
        </p>
      </div>

      {actionMsg && (
        <div className="p-4 bg-emerald-950/80 border border-emerald-700/60 rounded-lg text-emerald-300 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          {actionMsg}
        </div>
      )}

      <div className="space-y-4">
        {indents.map((indent) => (
          <div key={indent.id} className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs font-bold text-amber-400 bg-amber-950/60 border border-amber-800 px-2.5 py-1 rounded">
                  {indent.indentNumber}
                </span>
                <span className="font-semibold text-slate-100 text-sm">{indent.phcName}</span>
                <span
                  className={`px-2 py-0.5 rounded text-xs font-semibold border ${
                    indent.urgency === 'EMERGENCY'
                      ? 'bg-red-950/70 border-red-800 text-red-300'
                      : 'bg-amber-950/70 border-amber-800 text-amber-300'
                  }`}
                >
                  {indent.urgency}
                </span>
              </div>

              <div className="flex items-center gap-3 text-xs">
                <span className="text-slate-400">Date: {indent.createdAt}</span>
                <span
                  className={`px-2 py-0.5 rounded font-semibold border ${
                    indent.status === 'APPROVED' || indent.status === 'DELIVERED'
                      ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800'
                      : indent.status === 'REJECTED'
                      ? 'bg-red-950/60 text-red-400 border-red-800'
                      : 'bg-amber-950/60 text-amber-300 border-amber-800'
                  }`}
                >
                  {indent.status}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs bg-slate-950 p-4 rounded-lg border border-slate-800">
              <div>
                <span className="text-slate-500">Requested Medicine:</span>
                <div className="text-sm font-bold text-slate-100 mt-0.5">{indent.drugName}</div>
                <div className="text-slate-500 font-mono text-[11px]">{indent.drugCode}</div>
              </div>

              <div>
                <span className="text-slate-500">PHC Requested Quantity:</span>
                <div className="text-base font-bold text-amber-400 mt-0.5">{indent.requestedQty.toLocaleString()} units</div>
              </div>

              <div>
                <span className="text-slate-500">AI Recommended Buffer:</span>
                <div className="text-base font-bold text-emerald-400 mt-0.5">{indent.recommendedQty.toLocaleString()} units</div>
              </div>
            </div>

            {indent.notes && (
              <div className="text-xs text-slate-400 bg-slate-950/50 p-2.5 rounded border border-slate-800/80">
                <strong>Justification Note:</strong> {indent.notes}
              </div>
            )}

            {indent.status === 'PENDING' ? (
              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => handleReject(indent.id)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg border border-slate-700 transition-colors"
                >
                  Reject Requisition
                </button>
                <button
                  type="button"
                  onClick={() => handleApprove(indent.id, indent.requestedQty)}
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 shadow-sm"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Approve Requested ({indent.requestedQty})
                </button>
              </div>
            ) : (
              <div className="text-right text-xs text-slate-400 pt-1">
                Approved Quantity: <strong className="text-emerald-400">{indent.approvedQty || indent.requestedQty} units</strong>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
