import React, { useState } from 'react';
import { Users, CheckCircle2, Stethoscope, Save } from 'lucide-react';

export const PatientFootfall: React.FC = () => {
  const [opdCount, setOpdCount] = useState(148);
  const [ipdAdmissions, setIpdAdmissions] = useState(4);
  const [emergencyTriage, setEmergencyTriage] = useState(12);
  const [feverCases, setFeverCases] = useState(42);
  const [gastroCases, setGastroCases] = useState(18);
  const [respiratoryCases, setRespiratoryCases] = useState(25);
  const [saved, setSaved] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-10" id="patient-footfall-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Users className="w-5 h-5 text-teal-400" />
          Daily Patient Footfall & Morbidity Log
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Record outpatient (OPD) and inpatient (IPD) counts along with syndromic presentations to feed the AI demand model.
        </p>
      </div>

      {saved && (
        <div className="p-4 bg-teal-950/80 border border-teal-700/60 rounded-lg text-teal-200 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-teal-400" />
          Daily census and syndromic telemetry successfully logged and synced with district server!
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
        <div>
          <h2 className="text-sm font-semibold text-slate-200 mb-3">Facility Patient Census (Today)</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Total OPD Registrations</label>
              <input
                type="number"
                value={opdCount}
                onChange={(e) => setOpdCount(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100 font-mono focus:outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">New IPD Ward Admissions</label>
              <input
                type="number"
                value={ipdAdmissions}
                onChange={(e) => setIpdAdmissions(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100 font-mono focus:outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Emergency Triage Visits</label>
              <input
                type="number"
                value={emergencyTriage}
                onChange={(e) => setEmergencyTriage(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100 font-mono focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800">
          <h2 className="text-sm font-semibold text-slate-200 mb-3">Top Syndromic Presentations (Fever / Waterborne / Respiratory)</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Acute Febrile Illness / Fever</label>
              <input
                type="number"
                value={feverCases}
                onChange={(e) => setFeverCases(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100 font-mono focus:outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Acute Diarrheal / Gastroenteritis</label>
              <input
                type="number"
                value={gastroCases}
                onChange={(e) => setGastroCases(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100 font-mono focus:outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Acute Respiratory Infections</label>
              <input
                type="number"
                value={respiratoryCases}
                onChange={(e) => setRespiratoryCases(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100 font-mono focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800 flex justify-end">
          <button
            type="submit"
            className="px-5 py-2.5 bg-teal-600 hover:bg-teal-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm"
          >
            <Save className="w-4 h-4" />
            Submit Daily OPD Census
          </button>
        </div>
      </form>
    </div>
  );
};
