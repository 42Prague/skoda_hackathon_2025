import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export const useEmployees = (params?: any) => {
  return useQuery({
    queryKey: ['employees', params],
    queryFn: () => api.getEmployees(params),
    select: (response) => response.data,
  });
};

export const useEmployee = (id: string) => {
  return useQuery({
    queryKey: ['employee', id],
    queryFn: () => api.getEmployee(id),
    select: (response) => response.data,
    enabled: !!id,
  });
};

export const useEmployeeSkills = (id: string) => {
  return useQuery({
    queryKey: ['employee-skills', id],
    queryFn: () => api.getEmployeeSkills(id),
    select: (response) => response.data,
    enabled: !!id,
  });
};

export const useEmployeeQualifications = (id: string) => {
  return useQuery({
    queryKey: ['employee-qualifications', id],
    queryFn: () => api.getEmployeeQualifications(id),
    select: (response) => response.data,
    enabled: !!id,
  });
};

export const useEmployeeCareerPaths = (id: string) => {
  return useQuery({
    queryKey: ['employee-career-paths', id],
    queryFn: () => api.getEmployeeCareerPaths(id),
    select: (response) => response.data,
    enabled: !!id,
  });
};

export const useEmployeeRecommendations = (id: string) => {
  return useQuery({
    queryKey: ['employee-recommendations', id],
    queryFn: () => api.getEmployeeRecommendations(id),
    select: (response) => response.data,
    enabled: !!id,
  });
};
