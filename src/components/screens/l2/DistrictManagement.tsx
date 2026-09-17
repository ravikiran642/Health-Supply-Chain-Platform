import React from 'react';
import { Building2, Server, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export const DistrictManagement: React.FC = () => {
  const districtNodes = [
    {
      id: 'dist-ran',
      name: 'Ranchi District Health Office',
      civilSurgeon: 'Dr. Prabhat Kumar',
      phcCount: 42,
      nodeStatus: 'ONLINE',
      syncFrequency: 'Every 5 mins',
      freshness: '1 min ago',
      stockCompliance: '94.2%',
    },
    {
      id: 'dist-bok',
      name: 'Bokaro District Health Office',
      civilSurgeon: 'Dr. A.B. Prasad',
      phcCount: 28,
      nodeStatus: 'ONLINE',
      syncFrequency: 'Every 5 mins',
      freshness: '4 mins ago',
      stockCompliance: '88.0%',
    },
    {
      id: 'dist-ram',
      name: 'Ramgarh District Health Office',
      civilSurgeon: 'Dr. Neeta Tirkey',
      phcCount: 22,
      nodeStatus: 'ONLINE',
      syncFrequency: 'Every 15 mins',
      freshness: '11 mins ago',
      stockCompliance: '96.5%',
    },
    {
      id: 'dist-dhn',
      name: 'Dhanbad District Health Office',
      civilSurgeon: 'Dr. S.K. Jha',
      phcCount: 36,
      nodeStatus: 'ONLINE',
      syncFrequency: 'Every 5 mins',
      freshness: '6 mins ago',
      stockCompliance: '91.8%',
    },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="district-management-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Building2 className="w-5 h-5 text-emerald-400" />
          Jharkhand District Health Clusters & Nodes
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Monitor district health headquarters, civil surgeon contact directories, automated telemetry sync intervals, and compliance rates.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {districtNodes.map((dist) => (
          <div key={dist.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-base text-slate-100">{dist.name}</span>
              <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800">
                {dist.nodeStatus}
              </span>
            </div>
            <div className="text-xs text-slate-400">Civil Surgeon In-Charge: <strong className="text-slate-200">{dist.civilSurgeon}</strong></div>
            <div className="grid grid-cols-2 gap-2 bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
              <div>
                <span className="text-slate-500">Connected PHCs:</span>
                <div className="font-semibold text-slate-200 mt-0.5">{dist.phcCount} Facilities</div>
              </div>
              <div>
                <span className="text-slate-500">Stock Compliance:</span>
                <div className="font-semibold text-emerald-400 mt-0.5">{dist.stockCompliance}</div>
              </div>
              <div>
                <span className="text-slate-500">Sync Interval:</span>
                <div className="text-slate-300 mt-0.5">{dist.syncFrequency}</div>
              </div>
              <div>
                <span className="text-slate-500">Last Telemetry:</span>
                <div className="text-slate-300 mt-0.5 font-mono">{dist.freshness}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
