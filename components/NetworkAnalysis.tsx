import React, { useEffect, useState } from 'react';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || (process.env.VITE_API_URL) || 'http://localhost:8000';

interface NetworkInsights {
  hub_skills: Array<{ skill: string; pagerank: number; connections?: number }>;
  bridge_skills: Array<{ skill: string; betweenness: number; role?: string }>;
  communities_detected: number;
  network_density: number;
  avg_clustering_coefficient: number;
}

export const NetworkAnalysis: React.FC = () => {
  const [data, setData] = useState<NetworkInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    try {
      setLoading(true);
      const resp = await fetch(`${API_BASE_URL}/api/network-analysis`);
      const json = await resp.json();
      if (json.success) {
        setData(json.network_insights);
        setError(null);
      } else {
        setError('Failed to load network insights');
      }
    } catch (e: any) {
      setError('Backend unreachable');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-full text-cyan-400 font-mono animate-pulse">Loading network...</div>;
  if (error) return <div className="flex items-center justify-center h-full text-red-400 font-mono">{error} <button onClick={load} className="ml-3 px-2 py-1 border border-red-500/40 rounded text-xs">Retry</button></div>;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
          <h3 className="text-xs uppercase text-slate-500 mb-2">Hub Skills (PageRank)</h3>
          <div className="space-y-2 text-xs">
            {data.hub_skills.slice(0,8).map((h,i)=>(
              <div key={i} className="flex justify-between">
                <span className="text-slate-300">{h.skill}</span>
                <span className="text-green-400 font-mono">{h.pagerank.toFixed(3)}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4">
          <h3 className="text-xs uppercase text-slate-500 mb-2">Bridge Skills (Betweenness)</h3>
          <div className="space-y-2 text-xs">
            {data.bridge_skills.slice(0,8).map((b,i)=>(
              <div key={i} className="flex justify-between">
                <span className="text-slate-300">{b.skill}</span>
                <span className="text-purple-400 font-mono">{b.betweenness.toFixed(3)}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 flex flex-col justify-between">
          <div>
            <h3 className="text-xs uppercase text-slate-500 mb-2">Topology Metrics</h3>
            <div className="text-xs space-y-1 font-mono">
              <div>Communities: <span className="text-cyan-400">{data.communities_detected}</span></div>
              <div>Density: <span className="text-cyan-400">{data.network_density}</span></div>
              <div>Avg Clustering: <span className="text-cyan-400">{data.avg_clustering_coefficient}</span></div>
            </div>
          </div>
          <div className="mt-4 text-xs text-slate-500">Hubs & bridges inform resilience planning and cross-discipline mentoring.</div>
        </div>
      </div>
      <div className="flex justify-center">
        <button onClick={load} className="px-6 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/50 rounded text-cyan-400 text-xs font-bold tracking-wide">↻ Refresh Network</button>
      </div>
    </div>
  );
};
