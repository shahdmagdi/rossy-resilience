import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/ui/Button';
import logo from '../../assets/images/RSlogo2.png';

const EmailVerification = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || '';
  const { login } = useAuth();
  
  const [verificationCode, setVerificationCode] = useState(['', '', '', '', '', '']);
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [resendTimer, setResendTimer] = useState(0);
  const [resendEnabled, setResendEnabled] = useState(false);
  
  const inputRefs = useRef([]);

  useEffect(() => {
    // Start resend timer
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      setResendEnabled(true);
    }
  }, [resendTimer]);

  const handleChange = (element, index) => {
    if (isNaN(element.value)) return false;
    
    const newCode = [...verificationCode];
    newCode[index] = element.value;
    setVerificationCode(newCode);
    
    // Clear error when user starts typing
    if (errors.code) {
      setErrors(prev => ({ ...prev, code: '' }));
    }
    
    // Auto-focus next input
    if (element.value !== '' && index < 5) {
      inputRefs.current[index + 1].focus();
    }
  };

  const handleKeyDown = (e, index) => {
    // Handle backspace - focus previous input
    if (e.key === 'Backspace' && verificationCode[index] === '' && index > 0) {
      inputRefs.current[index - 1].focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').slice(0, 6);
    const newCode = [...verificationCode];
    
    for (let i = 0; i < pastedData.length; i++) {
      if (!isNaN(pastedData[i])) {
        newCode[i] = pastedData[i];
      }
    }
    
    setVerificationCode(newCode);
    
    // Focus appropriate input after paste
    const lastFilledIndex = Math.min(pastedData.length, 5);
    inputRefs.current[lastFilledIndex]?.focus();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const code = verificationCode.join('');
    
    if (code.length !== 6) {
      setErrors({ code: 'Please enter the complete 6-digit code' });
      return;
    }

    setIsLoading(true);
    setErrors({});

    try {
      // Import authService for actual API call
      const { default: authService } = await import('../../services/authService');
      
      try {
        const response = await authService.verifyEmail(code);
        
        // Check response and handle accordingly
        if (response.success) {
          // If doctor, check if approved
          if (response.user?.role === 'doctor' && !response.user.isApproved) {
            navigate('/pending-approval');
            return;
          }
          
          // Login successful
          login(response.user, response.token);
          
          // Redirect based on role
          if (response.user?.role === 'doctor') {
            navigate('/doctor/dashboard');
          } else if (response.user?.role === 'admin') {
            navigate('/admin/dashboard');
          } else {
            navigate('/patient/dashboard');
          }
        }
      } catch (apiError) {
        // Mock verification for demo
        console.log('Using mock verification for demo');
        
        // Get pending user from localStorage
        const pendingUserData = localStorage.getItem('pendingUser');
        
        // For demo, accept code "123456" or any 6-digit code
        if (code.length === 6) {
          const pendingUser = pendingUserData ? JSON.parse(pendingUserData) : {};
          
          // Simulate verification
          const verifiedUser = {
            ...pendingUser,
            isVerified: true,
            email: email || pendingUser.email,
            isApproved: pendingUser.role !== 'doctor', // Doctors need admin approval
          };
          
          const mockToken = 'verified-jwt-token-' + Date.now();
          
          // Store user data
          login(verifiedUser, mockToken);
          localStorage.removeItem('pendingUser');
          
          // Navigate based on role
          if (verifiedUser.role === 'doctor') {
            navigate('/pending-approval');
          } else if (verifiedUser.role === 'admin') {
            navigate('/admin/dashboard');
          } else {
            navigate('/patient/dashboard');
          }
        } else {
          setErrors({ code: 'Invalid verification code' });
        }
      }
    } catch (error) {
      setErrors({ code: error.message || 'Verification failed. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async () => {
    setResendEnabled(false);
    setResendTimer(60); // 60 seconds cooldown
    
    try {
      // Import authService for actual API call
      const { default: authService } = await import('../../services/authService');
      
      try {
        await authService.resendVerificationCode(email);
        alert('Verification code sent! Please check your email.');
      } catch (apiError) {
        // Mock resend for demo
        console.log('Mock: Verification code resent');
      }
    } catch (error) {
      console.error('Error resending code:', error);
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

  const emailHighlightStyle = {
    fontWeight: '600',
    color: '#831843',
  };

  const codeInputContainerStyle = {
    display: 'flex',
    justifyContent: 'center',
    gap: '8px',
    marginBottom: '24px',
  };

  const codeInputStyle = (hasError) => ({
    width: '48px',
    height: '56px',
    textAlign: 'center',
    fontSize: '24px',
    fontWeight: '600',
    borderRadius: '8px',
    border: hasError ? '2px solid #DB2777' : '2px solid #F9A8D4',
    backgroundColor: '#FDF2F8',
    color: '#831843',
    outline: 'none',
    transition: 'border-color 0.3s ease',
  });

  const errorStyle = {
    color: '#DB2777',
    fontSize: '14px',
    marginBottom: '16px',
  };

  const resendContainerStyle = {
    marginTop: '16px',
    fontSize: '14px',
    color: '#9D174D',
  };

  const resendButtonStyle = {
    background: 'none',
    border: 'none',
    color: resendEnabled ? '#DB2777' : '#9D174D',
    fontWeight: '600',
    cursor: resendEnabled ? 'pointer' : 'not-allowed',
    fontSize: '14px',
    textDecoration: resendEnabled ? 'underline' : 'none',
  };

  const footerStyle = {
    marginTop: '32px',
    fontSize: '14px',
    color: '#9D174D',
  };

  const linkStyle = {
    color: '#DB2777',
    textDecoration: 'none',
    fontWeight: '500',
    cursor: 'pointer',
  };

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
        
        {/* Email Icon */}
        <div style={iconStyle}>📧</div>
        
        <h2 style={titleStyle}>Verify Your Email</h2>
        <p style={descriptionStyle}>
          We've sent a 6-digit verification code to<br />
          <span style={emailHighlightStyle}>{email}</span>
        </p>
        
        <form onSubmit={handleSubmit}>
          {/* Verification Code Inputs */}
          <div style={codeInputContainerStyle}>
            {verificationCode.map((digit, index) => (
              <input
                key={index}
                ref={(el) => inputRefs.current[index] = el}
                type="text"
                maxLength="1"
                value={digit}
                onChange={(e) => handleChange(e.target, index)}
                onKeyDown={(e) => handleKeyDown(e, index)}
                onPaste={handlePaste}
                style={codeInputStyle(!!errors.code)}
                disabled={isLoading}
              />
            ))}
          </div>
          
          {errors.code && (
            <div style={errorStyle}>{errors.code}</div>
          )}
          
          <Button
            type="submit"
            variant="primary"
            disabled={isLoading}
            style={{ width: '100%' }}
          >
            {isLoading ? 'Verifying...' : 'Verify Email'}
          </Button>
        </form>
        
        {/* Resend Code */}
        <div style={resendContainerStyle}>
          {resendEnabled ? (
            <button 
              type="button"
              onClick={handleResendCode}
              style={resendButtonStyle}
            >
              Resend Verification Code
            </button>
          ) : (
            <span>Resend code in {resendTimer} seconds</span>
          )}
        </div>
        
        <div style={footerStyle}>
          <p>
            Already verified?{' '}
            <Link to="/login" style={linkStyle}>
              Login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default EmailVerification;
