// This handles all navigation in your app
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Public Pages
import Login from '../pages/public/Login';
import RoleSelection from '../pages/public/RoleSelection';
import Register from '../pages/public/Register';
import EmailVerification from '../pages/public/EmailVerification';
import ForgotPassword from '../pages/public/ForgotPassword';
import ResetPassword from '../pages/public/ResetPassword';
import PendingApproval from '../pages/public/PendingApproval';

// Admin Pages
import AdminDashboard from '../pages/admin/AdminDashboard';

// Patient Pages (placeholder for now)
// import PatientDashboard from '../pages/patient/Dashboard';
// import UploadDetection from '../pages/patient/UploadDetection';

// Doctor Pages (placeholder for now)
// import DoctorDashboard from '../pages/doctor/Dashboard';
// import MyPatients from '../pages/doctor/MyPatients';

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, isLoggedIn, isApproved } = useAuth();

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }

  // Check for role
  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/" replace />;
  }

  // Check for doctor approval
  if (user?.role === 'doctor' && !isApproved) {
    return <Navigate to="/pending-approval" replace />;
  }

  return children;
};

// Public Route - redirect if already logged in
const PublicRoute = ({ children }) => {
  const { isLoggedIn, isApproved, user } = useAuth();

  if (isLoggedIn) {
    // If doctor and not approved, go to pending approval
    if (user?.role === 'doctor' && !isApproved) {
      return <Navigate to="/pending-approval" replace />;
    }
    // Otherwise redirect to role-based dashboard
    if (user?.role === 'admin') {
      return <Navigate to="/admin/dashboard" replace />;
    }
    if (user?.role === 'doctor') {
      return <Navigate to="/doctor/dashboard" replace />;
    }
    return <Navigate to="/patient/dashboard" replace />;
  }

  return children;
};

const AppRoutes = () => {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route 
          path="/login" 
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          } 
        />
        
        <Route 
          path="/role-selection" 
          element={
            <PublicRoute>
              <RoleSelection />
            </PublicRoute>
          } 
        />
        
        <Route 
          path="/register" 
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          } 
        />
        
        <Route 
          path="/verify-email" 
          element={
            <PublicRoute>
              <EmailVerification />
            </PublicRoute>
          } 
        />
        
        <Route 
          path="/forgot-password" 
          element={
            <PublicRoute>
              <ForgotPassword />
            </PublicRoute>
          } 
        />
        
        <Route 
          path="/reset-password" 
          element={
            <PublicRoute>
              <ResetPassword />
            </PublicRoute>
          } 
        />
        
        <Route 
          path="/pending-approval" 
          element={<PendingApproval />} 
        />
        
        <Route path="/" element={<Navigate to="/login" replace />} />
        
        {/* Admin Routes */}
        <Route 
          path="/admin/dashboard" 
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          } 
        />
        
        {/* TODO: Add more routes as you build them */}
        
        {/* Patient Routes */}
        {/* <Route 
          path="/patient/dashboard" 
          element={
            <ProtectedRoute allowedRoles={['patient']}>
              <PatientDashboard />
            </ProtectedRoute>
          } 
        /> */}
        
        {/* Doctor Routes */}
        {/* <Route 
          path="/doctor/dashboard" 
          element={
            <ProtectedRoute allowedRoles={['doctor']}>
              <DoctorDashboard />
            </ProtectedRoute>
          } 
        /> */}

        {/* Catch all - 404 */}
        <Route path="*" element={<div>Page Not Found</div>} />
      </Routes>
    </Router>
  );
};

export default AppRoutes;
