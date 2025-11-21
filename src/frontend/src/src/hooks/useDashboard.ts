import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export const useDashboardMetrics = () => {
  return useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: () => api.getDashboardMetrics(),
    select: (response) => response.data,
    refetchInterval: 300000, // 5 minutes
  });
};

export const useTeamSkills = () => {
  return useQuery({
    queryKey: ['team-skills'],
    queryFn: () => api.getTeamSkills(),
    select: (response) => response.data,
  });
};

export const useRiskEmployees = () => {
  return useQuery({
    queryKey: ['risk-employees'],
    queryFn: () => api.getRiskEmployees(),
    select: (response) => response.data,
  });
};

export const usePredictedGaps = () => {
  return useQuery({
    queryKey: ['predicted-gaps'],
    queryFn: () => api.getPredictedGaps(),
    select: (response) => response.data,
  });
};
