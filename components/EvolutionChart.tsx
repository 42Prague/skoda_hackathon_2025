import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TimeSeriesPoint } from '../types';

interface EvolutionChartProps {
  data: TimeSeriesPoint[];
}

const EvolutionChart: React.FC<EvolutionChartProps> = ({ data }) => {
  return (
    <div className="w-full h-[400px] bg-slate-900/50 rounded-xl border border-slate-800 p-4">
       <div className="mb-4">
        <h3 className="text-purple-400 font-mono text-sm tracking-widest">EVOLUTIONARY TRAJECTORY (2015-2026)</h3>
        <p className="text-xs text-slate-500">Y-AXIS: SKILL_ADOPTION_RATE | X-AXIS: TIMELINE</p>
      </div>
      <ResponsiveContainer width="100%" height="85%">
        <AreaChart
          data={data}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorLegacy" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#64748b" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#64748b" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorSoftware" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
            </linearGradient>
             <linearGradient id="colorEV" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
            </linearGradient>
             <linearGradient id="colorAI" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#a855f7" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="year" stroke="#94a3b8" style={{ fontSize: '12px', fontFamily: 'monospace' }} />
          <YAxis stroke="#94a3b8" style={{ fontSize: '12px', fontFamily: 'monospace' }} />
          <Tooltip
            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9' }}
            itemStyle={{ fontFamily: 'monospace' }}
          />
          <Legend wrapperStyle={{ fontFamily: 'monospace', fontSize: '12px' }} />
          <Area type="monotone" dataKey="Legacy" stackId="1" stroke="#64748b" fill="url(#colorLegacy)" />
          <Area type="monotone" dataKey="Software" stackId="1" stroke="#06b6d4" fill="url(#colorSoftware)" />
          <Area type="monotone" dataKey="EV" stackId="1" stroke="#10b981" fill="url(#colorEV)" />
          <Area type="monotone" dataKey="AI" stackId="1" stroke="#a855f7" fill="url(#colorAI)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default EvolutionChart;