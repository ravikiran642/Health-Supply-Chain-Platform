import React from 'react';
import { Building, AlertTriangle, Bed, ArrowRightLeft, Users, FileCheck, CheckCircle2, TrendingUp } from 'lucide-react';

interface PhcOverview {
  id: string;
  name: string;
  medicalOfficer: string;
  stockStatus: 'CRITICAL' | 'REORDER' | 'ADEQUATE';
  totalBeds: number;
  occupiedBeds: number;
  staffPresent: string;
  pendingIndents: number;
}

const RANCHI_PHCS: PhcOverview[] = [
  {
    id: 'phc-ori',
    name: 'Ormanjhi PHC',
    medicalOfficer: 'Dr. Rameshwar Mahto',
    stockStatus: 'CRITICAL',
    totalBeds: 38,
    occupiedBeds: 26,
    staffPresent: '5 / 6 Staff Present',
    pendingIndents: 1,
  },
  {
    id: 'phc-kan',
    name: 'Kanke PHC',
    medicalOfficer: 'Dr. S. Kispotta',
    stockStatus: 'ADEQUATE',
    totalBeds: 45,
    occupiedBeds: 29,
    staffPresent: '8 / 8 Staff Present',
    pendingIndents: 1,
  },
  {
    id: 'phc-bun',
    name: 'Bundu PHC',
    medicalOfficer: 'Dr. Alok Baraik',
    stockStatus: 'REORDER',
    totalBeds: 30,
    occupiedBeds: 21,
    staffPresent: '4 / 5 Staff Present',
    pendingIndents: 0,
  },
  {
    id: 'phc-sil',
    name: 'Silli PHC',
    medicalOfficer: 'Dr. Meena Soren',
    stockStatus: 'ADEQUATE',
    totalBeds: 25,
    occupiedBeds: 12,
    staffPresent: '5 / 5 Staff Present',
    pendingIndents: 0,
  },
];

interface DistrictDashboardProps {
  onNavigate: (screen: string) => void;
}

export const DistrictDashboard: React.FC<DistrictDashboardProps> = ({ onNavigate }) => {
  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10" id="district-dashboard">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-amber-950/70 via-slate-900 to-slate-900 border border-amber-800/40 rounded-xl p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-900/60 text-amber-300 border border-amber-700/50">
                L3 — District Health Office
              </span>
              <span className="text-xs text-slate-400">Ranchi District Hub</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-100 mt-2">Ranchi District Healthcare Operations</h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              Real-time monitoring of 42 Primary Health Centres, hospital bed availability, PHC indent approvals, and local stock redistribution.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => onNavigate('indent_approvals')}
              className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm"
            >
              <FileCheck className="w-4 h-4" />
              Indent Approvals (2)
            </button>
            <button
              type="button"
              onClick={() => onNavigate('redistribution_recommendations')}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold border border-slate-700 flex items-center gap-2 transition-colors"
            >
              <ArrowRightLeft className="w-4 h-4 text-emerald-400" />
              Redistribution AI
            </button>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Total Supervised PHCs</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">42 Facilities</div>
          <div className="text-xs text-slate-400 mt-1">100% active data reporting</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">District Bed Occupancy</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">63.4%</div>
          <div className="text-xs text-slate-400 mt-1">88 of 138 beds occupied in sample</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Pending Indent Approvals</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">2 Requests</div>
          <div className="text-xs text-amber-500 mt-1">Ormanjhi & Kanke awaiting signoff</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Inter-PHC Redistribution</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">1 Recommended</div>
          <div className="text-xs text-emerald-500 mt-1">Kanke → Ormanjhi (Paracetamol)</div>
        </div>
      </div>

      {/* PHC Facilities Summary Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
            <Building className="w-4 h-4 text-amber-400" />
            Ranchi Primary Health Centres (PHC) Status
          </h2>
          <button
            type="button"
            onClick={() => onNavigate('phc_management')}
            className="text-xs text-amber-400 hover:text-amber-300 font-medium"
          >
            Manage All PHCs &rarr;
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">PHC Facility</th>
                <th className="py-3 px-4">Medical Officer In-Charge</th>
                <th className="py-3 px-4">Stock Health</th>
                <th className="py-3 px-4">Bed Occupancy</th>
                <th className="py-3 px-4">Duty Attendance</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {RANCHI_PHCS.map((phc) => (
                <tr key={phc.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 font-semibold text-slate-100">{phc.name}</td>
                  <td className="py-3.5 px-4 text-slate-300">{phc.medicalOfficer}</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
                        phc.stockStatus === 'CRITICAL'
                          ? 'bg-red-950/70 text-red-300 border-red-800'
                          : phc.stockStatus === 'REORDER'
                          ? 'bg-amber-950/70 text-amber-300 border-amber-800'
                          : 'bg-emerald-950/70 text-emerald-300 border-emerald-800'
                      }`}
                    >
                      {phc.stockStatus}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="font-semibold text-slate-100">{phc.occupiedBeds}</span> / {phc.totalBeds} beds ({Math.round((phc.occupiedBeds / phc.totalBeds) * 100)}%)
                  </td>
                  <td className="py-3.5 px-4 font-medium text-emerald-400">{phc.staffPresent}</td>
                  <td className="py-3.5 px-4 text-right">
                    {phc.pendingIndents > 0 ? (
                      <button
                        type="button"
                        onClick={() => onNavigate('indent_approvals')}
                        className="px-2.5 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded text-xs font-medium transition-colors"
                      >
                        Review Indent ({phc.pendingIndents})
                      </button>
                    ) : (
                      <span className="text-slate-500 text-xs">No pending requests</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
