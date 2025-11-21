/**
 * API utility functions for authenticated requests
 */

/**
 * Get the access token from localStorage
 */
export const getAccessToken = () => {
  return localStorage.getItem('access_token');
};

/**
 * Make an authenticated fetch request
 * Automatically includes the Authorization header with the JWT token
 */
export const authenticatedFetch = async (url, options = {}) => {
  const token = getAccessToken();
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // If token is invalid, clear auth and redirect to login
  if (response.status === 401) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('user');
    window.location.href = '/login';
    throw new Error('Authentication required');
  }

  return response;
};

