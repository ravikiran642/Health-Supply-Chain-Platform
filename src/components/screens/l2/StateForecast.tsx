import React from 'react';
import { TrendingUp, Sparkles, AlertCircle, Calendar } from 'lucide-react';

export const StateForecast: React.FC = () => {
  const forecasts = [
    {
      district: 'Ranchi District',
      projectedConsumptionIncrease: '+22%',
      primarySurgeDriver: 'Seasonal Viral Pyrexia & Dengue Post-Monsoon',
      topShortageRisk: 'Paracetamol 500mg, IV Fluids (NS/RL)',
      bufferHealthDays: '8 Days (Below 14-day threshold)',
      aiAction: 'Recommended Requisition: 45,000 units',
    },
    {
      district: 'Bokaro District',
      projectedConsumptionIncrease: '+18%',
      primarySurgeDriver: 'Industrial Respiratory & Acute Bronchitis',
      topShortageRisk: 'Salbutamol Nebulizer Solution, Amoxicillin',
      bufferHealthDays: '11 Days',
      aiAction: 'Recommended Requisition: 24,000 units',
    },
    {
      district: 'Dhanbad District',
      projectedConsumptionIncrease: '+9%',
      primarySurgeDriver: 'Chronic NCD (Diabetes / Hypertension)',
      topShortageRisk: 'Metformin 500mg, Amlodipine 5mg',
      bufferHealthDays: '21 Days (Adequate)',
      aiAction: 'Normal replenishment schedule',
    },
    {
      district: 'Ramgarh District',
      projectedConsumptionIncrease: '+14%',
      primarySurgeDriver: 'Gastroenteritis & Waterborne Pathogens',
      topShortageRisk: 'ORS Sachets, Zinc Sulfate Tablets',
      bufferHealthDays: '16 Days',
      aiAction: 'Preventive stock buffer transfer ready',
    },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="state-forecast-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-emerald-400" />
          State Demand Forecasting & Epidemic Spike Predictions
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Next 30–90 days aggregated medicine consumption projections for each Jharkhand district powered by decentralized federated learning.
        </p>
      </div>

      <div className="space-y-4">
        {forecasts.map((f) => (
          <div key={f.district} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <span className="font-bold text-base text-slate-100">{f.district}</span>
              <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800">
                {f.projectedConsumptionIncrease} Expected Demand Spike
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <span className="text-slate-500">Epidemiological Driver:</span>
                <div className="text-slate-200 font-medium mt-1">{f.primarySurgeDriver}</div>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <span className="text-slate-500">Vulnerable Medicines:</span>
                <div className="text-red-300 font-medium mt-1">{f.topShortageRisk}</div>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <span className="text-slate-500">Buffer Health:</span>
                <div className="text-amber-300 font-medium mt-1">{f.bufferHealthDays}</div>
              </div>
            </div>
            <div className="text-xs text-slate-400 flex items-center gap-1.5 pt-1">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              AI Recommendation: <strong className="text-slate-200">{f.aiAction}</strong>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
