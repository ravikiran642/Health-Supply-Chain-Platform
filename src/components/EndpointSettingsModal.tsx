import React, { useState } from 'react';
import { X, Server, RefreshCw, CheckCircle2, AlertCircle, RotateCcw, ExternalLink } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { DEFAULT_BACKEND_URL } from '../data/seedAccounts';

interface EndpointSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const EndpointSettingsModal: React.FC<EndpointSettingsModalProps> = ({ isOpen, onClose }) => {
  const {
    backendUrl,
    updateBackendUrl,
    resetBackendUrl,
    tunnelStatus,
    tunnelLatency,
    tunnelError,
    pingBackend,
    useMockMode,
    setUseMockMode,
  } = useAuth();

  const [inputUrl, setInputUrl] = useState<string>(backendUrl);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSave = () => {
    updateBackendUrl(inputUrl);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  const handleReset = () => {
    setInputUrl(DEFAULT_BACKEND_URL);
    resetBackendUrl();
  };

  const handleTestPing = async () => {
    setIsTesting(true);
    await pingBackend();
    setIsTesting(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden text-slate-200">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-lg bg-teal-500/10 border border-teal-500/30 text-teal-400">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-100 text-base">Backend Endpoint Configuration</h3>
              <p className="text-xs text-slate-400">FastAPI Authentication & RBAC Server</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5">
          {/* Target URL Input */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Backend Service URL
            </label>
            <div className="relative">
              <input
                type="text"
                value={inputUrl}
                onChange={(e) => setInputUrl(e.target.value)}
                placeholder="https://..."
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-xs sm:text-sm font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
              />
            </div>
            <div className="flex items-center justify-between mt-2">
              <span className="text-[11px] text-slate-500 font-mono">
                Default: {DEFAULT_BACKEND_URL}
              </span>
              <button
                type="button"
                onClick={handleReset}
                className="text-xs text-teal-400 hover:text-teal-300 flex items-center space-x-1"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset to Default</span>
              </button>
            </div>
          </div>

          {/* Connection Status Box */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-300">Live Health Status:</span>
              <div className="flex items-center space-x-1.5">
                {tunnelStatus === 'online' ? (
                  <span className="inline-flex items-center space-x-1 text-emerald-400 text-xs font-semibold">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Reachable ({tunnelLatency}ms)</span>
                  </span>
                ) : tunnelStatus === 'checking' ? (
                  <span className="inline-flex items-center space-x-1 text-amber-400 text-xs">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Probing...</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center space-x-1 text-rose-400 text-xs font-semibold">
                    <AlertCircle className="w-4 h-4" />
                    <span>Unreachable</span>
                  </span>
                )}
              </div>
            </div>

            {tunnelError && (
              <div className="mt-2 text-xs bg-rose-950/40 border border-rose-800/60 rounded-lg p-2.5 text-rose-300 space-y-1">
                <div className="font-semibold flex items-center space-x-1">
                  <span>Diagnostic Report:</span>
                </div>
                <p className="text-[11px] leading-relaxed text-rose-200/90">{tunnelError}</p>
                <div className="text-[11px] text-slate-400 pt-1 border-t border-rose-900/50">
                  Tip: Cloudflare TryCloudflare tunnels (<code className="text-slate-300">*.trycloudflare.com</code>)
                  are temporary. If the local tunnel is paused or re-run, check that <code className="text-teal-300">cloudflared tunnel --url http://localhost:8000</code> is actively running.
                </div>
              </div>
            )}
          </div>

          {/* Offline Mock Mode Option */}
          <div className="flex items-center justify-between p-3.5 rounded-xl border border-amber-500/20 bg-amber-500/5">
            <div>
              <div className="text-xs font-medium text-amber-200">Offline Simulation Mode</div>
              <div className="text-[11px] text-slate-400">
                Simulate auth responses locally when the Cloudflare tunnel is temporarily paused
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={useMockMode}
                onChange={(e) => setUseMockMode(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500"></div>
            </label>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-950/60">
          <button
            onClick={handleTestPing}
            disabled={isTesting}
            className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center space-x-1.5 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isTesting ? 'animate-spin text-teal-400' : ''}`} />
            <span>{isTesting ? 'Pinging...' : 'Test Connection'}</span>
          </button>

          <div className="flex items-center space-x-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            >
              Close
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-500 text-white transition shadow-sm"
            >
              {saveSuccess ? 'Saved!' : 'Apply Endpoint'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
