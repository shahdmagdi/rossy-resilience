// This file handles all login/register functions
import api from './api';

const authService = {
  // Login function - sends email and password to backend
  login: async (email, password) => {
    try {
      const response = await api.post('/auth/login', {
        email,
        password
      });
      
      // If login successful, save token and user data
      if (response.data.token) {
        localStorage.setItem('authToken', response.data.token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data?.message || 'Login failed. Please try again.';
    }
  },

  // Register function
  register: async (userData) => {
    try {
      const response = await api.post('/auth/register', userData);
      
      if (response.data.token) {
        localStorage.setItem('authToken', response.data.token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data?.message || 'Registration failed. Please try again.';
    }
  },

  // Verify email with verification code
  verifyEmail: async (code) => {
    try {
      const response = await api.post('/auth/verify-email', {
        verificationCode: code
      });
      
      if (response.data.token) {
        localStorage.setItem('authToken', response.data.token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data?.message || 'Email verification failed. Please try again.';
    }
  },

  // Resend verification code
  resendVerificationCode: async (email) => {
    try {
      const response = await api.post('/auth/resend-verification', {
        email
      });
      return response.data;
    } catch (error) {
      throw error.response?.data?.message || 'Failed to resend verification code.';
    }
  },

  // Forgot password - send reset email
  forgotPassword: async (email) => {
    try {
      const response = await api.post('/auth/forgot-password', {
        email
      });
      return response.data;
    } catch (error) {
      throw error.response?.data?.message || 'Failed to send reset email. Please try again.';
    }
  },

  // Reset password with token
  resetPassword: async (token, newPassword) => {
    try {
      const response = await api.post('/auth/reset-password', {
        token,
        password: newPassword
      });
      
      if (response.data.token) {
        localStorage.setItem('authToken', response.data.token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data?.message || 'Failed to reset password. Please try again.';
    }
  },

  // Check doctor approval status
  checkApprovalStatus: async () => {
    try {
      const response = await api.get('/auth/check-approval');
      return response.data;
    } catch (error) {
      throw error.response?.data?.message || 'Failed to check approval status.';
    }
  },

  // Logout function
  logout: () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    localStorage.removeItem('pendingUser');
  },

  // Check if user is logged in
  isLoggedIn: () => {
    return !!localStorage.getItem('authToken');
  },

  // Get current user
  getCurrentUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  // Get user role (patient or doctor)
  getUserRole: () => {
    const user = authService.getCurrentUser();
    return user?.role || null;
  },

  // Check if user is verified
  isVerified: () => {
    const user = authService.getCurrentUser();
    return user?.isVerified !== false;
  },

  // Check if user is approved (for doctors)
  isApproved: () => {
    const user = authService.getCurrentUser();
    // Patients are automatically approved
    if (user?.role === 'patient') return true;
    return user?.isApproved !== false;
  }
};

export default authService;
