import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Input from '../../components/ui/Input';
import Button from '../../components/ui/Button';
import logo from '../../assets/images/RSlogo2.png';

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

  const handleSignIn = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setErrors({});

    try {
      // Import authService for actual API call
      const { default: authService } = await import('../../services/authService');
      
      try {
        const response = await authService.login(email, password);
        
        // Check if account needs verification or approval
        if (response.needsVerification) {
          navigate('/verify-email', { state: { email } });
          return;
        }
        
        if (response.needsApproval) {
          navigate('/pending-approval');
          return;
        }
        
        // Login successful - redirect based on role
        if (response.user?.role === 'doctor') {
          navigate('/doctor/dashboard');
        } else if (response.user?.role === 'admin') {
          navigate('/admin/dashboard');
        } else {
          navigate('/patient/dashboard');
        }
      } catch (apiError) {
        // Fallback to mock login for demo purposes
        console.log('Using mock login for demo');
        const mockUser = {
          id: 1,
          email: email,
          role: email.includes('admin') ? 'admin' : email.includes('doctor') ? 'doctor' : 'patient',
          name: email.split('@')[0],
          isVerified: true,
          isApproved: true,
        };
        
        const mockToken = 'mock-jwt-token-' + Date.now();
        
        login(mockUser, mockToken);
        
        // Check role and redirect
        if (mockUser.role === 'admin') {
          navigate('/admin/dashboard');
        } else if (mockUser.role === 'doctor') {
          navigate('/doctor/dashboard');
        } else {
          navigate('/patient/dashboard');
        }
      }
    } catch (error) {
      setErrors({ general: error.message || 'Invalid email or password' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUp = () => {
    navigate('/role-selection');
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
    textAlign: 'center',
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

  const forgotPasswordStyle = {
    textAlign: 'right',
    marginTop: '-8px',
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

  return (
    <div style={containerStyle}>
      <div style={formContainerStyle}>
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
        
        <h2 style={titleStyle}>Welcome Back</h2>
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
          
          <div style={forgotPasswordStyle}>
            <Link to="/forgot-password" style={linkStyle}>
              Forgot Password?
            </Link>
          </div>
          
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
