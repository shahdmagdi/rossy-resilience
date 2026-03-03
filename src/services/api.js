// This is your main connection to the backend
// Think of it as the "phone line" between your frontend and backend

import axios from 'axios';

// Create axios instance
// IMPORTANT: Change this URL to your backend teammate's server address
const api = axios.create({
  baseURL: 'http://localhost:5000/api', // ← Ask your backend teammate for this URL!
  timeout: 10000, // 10 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add token to requests automatically
api.interceptors.request.use(
  (config) => {
    // Try both keys for compatibility
    const token = localStorage.getItem('authToken') || localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('authToken');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
