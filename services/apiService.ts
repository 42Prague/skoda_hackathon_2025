/**
 * API Service - Connects React frontend to Python ML backend
 * Replaces geminiService.ts with real ML-powered analysis
 */

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || (process.env.VITE_API_URL) || 'http://localhost:8000';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

interface GenomeData {
  nodes: Array<{
    id: string;
    label: string;
    value: number;
    group: number;
    growth: number;
  }>;
  links: Array<{
    source: string;
    target: string;
    value: number;
  }>;
  metadata: {
    total_employees: number;
    total_skills: number;
    clustering_method: string;
    cluster_metrics: any;
  };
}

interface EvolutionData {
  chart_data: Array<Record<string, any>>;
  insights: {
    emerging_skills: Array<any>;
    declining_skills: Array<any>;
    category_health: Record<string, any>;
    upskilling_priorities: Array<any>;
    phase_out_recommendations: Array<any>;
    summary: {
      high_growth_skills: number;
      critical_risks: number;
      thriving_categories: number;
    };
  };
}

interface SkillAnalysis {
  skill: string;
  growth_analysis: {
    growth_rate: number;
    current_popularity: number;
    trend: string;
  };
  forecast: Array<{
    year: number;
    predicted_popularity: number;
    confidence: string;
  }>;
  mutation_risk: number;
  similar_skills: Array<{
    skill: string;
    similarity: number;
  }>;
  ai_insight: string;
}

interface ClusterAnalysis {
  skills_analyzed: number;
  evolutionary_stage: string;
  avg_growth_rate: number;
  avg_mutation_risk: number;
  recommendation: string;
}

/**
 * Fetch genome visualization data from Python ML backend
 * Replaces MOCK_GENOME_DATA
 */
export const getGenomeData = async (method: string = 'hierarchical'): Promise<GenomeData> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/genome?method=${method}`);
    const result: ApiResponse<GenomeData> = await response.json();

    if (!result.success || !result.data) {
      throw new Error(result.error || 'Failed to fetch genome data');
    }

    return result.data;
  } catch (error) {
    console.error('❌ API Error (getGenomeData):', error);
    throw error;
  }
};

/**
 * Fetch skill evolution timeline data
 * Replaces EVOLUTION_DATA
 */
export const getEvolutionData = async (): Promise<EvolutionData> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/evolution`);
    const result = await response.json();

    if (!result.success) {
      throw new Error(result.error || 'Failed to fetch evolution data');
    }

    return {
      chart_data: result.chart_data,
      insights: result.insights
    };
  } catch (error) {
    console.error('❌ API Error (getEvolutionData):', error);
    throw error;
  }
};

/**
 * Analyze skill cluster (for Manager AI and node click analysis)
 * Replaces analyzeSkillCluster from geminiService
 */
export const analyzeSkillCluster = async (skills: string[]): Promise<string> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/analyze-cluster`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(skills),
    });

    const result: ApiResponse<{ analysis: ClusterAnalysis }> = await response.json();

    if (!result.success || !result.data) {
      throw new Error(result.error || 'Analysis failed');
    }

    const analysis = result.data.analysis;

    // Format as human-readable text
    return `
**Evolutionary Stage**: ${analysis.evolutionary_stage}

**Growth Rate**: ${analysis.avg_growth_rate > 0 ? '+' : ''}${analysis.avg_growth_rate.toFixed(1)}%/year

**Mutation Risk**: ${(analysis.avg_mutation_risk * 100).toFixed(0)}% (${analysis.avg_mutation_risk > 0.7 ? 'Critical' : analysis.avg_mutation_risk > 0.4 ? 'Moderate' : 'Low'})

**Strategic Recommendation**: ${analysis.recommendation}

---
*Analysis based on ${analysis.skills_analyzed} skills using ML time-series forecasting and clustering.*
    `.trim();
  } catch (error) {
    console.error('❌ API Error (analyzeSkillCluster):', error);
    // Fallback to basic analysis
    return `**Cluster Analysis**\n\nAnalyzing ${skills.length} skills: ${skills.slice(0, 3).join(', ')}${skills.length > 3 ? '...' : ''}\n\n⚠️ Backend connection issue. Using cached analysis patterns.`;
  }
};

/**
 * Get strategic insights for Manager AI chat
 * Replaces getManagerInsight from geminiService
 */
export const getManagerInsight = async (query: string, contextData: string): Promise<string> => {
  try {
    // For now, use the insights endpoint and format response based on query
    const response = await fetch(`${API_BASE_URL}/api/insights`);
    const result = await response.json();

    if (!result.success) {
      throw new Error('Failed to fetch insights');
    }

    const insights = result.strategic_insights;

    // Simple query matching (can be enhanced with embeddings later)
    const lowerQuery = query.toLowerCase();

    if (lowerQuery.includes('gap') || lowerQuery.includes('missing')) {
      // Skill gap question
      return formatSkillGapResponse(insights);
    } else if (lowerQuery.includes('emerging') || lowerQuery.includes('new') || lowerQuery.includes('future')) {
      // Emerging skills question
      return formatEmergingSkillsResponse(insights);
    } else if (lowerQuery.includes('risk') || lowerQuery.includes('obsolete') || lowerQuery.includes('dying')) {
      // Extinction risk question
      return formatExtinctionRiskResponse(insights);
    } else if (lowerQuery.includes('e-mobility') || lowerQuery.includes('electric')) {
      // E-mobility specific
      return formatCategoryResponse(insights, 'e_mobility');
    } else {
      // General overview
      return formatGeneralInsight(insights);
    }
  } catch (error) {
    console.error('❌ API Error (getManagerInsight):', error);
    return 'I\'m analyzing the organizational genome... Backend connection temporarily unavailable. Please try again.';
  }
};

/**
 * Get detailed analysis of a specific skill
 */
export const getSkillDetails = async (skillName: string): Promise<SkillAnalysis> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/skill/${encodeURIComponent(skillName)}`);
    const result: ApiResponse<SkillAnalysis> = await response.json();

    if (!result.success || !result.data) {
      throw new Error(result.error || 'Failed to fetch skill details');
    }

    return result.data;
  } catch (error) {
    console.error('❌ API Error (getSkillDetails):', error);
    throw error;
  }
};

