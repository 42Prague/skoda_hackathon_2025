import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

// Demo IDs as per requirements
const DEMO_TEAM_ID = 'SE';
const DEMO_EMPLOYEE_ID = 9186;

/**
 * Hook for team capability endpoint
 * GET /team/{team_id}/capability
 */
export const useCapability = (teamId: string = DEMO_TEAM_ID) => {
  return useQuery({
    queryKey: ['team-capability', teamId],
    queryFn: async () => {
      const response = await api.getTeamCapability(teamId);
      // Backend returns unified response with data field
      return response.data?.data || response.data;
    },
    enabled: !!teamId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
};

/**
 * Hook for team risk radar endpoint
 * GET /team/{team_id}/risk-radar
 */
export const useRiskRadar = (teamId: string = DEMO_TEAM_ID) => {
  return useQuery({
    queryKey: ['team-risk-radar', teamId],
    queryFn: async () => {
      const response = await api.getTeamRiskRadar(teamId);
      // Backend returns unified response with data field
      return response.data?.data || response.data;
    },
    enabled: !!teamId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
};

/**
 * Hook for team promotion readiness endpoint
 * GET /team/{team_id}/promotion-readiness
 */
export const usePromotionReadiness = (teamId: string = DEMO_TEAM_ID) => {
  return useQuery({
    queryKey: ['team-promotion-readiness', teamId],
    queryFn: async () => {
      const response = await api.getTeamPromotionReadiness(teamId);
      // Backend returns unified response with data field
      return response.data?.data || response.data;
    },
    enabled: !!teamId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
};

/**
 * Hook for employee career path endpoint
 * GET /employee/{employee_id}/career-path
 */
export const useCareerPath = (employeeId: string | number = DEMO_EMPLOYEE_ID) => {
  return useQuery({
    queryKey: ['employee-career-path', employeeId],
    queryFn: async () => {
      const response = await api.getEmployeeCareerPath(employeeId);
      // Backend returns unified response with data field
      return response.data?.data || response.data;
    },
    enabled: !!employeeId,
    staleTime: 10 * 60 * 1000, // 10 minutes (career paths change less frequently)
    retry: 2,
  });
};

/**
 * Hook for 5-year skill forecast endpoint
 * GET /forecast/skills-5y
 */
export const useForecast = (topN: number = 20) => {
  return useQuery({
    queryKey: ['skills-forecast-5y', topN],
    queryFn: async () => {
      const response = await api.getSkillsForecast5y(topN);
      // Backend returns unified response with data field
      return response.data?.data || response.data;
    },
    staleTime: 30 * 60 * 1000, // 30 minutes (forecasts change slowly)
    retry: 2,
  });
};
