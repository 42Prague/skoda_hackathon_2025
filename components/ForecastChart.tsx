import React from 'react';

interface ForecastPoint { year: number; predicted_popularity: number; confidence: string; }
interface ForecastChartProps { data: ForecastPoint[]; }

export const ForecastChart: React.FC<ForecastChartProps> = ({ data }) => {
  if (!data || data.length === 0) return null;
  return (
    <div className="mt-2 space-y-1 text-xs font-mono">
      {data.map((f, i) => (
        <div key={i} className="flex justify-between">
          <span>{f.year}</span>
          <span className="text-cyan-400">{f.predicted_popularity.toFixed(1)}%</span>
          <span className="text-slate-500">{f.confidence}</span>
        </div>
      ))}
    </div>
  );
};
