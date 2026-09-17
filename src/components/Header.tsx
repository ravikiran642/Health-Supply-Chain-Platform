import React from 'react';
import { RefreshCw, Server, Shield, LogOut, Sliders, CheckCircle2, AlertTriangle, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface HeaderProps {
  onOpenSettings: () => void;
  onToggleLogs: () => void;
  logsCount: number;
}

export const Header: React.FC<HeaderProps> = ({ onOpenSettings, onToggleLogs, logsCount }) => {
  const {
    user,
    isAuthenticated,
    logout,
    backendUrl,
    tunnelStatus,
    tunnelLatency,
    pingBackend,
    useMockMode,
    setUseMockMode,
    isLoading,
  } = useAuth();

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-slate-100 sticky top-0 z-30 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Platform Title */}
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-400">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-semibold text-slate-100 text-base sm:text-lg tracking-tight">
                  Health Supply Chain
                </span>
                <span className="hidden sm:inline-block px-2 py-0.5 text-xs font-medium rounded bg-teal-950 text-teal-300 border border-teal-800">
                  RBAC & Auth
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Multi-Tenant Authentication & Geographic Authorization
              </p>
            </div>
          </div>

          {/* Backend Connection Indicator & Quick Controls */}
          <div className="flex items-center space-x-2 sm:space-x-4">
            {/* Endpoint Connection Pill */}
            <div
              onClick={onOpenSettings}
              className="group flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 cursor-pointer transition text-xs"
              title={`Target Endpoint: ${backendUrl}\nClick to inspect or change`}
            >
              <Server className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-200" />
              <div className="flex items-center space-x-1.5">
                <span className="hidden md:inline text-slate-400 font-mono text-[11px] truncate max-w-[200px]">
                  {backendUrl.replace('https://', '')}
                </span>

                {/* Status Dot */}
                {tunnelStatus === 'checking' && (
                  <span className="flex items-center space-x-1 text-amber-400">
                    <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping"></span>
                    <span className="text-[11px]">Connecting</span>
                  </span>
                )}
                {tunnelStatus === 'online' && (
                  <span className="flex items-center space-x-1 text-emerald-400 font-medium">
                    <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                    <span className="text-[11px]">
                      Online {tunnelLatency !== null ? `(${tunnelLatency}ms)` : ''}
                    </span>
                  </span>
                )}
                {tunnelStatus === 'offline' && (
                  <span className="flex items-center space-x-1 text-rose-400 font-medium">
                    <span className="w-2 h-2 rounded-full bg-rose-400"></span>
                    <span className="text-[11px]">Tunnel Offline</span>
                  </span>
                )}
              </div>
              <Sliders className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-200 ml-1" />
            </div>

            {/* Offline Simulation Toggle */}
            <button
              onClick={() => setUseMockMode(!useMockMode)}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border transition flex items-center space-x-1.5 ${
                useMockMode
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30'
                  : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
              title="Toggle Offline Mock Mode for testing UI when Cloudflare tunnel is offline"
            >
              <span className={`w-1.5 h-1.5 rounded-full ${useMockMode ? 'bg-amber-400' : 'bg-slate-500'}`} />
              <span className="hidden lg:inline">{useMockMode ? 'Mock Active' : 'Live Endpoint'}</span>
            </button>

            {/* Ping Refresh Button */}
            <button
              onClick={pingBackend}
              disabled={isLoading || tunnelStatus === 'checking'}
              className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700/80 border border-slate-700 transition"
              title="Re-check backend health ping"
            >
              <RefreshCw
                className={`w-4 h-4 ${tunnelStatus === 'checking' ? 'animate-spin text-teal-400' : ''}`}
              />
            </button>

            {/* API Logs Drawer Button */}
            <button
              onClick={onToggleLogs}
              className="relative px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-slate-300 text-xs font-mono transition flex items-center space-x-1"
              title="View live HTTP API request & response logs"
            >
              <span>API Logs</span>
              {logsCount > 0 && (
                <span className="px-1.5 py-0.2 rounded-full bg-teal-500/30 text-teal-300 text-[10px] font-bold">
                  {logsCount}
                </span>
              )}
            </button>

            {/* User Session / Logout */}
            {isAuthenticated && user && (
              <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
                <div className="hidden sm:flex flex-col text-right">
                  <span className="text-xs font-medium text-slate-200 truncate max-w-[140px]">
                    {user.full_name}
                  </span>
                  <span className="text-[10px] text-teal-400 font-mono">
                    {user.roles && user.roles.length > 0
                      ? typeof user.roles[0] === 'string'
                        ? user.roles[0]
                        : user.roles[0].name
                      : 'User'}
                  </span>
                </div>
                <button
                  onClick={logout}
                  className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition flex items-center space-x-1 text-xs"
                  title="Revoke session and log out"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden md:inline">Sign Out</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
