import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/ui/Button';
import logo from '../../assets/images/RSlogo2.png';

const AdminDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  // Mock data for pending users (in real app, this would come from API)
  const [pendingPatients, setPendingPatients] = useState([
    { id: 1, name: 'John Smith', email: 'john@example.com', phone: '+1234567890', dateOfBirth: '1990-05-15', status: 'pending' },
    { id: 2, name: 'Sarah Johnson', email: 'sarah@example.com', phone: '+1234567891', dateOfBirth: '1985-08-22', status: 'pending' },
    { id: 3, name: 'Mike Wilson', email: 'mike@example.com', phone: '+1234567892', dateOfBirth: '1992-03-10', status: 'pending' },
  ]);
  
  const [pendingDoctors, setPendingDoctors] = useState([
    { id: 4, name: 'Dr. Emily Brown', email: 'emily@doctor.com', phone: '+1234567893', specialty: 'Cardiology', status: 'pending' },
    { id: 5, name: 'Dr. David Lee', email: 'david@doctor.com', phone: '+1234567894', specialty: 'Neurology', status: 'pending' },
    { id: 6, name: 'Dr. Lisa Chen', email: 'lisa@doctor.com', phone: '+1234567895', specialty: 'Pediatrics', status: 'pending' },
  ]);
  
  const [activeTab, setActiveTab] = useState('doctors');
  const [notification, setNotification] = useState(null);

  // Show notification
  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  // Approve user
  const handleApprove = (userId, userType) => {
    if (userType === 'doctor') {
      setPendingDoctors(prev => prev.filter(d => d.id !== userId));
    } else {
      setPendingPatients(prev => prev.filter(p => p.id !== userId));
    }
    showNotification(`User has been approved successfully!`);
  };

  // Reject user
  const handleReject = (userId, userType) => {
    if (userType === 'doctor') {
      setPendingDoctors(prev => prev.filter(d => d.id !== userId));
    } else {
      setPendingPatients(prev => prev.filter(p => p.id !== userId));
    }
    showNotification(`User has been rejected.`);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const containerStyle = {
    minHeight: '100vh',
    backgroundColor: '#FCE7F3',
  };

  const headerStyle = {
    backgroundColor: '#ffffff',
    padding: '16px 32px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };

  const logoContainerStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  };

  const logoImageStyle = {
    width: '40px',
    height: '40px',
    objectFit: 'contain',
  };

  const logoTextStyle = {
    fontSize: '22px',
    fontWeight: '700',
    color: '#831843',
  };

  const userInfoStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  };

  const userNameStyle = {
    fontSize: '14px',
    color: '#831843',
    fontWeight: '500',
  };

  const mainContentStyle = {
    padding: '32px',
    maxWidth: '1200px',
    margin: '0 auto',
  };

  const pageTitleStyle = {
    fontSize: '28px',
    fontWeight: '700',
    color: '#831843',
    marginBottom: '24px',
  };

  const tabContainerStyle = {
    display: 'flex',
    gap: '16px',
    marginBottom: '24px',
  };

  const tabStyle = (isActive) => ({
    padding: '12px 24px',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    backgroundColor: isActive ? '#DB2777' : '#ffffff',
    color: isActive ? '#ffffff' : '#831843',
    border: 'none',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    transition: 'all 0.3s ease',
  });

  const cardStyle = {
    backgroundColor: '#ffffff',
    borderRadius: '12px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
    overflow: 'hidden',
  };

  const cardHeaderStyle = {
    padding: '16px 24px',
    backgroundColor: '#FDF2F8',
    borderBottom: '1px solid #F9A8D4',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };

  const cardTitleStyle = {
    fontSize: '18px',
    fontWeight: '600',
    color: '#831843',
  };

  const badgeStyle = (count) => ({
    backgroundColor: count > 0 ? '#DB2777' : '#9CA3AF',
    color: '#ffffff',
    padding: '4px 12px',
    borderRadius: '20px',
    fontSize: '14px',
    fontWeight: '600',
  });

  const listStyle = {
    listStyle: 'none',
    padding: 0,
    margin: 0,
  };

  const listItemStyle = {
    padding: '16px 24px',
    borderBottom: '1px solid #F3F4F6',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };

  const userDetailsStyle = {
    flex: 1,
  };

  const userNameStyle2 = {
    fontSize: '16px',
    fontWeight: '600',
    color: '#111827',
    marginBottom: '4px',
  };

  const userEmailStyle = {
    fontSize: '14px',
    color: '#6B7280',
    marginBottom: '2px',
  };

  const userPhoneStyle = {
    fontSize: '13px',
    color: '#9CA3AF',
  };

  const specialtyStyle = {
    fontSize: '14px',
    color: '#DB2777',
    fontWeight: '500',
    marginTop: '4px',
  };

  const actionButtonsStyle = {
    display: 'flex',
    gap: '8px',
  };

  const approveButtonStyle = {
    padding: '8px 16px',
    backgroundColor: '#10B981',
    color: '#ffffff',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background-color 0.3s ease',
  };

  const rejectButtonStyle = {
    padding: '8px 16px',
    backgroundColor: '#EF4444',
    color: '#ffffff',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background-color 0.3s ease',
  };

  const emptyStateStyle = {
    padding: '48px',
    textAlign: 'center',
    color: '#6B7280',
    fontSize: '16px',
  };

  const notificationStyle = {
    position: 'fixed',
    top: '20px',
    right: '20px',
    padding: '16px 24px',
    borderRadius: '8px',
    backgroundColor: notification?.type === 'success' ? '#10B981' : '#EF4444',
    color: '#ffffff',
    fontSize: '14px',
    fontWeight: '500',
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
    zIndex: 1000,
  };

  return (
    <div style={containerStyle}>
      {/* Notification */}
      {notification && (
        <div style={notificationStyle}>
          {notification.message}
        </div>
      )}
      
      {/* Header */}
      <header style={headerStyle}>
        <div style={logoContainerStyle}>
          <img 
            src={logo} 
            alt="Rossy Resilience Logo" 
            style={logoImageStyle}
          />
          <span style={logoTextStyle}>Rossy Resilience</span>
        </div>
        
        <div style={userInfoStyle}>
          <span style={userNameStyle}>Welcome, {user?.name || 'Admin'}</span>
          <Button onClick={handleLogout} variant="outline" style={{ padding: '8px 16px' }}>
            Logout
          </Button>
        </div>
      </header>
      
      {/* Main Content */}
      <main style={mainContentStyle}>
        <h1 style={pageTitleStyle}>Admin Dashboard</h1>
        
        {/* Tabs */}
        <div style={tabContainerStyle}>
          <button 
            style={tabStyle(activeTab === 'doctors')}
            onClick={() => setActiveTab('doctors')}
          >
            Pending Doctors ({pendingDoctors.length})
          </button>
          <button 
            style={tabStyle(activeTab === 'patients')}
            onClick={() => setActiveTab('patients')}
          >
            Pending Patients ({pendingPatients.length})
          </button>
        </div>
        
        {/* Content */}
        {activeTab === 'doctors' && (
          <div style={cardStyle}>
            <div style={cardHeaderStyle}>
              <h2 style={cardTitleStyle}>Pending Doctor Approvals</h2>
              <span style={badgeStyle(pendingDoctors.length)}>{pendingDoctors.length} pending</span>
            </div>
            
            {pendingDoctors.length > 0 ? (
              <ul style={listStyle}>
                {pendingDoctors.map(doctor => (
                  <li key={doctor.id} style={listItemStyle}>
                    <div style={userDetailsStyle}>
                      <div style={userNameStyle2}>{doctor.name}</div>
                      <div style={userEmailStyle}>{doctor.email}</div>
                      <div style={userPhoneStyle}>{doctor.phone}</div>
                      <div style={specialtyStyle}>Specialty: {doctor.specialty}</div>
                    </div>
                    <div style={actionButtonsStyle}>
                      <button 
                        style={approveButtonStyle}
                        onClick={() => handleApprove(doctor.id, 'doctor')}
                        onMouseOver={(e) => e.target.style.backgroundColor = '#059669'}
                        onMouseOut={(e) => e.target.style.backgroundColor = '#10B981'}
                      >
                        Approve
                      </button>
                      <button 
                        style={rejectButtonStyle}
                        onClick={() => handleReject(doctor.id, 'doctor')}
                        onMouseOver={(e) => e.target.style.backgroundColor = '#DC2626'}
                        onMouseOut={(e) => e.target.style.backgroundColor = '#EF4444'}
                      >
                        Reject
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div style={emptyStateStyle}>
                No pending doctor approvals
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'patients' && (
          <div style={cardStyle}>
            <div style={cardHeaderStyle}>
              <h2 style={cardTitleStyle}>Pending Patient Approvals</h2>
              <span style={badgeStyle(pendingPatients.length)}>{pendingPatients.length} pending</span>
            </div>
            
            {pendingPatients.length > 0 ? (
              <ul style={listStyle}>
                {pendingPatients.map(patient => (
                  <li key={patient.id} style={listItemStyle}>
                    <div style={userDetailsStyle}>
                      <div style={userNameStyle2}>{patient.name}</div>
                      <div style={userEmailStyle}>{patient.email}</div>
                      <div style={userPhoneStyle}>{patient.phone}</div>
                      <div style={userPhoneStyle}>DOB: {patient.dateOfBirth}</div>
                    </div>
                    <div style={actionButtonsStyle}>
                      <button 
                        style={approveButtonStyle}
                        onClick={() => handleApprove(patient.id, 'patient')}
                        onMouseOver={(e) => e.target.style.backgroundColor = '#059669'}
                        onMouseOut={(e) => e.target.style.backgroundColor = '#10B981'}
                      >
                        Approve
                      </button>
                      <button 
                        style={rejectButtonStyle}
                        onClick={() => handleReject(patient.id, 'patient')}
                        onMouseOver={(e) => e.target.style.backgroundColor = '#DC2626'}
                        onMouseOut={(e) => e.target.style.backgroundColor = '#EF4444'}
                      >
                        Reject
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div style={emptyStateStyle}>
                No pending patient approvals
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminDashboard;
