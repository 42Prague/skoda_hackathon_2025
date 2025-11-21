import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export const useHeatmapData = (teamId?: string) => {
  return useQuery({
    queryKey: ['heatmap-data', teamId],
    queryFn: () => api.getHeatmapData(teamId),
    select: (response) => response.data,
  });
};

export const useHeatmapInsights = () => {
  return useQuery({
    queryKey: ['heatmap-insights'],
    queryFn: () => api.getHeatmapInsights(),
    select: (response) => response.data,
  });
};
