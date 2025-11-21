/**
 * Centralized API client for backend integration
 * All API calls should go through this module
 */

import { authenticatedFetch } from '../utils/api';

// Base API URL - adjust if backend is on different host/port
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Authentication API
 */
export const authAPI = {
  /**
   * Register a new user
   * @param {string} username - Username (max 50 chars, min 3)
   * @param {string} password - Password (min 6 chars)
   * @returns {Promise<{username: string, created_at: string}>}
   */
  async register(username, password) {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(error.detail || 'Registration failed');
    }

    return response.json();
  },

  /**
   * Login with username and password
   * @param {string} username - Username
   * @param {string} password - Password
   * @returns {Promise<{access_token: string, token_type: string}>}
   */
  async login(username, password) {
    const response = await fetch(`${API_BASE_URL}/api/auth/login/json`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail || 'Invalid credentials');
    }

    return response.json();
  },

  /**
   * Get current authenticated user
   * @returns {Promise<{username: string, created_at: string}>}
   */
  async getCurrentUser() {
    const response = await authenticatedFetch(`${API_BASE_URL}/api/auth/me`);
    if (!response.ok) {
      throw new Error('Failed to get current user');
    }
    return response.json();
  },

  /**
   * Verify token validity
   * @returns {Promise<{valid: boolean, username: string}>}
   */
  async verifyToken() {
    const response = await authenticatedFetch(`${API_BASE_URL}/api/auth/verify`);
    if (!response.ok) {
      throw new Error('Token verification failed');
    }
    return response.json();
  },
};

/**
 * Analytics API
 */
export const analyticsAPI = {
  /**
   * Get list of all employees
   * @returns {Promise<Array<{personal_number: string, name: string}>>}
   */
  async getEmployees() {
    const response = await fetch(`${API_BASE_URL}/api/analytics/employees`);
    if (!response.ok) {
      throw new Error('Failed to fetch employees');
    }
    return response.json();
  },

  /**
   * Get employee basic information
   * @param {string} employeeId - Employee personal number
   * @returns {Promise<{personal_number, name, field_of_study, current_profession, planned_profession, planned_position, education_category, start_year}>}
   */
  async getEmployee(employeeId) {
    const response = await fetch(`${API_BASE_URL}/api/analytics/employee/${employeeId}`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Employee ${employeeId} not found`);
      }
      throw new Error('Failed to fetch employee');
    }
    return response.json();
  },

  /**
   * Get employee skill profile
   * @param {string} employeeId - Employee personal number
   * @returns {Promise<{employeeId, currentProfession, plannedProfession, skills: Array, qualificationTimeline: Array, skillsExpiringSoon: Array}>}
   */
  async getEmployeeSkillProfile(employeeId) {
    const response = await fetch(`${API_BASE_URL}/api/analytics/employee/${employeeId}/skill-profile`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Employee ${employeeId} not found`);
      }
      throw new Error('Failed to fetch skill profile');
    }
    return response.json();
  },

  /**
   * Get learning recommendations for employee
   * @param {string} employeeId - Employee personal number
   * @returns {Promise<{employeeId, careerReadinessScore: number, aiRecommendations: Array, skillGaps: Array}>}
   */
  async getLearningRecommendations(employeeId) {
    const response = await fetch(`${API_BASE_URL}/api/analytics/employee/${employeeId}/learning-recommendations`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Employee ${employeeId} not found`);
      }
      throw new Error('Failed to fetch learning recommendations');
    }
    return response.json();
  },

  /**
   * Get employee skills
   * @param {string} employeeId - Employee personal number
   * @returns {Promise<Array<{skill_name, skill_theme, expertise_level, validity_end_date, skill_category}>>}
   */
  async getEmployeeSkills(employeeId) {
    const response = await fetch(`${API_BASE_URL}/api/analytics/employee/${employeeId}/skills`);
    if (!response.ok) {
      throw new Error('Failed to fetch employee skills');
    }
    return response.json();
  },

  /**
   * Get position readiness for target role
   * @param {string} employeeId - Employee personal number
   * @param {string} targetRole - Target role/position
   * @returns {Promise<{employeeId, targetRole, readinessScore: number, blockingSkills: Array}>}
   */
  async getPositionReadiness(employeeId, targetRole) {
    const response = await fetch(
      `${API_BASE_URL}/api/analytics/employee/${employeeId}/position-readiness?target_role=${encodeURIComponent(targetRole)}`
    );
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Employee ${employeeId} not found`);
      }
      throw new Error('Failed to fetch position readiness');
    }
    return response.json();
  },

  /**
   * Get team skills heatmap
   * @param {string} teamId - Team identifier
   * @param {string[]} memberIds - Array of employee IDs
   * @returns {Promise<{teamId, skills: string[], members: string[], heatmapMatrix: number[][]}>}
   */
  async getTeamHeatmap(teamId, memberIds) {
    if (!memberIds || memberIds.length === 0) {
      throw new Error('member_ids is required');
    }
    
    const memberIdsParam = memberIds.map(id => `member_ids=${encodeURIComponent(id)}`).join('&');
    const response = await fetch(`${API_BASE_URL}/api/analytics/team/${teamId}/heatmap?${memberIdsParam}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch team heatmap');
    }
    return response.json();
  },

  /**
   * Get company-wide skill trends
   * @returns {Promise<{yearlySkillCounts, emergingSkills, obsoleteSkills}>}
   */
  async getCompanySkillTrends() {
    const response = await fetch(`${API_BASE_URL}/api/analytics/company/skill-trends`);
    if (!response.ok) {
      throw new Error('Failed to fetch company skill trends');
    }
    return response.json();
  },

  /**
   * Get employee Degreed learning activity
   * @param {string} employeeId - Employee personal number
   * @returns {Promise<Array<{content_title, completion_date, provider, content_type, estimated_time_minutes, category, difficulty_level}>>}
   */
  async getDegreedActivity(employeeId) {
    const response = await fetch(`${API_BASE_URL}/api/analytics/employee/${employeeId}/degreed-activity`);
    if (!response.ok) {
      throw new Error('Failed to fetch Degreed activity');
    }
    return response.json();
  },
};

/**
 * Stats API
 */
export const statsAPI = {
  /**
   * Get courses for employee
   * @param {string} employeeId - Employee ID
   * @returns {Promise<Array<{content_id, content_title, content_provider, completed_date, content_type, estimated_learning_minutes, completion_rating}>>}
   */
  async getEmployeeCourses(employeeId) {
    const response = await fetch(`${API_BASE_URL}/api/stats/courses/${employeeId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch employee courses');
    }
    return response.json();
  },

  /**
   * Get employees by coordinator group
   * @param {string} coordinatorGroupId - Coordinator group ID
   * @returns {Promise<Array<{personal_number, user_name, profession, skills: Array}>>}
   */
  async getEmployeesByCoordinator(coordinatorGroupId) {
    const response = await fetch(`${API_BASE_URL}/api/stats/employees/by-coordinator/${coordinatorGroupId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch employees by coordinator');
    }
    return response.json();
  },

  /**
   * Lookup skills by IDs
   * @param {string[]} skillIds - Array of skill IDs
   * @returns {Promise<Array<{skill_id, skill_name, description}>>}
   */
  async lookupSkills(skillIds) {
    const response = await fetch(`${API_BASE_URL}/api/stats/skills/lookup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ skill_ids: skillIds }),
    });
    if (!response.ok) {
      throw new Error('Failed to lookup skills');
    }
    return response.json();
  },

  /**
   * Get global skills statistics
   * @returns {Promise<Array<{skill_id, skill_name, description, number_of_employees, quantity}>>}
   */
  async getGlobalSkills() {
    const response = await fetch(`${API_BASE_URL}/api/stats/skills-global`);
    if (!response.ok) {
      throw new Error('Failed to fetch global skills');
    }
    return response.json();
  },

  /**
   * Get employee skills (from stats API)
   * @param {string} employeeId - Employee ID
   * @returns {Promise<Array<{skill_id, proficiency_level, skill_name, description}>>}
   */
  async getEmployeeSkills(employeeId) {
    const response = await fetch(`${API_BASE_URL}/api/stats/employees/${employeeId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch employee skills');
    }
    return response.json();
  },

  /**
   * Get skills by coordinator group
   * @param {string} coordinatorGroupId - Coordinator group ID
   * @returns {Promise<Array<{skill_id, skill_name, description, number_of_employees, quantity}>>}
   */
  async getSkillsByCoordinator(coordinatorGroupId) {
    const response = await fetch(`${API_BASE_URL}/api/stats/skills/${coordinatorGroupId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch skills by coordinator');
    }
    return response.json();
  },
};

