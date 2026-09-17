import React, { useState } from 'react';
import { Server, CheckCircle2, AlertTriangle, ShieldCheck, Plus, RefreshCw } from 'lucide-react';

interface EdgeNode {
  id: string;
  name: string;
  tier: 'STATE' | 'DISTRICT';
  state: string;
  district?: string;
  ipAddress: string;
  status: 'ONLINE' | 'STANDBY' | 'PENDING_APPROVAL';
  lastHeartbeat: string;
  dataFreshness: string;
  modelAccuracy: number;
}

const INITIAL_NODES: EdgeNode[] = [
  {
    id: 'node-jh-state',
    name: 'Jharkhand State Hub Node',
    tier: 'STATE',
    state: 'Jharkhand',
    ipAddress: '10.14.0.12',
    status: 'ONLINE',
    lastHeartbeat: '12s ago',
    dataFreshness: '2 mins ago',
    modelAccuracy: 93.8,
  },
  {
    id: 'node-jh-ran',
    name: 'Ranchi District Edge Node',
    tier: 'DISTRICT',
    state: 'Jharkhand',
    district: 'Ranchi',
    ipAddress: '10.14.1.20',
    status: 'ONLINE',
    lastHeartbeat: '8s ago',
    dataFreshness: '1 min ago',
    modelAccuracy: 92.4,
  },
  {
    id: 'node-jh-bok',
    name: 'Bokaro District Edge Node',
    tier: 'DISTRICT',
    state: 'Jharkhand',
    district: 'Bokaro',
    ipAddress: '10.14.2.15',
    status: 'ONLINE',
    lastHeartbeat: '15s ago',
    dataFreshness: '4 mins ago',
    modelAccuracy: 91.2,
  },
  {
    id: 'node-jh-ram',
    name: 'Ramgarh District Edge Node',
    tier: 'DISTRICT',
    state: 'Jharkhand',
    district: 'Ramgarh',
    ipAddress: '10.14.3.40',
    status: 'STANDBY',
    lastHeartbeat: '45s ago',
    dataFreshness: '12 mins ago',
    modelAccuracy: 90.5,
  },
  {
    id: 'node-bh-pat',
    name: 'Patna District Edge Node',
    tier: 'DISTRICT',
    state: 'Bihar',
    district: 'Patna',
    ipAddress: '10.22.1.18',
    status: 'ONLINE',
    lastHeartbeat: '5s ago',
    dataFreshness: '1 min ago',
    modelAccuracy: 94.1,
  },
  {
    id: 'node-or-cut',
    name: 'Cuttack District Edge Node',
    tier: 'DISTRICT',
    state: 'Odisha',
    district: 'Cuttack',
    ipAddress: '10.31.2.9',
    status: 'PENDING_APPROVAL',
    lastHeartbeat: '2m ago',
    dataFreshness: 'Pending cert validation',
    modelAccuracy: 89.2,
  },
];

export const NodeManagement: React.FC = () => {
  const [nodes, setNodes] = useState<EdgeNode[]>(INITIAL_NODES);

  const handleApprove = (id: string) => {
    setNodes(nodes.map((n) => (n.id === id ? { ...n, status: 'ONLINE' } : n)));
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10" id="node-management-screen">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Server className="w-5 h-5 text-purple-400" />
            Federated Edge Node Registry
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Authorize state and district edge computation nodes, verify mTLS certificates, monitor heartbeats, and inspect local dataset freshness.
          </p>
        </div>

        <button
          type="button"
          onClick={() => alert('New edge registration token generated: HSC-NODE-KEY-8842-SEC')}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" />
          Register New Node
        </button>
      </div>

      {/* Nodes Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Node Name & Identifier</th>
                <th className="py-3 px-4">Cluster Tier</th>
                <th className="py-3 px-4">Location</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Telemetry Heartbeat</th>
                <th className="py-3 px-4">Data Freshness</th>
                <th className="py-3 px-4">Local Model Acc</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {nodes.map((node) => (
                <tr key={node.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4">
                    <div className="font-semibold text-slate-100">{node.name}</div>
                    <div className="text-[11px] text-slate-400 font-mono">{node.id} ({node.ipAddress})</div>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 border border-slate-700 text-slate-300">
                      {node.tier}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">
                    {node.district ? `${node.district}, ${node.state}` : node.state}
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium border ${
                        node.status === 'ONLINE'
                          ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800'
                          : node.status === 'STANDBY'
                          ? 'bg-amber-950/60 text-amber-400 border-amber-800'
                          : 'bg-purple-950/60 text-purple-300 border-purple-800'
                      }`}
                    >
                      {node.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-400">{node.lastHeartbeat}</td>
                  <td className="py-3.5 px-4 text-slate-300 font-medium">{node.dataFreshness}</td>
                  <td className="py-3.5 px-4 font-mono font-bold text-emerald-400">{node.modelAccuracy}%</td>
                  <td className="py-3.5 px-4 text-right">
                    {node.status === 'PENDING_APPROVAL' ? (
                      <button
                        type="button"
                        onClick={() => handleApprove(node.id)}
                        className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-medium transition-colors"
                      >
                        Approve Node
                      </button>
                    ) : (
                      <span className="text-slate-500 text-xs">Verified</span>
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
