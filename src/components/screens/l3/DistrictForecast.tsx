import React from 'react';
import { LineChart, Sparkles, TrendingUp } from 'lucide-react';

export const DistrictForecast: React.FC = () => {
  const phcForecasts = [
    {
      phc: 'Ormanjhi PHC',
      projected30DayDemand: '2,400 strips Paracetamol, 65 vials Insulin',
      predictedRisk: 'HIGH — Stock-out in 48 hours without replenishment',
      recommendedAction: 'Approve pending indent IND-RAN-ORI-2026-081',
      confidence: '94.2%',
    },
    {
      phc: 'Kanke PHC',
      projected30DayDemand: '1,800 strips Paracetamol, 400 Amoxicillin',
      predictedRisk: 'LOW — 28 days buffer available in central dispensary',
      recommendedAction: 'Safe to source 600 strips for Ormanjhi redistribution',
      confidence: '95.8%',
    },
    {
      phc: 'Bundu PHC',
      projected30DayDemand: '950 ORS sachets, 300 Zinc tabs',
      predictedRisk: 'MEDIUM — Moderate pediatric fever surge expected',
      recommendedAction: 'Maintain safety stock at 350 units',
      confidence: '91.0%',
    },
    {
      phc: 'Silli PHC',
      projected30DayDemand: '700 Metformin, 500 Amlodipine',
      predictedRisk: 'LOW — Stable chronic disease baseline',
      recommendedAction: 'Standard monthly supply dispatch',
      confidence: '93.5%',
    },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="district-forecast-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <LineChart className="w-5 h-5 text-amber-400" />
          Per-PHC 30-Day Demand & Outbreak Forecast
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Machine-learning powered 30-day medicine consumption projections and risk scores for all Ranchi district health centers.
        </p>
      </div>

      <div className="space-y-4">
        {phcForecasts.map((pf) => (
          <div key={pf.phc} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <span className="font-bold text-base text-slate-100">{pf.phc}</span>
              <span className="text-xs px-2.5 py-0.5 rounded font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800">
                Model Confidence: {pf.confidence}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <span className="text-slate-500">Projected 30-Day Consumption:</span>
                <div className="text-slate-200 font-medium mt-1">{pf.projected30DayDemand}</div>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <span className="text-slate-500">Stock-out Vulnerability:</span>
                <div className={`font-medium mt-1 ${pf.predictedRisk.includes('HIGH') ? 'text-red-300' : pf.predictedRisk.includes('MEDIUM') ? 'text-amber-300' : 'text-emerald-300'}`}>
                  {pf.predictedRisk}
                </div>
              </div>
            </div>
            <div className="text-xs text-slate-400 flex items-center gap-1.5 pt-1">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              Prescribed Action: <strong className="text-slate-200">{pf.recommendedAction}</strong>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
