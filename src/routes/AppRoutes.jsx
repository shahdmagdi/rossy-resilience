// This handles all navigation in your app
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Public Pages
import Login from '../pages/public/Login';
// import Register from '../pages/public/Register'; // Create next week
// import Landing from '../pages/public/Landing'; // Create next week

// Patient Pages (placeholder for now)
// import PatientDashboard from '../pages/patient/Dashboard';
// import UploadDetection from '../pages/patient/UploadDetection';

// Doctor Pages (placeholder for now)
// import DoctorDashboard from '../pages/doctor/Dashboard';
// import MyPatients from '../pages/doctor/MyPatients';

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, isLoggedIn } = useAuth();

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/" replace />;
  }

  return children;
};

const AppRoutes = () => {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Navigate to="/login" replace />} />
        
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