import React, { useState } from 'react';
import { X, Trash2, ChevronDown, ChevronUp, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ApiLogEntry } from '../types';

interface ApiLogsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ApiLogsDrawer: React.FC<ApiLogsDrawerProps> = ({ isOpen, onClose }) => {
  const { apiLogs, clearLogs, backendUrl } = useAuth();
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  if (!isOpen) return null;

  const toggleExpand = (id: string) => {
    setExpandedLogId(expandedLogId === id ? null : id);
  };

  const getStatusColor = (status: number) => {
    if (status >= 200 && status < 300) return 'text-emerald-400 bg-emerald-950/70 border-emerald-800';
    if (status >= 400 && status < 500) return 'text-amber-400 bg-amber-950/70 border-amber-800';
    return 'text-rose-400 bg-rose-950/70 border-rose-800';
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[500px] md:w-[600px] bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/70">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="font-semibold text-slate-100 text-sm">Auth API Request Inspector</h3>
            <span className="px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-300 text-[11px] font-mono font-bold">
              {apiLogs.length} calls
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono truncate max-w-[360px] mt-0.5">
            Target: {backendUrl}
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {apiLogs.length > 0 && (
            <button
              onClick={clearLogs}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
              title="Clear all API logs"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Logs List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {apiLogs.length === 0 ? (
          <div className="text-center py-16 text-slate-500 space-y-2">
            <Clock className="w-8 h-8 mx-auto opacity-50 text-slate-400" />
            <p className="text-sm">No API calls recorded yet</p>
            <p className="text-xs text-slate-600">
              Submit login, refresh tokens, or test permissions to view live traces.
            </p>
          </div>
        ) : (
          apiLogs.map((log: ApiLogEntry) => {
            const isExpanded = expandedLogId === log.id;
            return (
              <div
                key={log.id}
                className="rounded-xl border border-slate-800 bg-slate-950/70 overflow-hidden text-xs transition"
              >
                {/* Row Header */}
                <div
                  onClick={() => toggleExpand(log.id)}
                  className="p-3 cursor-pointer hover:bg-slate-900/60 flex items-center justify-between transition"
                >
                  <div className="flex items-center space-x-2.5 truncate">
                    <span
                      className={`px-1.5 py-0.5 rounded font-mono font-bold text-[10px] ${
                        log.method === 'GET'
                          ? 'bg-blue-950 text-blue-300'
                          : 'bg-emerald-950 text-emerald-300'
                      }`}
                    >
                      {log.method}
                    </span>
                    <span className="font-mono text-slate-200 truncate max-w-[220px] sm:max-w-[280px]">
                      {log.url.replace(backendUrl, '') || log.url}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    <span
                      className={`px-2 py-0.5 rounded-full font-mono text-[10px] font-semibold border ${getStatusColor(
                        log.status
                      )}`}
                    >
                      {log.status > 0 ? log.status : 'ERR'}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {log.durationMs}ms
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                    )}
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="p-3 border-t border-slate-800/80 bg-slate-900/40 space-y-2.5 font-mono text-[11px]">
                    <div>
                      <span className="text-slate-500 block text-[10px] uppercase font-semibold">
                        Timestamp & Full URL
                      </span>
                      <span className="text-slate-300 break-all">{log.url}</span>
                      <span className="text-slate-500 text-[10px] ml-2">({log.timestamp})</span>
                    </div>

                    {log.requestPayload && (
                      <div>
                        <span className="text-slate-500 block text-[10px] uppercase font-semibold">
                          Request Payload
                        </span>
                        <pre className="p-2 bg-slate-950 rounded-lg text-slate-300 overflow-x-auto text-[10px]">
                          {typeof log.requestPayload === 'object'
                            ? JSON.stringify(log.requestPayload, null, 2)
                            : String(log.requestPayload)}
                        </pre>
                      </div>
                    )}

                    {log.error && (
                      <div>
                        <span className="text-rose-400 block text-[10px] uppercase font-semibold">
                          Error Message
                        </span>
                        <div className="p-2 bg-rose-950/40 border border-rose-900/60 rounded-lg text-rose-200 text-[10px] break-all">
                          {log.error}
                        </div>
                      </div>
                    )}

                    {log.responseBody !== undefined && (
                      <div>
                        <span className="text-slate-500 block text-[10px] uppercase font-semibold">
                          Response Body
                        </span>
                        <pre className="p-2 bg-slate-950 rounded-lg text-teal-300/90 overflow-x-auto text-[10px] max-h-48 overflow-y-auto">
                          {typeof log.responseBody === 'object'
                            ? JSON.stringify(log.responseBody, null, 2)
                            : String(log.responseBody)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
