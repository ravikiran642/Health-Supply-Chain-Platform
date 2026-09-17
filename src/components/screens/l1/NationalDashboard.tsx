import React, { useState } from 'react';
import { Globe, TrendingUp, AlertTriangle, Bed, Users, ArrowUpRight, ArrowLeftRight, CheckCircle2 } from 'lucide-react';

interface StateSummary {
  code: string;
  name: string;
  stockOutRisk: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  riskScore: number;
  totalFacilities: number;
  totalBeds: number;
  occupiedBeds: number;
  staffAttendanceRate: number;
  activeCriticalAlerts: number;
}

const STATE_DATA: StateSummary[] = [
  {
    code: 'JH',
    name: 'Jharkhand',
    stockOutRisk: 'MEDIUM',
    riskScore: 38,
    totalFacilities: 1840,
    totalBeds: 12400,
    occupiedBeds: 8900,
    staffAttendanceRate: 88.4,
    activeCriticalAlerts: 3,
  },
  {
    code: 'BH',
    name: 'Bihar',
    stockOutRisk: 'HIGH',
    riskScore: 72,
    totalFacilities: 2450,
    totalBeds: 18200,
    occupiedBeds: 15400,
    staffAttendanceRate: 82.1,
    activeCriticalAlerts: 8,
  },
  {
    code: 'OR',
    name: 'Odisha',
    stockOutRisk: 'LOW',
    riskScore: 24,
    totalFacilities: 1620,
    totalBeds: 11200,
    occupiedBeds: 7200,
    staffAttendanceRate: 91.5,
    activeCriticalAlerts: 1,
  },
  {
    code: 'WB',
    name: 'West Bengal',
    stockOutRisk: 'MEDIUM',
    riskScore: 44,
    totalFacilities: 2180,
    totalBeds: 16500,
    occupiedBeds: 12100,
    staffAttendanceRate: 86.8,
    activeCriticalAlerts: 4,
  },
  {
    code: 'UP',
    name: 'Uttar Pradesh',
    stockOutRisk: 'HIGH',
    riskScore: 68,
    totalFacilities: 4900,
    totalBeds: 34000,
    occupiedBeds: 28900,
    staffAttendanceRate: 84.0,
    activeCriticalAlerts: 12,
  },
  {
    code: 'MH',
    name: 'Maharashtra',
    stockOutRisk: 'LOW',
    riskScore: 19,
    totalFacilities: 3200,
    totalBeds: 26000,
    occupiedBeds: 17500,
    staffAttendanceRate: 94.2,
    activeCriticalAlerts: 2,
  },
];

interface NationalDashboardProps {
  onNavigate: (screen: string) => void;
}

export const NationalDashboard: React.FC<NationalDashboardProps> = ({ onNavigate }) => {
  const [selectedState, setSelectedState] = useState<StateSummary | null>(null);

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'CRITICAL':
        return 'bg-red-950/70 border-red-800 text-red-300';
      case 'HIGH':
        return 'bg-amber-950/70 border-amber-800 text-amber-300';
      case 'MEDIUM':
        return 'bg-yellow-950/70 border-yellow-800 text-yellow-300';
      case 'LOW':
      default:
        return 'bg-emerald-950/70 border-emerald-800 text-emerald-300';
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10" id="national-dashboard">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-blue-950/70 via-slate-900 to-slate-900 border border-blue-800/40 rounded-xl p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-900/60 text-blue-300 border border-blue-700/50">
                L1 — National Command Center
              </span>
              <span className="text-xs text-slate-400">All India Health Supply Chain Grid</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-100 mt-2">National Health Logistics Dashboard</h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              State-wise stock-out vulnerability scores, critical care bed reserves, inter-state redistribution pipelines, and national epidemic surveillance.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => onNavigate('cross_state_redistribution')}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm"
            >
              <ArrowLeftRight className="w-4 h-4" />
              Inter-State Transfers
            </button>
            <button
              type="button"
              onClick={() => onNavigate('national_alerts')}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold border border-slate-700 flex items-center gap-2 transition-colors"
            >
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              National Alerts
            </button>
          </div>
        </div>
      </div>

      {/* National KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">National Average Stock-out Risk</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-2">24.2%</div>
          <div className="text-xs text-slate-400 mt-1">Weighted across 36 States & UTs</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Operational Hospital Beds</span>
            <Bed className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">1,18,300</div>
          <div className="text-xs text-slate-400 mt-1">74.6% national occupancy</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Average Staff Attendance</span>
            <Users className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">87.8%</div>
          <div className="text-xs text-slate-400 mt-1">Across 16,190 health facilities</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Active Inter-State Transfers</span>
            <ArrowLeftRight className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">2 Pipeline</div>
          <div className="text-xs text-emerald-400 mt-1">₹4,25,000 estimated savings</div>
        </div>
      </div>

      {/* State-Wise Heatmap & Comparison Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
              <Globe className="w-4 h-4 text-blue-400" />
              State-Wise Supply Chain Vulnerability & Capacity Map
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">Click any state to view localized logistics buffers and active deficit signals</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">State</th>
                <th className="py-3 px-4">Stock-out Risk</th>
                <th className="py-3 px-4">Vulnerability Score</th>
                <th className="py-3 px-4">Monitored Facilities</th>
                <th className="py-3 px-4">Beds (Occupied / Total)</th>
                <th className="py-3 px-4">Staff Attendance</th>
                <th className="py-3 px-4 text-right">Critical Alerts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {STATE_DATA.map((st) => (
                <tr
                  key={st.code}
                  onClick={() => setSelectedState(st)}
                  className="hover:bg-slate-800/50 cursor-pointer transition-colors"
                >
                  <td className="py-3.5 px-4 font-semibold text-slate-100 flex items-center gap-2">
                    <span className="w-6 h-6 rounded bg-slate-800 text-[11px] font-mono flex items-center justify-center text-slate-300">
                      {st.code}
                    </span>
                    {st.name}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${getRiskColor(st.stockOutRisk)}`}>
                      {st.stockOutRisk}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${
                            st.riskScore > 60 ? 'bg-red-500' : st.riskScore > 35 ? 'bg-amber-500' : 'bg-emerald-500'
                          }`}
                          style={{ width: `${st.riskScore}%` }}
                        ></div>
                      </div>
                      <span className="font-mono text-xs">{st.riskScore}/100</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">{st.totalFacilities.toLocaleString()}</td>
                  <td className="py-3.5 px-4 text-slate-300">
                    <span className="font-medium text-slate-100">{st.occupiedBeds.toLocaleString()}</span> / {st.totalBeds.toLocaleString()} ({Math.round((st.occupiedBeds / st.totalBeds) * 100)}%)
                  </td>
                  <td className="py-3.5 px-4 font-mono text-emerald-400 font-medium">
                    {st.staffAttendanceRate}%
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${st.activeCriticalAlerts > 5 ? 'text-red-400 bg-red-950/60' : 'text-slate-300 bg-slate-800'}`}>
                      {st.activeCriticalAlerts}
                    </span>
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
