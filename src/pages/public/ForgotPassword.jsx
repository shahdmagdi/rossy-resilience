import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Input from '../../components/ui/Input';
import Button from '../../components/ui/Button';
import logo from '../../assets/images/RSlogo2.png';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  
  const navigate = useNavigate();

  const validateEmail = () => {
    if (!email.trim()) {
      setErrors({ email: 'Email is required' });
      return false;
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      setErrors({ email: 'Please enter a valid email' });
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateEmail()) {
      return;
    }

    setIsLoading(true);
    setErrors({});

    try {
      // Import authService for actual API call
      const { default: authService } = await import('../../services/authService');
      
      try {
        await authService.forgotPassword(email);
        setEmailSent(true);
      } catch (apiError) {
        // Mock for demo
        console.log('Mock: Password reset email sent');
        setEmailSent(true);
      }
    } catch (error) {
      setErrors({ general: error.message || 'Failed to send reset email. Please try again.' });
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

  if (emailSent) {
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
          
          <h2 style={titleStyle}>Check Your Email</h2>
          <p style={descriptionStyle}>
            We've sent password reset instructions to<br />
            <strong>{email}</strong>
          </p>
          
          <div style={successStyle}>
            Please check your inbox and click the link to reset your password. 
            If you don't see the email, check your spam folder.
          </div>
          
          <Button
            onClick={() => navigate('/login')}
            variant="primary"
            style={{ width: '100%' }}
          >
            Back to Login
          </Button>
          
          <div style={footerStyle}>
            <p>
              Didn't receive the email?{' '}
              <button 
                onClick={() => setEmailSent(false)}
                style={{ background: 'none', border: 'none', ...linkStyle }}
              >
                Try again
              </button>
            </p>
          </div>
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
        <div style={iconStyle}>🔐</div>
        
        <h2 style={titleStyle}>Forgot Password?</h2>
        <p style={descriptionStyle}>
          No worries, we'll send you reset instructions
        </p>
        
        {errors.general && (
          <div style={errorBannerStyle}>{errors.general}</div>
        )}
        
        <form onSubmit={handleSubmit}>
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
          
          <Button
            type="submit"
            variant="primary"
            disabled={isLoading}
            style={{ width: '100%', marginTop: '8px' }}
          >
            {isLoading ? 'Sending...' : 'Send Reset Link'}
          </Button>
        </form>
        
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
};

export default ForgotPassword;
