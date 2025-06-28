import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ErrorBoundaryState } from '../types';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

class ErrorBoundary extends Component<Props, ErrorBoundaryState> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error Boundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo: {
        componentStack: errorInfo.componentStack || ''
      }
    });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="error-boundary">
          <div className="error-container">
            <h2>🚨 Something went wrong</h2>
            <details className="error-details">
              <summary>Error Details</summary>
              <div className="error-message">
                <strong>Error:</strong> {this.state.error?.message || 'Unknown error'}
              </div>
              {this.state.error?.stack && (
                <div className="error-stack">
                  <strong>Stack Trace:</strong>
                  <pre>{this.state.error.stack}</pre>
                </div>
              )}
              {this.state.errorInfo?.componentStack && (
                <div className="error-component-stack">
                  <strong>Component Stack:</strong>
                  <pre>{this.state.errorInfo.componentStack}</pre>
                </div>
              )}
            </details>
            <div className="error-actions">
              <button onClick={this.handleRetry} className="retry-button">
                Try Again
              </button>
              <button 
                onClick={() => window.location.reload()} 
                className="reload-button"
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;