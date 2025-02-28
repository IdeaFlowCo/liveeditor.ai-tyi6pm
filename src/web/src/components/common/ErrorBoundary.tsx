import React, { Component, ErrorInfo, ReactNode, useCallback } from 'react'; // React v18.2.0
import { Button } from '../common/Button';

/**
 * Props for the ErrorBoundary component
 */
interface ErrorBoundaryProps {
  /** Optional name for identifying this boundary in logs */
  name?: string;
  /** Optional custom fallback UI to display when an error occurs */
  fallback?: React.ReactNode | ((error: Error, reset: () => void) => React.ReactNode);
  /** Optional callback function that's called when an error is caught */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  /** Optional flag to disable error type detection */
  disableErrorTypeDetection?: boolean;
  /** Optional custom error message to display */
  errorMessage?: string;
  /** Flag to determine if error state should reset when props change */
  resetOnPropsChange?: boolean;
  /** Optional prop to compare for resetting error state */
  resetOnPropChange?: string;
  /** Children to be rendered when no error has occurred */
  children: ReactNode;
}

/**
 * State for the ErrorBoundary component
 */
interface ErrorBoundaryState {
  /** Whether an error has been caught */
  hasError: boolean;
  /** The error that was caught */
  error: Error | null;
  /** The type of error that occurred */
  errorType: 'network' | 'ai-service' | 'timeout' | 'auth' | 'validation' | 'general' | null;
}

/**
 * A React Error Boundary component that catches JavaScript errors in child components,
 * logs them, and displays a fallback UI instead of crashing the application.
 * 
 * Particularly important for the AI writing enhancement interface to prevent errors
 * in AI processing from breaking the entire document editing experience.
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorType: null
    };
  }

  /**
   * Static method called when an error is thrown in a descendant component.
   * Used to update the component state with error information.
   */
  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Determine the error type based on error message
    let errorType: 'network' | 'ai-service' | 'timeout' | 'auth' | 'validation' | 'general' = 'general';
    
    const errorMessage = error.message || '';
    
    // Check for network errors
    if (
      errorMessage.includes('network') ||
      errorMessage.includes('internet') ||
      errorMessage.includes('offline') ||
      errorMessage.includes('connection') ||
      errorMessage.includes('ECONNABORTED') ||
      errorMessage.includes('networkError')
    ) {
      errorType = 'network';
    }
    // Check for timeout errors
    else if (
      errorMessage.includes('timeout') ||
      errorMessage.includes('timed out') ||
      errorMessage.includes('ETIMEDOUT')
    ) {
      errorType = 'timeout';
    }
    // Check for authentication errors
    else if (
      errorMessage.includes('auth') ||
      errorMessage.includes('login') ||
      errorMessage.includes('permission') ||
      errorMessage.includes('unauthorized') ||
      errorMessage.includes('Unauthorized') ||
      errorMessage.includes('forbidden') ||
      errorMessage.includes('Forbidden')
    ) {
      errorType = 'auth';
    }
    // Check for validation errors
    else if (
      errorMessage.includes('validation') ||
      errorMessage.includes('invalid') ||
      errorMessage.includes('required') ||
      errorMessage.includes('must be')
    ) {
      errorType = 'validation';
    }
    // Check for AI service errors
    else if (
      errorMessage.includes('AI') ||
      errorMessage.includes('suggestion') ||
      errorMessage.includes('model') ||
      errorMessage.includes('OpenAI') ||
      errorMessage.includes('language model') ||
      errorMessage.includes('circuit breaker') ||
      error instanceof Error && error.name === 'CircuitBreakerOpenError'
    ) {
      errorType = 'ai-service';
    }
    
    // Return new state with error information
    return {
      hasError: true,
      error,
      errorType
    };
  }

  /**
   * Lifecycle method called after an error has been caught.
   * Used for logging errors and reporting to error monitoring services.
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log the error to the console
    console.error(
      `Error caught by ErrorBoundary${this.props.name ? ` (${this.props.name})` : ''}:`,
      error,
      errorInfo
    );
    
    // Call the custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  /**
   * Lifecycle method called after component updates.
   * Used to reset error state when specified props change.
   */
  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    // Reset error state if resetOnPropsChange is enabled and props have changed
    if (this.props.resetOnPropsChange && this.state.hasError) {
      if (this.props !== prevProps) {
        this.reset();
      }
    }
    
    // Reset error state if resetOnPropChange is specified and that prop has changed
    if (
      this.props.resetOnPropChange &&
      this.state.hasError &&
      prevProps[this.props.resetOnPropChange as keyof ErrorBoundaryProps] !== 
      this.props[this.props.resetOnPropChange as keyof ErrorBoundaryProps]
    ) {
      this.reset();
    }
  }

  /**
   * Resets the error state allowing the component to attempt to render its children again.
   */
  reset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorType: null
    });
  };

  /**
   * Determines the appropriate error message to display based on the error type.
   */
  getErrorMessage = (): string => {
    // Return custom error message if provided
    if (this.props.errorMessage) {
      return this.props.errorMessage;
    }
    
    // Return general message if error type detection is disabled
    if (this.props.disableErrorTypeDetection) {
      return 'An unexpected error occurred. Please try again later.';
    }
    
    // Return specific message based on error type
    switch (this.state.errorType) {
      case 'network':
        return 'Unable to connect to the server. Please check your internet connection and try again.';
      case 'timeout':
        return 'The request took too long to complete. Please try again later.';
      case 'auth':
        return 'You need to be logged in to perform this action. Please log in and try again.';
      case 'validation':
        return 'Please check your input and try again.';
      case 'ai-service':
        return 'AI service is temporarily unavailable. Please try again later or try a different approach.';
      default:
        return this.state.error?.message || 'An unexpected error occurred. Please try again.';
    }
  };

  /**
   * Renders either the fallback UI or children based on error state.
   */
  render(): ReactNode {
    const { hasError, error } = this.state;
    const { fallback, children } = this.props;
    
    if (hasError && error) {
      // Use custom fallback if provided
      if (fallback) {
        if (typeof fallback === 'function') {
          return fallback(error, this.reset);
        }
        return fallback;
      }
      
      // Default error UI
      return (
        <div className="error-boundary-fallback p-6 m-4 rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="error-boundary-content flex flex-col items-center text-center">
            <svg 
              className="h-12 w-12 text-[#DC3545] mb-4" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor" 
              aria-hidden="true"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
              />
            </svg>
            <h2 className="text-lg font-semibold mb-2">Something went wrong</h2>
            <p className="text-gray-600 mb-4">{this.getErrorMessage()}</p>
            <Button 
              onClick={this.reset} 
              variant="primary"
            >
              Try Again
            </Button>
          </div>
        </div>
      );
    }
    
    // If no error, render children normally
    return children;
  }
}

/**
 * A hook that creates an error boundary wrapper for easier usage in functional components.
 * 
 * @param options - Configuration options for the error boundary
 * @returns A function that wraps content in an error boundary
 * 
 * @example
 * const errorBoundary = useErrorBoundary();
 * return errorBoundary(
 *   <MyComponent />
 * );
 */
export const useErrorBoundary = (options: Omit<ErrorBoundaryProps, 'children'> = {}) => {
  const wrapWithErrorBoundary = useCallback(
    (children: ReactNode) => (
      <ErrorBoundary {...options}>
        {children}
      </ErrorBoundary>
    ),
    [options]
  );
  
  return wrapWithErrorBoundary;
};

export default ErrorBoundary;