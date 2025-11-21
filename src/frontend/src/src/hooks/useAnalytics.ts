import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export const useSkillTrends = () => {
  return useQuery({
    queryKey: ['skill-trends'],
    queryFn: () => api.getSkillTrends(),
    select: (response) => response.data,
  });
};

export const useSkillForecast = () => {
  return useQuery({
    queryKey: ['skill-forecast'],
    queryFn: () => api.getSkillForecast(),
    select: (response) => response.data,
  });
};

export const useQualificationCompliance = () => {
  return useQuery({
    queryKey: ['qualification-compliance'],
    queryFn: () => api.getQualificationCompliance(),
    select: (response) => response.data,
  });
};

export const useEmergingSkills = () => {
  return useQuery({
    queryKey: ['emerging-skills'],
    queryFn: () => api.getEmergingSkills(),
    select: (response) => response.data,
  });
};

export const useDecliningSkills = () => {
  return useQuery({
    queryKey: ['declining-skills'],
    queryFn: () => api.getDecliningSkills(),
    select: (response) => response.data,
  });
};

export const useJobTransitions = () => {
  return useQuery({
    queryKey: ['job-transitions'],
    queryFn: () => api.getJobTransitions(),
    select: (response) => response.data,
  });
};

export const useShortageForecasts = () => {
  return useQuery({
    queryKey: ['shortage-forecasts'],
    queryFn: () => api.getShortageForecasts(),
    select: (response) => response.data,
  });
};
