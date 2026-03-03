import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/ui/Button';
import logo from '../../assets/images/RSlogo2.png';

const PendingApproval = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [countdown, setCountdown] = useState(5);

  // Auto-redirect after countdown (for demo purposes)
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
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
    maxWidth: '480px',
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

  const iconContainerStyle = {
    width: '100px',
    height: '100px',
    borderRadius: '50%',
    backgroundColor: '#FEF3C7',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 24px',
    fontSize: '48px',
  };

  const titleStyle = {
    fontSize: '24px',
    fontWeight: '700',
    color: '#92400E',
    marginBottom: '16px',
  };

  const statusBoxStyle = {
    backgroundColor: '#FEF3C7',
    border: '1px solid #F59E0B',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '24px',
  };

  const statusTitleStyle = {
    fontSize: '18px',
    fontWeight: '600',
    color: '#92400E',
    marginBottom: '8px',
  };

  const statusMessageStyle = {
    fontSize: '14px',
    color: '#B45309',
    lineHeight: '1.6',
  };

  const userInfoStyle = {
    fontSize: '14px',
    color: '#9D174D',
    marginBottom: '24px',
  };

  const userNameStyle = {
    fontWeight: '600',
    color: '#831843',
  };

  const buttonContainerStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  };

  const infoBoxStyle = {
    backgroundColor: '#F3E8FF',
    border: '1px solid #9333EA',
    borderRadius: '8px',
    padding: '16px',
    marginTop: '24px',
    textAlign: 'left',
  };

  const infoTitleStyle = {
    fontSize: '14px',
    fontWeight: '600',
    color: '#7E22CE',
    marginBottom: '8px',
  };

  const infoListStyle = {
    fontSize: '13px',
    color: '#6B21A8',
    paddingLeft: '16px',
    lineHeight: '1.8',
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
        
        {/* Pending Icon */}
        <div style={iconContainerStyle}>⏳</div>
        
        <h2 style={titleStyle}>Account Pending Approval</h2>
        
        {/* Status Box */}
        <div style={statusBoxStyle}>
          <h3 style={statusTitleStyle}>Your account is pending admin approval</h3>
          <p style={statusMessageStyle}>
            Our admin team is reviewing your doctor registration. 
            You'll be notified once your account has been approved.
          </p>
        </div>
        
        {/* User Info */}
        <div style={userInfoStyle}>
          <p>
            Logged in as: <span style={userNameStyle}>{user?.name || user?.fullName || 'Doctor'}</span>
          </p>
          <p>
            Email: <span style={userNameStyle}>{user?.email}</span>
          </p>
          <p>
            Role: <span style={userNameStyle}>Doctor</span>
          </p>
        </div>
        
        {/* Action Buttons */}
        <div style={buttonContainerStyle}>
          <Button
            onClick={() => {
              // In a real app, this would check for approval status
              alert('This is a demo. In production, this would check if your account has been approved.');
            }}
            variant="primary"
          >
            Check Approval Status
          </Button>
          
          <Button
            onClick={handleLogout}
            variant="outline"
          >
            Logout
          </Button>
        </div>
        
        {/* Info Box */}
        <div style={infoBoxStyle}>
          <h4 style={infoTitleStyle}>What happens next?</h4>
          <ul style={infoListStyle}>
            <li>Our admin team will review your credentials</li>
            <li>You'll receive an email once approved</li>
            <li>After approval, you can access the doctor dashboard</li>
            <li>This typically takes 24-48 hours</li>
          </ul>
        </div>
        
        {/* Help Text */}
        <div style={{ ...userInfoStyle, marginTop: '16px' }}>
          <p>
            Need help?{' '}
            <Link to="/contact" style={{ color: '#DB2777', fontWeight: '500' }}>
              Contact Support
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default PendingApproval;
