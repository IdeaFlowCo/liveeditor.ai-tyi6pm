/**
 * Comprehensive error handling utility for AI writing enhancement application
 * 
 * Provides standardized error processing, categorization, reporting, and recovery
 * strategies to improve application resilience and user experience during failures.
 * 
 * @module error-handling
 * @version 1.0.0
 */

import { ApiError, handleApiError } from './api';
import analytics, { trackEvent } from '../lib/analytics';
import { EVENT_CATEGORY } from '../lib/analytics';
import { ERROR_MESSAGES, HTTP_STATUS, MAX_RETRY_ATTEMPTS, RETRY_DELAY } from '../constants/common';
import { isAxiosError } from 'axios'; // ^1.4.0

// Circuit breaker configuration
const CIRCUIT_BREAKER_THRESHOLD = 3;
const CIRCUIT_BREAKER_RESET_TIMEOUT = 30000; // 30 seconds

// Default values
const DEFAULT_ERROR_MESSAGE = 'An unexpected error occurred. Please try again later.';
const DEFAULT_NOTIFICATION_DURATION = 5000; // 5 seconds

// Global notification callback
let notificationCallback: ((message: string, type: NotificationType, duration: number) => void) | null = null;

/**
 * Enum defining the possible error types for categorization
 */
export enum ErrorTypes {
  NETWORK = 'NETWORK',
  TIMEOUT = 'TIMEOUT',
  API = 'API',
  AUTH = 'AUTH',
  VALIDATION = 'VALIDATION',
  AI_SERVICE = 'AI_SERVICE',
  UNKNOWN = 'UNKNOWN'
}

/**
 * Enum representing possible states of the circuit breaker
 */
export enum CircuitBreakerState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN'
}

/**
 * Enum defining the types of notifications
 */
export enum NotificationType {
  SUCCESS = 'SUCCESS',
  ERROR = 'ERROR',
  WARNING = 'WARNING',
  INFO = 'INFO'
}

/**
 * Error thrown when an operation is attempted while the circuit is open
 */
export class CircuitBreakerOpenError extends Error {
  serviceName: string;

  /**
   * Creates a new circuit breaker open error
   * 
   * @param serviceName - Name of the service with an open circuit
   */
  constructor(serviceName: string) {
    super(`Circuit breaker for ${serviceName} is open. Requests are temporarily suspended.`);
    this.name = 'CircuitBreakerOpenError';
    this.serviceName = serviceName;
    
    // Fix prototype chain for proper instanceof checks
    Object.setPrototypeOf(this, CircuitBreakerOpenError.prototype);
  }
}

/**
 * Implements the circuit breaker pattern to prevent cascading failures for external service calls
 */
export class CircuitBreaker {
  private serviceName: string;
  private state: CircuitBreakerState;
  private failureCount: number;
  private threshold: number;
  private resetTimeout: number;
  private lastFailureTime: number;

  /**
   * Creates a new circuit breaker instance for a specific service
   * 
   * @param serviceName - Name of the service being protected
   * @param options - Optional configuration options
   */
  constructor(
    serviceName: string,
    options: { threshold?: number; resetTimeout?: number } = {}
  ) {
    this.serviceName = serviceName;
    this.state = CircuitBreakerState.CLOSED;
    this.failureCount = 0;
    this.threshold = options.threshold || CIRCUIT_BREAKER_THRESHOLD;
    this.resetTimeout = options.resetTimeout || CIRCUIT_BREAKER_RESET_TIMEOUT;
    this.lastFailureTime = 0;
  }

