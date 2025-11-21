import React from 'react';

interface SkillDetailPanelProps {
  skillDetails: any;
}

export const SkillDetailPanel: React.FC<SkillDetailPanelProps> = ({ skillDetails }) => {
  if (!skillDetails) return null;
  return (
    <div className="space-y-3 mb-4">
      <div className="bg-slate-950 p-3 rounded border border-slate-800">
        <div className="text-xs uppercase text-slate-500 mb-2">Growth & Trend</div>
        <div className="flex items-center justify-between text-sm">
          <div>
            <div className="text-green-400 font-bold">{skillDetails.growth_analysis.growth_rate.toFixed(1)}%/yr</div>
            <div className="text-xs text-slate-400">Popularity: {skillDetails.growth_analysis.current_popularity.toFixed(1)}%</div>
          </div>
          <div className="text-xs font-mono px-2 py-1 rounded bg-slate-800 text-purple-300">{skillDetails.growth_analysis.trend.toUpperCase()}</div>
        </div>
      </div>
      <div className="bg-slate-950 p-3 rounded border border-slate-800">
        <div className="text-xs uppercase text-slate-500 mb-2">Forecast (2y)</div>
        <div className="space-y-1 text-xs font-mono">
          {skillDetails.forecast.map((f: any, i: number) => (
            <div key={i} className="flex justify-between">
              <span>{f.year}</span>
              <span className="text-cyan-400">{f.predicted_popularity.toFixed(1)}%</span>
              <span className="text-slate-500">{f.confidence}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-slate-950 p-3 rounded border border-slate-800">
        <div className="text-xs uppercase text-slate-500 mb-2">Mutation Risk</div>
        <div className="w-full h-3 bg-slate-800 rounded overflow-hidden">
          <div className={`h-full ${skillDetails.mutation_risk > 0.7 ? 'bg-red-500' : skillDetails.mutation_risk > 0.4 ? 'bg-yellow-500' : 'bg-green-500'}`} style={{ width: `${skillDetails.mutation_risk * 100}%` }}></div>
        </div>
        <div className="text-xs mt-1 text-slate-400">{(skillDetails.mutation_risk * 100).toFixed(0)}% risk</div>
      </div>
      <div className="bg-slate-950 p-3 rounded border border-slate-800">
        <div className="text-xs uppercase text-slate-500 mb-2">Similar Skills</div>
        <div className="flex flex-wrap gap-2">
          {skillDetails.similar_skills.slice(0,6).map((s: any, i: number) => (
            <span key={i} className="px-2 py-1 text-xs rounded bg-slate-800 text-slate-300 border border-slate-700">{s.skill || s}</span>
          ))}
        </div>
      </div>
    </div>
  );
};
