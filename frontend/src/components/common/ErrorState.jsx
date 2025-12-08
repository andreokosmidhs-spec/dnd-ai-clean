import React from 'react';

/**
 * Error State Component
 * Shows error message with optional retry
 */
const ErrorState = ({ message = 'Something went wrong', onRetry }) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      minHeight: '200px',
      textAlign: 'center'
    }}>
      <div style={{
        fontSize: '48px',
        marginBottom: '1rem'
      }}>
        ⚠️
      </div>
      <h3 style={{ color: '#e74c3c', marginBottom: '0.5rem', fontSize: '18px' }}>
        Error
      </h3>
      <p style={{ color: '#888', marginBottom: '1.5rem', fontSize: '14px', maxWidth: '400px' }}>
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            background: '#667eea',
            color: '#fff',
            border: 'none',
            padding: '0.5rem 1.5rem',
            borderRadius: '6px',
            fontSize: '14px',
            cursor: 'pointer',
            fontWeight: '600'
          }}
        >
          Try Again
        </button>
      )}
    </div>
  );
};

export default ErrorState;
