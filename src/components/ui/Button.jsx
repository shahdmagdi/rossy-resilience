import React from 'react';

const Button = ({ 
  children, 
  onClick, 
  type = 'button', 
  variant = 'primary', 
  disabled = false,
  className = '',
  ...props 
}) => {
  const baseStyles = {
    padding: '12px 24px',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'all 0.3s ease',
    border: 'none',
    outline: 'none',
    opacity: disabled ? 0.6 : 1,
  };

  const variants = {
    primary: {
      backgroundColor: '#DB2777',
      color: '#ffffff',
    },
    secondary: {
      backgroundColor: '#9D174D',
      color: '#ffffff',
    },
    outline: {
      backgroundColor: 'transparent',
      color: '#DB2777',
      border: '2px solid #DB2777',
    },
    danger: {
      backgroundColor: '#BE185D',
      color: '#ffffff',
    },
  };

  const buttonStyle = {
    ...baseStyles,
    ...variants[variant],
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      style={buttonStyle}
      className={className}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
