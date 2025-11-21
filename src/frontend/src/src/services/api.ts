import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Backend Contract Endpoints (MANDATORY)
  getTeamCapability: (teamId: string) => apiClient.get(`/team/${teamId}/capability`),
  getTeamRiskRadar: (teamId: string) => apiClient.get(`/team/${teamId}/risk-radar`),
  getTeamPromotionReadiness: (teamId: string) => apiClient.get(`/team/${teamId}/promotion-readiness`),
  getEmployeeCareerPath: (employeeId: string | number) => apiClient.get(`/employee/${employeeId}/career-path`),
  getSkillsForecast5y: (topN?: number) => apiClient.get('/forecast/skills-5y', { params: { top_n: topN } }),

  // Legacy endpoints (keeping for backwards compatibility)
  getDashboardMetrics: () => apiClient.get('/dashboard/metrics'),
  getTeamSkills: () => apiClient.get('/dashboard/team-skills'),
  getRiskEmployees: () => apiClient.get('/dashboard/risk-employees'),
  getPredictedGaps: () => apiClient.get('/dashboard/predicted-gaps'),

  // Employees
  getEmployees: (params?: any) => apiClient.get('/employees', { params }),
  getEmployee: (id: string) => apiClient.get(`/employees/${id}`),
  getEmployeeSkills: (id: string) => apiClient.get(`/employees/${id}/skills`),
  getEmployeeQualifications: (id: string) => apiClient.get(`/employees/${id}/qualifications`),
  getEmployeeCareerPaths: (id: string) => apiClient.get(`/employees/${id}/career-paths`),
  getEmployeeRecommendations: (id: string) => apiClient.get(`/employees/${id}/recommendations`),

  // Heatmap
  getHeatmapData: (teamId?: string) => apiClient.get('/heatmap', { params: { teamId } }),
  getHeatmapInsights: () => apiClient.get('/heatmap/insights'),

  // Succession
  getKeyRoles: () => apiClient.get('/succession/key-roles'),
  getSuccessors: () => apiClient.get('/succession/successors'),
  getSuccessionReadiness: () => apiClient.get('/succession/readiness'),

  // Analytics
  getSkillTrends: () => apiClient.get('/analytics/skill-trends'),
  getSkillForecast: () => apiClient.get('/analytics/forecast'),
  getQualificationCompliance: () => apiClient.get('/analytics/qualification-compliance'),
  getEmergingSkills: () => apiClient.get('/analytics/emerging-skills'),
  getDecliningSkills: () => apiClient.get('/analytics/declining-skills'),
  getJobTransitions: () => apiClient.get('/analytics/job-transitions'),
  getShortageForecasts: () => apiClient.get('/analytics/shortage-forecasts'),

  // Organization
  getOrgHierarchy: () => apiClient.get('/organization/hierarchy'),
  getDepartmentMetrics: (deptId: string) => apiClient.get(`/organization/departments/${deptId}/metrics`),

  // Skills Galaxy
  getSkillsGalaxy: () => apiClient.get('/galaxy/skills'),

  // AI Simulator
  simulateScenario: (scenario: any) => apiClient.post('/simulator/scenario', scenario),

  // AI Assistant
  sendMessage: (message: string, conversationId?: string) => 
    apiClient.post('/assistant/message', { message, conversationId }),
  getConversationHistory: (conversationId: string) => 
    apiClient.get(`/assistant/conversations/${conversationId}`),
  getSuggestedQueries: () => apiClient.get('/assistant/suggested-queries'),
  getRecentInsights: () => apiClient.get('/assistant/recent-insights'),
};

export default apiClient;