/**
 * Chatbot API
 */
export const chatbotAPI = {
  /**
   * Send chat message
   * @param {string} message - User message
   * @param {string} [userId] - Optional user ID
   * @param {string} [sessionId] - Optional session ID
   * @param {boolean} [useContext=true] - Use RAG context
   * @returns {Promise<{reply: string, message_id: string, context_used: boolean}>}
   */
  async sendMessage(message, userId = null, sessionId = null, useContext = true) {
    const response = await authenticatedFetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        user_id: userId,
        session_id: sessionId,
        use_context: useContext,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Chat request failed' }));
      throw new Error(error.detail || 'Failed to send message');
    }

    return response.json();
  },

  /**
   * Search courses
   * @param {string} query - Search query
   * @param {number} [limit=5] - Result limit (1-50)
   * @param {Object} [filters] - Optional filters: {course_level, provider, university, skill}
   * @returns {Promise<{query: string, count: number, results: Array}>}
   */
  async searchCourses(query, limit = 5, filters = {}) {
    const params = new URLSearchParams({
      query,
      limit: limit.toString(),
      ...filters,
    });

    const response = await fetch(`${API_BASE_URL}/api/courses/search?${params}`);
    if (!response.ok) {
      throw new Error('Failed to search courses');
    }
    return response.json();
  },
};

/**
 * Health API
 */
export const healthAPI = {
  /**
   * Basic health check
   * @returns {Promise<{status: string}>}
   */
  async checkHealth() {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    return response.json();
  },

  /**
   * Detailed health check
   * @returns {Promise<{status: string, services: Object}>}
   */
  async checkDetailedHealth() {
    const response = await fetch(`${API_BASE_URL}/health/detailed`);
    if (!response.ok) {
      throw new Error('Detailed health check failed');
    }
    return response.json();
  },
};

