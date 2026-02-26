import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Input from '../../components/ui/Input';
import Button from '../../components/ui/Button';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const validateForm = () => {
    const newErrors = {};
    
    if (!email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Please enter a valid email';
    }
    
    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSignIn = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      // Simulate API call - replace with actual API call
      console.log('Email:', email);
      console.log('Password:', password);
      
      // Simulate login - in production, this would be an API call
      const mockUser = {
        id: 1,
        email: email,
        role: email.includes('doctor') ? 'doctor' : 'patient',
        name: email.split('@')[0],
      };
      
      const mockToken = 'mock-jwt-token-' + Date.now();
      
      login(mockUser, mockToken);
      navigate('/');
    } catch (error) {
      setErrors({ general: 'Invalid email or password' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUp = () => {
    console.log('Sign Up clicked');
  };

  const containerStyle = {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FCE7F3',
    padding: '20px',
  };

  const formContainerStyle = {
    backgroundColor: '#ffffff',
    padding: '40px',
    borderRadius: '16px',
    boxShadow: '0 10px 40px rgba(219, 39, 119, 0.15)',
    width: '100%',
    maxWidth: '420px',
  };

  const titleStyle = {
    fontSize: '28px',
    fontWeight: '700',
    color: '#831843',
    marginBottom: '8px',
    textAlign: 'center',
  };

  const subtitleStyle = {
    fontSize: '14px',
    color: '#9D174D',
    marginBottom: '32px',
    textAlign: 'center',
  };

  const footerStyle = {
    marginTop: '24px',
    textAlign: 'center',
    fontSize: '14px',
    color: '#9D174D',
  };

  const linkStyle = {
    color: '#DB2777',
    textDecoration: 'none',
    fontWeight: '500',
    cursor: 'pointer',
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

  return (
    <div style={containerStyle}>
      <div style={formContainerStyle}>
        <h1 style={titleStyle}>Welcome Back</h1>
        <p style={subtitleStyle}>Sign in to continue to your account</p>
        
        {errors.general && (
          <div style={errorBannerStyle}>{errors.general}</div>
        )}
        
        <form onSubmit={handleSignIn}>
          <Input
            label="Email Address"
            type="email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            error={errors.email}
            required
          />
          
          <Input
            label="Password"
            type="password"
            name="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            error={errors.password}
            required
          />
          
          <Button
            type="submit"
            variant="primary"
            disabled={isLoading}
            style={{ width: '100%', marginTop: '8px' }}
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>
        
        <div style={footerStyle}>
          <p>
            Don't have an account?{' '}
            <span 
              style={linkStyle}
              onClick={handleSignUp}
            >
              Sign up
            </span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
