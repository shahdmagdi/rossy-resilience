import React from 'react';

const Input = ({ 
  label, 
  type = 'text', 
  value, 
  onChange, 
  placeholder, 
  error, 
  required = false,
  name,
  ...props 
}) => {
  const containerStyle = {
    marginBottom: '16px',
  };

  const labelStyle = {
    display: 'block',
    marginBottom: '6px',
    fontSize: '14px',
    fontWeight: '500',
    color: '#831843',
  };

  const inputStyle = {
    width: '100%',
    padding: '12px 16px',
    fontSize: '16px',
    border: error ? '2px solid #DB2777' : '2px solid #F9A8D4',
    borderRadius: '8px',
    outline: 'none',
    transition: 'border-color 0.3s ease, box-shadow 0.3s ease',
    boxSizing: 'border-box',
  };

  const errorStyle = {
    color: '#DB2777',
    fontSize: '12px',
    marginTop: '4px',
  };

  const handleFocus = (e) => {
    e.target.style.borderColor = '#DB2777';
    e.target.style.boxShadow = '0 0 0 3px rgba(219, 39, 119, 0.1)';
  };

  const handleBlur = (e) => {
    if (!error) {
      e.target.style.borderColor = '#F9A8D4';
      e.target.style.boxShadow = 'none';
    }
  };

  return (
    <div style={containerStyle}>
      {label && (
        <label style={labelStyle}>
          {label}
          {required && <span style={{ color: '#DB2777' }}> *</span>}
        </label>
      )}
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        style={inputStyle}
        onFocus={handleFocus}
        onBlur={handleBlur}
        {...props}
      />
      {error && <div style={errorStyle}>{error}</div>}
    </div>
  );
};

export default Input;
