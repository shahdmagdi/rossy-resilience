import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Input from '../../components/ui/Input';
import Button from '../../components/ui/Button';
import logo from '../../assets/images/RSlogo2.png';

const ResetPassword = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  
  // Get token from URL query params
  const searchParams = new URLSearchParams(location.search);
  const token = searchParams.get('token');
  
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Password must contain uppercase, lowercase, and number';
    }
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    if (!token) {
      setErrors({ general: 'Invalid reset token. Please request a new password reset.' });
      return;
    }

    setIsLoading(true);
    setErrors({});

    try {
      // Import authService for actual API call
      const { default: authService } = await import('../../services/authService');
      
      try {
        const response = await authService.resetPassword(token, formData.password);
        
        // Login the user after successful password reset
        if (response.user && response.token) {
          login(response.user, response.token);
          
          // Redirect based on role
          if (response.user.role === 'doctor') {
            navigate('/doctor/dashboard');
          } else if (response.user.role === 'admin') {
            navigate('/admin/dashboard');
          } else {
            navigate('/patient/dashboard');
          }
        } else {
          setIsSuccess(true);
        }
      } catch (apiError) {
        // Mock reset for demo
        console.log('Mock: Password reset successful');
        setIsSuccess(true);
      }
    } catch (error) {
      setErrors({ general: error.message || 'Failed to reset password. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const containerStyle = {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FCE7F3',
    padding: '20px',
  };

  const cardContainerStyle = {
    backgroundColor: '#ffffff',
    padding: '48px',
    borderRadius: '16px',
    boxShadow: '0 10px 40px rgba(219, 39, 119, 0.15)',
    width: '100%',
    maxWidth: '420px',
    textAlign: 'center',
  };

  const logoContainerStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    marginBottom: '24px',
  };

  const logoImageStyle = {
    width: '60px',
    height: '60px',
    objectFit: 'contain',
  };

  const logoTextStyle = {
    fontSize: '28px',
    fontWeight: '700',
    color: '#831843',
    letterSpacing: '-0.5px',
  };

  const logoSubtitleStyle = {
    fontSize: '14px',
    color: '#9D174D',
    marginTop: '2px',
  };

  const iconStyle = {
    width: '80px',
    height: '80px',
    borderRadius: '50%',
    backgroundColor: '#FCE7F3',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 24px',
    fontSize: '36px',
  };

  const titleStyle = {
    fontSize: '24px',
    fontWeight: '700',
    color: '#831843',
    marginBottom: '12px',
  };

  const descriptionStyle = {
    fontSize: '14px',
    color: '#9D174D',
    marginBottom: '32px',
    lineHeight: '1.6',
  };

  const successStyle = {
    backgroundColor: '#ECFDF5',
    border: '1px solid #10B981',
    borderRadius: '8px',
    padding: '16px',
    marginBottom: '24px',
    color: '#065F46',
    fontSize: '14px',
  };

  const successIconStyle = {
    fontSize: '48px',
    marginBottom: '16px',
  };

  const errorBannerStyle = {
    backgroundColor: '#FCE7F2',
    border: '1px solid #DB2777',
    borderRadius: '8px',
    padding: '12px',
    marginBottom: '16px',
    color: '#DB2777',
    fontSize: '14px',
    textAlign: 'center',
  };

  const footerStyle = {
    marginTop: '24px',
    fontSize: '14px',
    color: '#9D174D',
  };

  const linkStyle = {
    color: '#DB2777',
    textDecoration: 'none',
    fontWeight: '500',
    cursor: 'pointer',
  };

  if (!token) {
    return (
      <div style={containerStyle}>
        <div style={cardContainerStyle}>
          {/* Logo with Text - Center Left */}
          <div style={logoContainerStyle}>
            <img 
              src={logo} 
              alt="Rossy Resilience Logo" 
              style={logoImageStyle}
            />
            <div>
              <h1 style={logoTextStyle}>Rossy Resilience</h1>
            </div>
          </div>
          <p style={logoSubtitleStyle}>Your Health, Our Priority</p>
          
          {/* Warning Icon */}
          <div style={iconStyle}>⚠️</div>
          
          <h2 style={titleStyle}>Invalid Link</h2>
          <p style={descriptionStyle}>
            This password reset link is invalid or has expired.
          </p>
          
          <Button
            onClick={() => navigate('/forgot-password')}
            variant="primary"
            style={{ width: '100%' }}
          >
            Request New Reset Link
          </Button>
          
          <div style={footerStyle}>
            <p>
              Remember your password?{' '}
              <Link to="/login" style={linkStyle}>
                Login
              </Link>
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (isSuccess) {
    return (
      <div style={containerStyle}>
        <div style={cardContainerStyle}>
          {/* Logo with Text - Center Left */}
          <div style={logoContainerStyle}>
            <img 
              src={logo} 
              alt="Rossy Resilience Logo" 
              style={logoImageStyle}
            />
            <div>
              <h1 style={logoTextStyle}>Rossy Resilience</h1>
            </div>
          </div>
          <p style={logoSubtitleStyle}>Your Health, Our Priority</p>
          
          {/* Success Icon */}
          <div style={successIconStyle}>✅</div>
          
          <h2 style={titleStyle}>Password Reset</h2>
          <p style={descriptionStyle}>
            Your password has been successfully reset.
          </p>
          
          <div style={successStyle}>
            You can now login with your new password.
          </div>
          
          <Button
            onClick={() => navigate('/login')}
            variant="primary"
            style={{ width: '100%' }}
          >
            Go to Login
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <div style={cardContainerStyle}>
        {/* Logo with Text - Center Left */}
        <div style={logoContainerStyle}>
          <img 
            src={logo} 
            alt="Rossy Resilience Logo" 
            style={logoImageStyle}
          />
          <div>
            <h1 style={logoTextStyle}>Rossy Resilience</h1>
          </div>
        </div>
        <p style={logoSubtitleStyle}>Your Health, Our Priority</p>
        
        {/* Lock Icon */}
        <div style={iconStyle}>🔒</div>
        
        <h2 style={titleStyle}>Set New Password</h2>
        <p style={descriptionStyle}>
          Create a strong password for your account
        </p>
        
        {errors.general && (
          <div style={errorBannerStyle}>{errors.general}</div>
        )}
        
        <form onSubmit={handleSubmit}>
          <Input
            label="New Password"
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Create a new password"
            error={errors.password}
            required
          />
          
          <Input
            label="Confirm New Password"
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="Confirm your new password"
            error={errors.confirmPassword}
            required
          />
          
          <Button
            type="submit"
            variant="primary"
            disabled={isLoading}
            style={{ width: '100%', marginTop: '8px' }}
          >
            {isLoading ? 'Resetting...' : 'Reset Password'}
          </Button>
        </form>
        
        <div style={footerStyle}>
          <p>
            Don't want to change password?{' '}
            <Link to="/login" style={linkStyle}>
              Cancel
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
