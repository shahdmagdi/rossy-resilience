import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Button from '../../components/ui/Button';
import logo from '../../assets/images/RSlogo2.png';

const RoleSelection = () => {
  const navigate = useNavigate();

  const handleRoleSelect = (role) => {
    // Navigate to registration with the selected role
    navigate('/register', { state: { role } });
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
    maxWidth: '600px',
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

  const titleStyle = {
    fontSize: '28px',
    fontWeight: '700',
    color: '#831843',
    marginBottom: '8px',
  };

  const subtitleStyle = {
    fontSize: '16px',
    color: '#9D174D',
    marginBottom: '40px',
  };

  const roleContainerStyle = {
    display: 'flex',
    gap: '20px',
    marginBottom: '32px',
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
  };

  const roleCardStyle = {
    flex: '1',
    minWidth: '150px',
    maxWidth: '170px',
    padding: '24px 16px',
    borderRadius: '12px',
    border: '2px solid #F9A8D4',
    backgroundColor: '#FDF2F8',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '12px',
  };

  const roleIconStyle = {
    width: '56px',
    height: '56px',
    borderRadius: '50%',
    backgroundColor: '#FCE7F3',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '24px',
  };

  const roleTitleStyle = {
    fontSize: '16px',
    fontWeight: '600',
    color: '#831843',
  };

  const roleDescriptionStyle = {
    fontSize: '12px',
    color: '#9D174D',
    lineHeight: '1.5',
  };

  const footerStyle = {
    marginTop: '16px',
    fontSize: '14px',
    color: '#9D174D',
  };

  const linkStyle = {
    color: '#DB2777',
    textDecoration: 'none',
    fontWeight: '500',
    cursor: 'pointer',
  };

  const handleRoleHover = (e, isHovering) => {
    if (isHovering) {
      e.currentTarget.style.borderColor = '#DB2777';
      e.currentTarget.style.boxShadow = '0 8px 24px rgba(219, 39, 119, 0.2)';
      e.currentTarget.style.transform = 'translateY(-4px)';
    } else {
      e.currentTarget.style.borderColor = '#F9A8D4';
      e.currentTarget.style.boxShadow = 'none';
      e.currentTarget.style.transform = 'translateY(0)';
    }
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
        
        <h2 style={titleStyle}>Create Your Account</h2>
        <p style={subtitleStyle}>Join our caring community</p>
        
        <div style={roleContainerStyle}>
          {/* Patient Role Card */}
          <div 
            style={roleCardStyle}
            onClick={() => handleRoleSelect('patient')}
            onMouseEnter={(e) => handleRoleHover(e, true)}
            onMouseLeave={(e) => handleRoleHover(e, false)}
          >
            <div style={roleIconStyle}>🧑‍🤝‍🧑</div>
            <h3 style={roleTitleStyle}>Patient</h3>
            <p style={roleDescriptionStyle}>
              Register as a patient to receive care and support
            </p>
          </div>

          {/* Doctor Role Card */}
          <div 
            style={roleCardStyle}
            onClick={() => handleRoleSelect('doctor')}
            onMouseEnter={(e) => handleRoleHover(e, true)}
            onMouseLeave={(e) => handleRoleHover(e, false)}
          >
            <div style={roleIconStyle}>👨‍⚕️</div>
            <h3 style={roleTitleStyle}>Doctor</h3>
            <p style={roleDescriptionStyle}>
              Register as a healthcare professional to help patients
            </p>
          </div>

          {/* Admin Role Card */}
          <div 
            style={roleCardStyle}
            onClick={() => handleRoleSelect('admin')}
            onMouseEnter={(e) => handleRoleHover(e, true)}
            onMouseLeave={(e) => handleRoleHover(e, false)}
          >
            <div style={roleIconStyle}>👨‍💼</div>
            <h3 style={roleTitleStyle}>Admin</h3>
            <p style={roleDescriptionStyle}>
              Manage approvals and oversee the platform
            </p>
          </div>
        </div>
        
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

export default RoleSelection;
