import React, { useState } from 'react';
import { AlertNotification, RoleTier } from '../../../types';
import { INITIAL_ALERTS } from '../../../data/mockAppData';
import {
  Bell,
  AlertTriangle,
  AlertOctagon,
  Clock,
  CheckCheck,
  Filter,
  CheckCircle,
  Truck,
  Flame,
} from 'lucide-react';

interface NotificationsScreenProps {
  alerts?: AlertNotification[];
  tier?: RoleTier;
  onMarkAsRead?: (id: string) => void;
  onMarkAllAsRead?: () => void;
  onNavigateToScreen?: (screenId: string) => void;
  onNavigate?: (screenId: string) => void;
}

export const NotificationsScreen: React.FC<NotificationsScreenProps> = ({
  alerts,
  tier = 'L5',
  onMarkAsRead = (_id: string) => {},
  onMarkAllAsRead = () => {},
  onNavigateToScreen,
  onNavigate,
}) => {
  const [filterType, setFilterType] = useState<string>('ALL');

  const safeAlerts = Array.isArray(alerts) && alerts.length > 0 ? alerts : (INITIAL_ALERTS || []);
  const navigateFn = onNavigateToScreen || onNavigate || (() => {});

  const filteredAlerts = safeAlerts.filter((a) => {
    if (filterType === 'ALL') return true;
    if (filterType === 'UNREAD') return !a.isRead;
    if (filterType === 'CRITICAL') return a.severity === 'CRITICAL';
    if (filterType === 'STOCK_OUT') return a.type === 'STOCK_OUT';
    if (filterType === 'TRANSFERS') return a.type === 'TRANSFER_REQUEST';
    return true;
  });

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-950/70 border-red-800 text-red-300';
      case 'WARNING':
        return 'bg-amber-950/70 border-amber-800 text-amber-300';
      case 'INFO':
      default:
        return 'bg-blue-950/70 border-blue-800 text-blue-300';
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'STOCK_OUT':
        return <AlertTriangle className="w-5 h-5 text-red-400" />;
      case 'COLD_CHAIN':
        return <Flame className="w-5 h-5 text-amber-400" />;
      case 'TRANSFER_REQUEST':
        return <Truck className="w-5 h-5 text-emerald-400" />;
      case 'OUTBREAK_SIGNAL':
        return <AlertOctagon className="w-5 h-5 text-purple-400" />;
      default:
        return <Bell className="w-5 h-5 text-blue-400" />;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="notifications-screen-container">
      {/* Top action header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Bell className="w-5 h-5 text-emerald-400" />
            Alerts & Notifications
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time stock-out, cold chain excursions, batch expiry, and redistribution signals for your operational scope.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onMarkAllAsRead}
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <CheckCheck className="w-4 h-4 text-emerald-400" />
            Mark All as Read
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-800 text-xs">
        <span className="text-slate-500 flex items-center gap-1 px-1">
          <Filter className="w-3.5 h-3.5" /> Filter:
        </span>
        {[
          { id: 'ALL', label: `All (${safeAlerts.length})` },
          { id: 'UNREAD', label: `Unread (${safeAlerts.filter((a) => !a.isRead).length})` },
          { id: 'CRITICAL', label: `Critical (${safeAlerts.filter((a) => a.severity === 'CRITICAL').length})` },
          { id: 'STOCK_OUT', label: 'Stock-outs' },
          { id: 'TRANSFERS', label: 'Transfers' },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setFilterType(tab.id)}
            className={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-colors ${
              filterType === tab.id
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Alerts list */}
      <div className="space-y-3">
        {filteredAlerts.length === 0 ? (
          <div className="p-12 text-center bg-slate-900/60 border border-slate-800 rounded-xl">
            <CheckCircle className="w-10 h-10 text-emerald-500 mx-auto mb-3 opacity-80" />
            <h3 className="text-base font-semibold text-slate-200">No Notifications</h3>
            <p className="text-sm text-slate-400 mt-1">All supply chain signals are normal for the selected filter.</p>
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-4 rounded-xl border transition-all ${
                alert.isRead
                  ? 'bg-slate-900/60 border-slate-800/80 text-slate-400'
                  : 'bg-slate-900 border-slate-700/80 text-slate-200 shadow-md'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3.5">
                  <div className="p-2.5 rounded-lg bg-slate-800 border border-slate-700 shrink-0">
                    {getIcon(alert.type)}
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${getSeverityBadge(alert.severity)}`}>
                        {alert.severity}
                      </span>
                      <span className="text-xs px-2 py-0.5 bg-slate-800 text-slate-300 rounded font-mono">
                        {alert.type.replace('_', ' ')}
                      </span>
                      {alert.facility && (
                        <span className="text-xs text-slate-400 font-medium">
                          📍 {alert.facility}
                        </span>
                      )}
                      {alert.district && (
                        <span className="text-xs text-slate-400">
                          {alert.district} District
                        </span>
                      )}
                    </div>

                    <h3 className={`text-sm font-semibold mt-1.5 ${alert.isRead ? 'text-slate-300' : 'text-slate-100'}`}>
                      {alert.title}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                      {alert.description}
                    </p>

                    <div className="flex items-center gap-4 mt-3 text-[11px] text-slate-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {alert.timestamp}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col items-end gap-2 shrink-0">
                  {!alert.isRead && (
                    <button
                      type="button"
                      onClick={() => onMarkAsRead(alert.id)}
                      className="text-xs text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
                    >
                      Mark Read
                    </button>
                  )}
                  {alert.actionRequired && (
                    <button
                      type="button"
                      onClick={() => {
                        if (tier === 'L5') navigateFn('inventory_management');
                        else if (tier === 'L3') navigateFn('redistribution_recommendations');
                        else if (tier === 'L2') navigateFn('state_redistribution');
                        else if (tier === 'L1') navigateFn('cross_state_redistribution');
                        else navigateFn('admin_dashboard');
                      }}
                      className="px-2.5 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 text-xs font-medium rounded border border-emerald-600/40 transition-colors"
                    >
                      Take Action
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
