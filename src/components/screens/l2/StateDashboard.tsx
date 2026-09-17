import React, { useState } from 'react';
import { MapPin, AlertTriangle, Bed, ArrowLeftRight, TrendingUp, Users, CheckCircle2, ShieldAlert } from 'lucide-react';

interface DistrictMetric {
  code: string;
  name: string;
  facilitiesCount: number;
  stockOutRisk: 'LOW' | 'MEDIUM' | 'HIGH';
  bedOccupancyPercent: number;
  totalBeds: number;
  criticalShortages: string[];
  lastDataSync: string;
}

const JHARKHAND_DISTRICTS: DistrictMetric[] = [
  {
    code: 'RAN',
    name: 'Ranchi District',
    facilitiesCount: 42,
    stockOutRisk: 'MEDIUM',
    bedOccupancyPercent: 78,
    totalBeds: 2400,
    criticalShortages: ['Paracetamol 500mg', 'Insulin Regular'],
    lastDataSync: '3 mins ago',
  },
  {
    code: 'BOK',
    name: 'Bokaro District',
    facilitiesCount: 28,
    stockOutRisk: 'HIGH',
    bedOccupancyPercent: 84,
    totalBeds: 1600,
    criticalShortages: ['Anti-Rabies Vaccine', 'ORS Sachets'],
    lastDataSync: '5 mins ago',
  },
  {
    code: 'RAM',
    name: 'Ramgarh District',
    facilitiesCount: 22,
    stockOutRisk: 'LOW',
    bedOccupancyPercent: 62,
    totalBeds: 950,
    criticalShortages: ['None'],
    lastDataSync: '12 mins ago',
  },
  {
    code: 'DHN',
    name: 'Dhanbad District',
    facilitiesCount: 36,
    stockOutRisk: 'LOW',
    bedOccupancyPercent: 71,
    totalBeds: 2100,
    criticalShortages: ['Oxygen Cylinders (Low Buffer)'],
    lastDataSync: '8 mins ago',
  },
];

interface StateDashboardProps {
  onNavigate: (screen: string) => void;
}

export const StateDashboard: React.FC<StateDashboardProps> = ({ onNavigate }) => {
  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10" id="state-dashboard">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-emerald-950/70 via-slate-900 to-slate-900 border border-emerald-800/40 rounded-xl p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-900/60 text-emerald-300 border border-emerald-700/50">
                L2 — State Health Directorate
              </span>
              <span className="text-xs text-slate-400">Jharkhand State Health Operations</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-100 mt-2">Jharkhand State Supply Chain Dashboard</h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              District-wise medicine buffer inventory, intra-state redistribution queues, cold chain telemetry, and disease demand forecasts.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => onNavigate('state_redistribution')}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm"
            >
              <ArrowLeftRight className="w-4 h-4" />
              Intra-State Transfers
            </button>
            <button
              type="button"
              onClick={() => onNavigate('state_alerts')}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold border border-slate-700 flex items-center gap-2 transition-colors"
            >
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              State Alerts
            </button>
          </div>
        </div>
      </div>

      {/* State Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Monitored District Clusters</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">4 Districts</div>
          <div className="text-xs text-slate-400 mt-1">128 Total Primary Health Centres</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Average State Bed Occupancy</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">73.8%</div>
          <div className="text-xs text-slate-400 mt-1">5,190 / 7,050 beds occupied</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">Critical Stock-Out Facilities</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">3 Facilities</div>
          <div className="text-xs text-amber-500 mt-1">Intra-state transfers pending</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-xs font-medium text-slate-400">State FL Model Accuracy</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">93.8%</div>
          <div className="text-xs text-emerald-400 mt-1">Local edge node fully synced</div>
        </div>
      </div>

      {/* District-wise Status Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
          <MapPin className="w-4 h-4 text-emerald-400" />
          District-Wise Inventory & Bed Availability Heatmap
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">District</th>
                <th className="py-3 px-4">PHCs / Facilities</th>
                <th className="py-3 px-4">Stock-out Vulnerability</th>
                <th className="py-3 px-4">Bed Occupancy Rate</th>
                <th className="py-3 px-4">Active Critical Shortages</th>
                <th className="py-3 px-4 text-right">Data Freshness</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {JHARKHAND_DISTRICTS.map((dist) => (
                <tr key={dist.code} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 font-semibold text-slate-100 flex items-center gap-2">
                    <span className="w-6 h-6 rounded bg-slate-800 text-[11px] font-mono flex items-center justify-center text-slate-300">
                      {dist.code}
                    </span>
                    {dist.name}
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">{dist.facilitiesCount} Facilities</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
                        dist.stockOutRisk === 'HIGH'
                          ? 'bg-red-950/70 text-red-300 border-red-800'
                          : dist.stockOutRisk === 'MEDIUM'
                          ? 'bg-amber-950/70 text-amber-300 border-amber-800'
                          : 'bg-emerald-950/70 text-emerald-300 border-emerald-800'
                      }`}
                    >
                      {dist.stockOutRisk}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded-full"
                          style={{ width: `${dist.bedOccupancyPercent}%` }}
                        ></div>
                      </div>
                      <span className="font-mono text-xs">{dist.bedOccupancyPercent}%</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex flex-wrap gap-1">
                      {dist.criticalShortages.map((item, idx) => (
                        <span
                          key={idx}
                          className={`px-1.5 py-0.5 rounded text-[11px] ${
                            item === 'None'
                              ? 'text-slate-500'
                              : 'bg-red-950/60 text-red-300 border border-red-800/60'
                          }`}
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-right text-slate-400 font-mono">{dist.lastDataSync}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
