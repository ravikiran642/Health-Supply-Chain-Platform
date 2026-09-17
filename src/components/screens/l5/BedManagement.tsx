import React, { useState } from 'react';
import { Bed, Plus, Minus, CheckCircle2, UserPlus, AlertTriangle } from 'lucide-react';
import { BedCategory } from '../../../types';

interface BedManagementProps {
  beds: BedCategory[];
  onUpdateBeds: (beds: BedCategory[]) => void;
}

export const BedManagement: React.FC<BedManagementProps> = ({ beds = [], onUpdateBeds }) => {
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const safeBeds = beds || [];

  const handleAdjustOccupancy = (id: string, delta: number) => {
    const updated = safeBeds.map((b) => {
      if (b.id === id) {
        const newOcc = Math.max(0, Math.min(b.total, b.occupied + delta));
        return {
          ...b,
          occupied: newOcc,
          available: b.total - newOcc,
        };
      }
      return b;
    });

    onUpdateBeds(updated);
    setSuccessMsg('Bed occupancy status successfully synchronized with district portal.');
    setTimeout(() => setSuccessMsg(null), 2500);
  };

  const totalBeds = safeBeds.reduce((acc, b) => acc + (b.total || 0), 0);
  const totalOccupied = safeBeds.reduce((acc, b) => acc + (b.occupied || 0), 0);
  const totalAvailable = totalBeds - totalOccupied;

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="bed-management-screen">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Bed className="w-5 h-5 text-blue-400" />
            PHC Inpatient Bed Occupancy & Triage Tracker
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time admissions and discharge recording across General, Maternity, Oxygen-Supported, and Emergency wards.
          </p>
        </div>

        <div className="flex items-center gap-4 bg-slate-950 px-4 py-2.5 rounded-lg border border-slate-800 text-xs">
          <div>
            <span className="text-slate-500">Total Capacity:</span>
            <div className="font-bold text-slate-200">{totalBeds} Beds</div>
          </div>
          <div className="w-px h-6 bg-slate-800"></div>
          <div>
            <span className="text-slate-500">Occupied:</span>
            <div className="font-bold text-amber-400">{totalOccupied} Beds</div>
          </div>
          <div className="w-px h-6 bg-slate-800"></div>
          <div>
            <span className="text-slate-500">Vacant:</span>
            <div className="font-bold text-emerald-400">{totalAvailable} Beds</div>
          </div>
        </div>
      </div>

      {successMsg && (
        <div className="p-4 bg-emerald-950/80 border border-emerald-700/60 rounded-lg text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          {successMsg}
        </div>
      )}

      {/* Bed categories cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {safeBeds.map((category) => {
          const totalCount = category.total || 1;
          const occupiedCount = category.occupied || 0;
          const occupancyRate = Math.round((occupiedCount / totalCount) * 100);
          const isHighOccupancy = occupancyRate >= 85;

          return (
            <div
              key={category.id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 shadow-sm"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-base font-bold text-slate-100">{category.name}</h2>
                  <div className="text-xs text-slate-400 mt-0.5">
                    {category.total - category.occupied} vacant beds ready for admission
                  </div>
                </div>

                <span
                  className={`px-2 py-0.5 rounded text-xs font-semibold border ${
                    isHighOccupancy
                      ? 'bg-red-950/80 border-red-800 text-red-300'
                      : 'bg-emerald-950/80 border-emerald-800 text-emerald-300'
                  }`}
                >
                  {occupancyRate}% Occupied
                </span>
              </div>

              {/* Progress bar */}
              <div className="space-y-1">
                <div className="w-full h-2.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      isHighOccupancy ? 'bg-red-500' : occupancyRate > 50 ? 'bg-amber-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${occupancyRate}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-[11px] text-slate-500 font-mono">
                  <span>Occupied: {category.occupied}</span>
                  <span>Total: {category.total}</span>
                </div>
              </div>

              {/* Admission / Discharge Controls */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-800">
                <span className="text-xs font-medium text-slate-300">Fast Triage Actions:</span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleAdjustOccupancy(category.id, -1)}
                    disabled={category.occupied <= 0}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 text-xs font-semibold rounded border border-slate-700 flex items-center gap-1 transition-colors"
                  >
                    <Minus className="w-3.5 h-3.5 text-emerald-400" />
                    Discharge (-1)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleAdjustOccupancy(category.id, 1)}
                    disabled={category.occupied >= category.total}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-xs font-semibold rounded flex items-center gap-1 transition-colors shadow-sm"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Admit Patient (+1)
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
