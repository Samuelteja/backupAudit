// src/services/api.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const signup = (tenantName, email, password) => {
  const payload = { tenant_name: tenantName, email, password };
  return apiClient.post('/users/', payload);
};

export const login = (email, password) => {
  const formData = new FormData();
  formData.append('username', email);
  formData.append('password', password);
  return apiClient.post('/token', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};


// --- User Endpoints ---

/**
 * Fetches the profile of the currently logged-in user.
 * The interceptor above will automatically add the required token.
 * @returns {Promise} An axios promise with the user's data.
 */
export const getUsersMe = () => {
  return apiClient.get('/users/me');
};

export default apiClient;


/**
 * Fetches all backup jobs for the logged-in user's tenant.
 * The auth token is added automatically by the interceptor.
 * @returns {Promise} An axios promise with the list of jobs.
 */
export const getJobs = () => {
  return apiClient.get('/jobs/');
};