  /**
   * Executes an operation with circuit breaker protection
   * 
   * @param operation - The operation to execute
   * @param fallback - Optional fallback function if circuit is open
   * @returns Promise resolving to operation result or fallback result
   */
  async execute<T>(
    operation: () => Promise<T>,
    fallback?: () => Promise<T>
  ): Promise<T> {
    // Check if circuit is open
    if (this.state === CircuitBreakerState.OPEN) {
      const now = Date.now();
      const timeElapsedSinceLastFailure = now - this.lastFailureTime;

      // Check if the reset timeout has elapsed
      if (timeElapsedSinceLastFailure >= this.resetTimeout) {
        // Transition to half-open state to test if the service has recovered
        this.state = CircuitBreakerState.HALF_OPEN;
      } else {
        // Circuit is still open
        if (fallback) {
          return fallback();
        }
        throw new CircuitBreakerOpenError(this.serviceName);
      }
    }

    try {
      // Execute the operation
      const result = await operation();
      
      // If the operation was successful, record success
      this.recordSuccess();
      
      return result;
    } catch (error) {
      // Record the failure and update circuit state
      this.recordFailure(error as Error);
      
      // If fallback provided, execute it
      if (fallback) {
        return fallback();
      }
      
      // Re-throw the original error
      throw error;
    }
  }

  /**
   * Records a successful operation and resets failure count
   */
  recordSuccess(): void {
    this.failureCount = 0;
    
    // If in half-open state, transition to closed
    if (this.state === CircuitBreakerState.HALF_OPEN) {
      this.state = CircuitBreakerState.CLOSED;
      
      // Track the circuit state change in analytics
      trackEvent(EVENT_CATEGORY.PERFORMANCE, 'circuit_breaker_closed', {
        serviceName: this.serviceName
      });
    }
  }

  /**
   * Records a failed operation and updates circuit state if needed
   * 
   * @param error - The error that occurred
   */
  recordFailure(error: Error): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    
    // If in half-open state, immediately transition to open
    if (this.state === CircuitBreakerState.HALF_OPEN) {
      this.state = CircuitBreakerState.OPEN;
    } else if (this.state === CircuitBreakerState.CLOSED && this.failureCount >= this.threshold) {
      // If threshold exceeded, transition to open
      this.state = CircuitBreakerState.OPEN;
      
      // Log circuit breaker trip
      console.warn(`Circuit breaker for ${this.serviceName} tripped after ${this.failureCount} failures`);
    }
    
    // Track the circuit state change in analytics if state changed to open
    if (this.state === CircuitBreakerState.OPEN) {
      trackEvent(EVENT_CATEGORY.PERFORMANCE, 'circuit_breaker_open', {
        serviceName: this.serviceName,
        error: error.message,
        failureCount: this.failureCount
      });
    }
  }

  /**
   * Manually resets the circuit breaker to closed state
   */
  reset(): void {
    this.failureCount = 0;
    this.state = CircuitBreakerState.CLOSED;
    
    // Track circuit reset in analytics
    trackEvent(EVENT_CATEGORY.PERFORMANCE, 'circuit_breaker_reset', {
      serviceName: this.serviceName
    });
  }

  /**
   * Gets the current state of the circuit breaker
   * 
   * @returns Current circuit breaker state
   */
  getState(): CircuitBreakerState {
    return this.state;
  }
}

/**
 * Sets a callback function that will be used to display notifications
 * 
 * @param callback - Function that displays notifications
 */
export function setNotificationCallback(
  callback: (message: string, type: NotificationType, duration: number) => void
): void {
  notificationCallback = callback;
}

/**
 * Primary error handling function that processes, logs, and displays errors appropriately
 * 
 * @param error - The error to handle
 * @param options - Additional options for error handling
 * @returns Processed error with additional context
 */
export function handleError(
  error: Error,
  options: {
    showNotification?: boolean;
    logError?: boolean;
    context?: Record<string, any>;
    customMessage?: string;
  } = {}
): Error {
  // Set default options
  const opts = {
    showNotification: true,
    logError: true,
    context: {},
    customMessage: '',
    ...options
  };

  // Handle API errors
  if (error instanceof ApiError) {
    // ApiError is already processed
  } else if (isAxiosError(error)) {
    // Process Axios errors through the API error handler
    error = handleApiError(error);
  }

  // Categorize error type
  const errorType = categorizeError(error);

  // Log error if enabled
  if (opts.logError) {
    logError(error, errorType, opts.context);
  }

  // Show notification if enabled
  if (opts.showNotification) {
    displayErrorNotification(error, opts.customMessage);
  }

  // Report error to analytics if it's not a user input error
  if (errorType !== ErrorTypes.VALIDATION) {
    trackEvent(EVENT_CATEGORY.PERFORMANCE, 'error_occurred', {
      errorType,
      message: error.message,
      name: error.name,
      ...opts.context
    });
  }

  // Return the processed error for further handling
  return error;
}

