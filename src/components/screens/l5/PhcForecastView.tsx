import React from 'react';
import { Sparkles, TrendingUp, AlertTriangle, Calendar } from 'lucide-react';

export const PhcForecastView: React.FC = () => {
  const forecastItems = [
    {
      drug: 'Paracetamol 500mg',
      currentStock: '120 strips',
      predicted30DayNeed: '1,450 strips',
      bufferDeficit: '-1,330 strips',
      risk: 'CRITICAL',
      reason: 'Monsoon seasonal viral fever spike',
    },
    {
      drug: 'Amoxicillin 500mg',
      currentStock: '450 strips',
      predicted30DayNeed: '580 strips',
      bufferDeficit: '-130 strips',
      risk: 'REORDER',
      reason: 'Respiratory tract infections in pediatric OPD',
    },
    {
      drug: 'ORS Sachets',
      currentStock: '600 sachets',
      predicted30DayNeed: '800 sachets',
      bufferDeficit: '-200 sachets',
      risk: 'REORDER',
      reason: 'Waterborne gastroenteritis cluster in Ormanjhi block',
    },
    {
      drug: 'Metformin 500mg',
      currentStock: '750 strips',
      predicted30DayNeed: '600 strips',
      bufferDeficit: 'Surplus +150',
      risk: 'ADEQUATE',
      reason: 'Steady chronic NCD patient refill curve',
    },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10" id="phc-forecast-view-screen">
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-teal-400" />
          Ormanjhi PHC AI Demand Forecast & Replenishment
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Predictive consumption model tailored to local Ormanjhi seasonal morbidity trends and historical OPD prescription volume.
        </p>
      </div>

      <div className="space-y-4">
        {forecastItems.map((item) => (
          <div key={item.drug} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="font-bold text-base text-slate-100">{item.drug}</span>
              <span
                className={`px-2 py-0.5 rounded text-xs font-semibold border ${
                  item.risk === 'CRITICAL'
                    ? 'bg-red-950/70 border-red-800 text-red-300'
                    : item.risk === 'REORDER'
                    ? 'bg-amber-950/70 border-amber-800 text-amber-300'
                    : 'bg-emerald-950/70 border-emerald-800 text-emerald-300'
                }`}
              >
                {item.risk}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs bg-slate-950 p-3 rounded-lg border border-slate-800">
              <div>
                <span className="text-slate-500">Current In-Hand:</span>
                <div className="font-bold text-slate-200 mt-0.5">{item.currentStock}</div>
              </div>
              <div>
                <span className="text-slate-500">Projected 30-Day Need:</span>
                <div className="font-bold text-teal-400 mt-0.5">{item.predicted30DayNeed}</div>
              </div>
              <div>
                <span className="text-slate-500">Expected Gap:</span>
                <div
                  className={`font-bold mt-0.5 ${
                    item.bufferDeficit.includes('-') ? 'text-red-400' : 'text-emerald-400'
                  }`}
                >
                  {item.bufferDeficit}
                </div>
              </div>
            </div>

            <div className="text-xs text-slate-400 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-teal-400" />
              Epidemiological Driver: <span className="text-slate-300">{item.reason}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
