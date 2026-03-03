import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isVerified, setIsVerified] = useState(true);
  const [isApproved, setIsApproved] = useState(true);

  useEffect(() => {
    // Check for existing auth token on mount
    const token = localStorage.getItem('authToken');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        setUser(parsedUser);
        setIsLoggedIn(true);
        setIsVerified(parsedUser.isVerified !== false);
        setIsApproved(parsedUser.isApproved !== false);
      } catch (e) {
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
      }
    }
    setLoading(false);
  }, []);

  const login = (userData, token) => {
    // Store auth data
    localStorage.setItem('authToken', token);
    localStorage.setItem('user', JSON.stringify(userData));
    
    setUser(userData);
    setIsLoggedIn(true);
    setIsVerified(userData.isVerified !== false);
    setIsApproved(userData.isApproved !== false);
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    localStorage.removeItem('pendingUser');
    setUser(null);
    setIsLoggedIn(false);
    setIsVerified(true);
    setIsApproved(true);
  };

  const updateUser = (userData) => {
    // Update user data while keeping the session
    const token = localStorage.getItem('authToken');
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const checkApprovalStatus = async () => {
    // In a real app, this would call the backend to check if doctor is approved
    try {
      const { default: authService } = await import('../services/authService');
      const response = await authService.checkApprovalStatus();
      
      if (response.isApproved) {
        setIsApproved(true);
        const updatedUser = { ...user, isApproved: true };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        setUser(updatedUser);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error checking approval status:', error);
      return false;
    }
  };

  const value = {
    user,
    isLoggedIn,
    loading,
    isVerified,
    isApproved,
    login,
    logout,
    updateUser,
    checkApprovalStatus,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
