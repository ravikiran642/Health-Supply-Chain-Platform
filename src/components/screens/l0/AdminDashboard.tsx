import React from 'react';
import {
  Activity,
  Server,
  Cpu,
  Users,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Database,
  ArrowUpRight,
  Play,
  RotateCw,
} from 'lucide-react';

interface AdminDashboardProps {
  onNavigate: (screen: string) => void;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ onNavigate }) => {
  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10" id="l0-admin-dashboard">
      {/* Top Welcome / Status Banner */}
      <div className="bg-gradient-to-r from-purple-950/70 via-slate-900 to-slate-900 border border-purple-800/40 rounded-xl p-6 relative overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-900/60 text-purple-300 border border-purple-700/50">
                L0 — Platform Control Plane
              </span>
              <span className="flex items-center gap-1 text-xs text-emerald-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                System Healthy
              </span>
            </div>
            <h1 className="text-2xl font-bold text-slate-100 mt-2">Central System & FL Admin Dashboard</h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              Real-time platform telemetry, federated learning round orchestration, node registry, and access control across 32 state and district clusters.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => onNavigate('fl_orchestration')}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm"
            >
              <Cpu className="w-4 h-4" />
              FL Orchestrator
            </button>
            <button
              type="button"
              onClick={() => onNavigate('audit_logs')}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold border border-slate-700 flex items-center gap-2 transition-colors"
            >
              <ShieldCheck className="w-4 h-4 text-purple-400" />
              Audit Trail
            </button>
          </div>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Active Nodes</span>
            <Server className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">32 / 32</div>
          <div className="flex items-center gap-1 text-xs text-emerald-400 mt-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> 100% online telemetry
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Current FL Round</span>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">Round #14</div>
          <div className="flex items-center gap-1 text-xs text-cyan-400 mt-1">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            68% convergence reached
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Global Model Accuracy</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">93.4%</div>
          <div className="flex items-center gap-1 text-xs text-emerald-400 mt-1">
            <ArrowUpRight className="w-3.5 h-3.5" /> +1.3% from Round #13
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Registered Users</span>
            <Users className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">24 Accounts</div>
          <div className="text-xs text-slate-400 mt-1">Across 5 hierarchical tiers</div>
        </div>
      </div>

      {/* System Infrastructure Health & Active FL Round */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 2 Cols: System Telemetry */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
              <Database className="w-4 h-4 text-emerald-400" />
              Core Microservices & Database Status
            </h2>
            <span className="text-xs px-2 py-0.5 bg-emerald-950/60 text-emerald-400 border border-emerald-800 rounded">
              All Services Operational
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { name: 'FastAPI Backend Core', status: 'Healthy', latency: '14ms', load: '12% CPU' },
              { name: 'PostgreSQL Relational DB', status: 'Healthy', latency: '3ms', load: 'Conn: 18/100' },
              { name: 'Redis Cache & Pub/Sub', status: 'Healthy', latency: '<1ms', load: 'Hit rate: 98.4%' },
              { name: 'Celery FL Worker Cluster', status: 'Active', latency: '28 workers', load: 'Queue: 0 pending' },
            ].map((svc) => (
              <div key={svc.name} className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-200">{svc.name}</span>
                  <span className="flex items-center gap-1 text-xs text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" /> {svc.status}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 mt-2">
                  <span>Latency: <strong className="text-slate-300">{svc.latency}</strong></span>
                  <span>{svc.load}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Quick Actions */}
          <div className="pt-3 border-t border-slate-800 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => onNavigate('user_management')}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded border border-slate-700 transition-colors"
            >
              Manage Users & Roles
            </button>
            <button
              type="button"
              onClick={() => onNavigate('node_management')}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded border border-slate-700 transition-colors"
            >
              Approve District Nodes
            </button>
            <button
              type="button"
              onClick={() => onNavigate('system_settings')}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded border border-slate-700 transition-colors"
            >
              Configure Master Data
            </button>
          </div>
        </div>

        {/* 1 Col: Live FL Status */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-400" />
              FL Round #14 Live
            </h2>
            <span className="text-xs font-mono text-purple-300">FedAvg</span>
          </div>

          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs text-slate-400 mb-1">
                <span>Convergence Progress</span>
                <span className="font-semibold text-purple-300">68%</span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-purple-500 rounded-full transition-all duration-500" style={{ width: '68%' }}></div>
              </div>
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Participating Nodes:</span>
                <span className="font-semibold text-slate-200">28 of 32 (87.5%)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Current Loss:</span>
                <span className="font-mono text-emerald-400">0.082</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Est. Round Completion:</span>
                <span className="text-slate-300">~14 minutes</span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onNavigate('fl_orchestration')}
              className="w-full py-2 bg-purple-950/80 hover:bg-purple-900 text-purple-300 border border-purple-700/60 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
            >
              Open FL Orchestration
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
