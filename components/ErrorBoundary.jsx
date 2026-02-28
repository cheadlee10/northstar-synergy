/**
 * Error Boundary Component
 * Catches React component errors and WebSocket failures
 * Provides fallback UI and recovery options
 */

import React, { Component } from 'react';
import PropTypes from 'prop-types';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
      isWebSocketError: false,
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    const { onError, logErrors } = this.props;

    // Detect WebSocket errors
    const isWebSocketError =
      error?.message?.includes('WebSocket') ||
      error?.message?.includes('Socket') ||
      error?.message?.includes('Connection');

    const newErrorCount = this.state.errorCount + 1;

    this.setState({
      error,
      errorInfo,
      errorCount: newErrorCount,
      isWebSocketError,
    });

    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('[ErrorBoundary] Error caught:', error);
      console.error('[ErrorBoundary] Error info:', errorInfo);
    }

    // Call custom error handler
    if (onError) {
      onError(error, errorInfo, { isWebSocketError });
    }

    // Log to external service in production
    if (logErrors && process.env.NODE_ENV === 'production') {
      this.logErrorToService(error, errorInfo);
    }

    // Auto-reset after 30 seconds if error count is low
    if (newErrorCount < 3) {
      setTimeout(() => {
        this.resetError();
      }, 30000);
    }
  }

  resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  logErrorToService = async (error, errorInfo) => {
    try {
      // Send to error tracking service (Sentry, LogRocket, etc.)
      const errorPayload = {
        message: error?.toString(),
        stack: error?.stack,
        componentStack: errorInfo?.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
      };

      // Placeholder for actual error service integration
      console.log('[ErrorBoundary] Error logged to service:', errorPayload);
    } catch (err) {
      console.error('[ErrorBoundary] Failed to log error:', err);
    }
  };

  render() {
    const { hasError, error, errorInfo, errorCount, isWebSocketError } = this.state;
    const { children, fallback, showDetails } = this.props;

    if (hasError) {
      // Custom fallback provided
      if (fallback && typeof fallback === 'function') {
        return fallback(error, errorInfo, this.resetError);
      }

      // Default error UI
      return (
        <div
          className="error-boundary-container"
          style={styles.container}
          role="alert"
          aria-live="assertive"
        >
          <div style={styles.content}>
            {isWebSocketError ? (
              <WebSocketErrorUI error={error} onRetry={this.resetError} />
            ) : (
              <ComponentErrorUI
                error={error}
                errorInfo={errorInfo}
                showDetails={showDetails}
                onRetry={this.resetError}
                errorCount={errorCount}
              />
            )}
          </div>
        </div>
      );
    }

    return children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  fallback: PropTypes.func,
  onError: PropTypes.func,
  logErrors: PropTypes.bool,
  showDetails: PropTypes.bool,
};

ErrorBoundary.defaultProps = {
  fallback: null,
  onError: null,
  logErrors: false,
  showDetails: process.env.NODE_ENV === 'development',
};

/**
 * WebSocket Connection Error UI
 */
const WebSocketErrorUI = ({ error, onRetry }) => (
  <div style={styles.errorBox}>
    <div style={styles.iconContainer}>
      <div style={styles.warningIcon}>⚠️</div>
    </div>
    <h2 style={styles.title}>Connection Lost</h2>
    <p style={styles.message}>
      Unable to connect to the server. This usually means:
    </p>
    <ul style={styles.list}>
      <li>The server is temporarily unavailable</li>
      <li>Your internet connection was interrupted</li>
      <li>A network firewall is blocking the connection</li>
    </ul>
    <p style={styles.subMessage}>
      The app will automatically attempt to reconnect. You can retry manually below.
    </p>
    <div style={styles.errorDetails}>
      <code style={styles.code}>{error?.message || 'Unknown connection error'}</code>
    </div>
    <div style={styles.buttonGroup}>
      <button onClick={onRetry} style={styles.primaryButton}>
        Try Again
      </button>
    </div>
  </div>
);

