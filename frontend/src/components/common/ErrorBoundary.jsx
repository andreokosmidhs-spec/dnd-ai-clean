import React from 'react';

/**
 * Error Boundary Component
 * Catches runtime errors in React component tree
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          padding: '2rem',
          textAlign: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        }}>
          <div style={{
            background: 'rgba(0,0,0,0.8)',
            padding: '2rem',
            borderRadius: '12px',
            maxWidth: '500px'
          }}>
            <h1 style={{ color: '#fff', fontSize: '24px', marginBottom: '1rem' }}>
              ⚠️ Something went wrong
            </h1>
            <p style={{ color: '#ccc', marginBottom: '1.5rem' }}>
              The application encountered an unexpected error.
            </p>
            <button
              onClick={this.handleReload}
              style={{
                background: '#667eea',
                color: '#fff',
                border: 'none',
                padding: '0.75rem 1.5rem',
                borderRadius: '8px',
                fontSize: '16px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