/**
 * Identifies error type and category for appropriate handling
 * 
 * @param error - The error to categorize
 * @returns Categorized error type
 */
export function categorizeError(error: Error): ErrorTypes {
  // Check for API error
  if (error instanceof ApiError) {
    // Check for specific API error types
    if (error.status === HTTP_STATUS.UNAUTHORIZED || error.status === HTTP_STATUS.FORBIDDEN) {
      return ErrorTypes.AUTH;
    }
    
    if (error.status === HTTP_STATUS.BAD_REQUEST) {
      return ErrorTypes.VALIDATION;
    }
    
    if (error.details?.networkError) {
      return ErrorTypes.NETWORK;
    }
    
    if (error.details?.timeout) {
      return ErrorTypes.TIMEOUT;
    }
    
    return ErrorTypes.API;
  }
  
  // Check for circuit breaker error
  if (error instanceof CircuitBreakerOpenError) {
    return ErrorTypes.AI_SERVICE;
  }
  
  // Check for network error
  if (
    error.message?.includes('network') || 
    error.message?.includes('internet') || 
    error.message?.includes('offline')
  ) {
    return ErrorTypes.NETWORK;
  }
  
  // Check for timeout error
  if (
    error.message?.includes('timeout') ||
    error.message?.includes('timed out')
  ) {
    return ErrorTypes.TIMEOUT;
  }
  
  // Check for authentication error
  if (
    error.message?.includes('auth') ||
    error.message?.includes('login') ||
    error.message?.includes('permission') ||
    error.message?.includes('unauthorized')
  ) {
    return ErrorTypes.AUTH;
  }
  
  // Check for AI service error
  if (
    error.message?.includes('AI') ||
    error.message?.includes('suggestion') ||
    error.message?.includes('model')
  ) {
    return ErrorTypes.AI_SERVICE;
  }
  
  // Default to unknown
  return ErrorTypes.UNKNOWN;
}

/**
 * Retrieves a user-friendly error message based on the error type and details
 * 
 * @param error - The error object
 * @param errorType - Categorized error type
 * @returns User-friendly error message
 */
export function getErrorMessage(error: Error, errorType: ErrorTypes): string {
  // Use error message if available
  if (error.message && error.message !== 'Error') {
    return error.message;
  }
  
  // Use predefined error messages based on type
  switch (errorType) {
    case ErrorTypes.NETWORK:
      return ERROR_MESSAGES.NETWORK;
    
    case ErrorTypes.TIMEOUT:
      return 'Request timed out. Please try again later.';
    
    case ErrorTypes.AUTH:
      return ERROR_MESSAGES.UNAUTHORIZED;
    
    case ErrorTypes.VALIDATION:
      // For validation errors, we should have more specific messages
      if (error instanceof ApiError && error.details) {
        return error.message;
      }
      return 'Please check your input and try again.';
    
    case ErrorTypes.AI_SERVICE:
      return ERROR_MESSAGES.AI_SERVICE_UNAVAILABLE;
    
    case ErrorTypes.API:
      if (error instanceof ApiError) {
        return error.message;
      }
      return 'An error occurred while communicating with the server.';
    
    case ErrorTypes.UNKNOWN:
    default:
      return DEFAULT_ERROR_MESSAGE;
  }
}

/**
 * Implements exponential backoff retry logic for failed operations
 * 
 * @param operation - Function to execute with retry logic
 * @param options - Configuration options
 * @returns Promise resolving to the operation result
 */
