import React from 'react';

export function App() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col items-center justify-center p-6">
      <div className="max-w-2xl w-full bg-slate-800 rounded-xl p-8 border border-slate-700 shadow-xl space-y-4">
        <h1 className="text-2xl font-bold text-emerald-400">
          Health Supply Chain Platform
        </h1>
        <p className="text-sm text-slate-300">
          FastAPI &amp; PyTorch Federated Learning Backend Service.
        </p>
        <div className="bg-slate-950 p-4 rounded-lg font-mono text-xs text-slate-400 space-y-1">
          <div>Status: Active</div>
          <div>Stack: Python 3.11+, FastAPI, PostgreSQL 16, Redis 7, PyTorch</div>
          <div>Endpoints: /api/v1/fl/trigger-round, /api/v1/forecast/facility/:id</div>
        </div>
      </div>
    </div>
  );
}
export default App;