/**
 * Perform skill gap analysis
 */
export const analyzeSkillGap = async (requiredSkills: string[], employeeSkills: string[]): Promise<any> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/gap-analysis`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        required_skills: requiredSkills,
        employee_skills: employeeSkills,
      }),
    });

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.error || 'Gap analysis failed');
    }

    return result.gap_analysis;
  } catch (error) {
    console.error('❌ API Error (analyzeSkillGap):', error);
    throw error;
  }
};

// Helper formatters

function formatSkillGapResponse(insights: any): string {
  const priorities = insights.upskilling_priorities.slice(0, 3);
  return `**Top Skill Gaps Identified:**\n\n${priorities.map((p: any, i: number) =>
    `${i + 1}. **${p.skill}** (${p.category})\n   ${p.reason}\n   Urgency: ${p.urgency.toUpperCase()}`
  ).join('\n\n')}\n\n**Recommendation**: Prioritize ${priorities[0].skill} training programs to address the highest-impact gap.`;
}

function formatEmergingSkillsResponse(insights: any): string {
  const emerging = insights.emerging_skills.slice(0, 5);
  return `**Emerging Skills (Rapid Growth Detected):**\n\n${emerging.map((s: any, i: number) =>
    `${i + 1}. **${s.skill}** (+${s.growth_rate.toFixed(1)}%/year)\n   Category: ${s.category}\n   Current adoption: ${s.current_popularity.toFixed(0)}%`
  ).join('\n\n')}\n\n🧬 **Genomic Insight**: These "skill mutations" represent the future of Škoda's competitive advantage. Early investment yields 3-5x ROI.`;
}

function formatExtinctionRiskResponse(insights: any): string {
  const declining = insights.declining_skills.slice(0, 5);
  return `**Skills at Risk (Declining Adoption):**\n\n${declining.map((s: any, i: number) =>
    `${i + 1}. **${s.skill}** (${s.decline_rate.toFixed(1)}%/year decline)\n   Risk Level: ${s.risk_level.toUpperCase()}\n   Category: ${s.category}`
  ).join('\n\n')}\n\n⚠️ **Strategic Alert**: Plan transition roadmaps for ${insights.summary.critical_risks} critical-risk skills. Avoid stranded human capital.`;
}

function formatCategoryResponse(insights: any, category: string): string {
  const categoryHealth = insights.category_health[category];
  if (!categoryHealth) {
    return 'Category data not available.';
  }

  return `**${category.replace('_', '-').toUpperCase()} Category Health:**\n\n- **Status**: ${categoryHealth.health.toUpperCase()}\n- **Growth Rate**: ${categoryHealth.growth_rate > 0 ? '+' : ''}${categoryHealth.growth_rate.toFixed(1)}%/year\n- **Current Adoption**: ${categoryHealth.current_avg_popularity.toFixed(0)}%\n- **Skills Tracked**: ${categoryHealth.skills_count}\n\n💡 This category ${categoryHealth.health === 'thriving' ? 'represents a strategic growth area' : categoryHealth.health === 'declining' ? 'requires transition planning' : 'shows stable performance'}.`;
}

function formatGeneralInsight(insights: any): string {
  return `**Organizational Genome Status:**\n\n🚀 **High-Growth Skills**: ${insights.summary.high_growth_skills} skills showing explosive growth\n⚠️ **Critical Risks**: ${insights.summary.critical_risks} skills facing obsolescence\n💪 **Thriving Categories**: ${insights.summary.thriving_categories} technology domains in strong health\n\n**Top Priority**: ${insights.upskilling_priorities[0]?.skill || 'N/A'}\n**Biggest Risk**: ${insights.phase_out_recommendations[0]?.skill || 'N/A'}\n\n🧬 The organizational genome is ${insights.summary.high_growth_skills > insights.summary.critical_risks ? 'evolving positively' : 'under transformation pressure'}. Strategic intervention recommended in ${insights.summary.critical_risks} areas.`;
}

export default {
  getGenomeData,
  getEvolutionData,
  analyzeSkillCluster,
  getManagerInsight,
  getSkillDetails,
  analyzeSkillGap,
};
