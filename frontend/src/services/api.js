import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Get list of employees
  getEmployees: async () => {
    const response = await api.get('/api/employees');
    return response.data;
  },

  // Get list of roles
  getRoles: async () => {
    const response = await api.get('/api/roles');
    return response.data;
  },

  // Get employee profile
  getProfile: async (personalNumber) => {
    const response = await api.get('/api/profile', {
      params: { personal_number: personalNumber },
    });
    return response.data;
  },

  // Get gaps between employee and role
  getGaps: async (personalNumber, roleId) => {
    const response = await api.get('/api/gaps', {
      params: {
        personal_number: personalNumber,
        role_id: roleId,
      },
    });
    return response.data;
  },

  // Generate AI learning plan
  generateAIPlan: async (data) => {
    const response = await api.post('/api/ai-plan', data);
    return response.data;
  },
};

export default apiService;