/**
 * Component Error UI
 */
const ComponentErrorUI = ({
  error,
  errorInfo,
  showDetails,
  onRetry,
  errorCount,
}) => (
  <div style={styles.errorBox}>
    <div style={styles.iconContainer}>
      <div style={styles.errorIcon}>❌</div>
    </div>
    <h2 style={styles.title}>Something went wrong</h2>
    <p style={styles.message}>
      The application encountered an unexpected error and couldn't recover automatically.
    </p>

    {errorCount >= 3 && (
      <div style={styles.warningMessage}>
        <strong>⚠️ Multiple errors detected:</strong> The app has encountered {errorCount}{' '}
        errors. Please consider refreshing the page.
      </div>
    )}

    {showDetails && error && (
      <details style={styles.details}>
        <summary style={styles.summary}>Error Details</summary>
        <div style={styles.errorDetails}>
          <h4>Error Message:</h4>
          <code style={styles.code}>{error.toString()}</code>
          {error.stack && (
            <>
              <h4>Stack Trace:</h4>
              <code style={styles.code}>{error.stack}</code>
            </>
          )}
          {errorInfo?.componentStack && (
            <>
              <h4>Component Stack:</h4>
              <code style={styles.code}>{errorInfo.componentStack}</code>
            </>
          )}
        </div>
      </details>
    )}

    <div style={styles.buttonGroup}>
      <button onClick={onRetry} style={styles.primaryButton}>
        Try Again
      </button>
      <button
        onClick={() => window.location.reload()}
        style={styles.secondaryButton}
      >
        Refresh Page
      </button>
    </div>
  </div>
);

/**
 * Styles
 */
const styles = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    padding: '20px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif',
  },
  content: {
    width: '100%',
    maxWidth: '500px',
  },
  errorBox: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '40px 30px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    textAlign: 'center',
  },
  iconContainer: {
    marginBottom: '20px',
  },
  errorIcon: {
    fontSize: '48px',
    lineHeight: '1',
  },
  warningIcon: {
    fontSize: '48px',
    lineHeight: '1',
  },
  title: {
    margin: '20px 0 10px 0',
    fontSize: '24px',
    fontWeight: '600',
    color: '#333',
  },
  message: {
    margin: '15px 0',
    fontSize: '14px',
    color: '#666',
    lineHeight: '1.5',
  },
  subMessage: {
    margin: '15px 0',
    fontSize: '13px',
    color: '#888',
    fontStyle: 'italic',
  },
  list: {
    textAlign: 'left',
    margin: '15px 0 20px 20px',
    fontSize: '13px',
    color: '#666',
    lineHeight: '1.8',
  },
  details: {
    marginTop: '20px',
    textAlign: 'left',
    cursor: 'pointer',
  },
  summary: {
    padding: '10px',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: '600',
    color: '#666',
  },
  errorDetails: {
    marginTop: '15px',
    padding: '15px',
    backgroundColor: '#f5f5f5',
    borderRadius: '4px',
    textAlign: 'left',
    maxHeight: '300px',
    overflowY: 'auto',
    fontSize: '11px',
  },
  code: {
    display: 'block',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    color: '#c7254e',
    fontFamily: '"Courier New", monospace',
    lineHeight: '1.4',
  },
  warningMessage: {
    margin: '20px 0',
    padding: '12px',
    backgroundColor: '#fff3cd',
    border: '1px solid #ffc107',
    borderRadius: '4px',
    fontSize: '13px',
    color: '#856404',
  },
  buttonGroup: {
    display: 'flex',
    gap: '10px',
    justifyContent: 'center',
    marginTop: '25px',
  },
  primaryButton: {
    padding: '10px 24px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  secondaryButton: {
    padding: '10px 24px',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
};

export default ErrorBoundary;
