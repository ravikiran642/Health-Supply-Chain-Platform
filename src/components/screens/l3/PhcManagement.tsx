import React, { useState } from 'react';
import { Stethoscope, Phone, MapPin, Bed, CheckCircle2, Edit2 } from 'lucide-react';

interface PhcDetail {
  id: string;
  name: string;
  code: string;
  moName: string;
  moPhone: string;
  generalBeds: number;
  oxygenBeds: number;
  icuBeds: number;
  distanceFromDistrictHubKm: number;
}

const INITIAL_PHCS: PhcDetail[] = [
  {
    id: 'phc-ori',
    name: 'Ormanjhi Primary Health Centre',
    code: 'JH-RAN-ORI',
    moName: 'Dr. Rameshwar Mahto',
    moPhone: '+91 94311 88421',
    generalBeds: 28,
    oxygenBeds: 6,
    icuBeds: 4,
    distanceFromDistrictHubKm: 18.5,
  },
  {
    id: 'phc-kan',
    name: 'Kanke Primary Health Centre',
    code: 'JH-RAN-KAN',
    moName: 'Dr. S. Kispotta',
    moPhone: '+91 94311 99201',
    generalBeds: 32,
    oxygenBeds: 8,
    icuBeds: 5,
    distanceFromDistrictHubKm: 12.0,
  },
  {
    id: 'phc-bun',
    name: 'Bundu Sub-Divisional Hospital & PHC',
    code: 'JH-RAN-BUN',
    moName: 'Dr. Alok Baraik',
    moPhone: '+91 94311 66312',
    generalBeds: 22,
    oxygenBeds: 6,
    icuBeds: 2,
    distanceFromDistrictHubKm: 42.0,
  },
  {
    id: 'phc-sil',
    name: 'Silli Primary Health Centre',
    code: 'JH-RAN-SIL',
    moName: 'Dr. Meena Soren',
    moPhone: '+91 94311 55198',
    generalBeds: 20,
    oxygenBeds: 4,
    icuBeds: 1,
    distanceFromDistrictHubKm: 58.0,
  },
];

export const PhcManagement: React.FC = () => {
  const [phcs, setPhcs] = useState<PhcDetail[]>(INITIAL_PHCS);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editPhone, setEditPhone] = useState('');

  const handleStartEdit = (phc: PhcDetail) => {
    setEditingId(phc.id);
    setEditPhone(phc.moPhone);
  };

  const handleSaveEdit = (id: string) => {
    setPhcs(phcs.map((p) => (p.id === id ? { ...p, moPhone: editPhone } : p)));
    setEditingId(null);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="phc-management-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Stethoscope className="w-5 h-5 text-amber-400" />
          Ranchi District PHC Facilities & Medical Officer Directory
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Maintain facility records, verified bed infrastructure capacity, and official medical officer contact channels.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {phcs.map((phc) => (
          <div key={phc.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-base font-bold text-slate-100">{phc.name}</h2>
                <div className="text-xs text-slate-500 font-mono mt-0.5">{phc.code}</div>
              </div>
              <span className="text-xs text-slate-400 font-mono">{phc.distanceFromDistrictHubKm} km away</span>
            </div>

            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Medical Officer:</span>
                <span className="font-semibold text-slate-200">{phc.moName}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Phone:</span>
                {editingId === phc.id ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={editPhone}
                      onChange={(e) => setEditPhone(e.target.value)}
                      className="px-2 py-0.5 bg-slate-900 border border-slate-700 rounded text-slate-200 text-xs w-32"
                    />
                    <button
                      type="button"
                      onClick={() => handleSaveEdit(phc.id)}
                      className="text-emerald-400 hover:text-emerald-300 font-semibold"
                    >
                      Save
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-slate-300">{phc.moPhone}</span>
                    <button
                      type="button"
                      onClick={() => handleStartEdit(phc)}
                      className="text-slate-500 hover:text-amber-400"
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="p-2 bg-slate-950 rounded border border-slate-800">
                <div className="text-slate-500 text-[11px]">General</div>
                <div className="text-sm font-bold text-slate-100 mt-0.5">{phc.generalBeds} Beds</div>
              </div>
              <div className="p-2 bg-slate-950 rounded border border-slate-800">
                <div className="text-slate-500 text-[11px]">Oxygen</div>
                <div className="text-sm font-bold text-blue-400 mt-0.5">{phc.oxygenBeds} Beds</div>
              </div>
              <div className="p-2 bg-slate-950 rounded border border-slate-800">
                <div className="text-slate-500 text-[11px]">ICU / High Care</div>
                <div className="text-sm font-bold text-emerald-400 mt-0.5">{phc.icuBeds} Beds</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
