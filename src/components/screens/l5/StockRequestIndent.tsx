import React, { useState } from 'react';
import { Send, Sparkles, CheckCircle2, Clock, Package, AlertCircle } from 'lucide-react';
import { InventoryItem, IndentRequest } from '../../../types';
import { INITIAL_INDENTS } from '../../../data/mockAppData';

interface StockRequestIndentProps {
  inventory: InventoryItem[];
}

export const StockRequestIndent: React.FC<StockRequestIndentProps> = ({ inventory = [] }) => {
  const safeInventory = inventory || [];
  const [indents, setIndents] = useState<IndentRequest[]>(
    (INITIAL_INDENTS || []).filter((i) => (i.phcName || '').includes('Ormanjhi'))
  );
  const firstCode = safeInventory[0]?.code || safeInventory[0]?.drugCode || 'MED-PCM-500';
  const [selectedDrug, setSelectedDrug] = useState(firstCode);
  const [requestedQty, setRequestedQty] = useState(1200);
  const [urgency, setUrgency] = useState<'ROUTINE' | 'URGENT' | 'EMERGENCY'>('URGENT');
  const [notes, setNotes] = useState('');
  const [submittedMsg, setSubmittedMsg] = useState<string | null>(null);

  const currentDrug =
    safeInventory.find((i) => (i.code || i.drugCode) === selectedDrug) || safeInventory[0];
  const recommendedQty = Math.max(
    500,
    (currentDrug?.minRequired || 50) * 3 - (currentDrug?.currentStock || 0)
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newIndent: IndentRequest = {
      id: `ind-${Date.now()}`,
      indentNumber: `IND-RAN-ORI-2026-${Math.floor(100 + Math.random() * 900)}`,
      phcId: 'phc-orm-01',
      phcName: 'Ormanjhi PHC',
      districtId: 'dist-ran-01',
      districtName: 'Ranchi District',
      drugName: currentDrug?.name || 'Essential Drug',
      drugCode: selectedDrug,
      requestedQty: Number(requestedQty),
      recommendedQty,
      urgency,
      status: 'PENDING',
      createdAt: 'Just now',
      notes,
    };

    setIndents([newIndent, ...indents]);
    setSubmittedMsg(`Indent ${newIndent.indentNumber} successfully routed to Ranchi District Health Office!`);
    setNotes('');
    setTimeout(() => setSubmittedMsg(null), 4000);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="stock-request-indent-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Send className="w-5 h-5 text-teal-400" />
          PHC Stock Requisition & Indent Filing
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Submit electronic indent requisitions to Ranchi District Health Officer. The system automatically computes federated demand recommendations based on historical consumption.
        </p>
      </div>

      {submittedMsg && (
        <div className="p-4 bg-teal-950/80 border border-teal-700/60 rounded-lg text-teal-200 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
          {submittedMsg}
        </div>
      )}

      {/* New Indent Form */}
      <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-base font-bold text-slate-200">File New Stock Requisition</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Select Medicine / Vaccine</label>
            <select
              value={selectedDrug}
              onChange={(e) => setSelectedDrug(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-teal-500"
            >
              {safeInventory.map((item) => {
                const itemCode = item.code || item.drugCode || item.id;
                return (
                  <option key={item.id} value={itemCode}>
                    {item.name} ({itemCode}) — Current: {item.currentStock} {item.unit}
                  </option>
                );
              })}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Requisition Urgency Tier</label>
            <select
              value={urgency}
              onChange={(e) => setUrgency(e.target.value as any)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-teal-500"
            >
              <option value="ROUTINE">Routine Monthly Restock</option>
              <option value="URGENT">Urgent (Buffer Depleted)</option>
              <option value="EMERGENCY">Emergency (Zero Stock / Stock-out)</option>
            </select>
          </div>
        </div>

        {/* AI Recommendation box */}
        <div className="p-4 bg-slate-950 rounded-lg border border-teal-900/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-teal-400 font-semibold">
            <Sparkles className="w-4 h-4 text-teal-400" />
            AI Recommended 30-Day Buffer:
            <span className="text-slate-100 font-bold text-sm">{recommendedQty} {currentDrug?.unit}</span>
          </div>
          <button
            type="button"
            onClick={() => setRequestedQty(recommendedQty)}
            className="text-xs text-teal-400 hover:text-teal-300 font-medium underline text-left sm:text-right"
          >
            Apply Suggested Quantity
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Requested Quantity ({currentDrug?.unit})</label>
            <input
              type="number"
              required
              value={requestedQty}
              onChange={(e) => setRequestedQty(Number(e.target.value))}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 font-mono focus:outline-none focus:border-teal-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Clinical Justification / Note</label>
            <input
              type="text"
              placeholder="e.g. Surge in monsoon fever cases at OPD"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-teal-500"
            />
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            className="px-5 py-2.5 bg-teal-600 hover:bg-teal-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm"
          >
            <Send className="w-4 h-4" />
            Submit Indent to District Office
          </button>
        </div>
      </form>

      {/* Submitted Indents History */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-base font-bold text-slate-200">Recent Indents for Ormanjhi PHC</h2>

        <div className="space-y-3">
          {indents.map((indent) => (
            <div
              key={indent.id}
              className="p-4 bg-slate-950 rounded-lg border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-teal-400">{indent.indentNumber}</span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${
                      indent.urgency === 'EMERGENCY'
                        ? 'bg-red-950 text-red-300 border-red-800'
                        : 'bg-amber-950 text-amber-300 border-amber-800'
                    }`}
                  >
                    {indent.urgency}
                  </span>
                </div>
                <div className="text-sm font-semibold text-slate-200 mt-1">
                  {indent.drugName} — {indent.requestedQty.toLocaleString()} units
                </div>
                <div className="text-slate-500 mt-0.5">Submitted: {indent.createdAt}</div>
              </div>

              <div className="flex items-center gap-3">
                <span
                  className={`px-2.5 py-1 rounded text-xs font-semibold border ${
                    indent.status === 'APPROVED' || indent.status === 'DELIVERED'
                      ? 'bg-emerald-950/80 border-emerald-800 text-emerald-300'
                      : indent.status === 'REJECTED'
                      ? 'bg-red-950/80 border-red-800 text-red-300'
                      : 'bg-amber-950/80 border-amber-800 text-amber-300'
                  }`}
                >
                  {indent.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
