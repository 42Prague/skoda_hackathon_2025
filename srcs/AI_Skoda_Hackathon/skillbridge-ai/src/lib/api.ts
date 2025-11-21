// API client for backend communication

const API_URL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api`
  : 'http://localhost:3000/api';

// Store auth token
let authToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  authToken = token;
  if (token) {
    localStorage.setItem('authToken', token);
  } else {
    localStorage.removeItem('authToken');
  }
};

export const getAuthToken = () => {
  if (!authToken) {
    authToken = localStorage.getItem('authToken');
  }
  return authToken;
};

// Generic fetch wrapper
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Network error' }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
}

// Auth API
export const authAPI = {
  login: async (email: string, password: string) => {
    const data = await apiFetch<{ token: string; user: any }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setAuthToken(data.token);
    return data;
  },

  register: async (userData: {
    email: string;
    password: string;
    firstName: string;
    lastName: string;
    role?: string;
  }) => {
    const data = await apiFetch<{ token: string; user: any }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    setAuthToken(data.token);
    return data;
  },

  logout: () => {
    setAuthToken(null);
  },

  getCurrentUser: async () => {
    return apiFetch<{ user: any }>('/auth/me');
  },

  getDemoEmployees: async () => {
    return apiFetch<{
      employee: any;
      manager: any;
      password: string;
    }>('/auth/demo-employees');
  },
};

// Dashboard API
export const dashboardAPI = {
  getEmployeeDashboard: async (userId: string) => {
    return apiFetch<{
      user: any;
      skillRelevanceScore: number;
      riskLevel: string;
      userSkills: any[];
      skillRisks: any[];
      careerPaths: any[];
      enrollments: any[];
      recommendedCourses: any[];
      assessments: any[];
    }>(`/dashboard/employee/${userId}`);
  },

  getManagerDashboard: async (managerId: string) => {
    return apiFetch<{
      teamSize: number;
      avgRelevance: number;
      highRiskCount: number;
      avgProgress: number;
      riskDistribution: Array<{ risk: string; count: number }>;
      teamMembers: any[];
      availablePositions?: any[];
    }>(`/dashboard/manager/${managerId}`);
  },

  getEmployeeDetail: async (employeeId: string) => {
    return apiFetch<{
      user: any;
      skills: any[];
      skillRisks: any[];
      enrollments: any[];
    }>(`/dashboard/employee-detail/${employeeId}`);
  },

  getJobMatches: async (userId: string) => {
    return apiFetch<{
      matches: any[];
      perfectMatches: any[]; // ≥85% fitness
      middleMatches: any[];  // 50-84% fitness
      lowMatches: any[];     // <50% fitness
    }>(`/dashboard/employee/${userId}/job-matches`);
  },

  applyForJob: async (userId: string, jobPositionId: string) => {
    return apiFetch<{
      application: any;
      match: any;
      message: string;
    }>(`/dashboard/employee/${userId}/job-applications`, {
      method: 'POST',
      body: JSON.stringify({ jobPositionId }),
    });
  },
};

// Users API
export const usersAPI = {
  getUsers: async () => {
    return apiFetch<{ users: any[] }>('/users');
  },

  getUserById: async (userId: string) => {
    return apiFetch<{ user: any }>(`/users/${userId}`);
  },

  getTeam: async (managerId: string) => {
    return apiFetch<{ team: any[] }>(`/users/team/${managerId}`);
  },
};

// Skills API
export const skillsAPI = {
  getSkills: async (category?: string) => {
    const query = category ? `?category=${encodeURIComponent(category)}` : '';
    return apiFetch<{ skills: any[] }>(`/skills${query}`);
  },

  getUserSkills: async (userId: string) => {
    return apiFetch<{ userSkills: any[] }>(`/skills/user/${userId}`);
  },

  updateUserSkill: async (userId: string, skillData: {
    skillId: string;
    level: number;
    notes?: string;
  }) => {
    return apiFetch<{ userSkill: any }>(`/skills/user/${userId}`, {
      method: 'POST',
      body: JSON.stringify(skillData),
    });
  },
};

// Courses API
export const coursesAPI = {
  getCourses: async () => {
    return apiFetch<{ courses: any[] }>('/courses');
  },

  getCourseById: async (courseId: string) => {
    return apiFetch<{ course: any }>(`/courses/${courseId}`);
  },

  enrollInCourse: async (userId: string, courseId: string) => {
    return apiFetch<{ enrollment: any }>('/courses/enroll', {
      method: 'POST',
      body: JSON.stringify({ userId, courseId }),
    });
  },

  getUserEnrollments: async (userId: string) => {
    return apiFetch<{ enrollments: any[] }>(`/courses/enrollments/${userId}`);
  },
};

// Career Paths API
export const careerPathsAPI = {
  getCareerPaths: async () => {
    return apiFetch<{ careerPaths: any[] }>('/career-paths');
  },

  getCareerPathById: async (pathId: string) => {
    return apiFetch<{ careerPath: any }>(`/career-paths/${pathId}`);
  },
};

// Employee Skill Risk API
export const skillRiskAPI = {
  getEmployeeRisks: async (employeeId?: string) => {
    const query = employeeId ? `?employeeId=${encodeURIComponent(employeeId)}` : '';
    return apiFetch<{ risks: any[]; count: number }>(`/employee-skill-risks${query}`);
  },

  getEmployeeRisksByEmployeeId: async (employeeId: string) => {
    return apiFetch<{ risks: any[] }>(`/employee-skill-risks/employee/${employeeId}`);
  },
};

// Job Positions API
export const jobPositionsAPI = {
  getJobPositions: async (status?: string, department?: string) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (department) params.append('department', department);
    const query = params.toString() ? `?${params.toString()}` : '';
    return apiFetch<{ jobPositions: any[] }>(`/job-positions${query}`);
  },

  getJobPositionById: async (id: string) => {
    return apiFetch<{ jobPosition: any }>(`/job-positions/${id}`);
  },

  createJobPosition: async (jobPositionData: {
    title: string;
    description?: string;
    department?: string;
    location?: string;
    employmentType?: string;
    status?: string;
    requiredExperience?: string;
    closingDate?: string;
    skills?: Array<{ skillId: string; requiredLevel?: number; weight?: number; isRequired?: boolean }>;
  }) => {
    return apiFetch<{ jobPosition: any }>('/job-positions', {
      method: 'POST',
      body: JSON.stringify(jobPositionData),
    });
  },
};

export default {
  auth: authAPI,
  dashboard: dashboardAPI,
  users: usersAPI,
  skills: skillsAPI,
  courses: coursesAPI,
  careerPaths: careerPathsAPI,
  skillRisk: skillRiskAPI,
  jobPositions: jobPositionsAPI,
};
