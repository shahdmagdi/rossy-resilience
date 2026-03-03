import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import Input from '../../components/ui/Input';
import Button from '../../components/ui/Button';
import logo from '../../assets/images/RSlogo2.png';

const Register = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const selectedRole = location.state?.role || 'patient';
  
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    phoneNumber: '',
    dateOfBirth: '',
  });
  
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    } else if (formData.fullName.trim().length < 2) {
      newErrors.fullName = 'Full name must be at least 2 characters';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }
    
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
    
    if (!formData.phoneNumber.trim()) {
      newErrors.phoneNumber = 'Phone number is required';
    } else if (!/^\+?[\d\s-]{10,}$/.test(formData.phoneNumber.replace(/\s/g, ''))) {
      newErrors.phoneNumber = 'Please enter a valid phone number';
    }
    
    if (!formData.dateOfBirth) {
      newErrors.dateOfBirth = 'Date of birth is required';
    } else {
      const birthDate = new Date(formData.dateOfBirth);
      const today = new Date();
      const age = today.getFullYear() - birthDate.getFullYear();
      if (birthDate > today) {
        newErrors.dateOfBirth = 'Date of birth cannot be in the future';
      } else if (age < 13) {
        newErrors.dateOfBirth = 'You must be at least 13 years old';
      }
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

    setIsLoading(true);
    setErrors({});

    try {
      // Prepare registration data
      const registrationData = {
        fullName: formData.fullName,
        email: formData.email,
        password: formData.password,
        phoneNumber: formData.phoneNumber,
        dateOfBirth: formData.dateOfBirth,
        role: selectedRole,
      };

      // Import authService for actual API call
      const { default: authService } = await import('../../services/authService');
      
      try {
        const response = await authService.register(registrationData);
        
        // If registration successful, navigate to verification
        if (response.requiresVerification) {
          navigate('/verify-email', { state: { email: formData.email } });
        } else {
          // Direct login for admin or approved users
          navigate('/');
        }
      } catch (apiError) {
        // Mock registration for demo purposes
        console.log('Using mock registration for demo');
        
        // Store pending user data for verification
        const pendingUser = {
          ...registrationData,
          id: Date.now(),
          isVerified: false,
          isApproved: selectedRole !== 'doctor', // Doctors need approval, patients and admins are auto-approved
        };
        
        localStorage.setItem('pendingUser', JSON.stringify(pendingUser));
        
        // Navigate to email verification
        navigate('/verify-email', { state: { email: formData.email } });
      }
    } catch (error) {
      setErrors({ general: error.message || 'Registration failed. Please try again.' });
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

  const formContainerStyle = {
    backgroundColor: '#ffffff',
    padding: '40px',
    borderRadius: '16px',
    boxShadow: '0 10px 40px rgba(219, 39, 119, 0.15)',
    width: '100%',
    maxWidth: '480px',
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

  const instructionStyle = {
    fontSize: '14px',
    color: '#9D174D',
    marginBottom: '24px',
    textAlign: 'center',
  };

  const roleIndicatorStyle = {
    display: 'flex',
    justifyContent: 'center',
    gap: '12px',
    marginBottom: '24px',
    padding: '12px',
    backgroundColor: '#FDF2F8',
    borderRadius: '8px',
  };

  const roleLabelStyle = {
    fontSize: '14px',
    color: '#831843',
    fontWeight: '500',
  };

  const roleOptionStyle = (role) => ({
    padding: '8px 16px',
    borderRadius: '20px',
    fontSize: '14px',
    fontWeight: '600',
    backgroundColor: selectedRole === role ? '#DB2777' : 'transparent',
    color: selectedRole === role ? '#ffffff' : '#9D174D',
    border: selectedRole === role ? 'none' : '1px solid #F9A8D4',
    cursor: 'default',
    transition: 'all 0.3s ease',
  });

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
        
        <h2 style={titleStyle}>Create Your Account</h2>
        <p style={instructionStyle}>Choose your role and fill in your details</p>
        
        {/* Role Indicator */}
        <div style={roleIndicatorStyle}>
          <span style={roleLabelStyle}>I am a:</span>
          <span style={roleOptionStyle('patient')}>Patient</span>
          <span style={roleOptionStyle('doctor')}>Doctor</span>
          <span style={roleOptionStyle('admin')}>Admin</span>
        </div>
        
        {errors.general && (
          <div style={errorBannerStyle}>{errors.general}</div>
        )}
        
        <form onSubmit={handleSubmit}>
          <Input
            label="Full Name"
            type="text"
            name="fullName"
            value={formData.fullName}
            onChange={handleChange}
            placeholder="Enter your full name"
            error={errors.fullName}
            required
          />
          
          <Input
            label="Email Address"
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="Enter your email"
            error={errors.email}
            required
          />
          
          <Input
            label="Password"
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Create a password"
            error={errors.password}
            required
          />
          
          <Input
            label="Confirm Password"
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="Confirm your password"
            error={errors.confirmPassword}
            required
          />
          
          <Input
            label="Phone Number"
            type="tel"
            name="phoneNumber"
            value={formData.phoneNumber}
            onChange={handleChange}
            placeholder="Enter your phone number"
            error={errors.phoneNumber}
            required
          />
          
          <Input
            label="Date of Birth"
            type="date"
            name="dateOfBirth"
            value={formData.dateOfBirth}
            onChange={handleChange}
            error={errors.dateOfBirth}
            required
          />
          
          <Button
            type="submit"
            variant="primary"
            disabled={isLoading}
            style={{ width: '100%', marginTop: '16px' }}
          >
            {isLoading ? 'Creating Account...' : 'Create Account'}
          </Button>
        </form>
        
        <div style={footerStyle}>
          <p>
            Already have an account?{' '}
            <Link to="/login" style={linkStyle}>
              Login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