export async function retryWithBackoff<T>(
  operation: () => Promise<T>,
  options: {
    maxAttempts?: number;
    initialDelay?: number;
    maxDelay?: number;
    factor?: number;
    retryCondition?: (error: Error) => boolean;
    onRetry?: (error: Error, attempt: number, delay: number) => void;
  } = {}
): Promise<T> {
  // Set up retry parameters
  const maxAttempts = options.maxAttempts || MAX_RETRY_ATTEMPTS;
  const initialDelay = options.initialDelay || RETRY_DELAY;
  const maxDelay = options.maxDelay || 30000; // 30 seconds max delay
  const factor = options.factor || 2; // Exponential factor
  const retryCondition = options.retryCondition || isRetryableError;
  const onRetry = options.onRetry;
  
  let attempts = 0;
  
  // Create recursive retry function
  const retry = async (): Promise<T> => {
    try {
      // Attempt the operation
      return await operation();
    } catch (error) {
      attempts++;
      
      // Check if we should retry
      if (attempts < maxAttempts && retryCondition(error as Error)) {
        // Calculate backoff delay with jitter
        const delay = Math.min(
          initialDelay * Math.pow(factor, attempts - 1) + Math.random() * 100,
          maxDelay
        );
        
        // Call onRetry callback if provided
        if (onRetry) {
          onRetry(error as Error, attempts, delay);
        }
        
        // Wait for the calculated delay
        await new Promise(resolve => setTimeout(resolve, delay));
        
        // Retry the operation
        return retry();
      }
      
      // If we've hit max attempts or the error isn't retryable, rethrow
      throw error;
    }
  };
  
  // Start the retry process
  return retry();
}

/**
 * Determines if an error should trigger a retry attempt
 * 
 * @param error - The error to evaluate
 * @returns Whether the error is retryable
 */
export function isRetryableError(error: Error): boolean {
  // Network connectivity errors are retryable
  if (categorizeError(error) === ErrorTypes.NETWORK) {
    return true;
  }
  
  // Timeout errors are retryable
  if (categorizeError(error) === ErrorTypes.TIMEOUT) {
    return true;
  }
  
  // API errors with specific status codes
  if (error instanceof ApiError) {
    // Server errors (5xx) are retryable
    if (error.status >= 500 && error.status < 600) {
      return true;
    }
    
    // Rate limiting (429) is retryable
    if (error.status === HTTP_STATUS.TOO_MANY_REQUESTS) {
      return true;
    }
    
    // Client errors are generally not retryable (except those above)
    if (error.status >= 400 && error.status < 500) {
      return false;
    }
  }
  
  // Default to not retryable for unknown errors
  return false;
}

/**
 * Shows a user-friendly error notification
 * 
 * @param error - The error object
 * @param customMessage - Optional custom message to display
 */
export function displayErrorNotification(error: Error, customMessage?: string): void {
  const errorType = categorizeError(error);
  const message = customMessage || getErrorMessage(error, errorType);
  
  // Determine notification duration based on error type
  let duration = DEFAULT_NOTIFICATION_DURATION;
  if (errorType === ErrorTypes.AUTH) {
    duration = 8000; // Authentication errors need more time to read
  } else if (errorType === ErrorTypes.NETWORK) {
    duration = 0; // Network errors should persist until connectivity is restored
  }
  
  // Show the notification
  showNotification(message, NotificationType.ERROR, duration);
  
  // Track error notification event
  trackEvent(EVENT_CATEGORY.UI, 'error_notification_shown', {
    errorType,
    message
  });
}

/**
 * Creates and displays a notification using the registered callback or DOM-based fallback
 * 
 * @param message - Notification message
 * @param type - Notification type (success, error, etc.)
 * @param duration - How long the notification should be displayed (0 for no auto-dismiss)
 */
