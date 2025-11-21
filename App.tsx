import React, { useState, useEffect } from 'react';
import { AppView, SkillNode } from './types';
import GenomeGraph from './components/GenomeGraph';
import EvolutionChart from './components/EvolutionChart';
import { DataUpload } from './components/DataUpload';
import { InsightsDashboard } from './components/InsightsDashboard';
import { NetworkAnalysis } from './components/NetworkAnalysis';
import ErrorBoundary from './components/ErrorBoundary';
import { analyzeSkillCluster, getManagerInsight, getGenomeData, getEvolutionData, getSkillDetails } from './services/apiService';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || (process.env.VITE_API_URL) || 'http://localhost:8000';

// Icons (Simple SVG inline to avoid external deps)
const IconDna = () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>;
const IconChart = () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>;
const IconBrain = () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>;
const IconUpload = () => <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>;

const App: React.FC = () => {
  const [activeView, setActiveView] = useState<AppView>(AppView.GENOME);
  const [selectedNode, setSelectedNode] = useState<SkillNode | null>(null);
  const [aiAnalysis, setAiAnalysis] = useState<string>("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState<{role: string, text: string}[]>([]);

  // Real data from ML backend
  const [genomeData, setGenomeData] = useState<any>(null);
  const [evolutionData, setEvolutionData] = useState<any>(null);
  const [insights, setInsights] = useState<any>(null);
  const [skillDetails, setSkillDetails] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [useBackend, setUseBackend] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load data from backend on mount
  useEffect(() => {
    loadBackendData();

    // Listen for data upload events to reload backend data
    const handleDataUploaded = () => {
      console.log('[INFO] Data uploaded, reloading backend...');
      loadBackendData();
    };

    window.addEventListener('dataUploaded', handleDataUploaded);

    return () => {
      window.removeEventListener('dataUploaded', handleDataUploaded);
    };
  }, []);

  const loadBackendData = async () => {
    if (!useBackend) return;

    try {
      setIsLoading(true);

      // Genome data
      const genome = await getGenomeData('hierarchical');
      setGenomeData(genome);
      // Evolution data
      const evolution = await getEvolutionData();
      setEvolutionData(evolution.chart_data);
      // Insights data
      const insightsResp = await fetch(`${API_BASE_URL}/api/insights`);
      const insightsJson = await insightsResp.json();
      if (insightsJson.success) setInsights(insightsJson.strategic_insights);

      setError(null);
      console.log('[OK] Backend data loaded successfully');
    } catch (err:any) {
      console.warn('[WARN] Backend unavailable:', err);
      setUseBackend(false);
      setError('Backend unreachable');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Cluster Analysis + Skill details
  const handleAnalyzeCluster = async (node: SkillNode) => {
    setSelectedNode(node);
    setIsAnalyzing(true);
    setAiAnalysis('Sequencing genome data...');
    setSkillDetails(null);
    try {
      const clusterSkills = genomeData?.nodes
        .filter((n: any) => n.group === node.group)
        .map((n: any) => n.label) || [];
      const clusterResult = await analyzeSkillCluster(clusterSkills);
      setAiAnalysis(clusterResult);
      const detail = await getSkillDetails(node.label);
      setSkillDetails(detail);
    } catch (e) {
      console.error('Skill detail fetch failed', e);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleManagerChat = async () => {
    if(!chatInput.trim()) return;
    const newHistory = [...chatHistory, { role: 'user', text: chatInput }];
    setChatHistory(newHistory);
    setChatInput("");

    const response = await getManagerInsight(chatInput, JSON.stringify(genomeData.nodes));
    setChatHistory([...newHistory, { role: 'ai', text: response }]);
  };

  return (
    <ErrorBoundary>
      <div className="flex h-screen bg-brand-dark text-slate-200 overflow-hidden font-sans selection:bg-brand-primary selection:text-brand-dark">

      {/* Sidebar Navigation */}
      <div className="w-20 lg:w-64 flex-shrink-0 border-r border-slate-800 flex flex-col bg-brand-dark/95 backdrop-blur-md z-20">
        <div className="h-16 flex items-center justify-center lg:justify-start lg:px-6 border-b border-slate-800">
          <div className="w-8 h-8 rounded bg-brand-primary flex items-center justify-center text-brand-dark font-bold animate-pulse-slow">
            S
          </div>
          <span className="hidden lg:block ml-3 font-bold text-lg tracking-wider text-white">SKILL<span className="text-brand-primary">DNA</span></span>
        </div>

        <nav className="flex-1 py-6 space-y-2 px-2 lg:px-4">
          <button
            onClick={() => setActiveView(AppView.GENOME)}
            className={`w-full flex items-center p-3 rounded-lg transition-all duration-200 ${activeView === AppView.GENOME ? 'bg-brand-primary/10 text-brand-primary border border-brand-primary/20 shadow-[0_0_15px_rgba(6,182,212,0.2)]' : 'hover:bg-slate-800 text-slate-400'}`}
          >
            <IconDna />
            <span className="hidden lg:block ml-3 font-medium">Genome Map</span>
          </button>
          <button
            onClick={() => setActiveView(AppView.EVOLUTION)}
            className={`w-full flex items-center p-3 rounded-lg transition-all duration-200 ${activeView === AppView.EVOLUTION ? 'bg-brand-secondary/10 text-brand-secondary border border-brand-secondary/20 shadow-[0_0_15px_rgba(139,92,246,0.2)]' : 'hover:bg-slate-800 text-slate-400'}`}
          >
            <IconChart />
            <span className="hidden lg:block ml-3 font-medium">Evolution</span>
          </button>
          <button
            onClick={() => setActiveView(AppView.INSIGHTS)}
            className={`w-full flex items-center p-3 rounded-lg transition-all duration-200 ${activeView === AppView.INSIGHTS ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20 shadow-[0_0_15px_rgba(139,92,246,0.2)]' : 'hover:bg-slate-800 text-slate-400'}`}
          >
            <IconChart />
            <span className="hidden lg:block ml-3 font-medium">Strategic Insights</span>
          </button>
          <button
            onClick={() => setActiveView(AppView.MANAGER_AI)}
            className={`w-full flex items-center p-3 rounded-lg transition-all duration-200 ${activeView === AppView.MANAGER_AI ? 'bg-brand-accent/10 text-brand-accent border border-brand-accent/20 shadow-[0_0_15px_rgba(16,185,129,0.2)]' : 'hover:bg-slate-800 text-slate-400'}`}
          >
            <IconBrain />
            <span className="hidden lg:block ml-3 font-medium">Manager AI</span>
          </button>
          <button
            onClick={() => setActiveView(AppView.NETWORK)}
            className={`w-full flex items-center p-3 rounded-lg transition-all duration-200 ${activeView === AppView.NETWORK ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.2)]' : 'hover:bg-slate-800 text-slate-400'}`}
          >
            <IconDna />
            <span className="hidden lg:block ml-3 font-medium">Network</span>
          </button>
          <button
            onClick={() => setActiveView(AppView.UPLOAD)}
            className={`w-full flex items-center p-3 rounded-lg transition-all duration-200 ${activeView === AppView.UPLOAD ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 shadow-[0_0_15px_rgba(234,179,8,0.2)]' : 'hover:bg-slate-800 text-slate-400'}`}
          >
            <IconUpload />
            <span className="hidden lg:block ml-3 font-medium">Upload Data</span>
          </button>
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="hidden lg:block p-3 bg-slate-900 rounded border border-slate-700">
            <div className="text-xs text-slate-500 uppercase">System Status</div>
            <div className="flex items-center mt-1">
              <div className={`w-2 h-2 rounded-full mr-2 animate-pulse ${useBackend ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
              <span className={`text-xs font-mono ${useBackend ? 'text-green-400' : 'text-yellow-400'}`}>
                {useBackend ? 'ONLINE // ML_BACKEND' : 'DEMO // MOCK_DATA'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-slate-800 bg-brand-dark/50 backdrop-blur flex items-center justify-between px-8 z-10">
          <h1 className="text-xl font-mono text-slate-300">
            {activeView === AppView.GENOME && 'ORG_GENOME_VISUALIZER_V1'}
            {activeView === AppView.EVOLUTION && 'TEMPORAL_SKILL_ANALYSIS'}
            {activeView === AppView.INSIGHTS && 'STRATEGIC_INSIGHTS_ENGINE'}
            {activeView === AppView.MANAGER_AI && 'INTELLIGENCE_CORE_INTERFACE'}
            {activeView === AppView.NETWORK && 'SKILL_NETWORK_ANALYSIS'}
            {activeView === AppView.UPLOAD && 'DATA_UPLOAD_SYSTEM'}
          </h1>
          <div className="flex items-center space-x-4">
             <div className="text-xs font-mono text-slate-500">DATASET: ŠKODA_2013-2025</div>
             <button className="px-3 py-1 rounded border border-brand-primary/30 text-brand-primary text-xs hover:bg-brand-primary/10"
              onClick={async () => {
                try {
                  // Call backend PDF export endpoint
                  const response = await fetch(`${API_BASE_URL}/api/export-report`);

                  if (!response.ok) {
                    throw new Error(`PDF export failed: ${response.statusText}`);
                  }

                  // Get PDF blob from response
                  const pdfBlob = await response.blob();

                  // Create download link
                  const url = URL.createObjectURL(pdfBlob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `skill_dna_executive_report_${new Date().toISOString().split('T')[0]}.pdf`;
                  document.body.appendChild(a);
                  a.click();

                  // Cleanup
                  document.body.removeChild(a);
                  URL.revokeObjectURL(url);

                  console.log('[OK] PDF exported successfully');
                } catch (err) {
                  console.error('[ERROR] PDF export failed:', err);
                  alert('Failed to export PDF report. Please check backend connection.');
                }
              }}>EXPORT REPORT</button>
          </div>
        </header>

        {/* View Content */}
        <div className="flex-1 overflow-y-auto p-6 relative">
          
          {/* Background Grid Effect */}
          <div className="absolute inset-0 pointer-events-none opacity-10" 
               style={{ backgroundImage: 'radial-gradient(#334155 1px, transparent 1px)', backgroundSize: '20px 20px' }}>
          </div>

          {activeView === AppView.GENOME && (
            <div className="flex h-full gap-6">
              <div className="flex-1 flex flex-col">
                <div className="flex-1 relative">
                  {isLoading ? (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-cyan-400 font-mono animate-pulse">Loading genome data...</div>
                    </div>
                  ) : error ? (
                    <div className="flex items-center justify-center h-full text-red-400 font-mono">
                      {error}
                      <button onClick={loadBackendData} className="ml-3 px-2 py-1 border border-red-500/30 rounded text-xs hover:bg-red-500/20">Retry</button>
                    </div>
                  ) : (
                    genomeData && (
                      <GenomeGraph
                        data={genomeData}
                        onNodeClick={handleAnalyzeCluster}
                      />
                    )
                  )}
                </div>
                {/* Legend */}
                <div className="h-16 mt-4 flex items-center space-x-6 px-4 bg-slate-900/50 rounded border border-slate-800">
                   <div className="flex items-center"><div className="w-3 h-3 rounded-full bg-[#64748b] mr-2"></div><span className="text-xs font-mono text-slate-400">Legacy Engineering</span></div>
                   <div className="flex items-center"><div className="w-3 h-3 rounded-full bg-[#06b6d4] mr-2"></div><span className="text-xs font-mono text-slate-400">Software/Cloud</span></div>
                   <div className="flex items-center"><div className="w-3 h-3 rounded-full bg-[#10b981] mr-2"></div><span className="text-xs font-mono text-slate-400">E-Mobility</span></div>
                   <div className="flex items-center"><div className="w-3 h-3 rounded-full bg-[#a855f7] mr-2 animate-pulse"></div><span className="text-xs font-mono text-slate-400">AI Mutation (Emerging)</span></div>
                </div>
              </div>

              {/* Insight Panel */}
              <div className="w-80 flex-shrink-0 bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col shadow-2xl">
                <h2 className="text-brand-primary font-bold mb-4 uppercase tracking-widest border-b border-slate-800 pb-2">Genome Sequencer</h2>
                
                {!selectedNode ? (
                  <div className="flex-1 flex items-center justify-center text-slate-600 text-sm text-center px-4">
                    Select a node in the genome graph to analyze its DNA structure and evolutionary path.
                  </div>
                ) : (
                  <div className="flex-1 flex flex-col animate-in fade-in duration-500">
                    <div className="mb-4">
                      <div className="text-xs text-slate-500 uppercase mb-1">Selected Skill</div>
                      <div className="text-2xl font-mono text-white">{selectedNode.label}</div>
                      <div className={`text-xs font-bold mt-1 inline-block px-2 py-1 rounded ${selectedNode.growth > 0 ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
                        {selectedNode.growth > 0 ? '+' : ''}{(selectedNode.growth * 100).toFixed(0)}% GROWTH
                      </div>
                    </div>

                    <div className="bg-slate-950 p-3 rounded border border-slate-800 mb-4">
                      <div className="text-xs text-purple-400 mb-2 flex items-center">
                        <IconBrain /> <span className="ml-2">AI ANALYSIS</span>
                      </div>
                      {isAnalyzing ? (
                        <div className="text-xs font-mono text-slate-400 animate-pulse">Processing cluster semantics...</div>
                      ) : (
                        <p className="text-sm text-slate-300 leading-relaxed font-light whitespace-pre-line">
                          {aiAnalysis}
                        </p>
                      )}
                    </div>

                    {skillDetails && (
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
                    )}

                    <div className="mt-auto">
                      <button className="w-full py-2 bg-brand-primary/20 hover:bg-brand-primary/30 text-brand-primary border border-brand-primary/50 rounded transition-colors text-sm font-bold uppercase">
                        View Training Path
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeView === AppView.EVOLUTION && (
            <div className="h-full flex flex-col gap-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {Object.entries(insights?.category_health || {}).map(([name, data]: any) => (
                  <div key={name} className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                    <div className="text-xs text-slate-500 uppercase">Category</div>
                    <div className="text-lg font-bold text-white">{name}</div>
                    <div className="mt-2 h-1 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-brand-primary"
                        style={{ width: `${Math.min(Math.max(((data.growth_rate + 10) / 30) * 100, 5), 100)}%`, backgroundColor: data.growth_rate < 0 ? '#ef4444' : '#10b981' }}
                      ></div>
                    </div>
                    <div className="text-xs mt-2 flex justify-between text-slate-400">
                      <span>{data.health}</span>
                      <span>{data.growth_rate > 0 ? '+' : ''}{data.growth_rate}%/yr</span>
                    </div>
                  </div>
                ))}
              </div>
              {evolutionData && <EvolutionChart data={evolutionData} />}
              <div className="bg-purple-900/20 border border-purple-500/30 p-4 rounded-lg flex items-start space-x-4">
                <div className="p-2 bg-purple-500/20 rounded-full text-purple-400"><IconDna /></div>
                <div>
                  <h4 className="text-purple-300 font-bold text-sm">PREDICTIVE MUTATION ALERT</h4>
                  <p className="text-slate-400 text-sm mt-1">AI forecasting models indicate a surge in emerging AI-aligned engineering skills. Continuous monitoring enabled.</p>
                </div>
              </div>
            </div>
          )}

          {activeView === AppView.MANAGER_AI && (
            <div className="max-w-4xl mx-auto h-full flex flex-col">
              <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
                {chatHistory.length === 0 && (
                  <div className="text-center mt-20 opacity-50">
                     <div className="w-20 h-20 bg-slate-800 rounded-full mx-auto flex items-center justify-center mb-4">
                       <IconBrain />
                     </div>
                     <h3 className="text-xl font-mono text-slate-300">SKILL_DNA INTELLIGENCE</h3>
                     <p className="text-slate-500 mt-2 max-w-md mx-auto">Ask about skill gaps, team diversity, or mentor recommendations based on the Škoda organizational genome.</p>
                     <div className="mt-8 grid grid-cols-2 gap-2 max-w-lg mx-auto text-sm">
                        <button onClick={() => setChatInput("Identify the biggest skill gap in E-Mobility.")} className="p-2 border border-slate-700 rounded hover:bg-slate-800 text-left text-cyan-400">"Identify gaps in E-Mobility"</button>
                        <button onClick={() => setChatInput("Who can mentor Junior Python devs?")} className="p-2 border border-slate-700 rounded hover:bg-slate-800 text-left text-cyan-400">"Find mentors for Python"</button>
                     </div>
                  </div>
                )}
                {chatHistory.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] p-4 rounded-xl ${msg.role === 'user' ? 'bg-brand-primary/20 text-brand-primary border border-brand-primary/30' : 'bg-slate-800 text-slate-200 border border-slate-700'}`}>
                       {msg.text}
                    </div>
                  </div>
                ))}
              </div>

              <div className="p-4 bg-slate-900/80 backdrop-blur border-t border-slate-800 rounded-t-xl">
                 <div className="relative">
                   <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleManagerChat()}
                    placeholder="Query the organizational genome..."
                    className="w-full bg-slate-950 border border-slate-700 text-white p-4 rounded-lg focus:ring-2 focus:ring-brand-primary focus:border-transparent outline-none pr-12 font-mono"
                   />
                   <button onClick={handleManagerChat} className="absolute right-2 top-2 p-2 text-brand-primary hover:text-white">
                      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" /></svg>
                   </button>
                 </div>
              </div>
            </div>
          )}

          {activeView === AppView.INSIGHTS && (
            <div className="h-full overflow-y-auto">
              <InsightsDashboard />
            </div>
          )}

          {activeView === AppView.NETWORK && (
            <div className="h-full overflow-y-auto">
              <div className="mb-4">
                <h3 className="text-cyan-400 font-mono text-sm tracking-widest">STRUCTURAL CONNECTIVITY</h3>
                <p className="text-xs text-slate-500">HUBS • BRIDGES • COMMUNITIES • DENSITY</p>
              </div>
              <NetworkAnalysis />
            </div>
          )}

          {activeView === AppView.UPLOAD && (
            <div className="max-w-5xl mx-auto h-full overflow-y-auto">
              <DataUpload />
            </div>
          )}

        </div>
      </main>
    </div>
    </ErrorBoundary>
  );
};

export default App;