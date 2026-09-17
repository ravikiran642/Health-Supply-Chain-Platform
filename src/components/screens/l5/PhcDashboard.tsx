import React from 'react';
import {
  Hospital,
  Package,
  Bed,
  UserCheck,
  AlertCircle,
  ArrowRight,
  TrendingDown,
  CheckCircle2,
  AlertTriangle,
  QrCode,
  Send,
  Truck,
} from 'lucide-react';
import { InventoryItem, BedCategory, StaffMember } from '../../../types';

interface PhcDashboardProps {
  inventory: InventoryItem[];
  beds: BedCategory[];
  staff: StaffMember[];
  onNavigate: (screen: string) => void;
}

export const PhcDashboard: React.FC<PhcDashboardProps> = ({
  inventory = [],
  beds = [],
  staff = [],
  onNavigate,
}) => {
  const safeInventory = inventory || [];
  const safeBeds = beds || [];
  const safeStaff = staff || [];

  const criticalCount = safeInventory.filter((i) => i.status === 'CRITICAL').length;
  const reorderCount = safeInventory.filter((i) => i.status === 'REORDER').length;
  const adequateCount = safeInventory.filter((i) => i.status === 'ADEQUATE').length;

  const totalBeds = safeBeds.reduce((acc, b) => acc + (b.total || 0), 0);
  const occupiedBeds = safeBeds.reduce((acc, b) => acc + (b.occupied || 0), 0);
  const availableBeds = totalBeds - occupiedBeds;

  const presentStaff = safeStaff.filter((s) => s.status === 'PRESENT' || s.status === 'ON_DUTY').length;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10" id="phc-dashboard">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-teal-950/70 via-slate-900 to-slate-900 border border-teal-800/40 rounded-xl p-6 relative overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-900/60 text-teal-300 border border-teal-700/50">
                L5 — Primary Health Centre
              </span>
              <span className="text-xs text-slate-400">Ormanjhi PHC, Ranchi District, Jharkhand</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-100 mt-2">Ormanjhi PHC Facility Dashboard</h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              Real-time clinical drug inventory, inpatient bed occupancy tracker, daily staff attendance roster, and district indent requisitions.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onNavigate('inventory_management')}
              className="px-3.5 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
            >
              <Package className="w-4 h-4" />
              Manage Stock
            </button>
            <button
              type="button"
              onClick={() => onNavigate('stock_request')}
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-colors"
            >
              <Send className="w-4 h-4 text-teal-400" />
              Indent Request
            </button>
          </div>
        </div>
      </div>

      {/* 4 Primary Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Stock Status */}
        <div
          onClick={() => onNavigate('inventory_management')}
          className="bg-slate-900 border border-slate-800 rounded-xl p-5 cursor-pointer hover:border-slate-700 transition-colors"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Drug Inventory Health</span>
            <Package className="w-4 h-4 text-teal-400" />
          </div>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-2xl font-bold text-slate-100">{inventory.length}</span>
            <span className="text-xs text-slate-400">monitored drugs</span>
          </div>
          <div className="flex items-center gap-2 mt-3 text-xs">
            <span className="px-2 py-0.5 rounded bg-red-950/80 text-red-400 border border-red-800 font-semibold">
              🔴 {criticalCount} Critical
            </span>
            <span className="px-2 py-0.5 rounded bg-amber-950/80 text-amber-400 border border-amber-800 font-semibold">
              🟡 {reorderCount} Reorder
            </span>
            <span className="px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800 font-semibold">
              🟢 {adequateCount}
            </span>
          </div>
        </div>

        {/* Card 2: Bed Occupancy */}
        <div
          onClick={() => onNavigate('bed_management')}
          className="bg-slate-900 border border-slate-800 rounded-xl p-5 cursor-pointer hover:border-slate-700 transition-colors"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Bed Occupancy Status</span>
            <Bed className="w-4 h-4 text-blue-400" />
          </div>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-2xl font-bold text-slate-100">{occupiedBeds}</span>
            <span className="text-xs text-slate-400">/ {totalBeds} occupied</span>
          </div>
          <div className="flex items-center justify-between text-xs mt-3">
            <span className="text-emerald-400 font-semibold">{availableBeds} beds vacant</span>
            <span className="text-slate-400 font-mono">{Math.round((occupiedBeds / totalBeds) * 100)}% utilized</span>
          </div>
        </div>

        {/* Card 3: Staff Attendance */}
        <div
          onClick={() => onNavigate('staff_attendance')}
          className="bg-slate-900 border border-slate-800 rounded-xl p-5 cursor-pointer hover:border-slate-700 transition-colors"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Staff On Duty</span>
            <UserCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-2xl font-bold text-emerald-400">{presentStaff}</span>
            <span className="text-xs text-slate-400">/ {staff.length} rostered</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-400 mt-3">
            <CheckCircle2 className="w-3.5 h-3.5" /> Medical Officer Present
          </div>
        </div>

        {/* Card 4: Urgent Alerts */}
        <div
          onClick={() => onNavigate('alerts')}
          className="bg-slate-900 border border-slate-800 rounded-xl p-5 cursor-pointer hover:border-slate-700 transition-colors"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Facility Active Alerts</span>
            <AlertCircle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-2xl font-bold text-amber-400">2 Active</span>
          </div>
          <div className="text-xs text-slate-400 mt-3 truncate">
            Paracetamol stock-out & Cold freezer warning
          </div>
        </div>
      </div>

      {/* Critical Shortage Alert Banner */}
      {criticalCount > 0 && (
        <div className="p-4 bg-red-950/60 border border-red-800/80 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-900/80 text-red-200">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-red-200">
                Critical Stock-Out Alert: {criticalCount} Life-Saving Drugs Below Safety Buffer
              </h3>
              <p className="text-xs text-red-300 mt-0.5">
                Paracetamol 500mg, BCG Vaccine, and Human Insulin Regular require immediate district replenishment or inter-PHC transfer.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onNavigate('stock_request')}
              className="px-3.5 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded text-xs font-semibold whitespace-nowrap transition-colors"
            >
              Order from District
            </button>
            <button
              type="button"
              onClick={() => onNavigate('redistribution_requests')}
              className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded text-xs font-semibold whitespace-nowrap transition-colors"
            >
              Transfer Inbound
            </button>
          </div>
        </div>
      )}

      {/* Quick Action Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Clinical Drug Stock Status Snapshot */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
              <Package className="w-4 h-4 text-teal-400" />
              Clinical Drug Stock Status (🔴 🟡 🟢)
            </h2>
            <button
              type="button"
              onClick={() => onNavigate('inventory_management')}
              className="text-xs text-teal-400 hover:text-teal-300 font-medium"
            >
              Full Inventory &rarr;
            </button>
          </div>

          <div className="space-y-2.5">
            {safeInventory.slice(0, 5).map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs"
              >
                <div>
                  <div className="font-semibold text-slate-200">{item.name}</div>
                  <div className="text-slate-500 text-[11px] font-mono mt-0.5">
                    Batch: {item.batchNumber} • Exp: {item.expiryDate}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-slate-100">
                    {item.currentStock} <span className="text-[11px] font-normal text-slate-400">{item.unit}</span>
                  </div>
                  <span
                    className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold mt-1 ${
                      item.status === 'CRITICAL'
                        ? 'bg-red-950 text-red-400 border border-red-800'
                        : item.status === 'REORDER'
                        ? 'bg-amber-950 text-amber-400 border border-amber-800'
                        : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                    }`}
                  >
                    {item.status === 'CRITICAL' ? '🔴 Critical' : item.status === 'REORDER' ? '🟡 Reorder' : '🟢 Adequate'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live Bed Utilization Snapshot */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
              <Bed className="w-4 h-4 text-blue-400" />
              Inpatient Bed Utilization
            </h2>
            <button
              type="button"
              onClick={() => onNavigate('bed_management')}
              className="text-xs text-blue-400 hover:text-blue-300 font-medium"
            >
              Update Occupancy &rarr;
            </button>
          </div>

          <div className="space-y-3">
            {safeBeds.map((b) => (
              <div key={b.id} className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs space-y-1.5">
                <div className="flex justify-between font-medium text-slate-200">
                  <span>{b.name}</span>
                  <span className="font-mono text-slate-300">
                    {b.occupied} / {b.total} ({b.total - b.occupied} vacant)
                  </span>
                </div>
                <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      b.occupied / b.total > 0.85
                        ? 'bg-red-500'
                        : b.occupied / b.total > 0.6
                        ? 'bg-amber-500'
                        : 'bg-emerald-500'
                    }`}
                    style={{ width: `${(b.occupied / b.total) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