export function showNotification(
  message: string,
  type: NotificationType = NotificationType.INFO,
  duration: number = DEFAULT_NOTIFICATION_DURATION
): void {
  // Use registered callback if available
  if (notificationCallback) {
    notificationCallback(message, type, duration);
    return;
  }
  
  // Fallback to DOM-based notification if no callback registered
  // This allows the utility to work without requiring specific UI framework
  
  // Create notification element
  const notification = document.createElement('div');
  
  // Apply base styles
  Object.assign(notification.style, {
    position: 'fixed',
    top: '20px',
    right: '20px',
    padding: '12px 20px',
    borderRadius: '4px',
    boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
    zIndex: '9999',
    maxWidth: '300px',
    animation: 'fade-in 0.3s ease-out forwards',
    fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontSize: '14px'
  });
  
  // Apply type-specific styles
  switch (type) {
    case NotificationType.SUCCESS:
      Object.assign(notification.style, {
        backgroundColor: '#28A745',
        color: 'white'
      });
      break;
    
    case NotificationType.ERROR:
      Object.assign(notification.style, {
        backgroundColor: '#DC3545',
        color: 'white'
      });
      break;
    
    case NotificationType.WARNING:
      Object.assign(notification.style, {
        backgroundColor: '#FFC107',
        color: 'black'
      });
      break;
    
    case NotificationType.INFO:
    default:
      Object.assign(notification.style, {
        backgroundColor: '#2C6ECB',
        color: 'white'
      });
      break;
  }
  
  // Set content
  notification.textContent = message;
  
  // Add to DOM
  document.body.appendChild(notification);
  
  // Set auto-dismiss timer if duration > 0
  if (duration > 0) {
    setTimeout(() => {
      notification.style.animation = 'fade-out 0.3s ease-in forwards';
      setTimeout(() => {
        notification.remove();
      }, 300);
    }, duration);
  }
  
  // Allow click to dismiss
  notification.addEventListener('click', () => {
    notification.style.animation = 'fade-out 0.3s ease-in forwards';
    setTimeout(() => {
      notification.remove();
    }, 300);
  });
  
  // Add animation styles to document if they don't exist
  if (!document.getElementById('notification-animations')) {
    const style = document.createElement('style');
    style.id = 'notification-animations';
    style.textContent = `
      @keyframes fade-in {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
      }
      @keyframes fade-out {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(-20px); }
      }
    `;
    document.head.appendChild(style);
  }
}

/**
 * Logs error details to appropriate channels based on environment and severity
 * 
 * @param error - The error object
 * @param errorType - Categorized error type
 * @param context - Additional context information
 */
export function logError(
  error: Error,
  errorType: ErrorTypes,
  context: Record<string, any> = {}
): void {
  // Create error details object with timestamp
  const errorDetails = {
    timestamp: new Date().toISOString(),
    name: error.name,
    message: error.message,
    type: errorType,
    stack: error.stack,
    ...context
  };
  
  // Remove sensitive information before logging
  const sanitizedDetails = { ...errorDetails };
  ['password', 'token', 'auth', 'key', 'secret'].forEach(term => {
    Object.keys(sanitizedDetails).forEach(key => {
      if (typeof sanitizedDetails[key] === 'string' && key.toLowerCase().includes(term)) {
        sanitizedDetails[key] = '[REDACTED]';
      }
    });
  });
  
  // Log to console in development
  if (process.env.NODE_ENV !== 'production') {
    console.error('Error:', sanitizedDetails);
  }
  
  // Send to analytics error tracking
  trackEvent(EVENT_CATEGORY.PERFORMANCE, 'error_captured', {
    errorType,
    message: error.message,
    name: error.name,
    ...sanitizedDetails
  });
  
  // For critical errors, ensure immediate notification
  if (
    errorType === ErrorTypes.AI_SERVICE || 
    errorType === ErrorTypes.NETWORK ||
    (error instanceof ApiError && error.status >= 500)
  ) {
    // Log critical error with additional context
    console.warn('Critical error detected:', errorType, error.message);
  }
}