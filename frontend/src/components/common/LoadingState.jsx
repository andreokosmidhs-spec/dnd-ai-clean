import React from 'react';

/**
 * Loading State Component
 * Shows a spinner during async operations
 */
const LoadingState = ({ message = 'Loading...' }) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      minHeight: '200px'
    }}>
      <div style={{
        width: '40px',
        height: '40px',
        border: '4px solid rgba(255,255,255,0.1)',
        borderTopColor: '#667eea',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite'
      }} />
      <p style={{ marginTop: '1rem', color: '#888', fontSize: '14px' }}>
        {message}
      </p>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default LoadingState;
