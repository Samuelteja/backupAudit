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

export const getTenantUsers = () => {
  return apiClient.get('/tenant/users');
};

export const inviteUser = (email, role) => {
  return apiClient.post('/tenant/users', { email, role });
};

/**
 * Fetches the list of unprotected assets for the logged-in user's tenant.
 * The auth token is added automatically by the interceptor.
 * @returns {Promise} An axios promise with a list of VM name strings.
 */
export const getUnprotectedAssets = () => {
  console.log("Fetching unprotected assets in API.JS...");
  return apiClient.get('/tenant/unprotected-assets');
};

/**
 * Fetches the high-level alert and job summary for the tenant.
 * The auth token is added automatically by the interceptor.
 * @returns {Promise} An axios promise with the summary data object.
 */
export const getAlertsSummary = () => {
  return apiClient.get('/tenant/alerts/summary');
};

export const getAlerts = (filters = {}) => {
  // We now accept an object of filters.
  const params = {};
  if (filters.alertName) {
    params.alert_name = filters.alertName;
  }
  if (filters.severity) {
    params.severity = filters.severity;
  }

  return apiClient.get('/tenant/alerts', { params });
};

/**
 * Marks a specific alert as read.
 * @param {number} alertId The ID of the alert to acknowledge.
 * @returns {Promise} An axios promise with the updated alert object.
 */
export const markAlertAsRead = (alertId) => {
  console.log("Marking alert %d as read", alertId);
  return apiClient.post(`/alerts/${alertId}/read`);
};

/**
 * Fetches the intelligently grouped and aggregated alert data.
 * @returns {Promise} An axios promise with the grouped alert data.
 */
export const getGroupedAlerts = () => {
  return apiClient.get('/tenant/alerts/grouped');
};

// To create the initial analysis task
export const createAnalysisTask = (jobDbId) => {
  return apiClient.post(`/jobs/${jobDbId}/analysis-tasks`);
};

// To poll for the status and final result
export const getTaskResult = (taskId) => {
  return apiClient.get(`/agent-tasks/${taskId}`);
};

// Fetches the high-level details for a single job.
export const getJobById = (jobDbId) => {
    return apiClient.get(`/jobs/${jobDbId}`);
};