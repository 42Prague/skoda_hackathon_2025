import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export const useKeyRoles = () => {
  return useQuery({
    queryKey: ['key-roles'],
    queryFn: () => api.getKeyRoles(),
    select: (response) => response.data,
  });
};

export const useSuccessors = () => {
  return useQuery({
    queryKey: ['successors'],
    queryFn: () => api.getSuccessors(),
    select: (response) => response.data,
  });
};

export const useSuccessionReadiness = () => {
  return useQuery({
    queryKey: ['succession-readiness'],
    queryFn: () => api.getSuccessionReadiness(),
    select: (response) => response.data,
  });
};
