import React, { useEffect, useState } from 'react';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || (process.env.VITE_API_URL) || 'http://localhost:8000';

interface StrategicInsights {
  emerging_skills: Array<{
    skill: string;
    category: string;
    growth_rate: number;
    current_popularity: number;
    urgency: string;
  }>;
  declining_skills: Array<{
    skill: string;
    category: string;
    decline_rate: number;
    current_popularity: number;
    risk_level: string;
  }>;
  category_health: {
    [key: string]: {
      growth_rate: number;
      current_avg_popularity: number;
      health: string;
      skills_count: number;
    };
  };
  upskilling_priorities: Array<{
    skill: string;
    reason: string;
    urgency: string;
    category: string;
  }>;
  phase_out_recommendations: Array<{
    skill: string;
    reason: string;
    risk_level: string;
    category: string;
  }>;
  summary: {
    high_growth_skills: number;
    critical_risks: number;
    thriving_categories: number;
  };
}

export const InsightsDashboard: React.FC = () => {
  const [insights, setInsights] = useState<StrategicInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadInsights();
  }, []);

  const [network, setNetwork] = useState<any>(null);

  const loadInsights = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/insights`);
      const data = await response.json();

      if (data.success) {
        setInsights(data.strategic_insights);
      } else {
        setError('Failed to load insights');
      }

      const netResp = await fetch(`${API_BASE_URL}/api/network-analysis`);
      const netJson = await netResp.json();
      if (netJson.success) setNetwork(netJson.network_insights);
    } catch (err) {
      console.error('Failed to load strategic insights:', err);
      setError('Backend unavailable');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-cyan-400 font-mono animate-pulse">Loading strategic insights...</div>
      </div>
    );
  }

  if (error || !insights) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-400 font-mono">
          ⚠️ {error || 'No insights available'}
          <button
            onClick={loadInsights}
            className="ml-4 px-3 py-1 bg-cyan-500/20 hover:bg-cyan-500/30 rounded border border-cyan-500/50 text-cyan-400 text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      'Legacy Engineering': 'bg-slate-600',
      'Software/Cloud': 'bg-cyan-600',
      'E-Mobility': 'bg-green-600',
      'AI/Emerging': 'bg-purple-600'
    };
    return colors[category] || 'bg-gray-600';
  };

  const getHealthColor = (health: string) => {
    const colors: { [key: string]: string } = {
      'thriving': 'text-green-400',
      'growing': 'text-cyan-400',
      'stable': 'text-yellow-400',
      'declining': 'text-red-400'
    };
    return colors[health] || 'text-gray-400';
  };

  return (
    <div className="h-full overflow-y-auto space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-green-900/30 to-green-900/10 border border-green-500/30 rounded-lg p-4">
          <div className="text-3xl font-bold text-green-400">{insights.summary.high_growth_skills}</div>
          <div className="text-sm text-green-300/70 mt-1">High-Growth Skills</div>
          <div className="text-xs text-slate-400 mt-2">Emerging competencies with explosive demand</div>
        </div>

        <div className="bg-gradient-to-br from-red-900/30 to-red-900/10 border border-red-500/30 rounded-lg p-4">
          <div className="text-3xl font-bold text-red-400">{insights.summary.critical_risks}</div>
          <div className="text-sm text-red-300/70 mt-1">Critical Risk Skills</div>
          <div className="text-xs text-slate-400 mt-2">Rapidly declining - immediate action required</div>
        </div>

        <div className="bg-gradient-to-br from-purple-900/30 to-purple-900/10 border border-purple-500/30 rounded-lg p-4">
          <div className="text-3xl font-bold text-purple-400">{insights.summary.thriving_categories}</div>
          <div className="text-sm text-purple-300/70 mt-1">Thriving Categories</div>
          <div className="text-xs text-slate-400 mt-2">Skill domains with strong positive momentum</div>
        </div>
      </div>

      {/* Category Health */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
        <h3 className="text-xl font-bold text-white mb-4 uppercase tracking-wide">Category Health Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(insights.category_health).map(([category, data]) => (
            <div key={category} className="bg-slate-950 border border-slate-800 rounded-lg p-4">
              <div className="text-sm font-mono text-slate-400">{category}</div>
              <div className={`text-2xl font-bold mt-2 ${getHealthColor(data.health)}`}>
                {data.health.toUpperCase()}
              </div>
              <div className="mt-3 space-y-1 text-xs text-slate-500">
                <div>Growth: <span className={data.growth_rate > 0 ? 'text-green-400' : 'text-red-400'}>
                  {data.growth_rate > 0 ? '+' : ''}{data.growth_rate}%/year
                </span></div>
                <div>Avg Popularity: {data.current_avg_popularity.toFixed(1)}%</div>
                <div>Skills: {data.skills_count}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Emerging Skills */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
        <h3 className="text-xl font-bold text-green-400 mb-4 uppercase tracking-wide">
          🚀 Emerging Skills (Top 10)
        </h3>
        <div className="space-y-3">
          {insights.emerging_skills.slice(0, 10).map((skill, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between bg-slate-950 border border-slate-800 rounded-lg p-4 hover:border-green-500/50 transition-colors"
            >
              <div className="flex items-center space-x-4 flex-1">
                <div className="text-2xl font-bold text-green-400">#{idx + 1}</div>
                <div className="flex-1">
                  <div className="font-bold text-white">{skill.skill}</div>
                  <div className="text-xs text-slate-400 mt-1">
                    <span className={`inline-block px-2 py-0.5 rounded ${getCategoryColor(skill.category)} text-white text-xs`}>
                      {skill.category}
                    </span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-green-400">+{skill.growth_rate}%</div>
                <div className="text-xs text-slate-400">per year</div>
                <div className={`text-xs mt-1 px-2 py-0.5 rounded ${skill.urgency === 'high' ? 'bg-red-500/20 text-red-400 border border-red-500/50' : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/50'}`}>
                  {skill.urgency.toUpperCase()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Declining Skills */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
        <h3 className="text-xl font-bold text-red-400 mb-4 uppercase tracking-wide">
          ⚠️ Declining Skills (Top 10)
        </h3>
        <div className="space-y-3">
          {insights.declining_skills.slice(0, 10).map((skill, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between bg-slate-950 border border-slate-800 rounded-lg p-4 hover:border-red-500/50 transition-colors"
            >
              <div className="flex items-center space-x-4 flex-1">
                <div className="text-2xl font-bold text-red-400">#{idx + 1}</div>
                <div className="flex-1">
                  <div className="font-bold text-white">{skill.skill}</div>
                  <div className="text-xs text-slate-400 mt-1">
                    <span className={`inline-block px-2 py-0.5 rounded ${getCategoryColor(skill.category)} text-white text-xs`}>
                      {skill.category}
                    </span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-red-400">{skill.decline_rate}%</div>
                <div className="text-xs text-slate-400">per year</div>
                <div className={`text-xs mt-1 px-2 py-0.5 rounded ${skill.risk_level === 'critical' ? 'bg-red-500/20 text-red-400 border border-red-500/50' : 'bg-orange-500/20 text-orange-400 border border-orange-500/50'}`}>
                  {skill.risk_level.toUpperCase()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Upskilling Priorities */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
        <h3 className="text-xl font-bold text-cyan-400 mb-4 uppercase tracking-wide">
          📚 Upskilling Priorities
        </h3>
        <div className="space-y-2">
          {insights.upskilling_priorities.map((priority, idx) => (
            <div key={idx} className="bg-slate-950 border border-slate-800 rounded-lg p-4 hover:border-cyan-500/50 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="font-bold text-white">{priority.skill}</div>
                  <div className="text-sm text-slate-400 mt-1">{priority.reason}</div>
                  <span className={`inline-block mt-2 px-2 py-0.5 rounded text-xs ${getCategoryColor(priority.category)} text-white`}>
                    {priority.category}
                  </span>
                </div>
                <div className={`px-3 py-1 rounded text-xs font-bold ${priority.urgency === 'high' ? 'bg-red-500/20 text-red-400 border border-red-500/50' : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/50'}`}>
                  {priority.urgency.toUpperCase()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Phase Out Recommendations */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
        <h3 className="text-xl font-bold text-orange-400 mb-4 uppercase tracking-wide">
          🔄 Phase-Out Recommendations
        </h3>
        <div className="space-y-2">
          {insights.phase_out_recommendations.map((recommendation, idx) => (
            <div key={idx} className="bg-slate-950 border border-slate-800 rounded-lg p-4 hover:border-orange-500/50 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="font-bold text-white">{recommendation.skill}</div>
                  <div className="text-sm text-slate-400 mt-1">{recommendation.reason}</div>
                  <span className={`inline-block mt-2 px-2 py-0.5 rounded text-xs ${getCategoryColor(recommendation.category)} text-white`}>
                    {recommendation.category}
                  </span>
                </div>
                <div className={`px-3 py-1 rounded text-xs font-bold ${recommendation.risk_level === 'critical' ? 'bg-red-500/20 text-red-400 border border-red-500/50' : 'bg-orange-500/20 text-orange-400 border border-orange-500/50'}`}>
                  {recommendation.risk_level.toUpperCase()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Refresh Button */}
      <div className="flex justify-center pb-6">
        <button
          onClick={loadInsights}
          className="px-6 py-3 bg-cyan-500/20 hover:bg-cyan-500/30 rounded-lg border border-cyan-500/50 text-cyan-400 font-bold uppercase tracking-wide transition-colors"
        >
          ↻ Refresh Insights
        </button>
      </div>
    </div>
  );
};
