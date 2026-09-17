import React, { useState } from 'react';
import { Settings, Save, Sliders, CheckCircle2, ShieldAlert, Thermometer, Calendar } from 'lucide-react';

export const SystemSettings: React.FC = () => {
  const [minBufferDays, setMinBufferDays] = useState(14);
  const [emergencyBufferDays, setEmergencyBufferDays] = useState(3);
  const [coldChainMinTemp, setColdChainMinTemp] = useState(2);
  const [coldChainMaxTemp, setColdChainMaxTemp] = useState(8);
  const [expiryWarningDays, setExpiryWarningDays] = useState(60);
  const [flMinQuorum, setFlMinQuorum] = useState(75);
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-10" id="system-settings-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Settings className="w-5 h-5 text-purple-400" />
          National Supply Chain System Settings & Thresholds
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Define platform-wide safety buffers, cold chain excursion ceilings, expiry warning lead times, and federated learning aggregation parameters.
        </p>
      </div>

      {saved && (
        <div className="p-4 bg-emerald-950/80 border border-emerald-700/60 rounded-lg text-emerald-300 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          National threshold rules have been updated and broadcast to all 32 edge clusters!
        </div>
      )}

      <form onSubmit={handleSave} className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
        <div>
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-3">
            <Sliders className="w-4 h-4 text-purple-400" />
            Inventory & Safety Buffer Days
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Standard Safety Stock Buffer (Days)</label>
              <input
                type="number"
                value={minBufferDays}
                onChange={(e) => setMinBufferDays(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-purple-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">Facilities below this threshold enter 🟡 Reorder status.</p>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Critical Emergency Threshold (Days)</label>
              <input
                type="number"
                value={emergencyBufferDays}
                onChange={(e) => setEmergencyBufferDays(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-purple-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">Facilities below this trigger 🔴 Critical Stock-out alert.</p>
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-3">
            <Thermometer className="w-4 h-4 text-cyan-400" />
            Vaccine Cold Chain Temperature Boundaries (°C)
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">ILR Minimum Safe Temperature (°C)</label>
              <input
                type="number"
                value={coldChainMinTemp}
                onChange={(e) => setColdChainMinTemp(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-purple-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">ILR Maximum Safe Temperature (°C)</label>
              <input
                type="number"
                value={coldChainMaxTemp}
                onChange={(e) => setColdChainMaxTemp(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-purple-500"
              />
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-3">
            <Calendar className="w-4 h-4 text-amber-400" />
            Batch Expiry & Federated Learning Hyperparameters
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Near-Expiry Warning Lead Time (Days)</label>
              <input
                type="number"
                value={expiryWarningDays}
                onChange={(e) => setExpiryWarningDays(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-purple-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">FL Node Aggregation Quorum (%)</label>
              <input
                type="number"
                value={flMinQuorum}
                onChange={(e) => setFlMinQuorum(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-purple-500"
              />
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800 flex justify-end">
          <button
            type="submit"
            className="px-5 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm"
          >
            <Save className="w-4 h-4" />
            Broadcast Threshold Configuration
          </button>
        </div>
      </form>
    </div>
  );
};
