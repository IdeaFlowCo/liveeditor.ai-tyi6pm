/**
 * Utility module for tracking user events, performance metrics, and errors in the application.
 * Provides functions to monitor key user interactions, AI feature usage, and application performance.
 * 
 * @module tracking
 * @version 1.0.0
 */

import * as Sentry from '@sentry/browser'; // @sentry/browser ^7.0.0
import { BrowserTracing } from '@sentry/tracing'; // @sentry/tracing ^7.0.0
import { 
  EVENT_CATEGORY,
  USER_EVENTS,
  DOCUMENT_EVENTS,
  AI_EVENTS,
  NAVIGATION_EVENTS,
  PERFORMANCE_EVENTS,
  METRIC_EVENTS
} from '../lib/analytics/events';
import { TrackingEvent } from '../lib/analytics/events';
import analytics from '../lib/analytics';
import { Document, User, Suggestion } from '../types';

// Constants for Sentry configuration
const SENTRY_DSN = process.env.REACT_APP_SENTRY_DSN;
const SENTRY_ENVIRONMENT = process.env.REACT_APP_ENVIRONMENT || 'development';
const SENTRY_RELEASE = process.env.REACT_APP_VERSION || '1.0.0';
const IS_DEV_ENV = process.env.NODE_ENV === 'development';

// Performance tracking constants
const PERF_TRACING_ORIGINS = ['localhost', 'your-production-domain.com'];
const PERF_SAMPLE_RATE = 0.1; // 10% of transactions

/**
 * Configuration options for tracking initialization
 */
interface TrackingConfig {
  /** Whether to enable tracking and monitoring */
  enabled?: boolean;
  /** Custom Sentry DSN if not using environment variable */
  sentryDsn?: string;
  /** Environment name */
  environment?: string;
  /** Application version */
  release?: string;
  /** Debug mode toggle */
  debug?: boolean;
  /** Whether to disable analytics */
  disableAnalytics?: boolean;
  /** Whether to disable error tracking */
  disableErrorTracking?: boolean;
}

/**
 * Options for sanitizing tracking data
 */
interface SanitizeOptions {
  /** Fields to remove from tracking data */
  excludeFields?: string[];
  /** Maximum string length for field values */
  maxValueLength?: number;
  /** Whether to remove document content */
  excludeDocumentContent?: boolean;
}

/**
 * Initializes tracking services with necessary configuration.
 * Sets up Sentry for error tracking and performance monitoring.
 *
 * @param {TrackingConfig} config - Configuration options for tracking services
 */
export const initializeTracking = (config: TrackingConfig = {}): void => {
  const isEnabled = config.enabled !== false;
  
  if (!isEnabled) {
    // Early return if tracking is explicitly disabled
    console.log('Tracking has been disabled by configuration');
    return;
  }

  // Initialize error tracking with Sentry
  if (!config.disableErrorTracking) {
    const dsn = config.sentryDsn || SENTRY_DSN;
    if (dsn) {
      Sentry.init({
        dsn,
        environment: config.environment || SENTRY_ENVIRONMENT,
        release: config.release || SENTRY_RELEASE,
        integrations: [
          new BrowserTracing({
            tracingOrigins: PERF_TRACING_ORIGINS,
          }),
        ],
        // Set sample rates based on environment
        tracesSampleRate: IS_DEV_ENV ? 1.0 : PERF_SAMPLE_RATE,
        // Enable debug in development for easier troubleshooting
        debug: config.debug || IS_DEV_ENV,
        // Don't send errors in development unless explicitly enabled
        enabled: !IS_DEV_ENV || config.debug === true,
      });
      
      if (IS_DEV_ENV) {
        console.log('Sentry initialized for error tracking and performance monitoring');
      }
    } else if (IS_DEV_ENV) {
      console.warn('Sentry DSN not provided, error tracking disabled');
    }
  }

  // Initialize custom analytics
  if (!config.disableAnalytics) {
    analytics.initialize({
      debug: config.debug || IS_DEV_ENV,
      disableTracking: IS_DEV_ENV && !config.debug, // Disabled in dev unless debug is on
    });
    
    if (IS_DEV_ENV) {
      console.log('Analytics system initialized');
    }
  }
};

/**
 * Sanitizes event data to remove sensitive information
 * 
 * @param {any} data - Raw event data to be sanitized
 * @param {SanitizeOptions} options - Options for sanitization
 * @returns {any} Sanitized data safe for tracking
 */
const sanitizeEventData = (data: any, options: SanitizeOptions = {}): any => {
  if (!data) return data;
  
  const { 
    excludeFields = ['password', 'token', 'authorization', 'content'],
    maxValueLength = 500,
    excludeDocumentContent = true 
  } = options;
  
  const sanitized: any = { ...data };
  
  // Remove sensitive fields
  for (const field of excludeFields) {
    if (field in sanitized) {
      delete sanitized[field];
    }
  }
  
  // Special handling for document content
  if (excludeDocumentContent && sanitized.document?.content) {
    sanitized.document = { ...sanitized.document };
    delete sanitized.document.content;
  }
  
  // Truncate long string values
  Object.keys(sanitized).forEach(key => {
    if (typeof sanitized[key] === 'string' && sanitized[key].length > maxValueLength) {
      sanitized[key] = `${sanitized[key].substring(0, maxValueLength)}...`;
    }
    
    // Recursively sanitize nested objects
    if (typeof sanitized[key] === 'object' && sanitized[key] !== null) {
      sanitized[key] = sanitizeEventData(sanitized[key], options);
    }
  });
  
  return sanitized;
};

/**
 * Tracks a custom event with the analytics system
 *
 * @param {string} eventType - Type of event being tracked
 * @param {object} eventData - Data associated with the event
 */
export const trackEvent = (eventType: string, eventData: object = {}): void => {
  const sanitizedData = sanitizeEventData(eventData);
  
  // Determine the appropriate category based on event type
  let category = EVENT_CATEGORY.USER; // Default category
  
  if (eventType.startsWith('document_')) {
    category = EVENT_CATEGORY.DOCUMENT;
  } else if (eventType.startsWith('ai_')) {
    category = EVENT_CATEGORY.AI;
  } else if (eventType.startsWith('navigation_')) {
    category = EVENT_CATEGORY.NAVIGATION;
  } else if (eventType.startsWith('performance_')) {
    category = EVENT_CATEGORY.PERFORMANCE;
  }
  
  // Add standard metadata
  const enhancedData = {
    ...sanitizedData,
    timestamp: new Date().toISOString(),
    eventType,
  };
  
  // Send to analytics service
  analytics.trackEvent(category, eventType, enhancedData);
  
  // Log events in development for debugging
  if (IS_DEV_ENV) {
    console.log(`[EVENT] ${category}:${eventType}`, enhancedData);
  }
};

/**
 * Tracks events related to document interactions
 *
 * @param {string} eventType - Type of document event
 * @param {Document} document - Document being acted upon
 * @param {object} additionalData - Additional event information
 */
export const trackDocumentEvent = (
  eventType: string, 
  document: Document, 
  additionalData: object = {}
): void => {
  // Extract relevant metadata from document
  const documentMetadata = {
    documentId: document.id,
    title: document.metadata?.title,
    wordCount: document.stats?.wordCount,
    charCount: document.stats?.characterCount,
    isAnonymous: document.isAnonymous,
    state: document.state,
    // Don't include the actual content
  };
  
  // Combine document metadata with additional data
  const eventData = {
    ...additionalData,
    document: documentMetadata,
  };
  
  // Track the event
  trackEvent(eventType, eventData);
  
  // Also track document metrics for analysis
  if (document.stats && 
      (eventType === DOCUMENT_EVENTS.CREATE || 
       eventType === DOCUMENT_EVENTS.SAVE)) {
    trackEvent(METRIC_EVENTS.WORD_COUNT, {
      documentId: document.id,
      wordCount: document.stats.wordCount,
      characterCount: document.stats.characterCount,
    });
  }
};

/**
 * Tracks AI-related interactions including suggestion generation and acceptance
 *
 * @param {string} eventType - Type of AI interaction
 * @param {object} aiData - AI interaction details
 */
export const trackAiInteraction = (
  eventType: string, 
  aiData: object = {}
): void => {
  // Sanitize AI data to remove potentially sensitive content
  const sanitizedData = sanitizeEventData(aiData, { 
    excludeDocumentContent: true,
    excludeFields: ['content', 'originalText', 'suggestedText'],
  });
  
  // Add performance metrics for AI operations if available
  if (sanitizedData.processingTime) {
    trackEvent(PERFORMANCE_EVENTS.AI_RESPONSE_TIME, {
      processingTime: sanitizedData.processingTime,
      eventType,
    });
  }
  
  // Track suggestion metrics if applicable
  if (eventType === AI_EVENTS.ACCEPT_SUGGESTION || 
      eventType === AI_EVENTS.REJECT_SUGGESTION) {
    trackEvent(METRIC_EVENTS.SUGGESTION_ACCEPTANCE_RATE, {
      action: eventType === AI_EVENTS.ACCEPT_SUGGESTION ? 'accept' : 'reject',
      suggestionType: sanitizedData.suggestionType || 'unknown',
      templateId: sanitizedData.templateId,
    });
  }
  
  // Track the main AI event
  trackEvent(eventType, sanitizedData);
};

/**
 * Tracks application errors with Sentry
 *
 * @param {Error} error - Error object to be tracked
 * @param {object} contextData - Additional context for the error
 */
export const trackError = (error: Error, contextData: object = {}): void => {
  // Sanitize context data
  const sanitizedContext = sanitizeEventData(contextData);
  
  // Determine error severity based on context
  let severity = 'error';
  if (sanitizedContext.fatal) {
    severity = 'fatal';
  } else if (sanitizedContext.warning) {
    severity = 'warning';
  }
  
  // Set context in Sentry
  Sentry.setContext('error_details', sanitizedContext);
  
  // Set tag for error category if available
  if (sanitizedContext.category) {
    Sentry.setTag('error.category', sanitizedContext.category);
  }
  
  // Set extra context data for Sentry
  Object.entries(sanitizedContext).forEach(([key, value]) => {
    Sentry.setExtra(key, value);
  });
  
  // Capture exception in Sentry
  Sentry.captureException(error, {
    level: severity as Sentry.SeverityLevel,
  });
  
  // Also track in analytics for frequency analysis
  trackEvent('app_error', {
    errorMessage: error.message,
    errorName: error.name,
    stack: IS_DEV_ENV ? error.stack : undefined,
    ...sanitizedContext,
  });
  
  // Log error in development
  if (IS_DEV_ENV) {
    console.error('[ERROR TRACKED]', error, sanitizedContext);
  }
};

/**
 * Interface for performance tracker object
 */
interface PerformanceTracker {
  /** Method to stop tracking and record performance metrics */
  stop: () => void;
  /** Method to add a marker point in the timeline */
  mark: (markerName: string) => void;
}

/**
 * Begins performance measurement for a specific operation
 *
 * @param {string} operationName - Name of the operation to measure
 * @returns {PerformanceTracker} Tracker object with stop method to end measurement
 */
export const startPerformanceTracking = (operationName: string): PerformanceTracker => {
  const startTime = performance.now();
  const markers: {[key: string]: number} = {};
  const transactionId = `${operationName}-${Date.now()}`;
  
  // Create a Sentry transaction for more detailed tracking
  const transaction = Sentry.startTransaction({
    name: operationName,
    op: 'performance.measure',
  });
  
  // Set current transaction for Sentry
  Sentry.configureScope(scope => {
    scope.setSpan(transaction);
  });
  
  // Return tracker object with methods to stop and mark
  return {
    /**
     * Stops the performance measurement and records metrics
     */
    stop: () => {
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      // Finish Sentry transaction
      transaction.finish();
      
      // Track performance in analytics
      trackEvent(PERFORMANCE_EVENTS.API_LATENCY, {
        operation: operationName,
        duration,
        startTime,
        endTime,
        markers,
        transactionId,
      });
      
      if (IS_DEV_ENV) {
        console.log(`[PERFORMANCE] ${operationName}: ${duration.toFixed(2)}ms`);
        if (Object.keys(markers).length > 0) {
          console.log('[PERFORMANCE] Markers:', markers);
        }
      }
    },
    
    /**
     * Adds a marker point in the performance timeline
     * 
     * @param {string} markerName - Name of the marker point
     */
    mark: (markerName: string) => {
      const markerTime = performance.now();
      const timeSinceStart = markerTime - startTime;
      markers[markerName] = timeSinceStart;
      
      // Create a span for this marker in Sentry
      const span = transaction.startChild({
        op: 'mark',
        description: markerName,
      });
      span.finish();
      
      if (IS_DEV_ENV) {
        console.log(`[PERFORMANCE] ${operationName} - ${markerName}: ${timeSinceStart.toFixed(2)}ms`);
      }
    }
  };
};

/**
 * Tracks page view events with relevant metadata
 *
 * @param {string} pageName - Name of the page being viewed
 * @param {object} pageData - Additional page metadata
 */
export const trackPageView = (pageName: string, pageData: object = {}): void => {
  // Get referrer information if available
  const referrer = document.referrer || '';
  const url = window.location.href;
  const path = window.location.pathname;
  
  // Collect page load performance metrics
  const perfData = window.performance?.timing;
  let loadTime = 0;
  
  if (perfData) {
    loadTime = perfData.loadEventEnd - perfData.navigationStart;
  }
  
  // Combine all page view data
  const eventData = {
    pageName,
    path,
    url,
    referrer,
    loadTime,
    viewportWidth: window.innerWidth,
    viewportHeight: window.innerHeight,
    ...pageData,
  };
  
  // Track page view event
  trackEvent(NAVIGATION_EVENTS.PAGE_VIEW, eventData);
  
  // Also track performance data separately
  if (loadTime > 0) {
    trackEvent(PERFORMANCE_EVENTS.PAGE_LOAD, {
      pageName,
      loadTime,
      domContentLoaded: perfData.domContentLoadedEventEnd - perfData.navigationStart,
      firstPaint: perfData.responseEnd - perfData.navigationStart,
    });
  }
};

/**
 * Sets user context information for tracking
 *
 * @param {User} user - User object containing identity information
 */
export const setUserContext = (user: User): void => {
  if (!user) return;
  
  // Extract only necessary non-sensitive user information
  const userContext = {
    id: user.id,
    isAnonymous: user.isAnonymous === true,
    email: user.email, // Sentry will hash this value for privacy
    role: user.role,
  };
  
  // Set user context in Sentry
  Sentry.setUser(userContext);
  
  // Set user identity in analytics
  analytics.setUserIdentity(user.id, {
    accountType: user.role,
    isAnonymous: user.isAnonymous === true,
    creationDate: user.createdAt,
    emailVerified: user.emailVerified,
  });
  
  if (IS_DEV_ENV) {
    console.log('[TRACKING] User context set:', userContext);
  }
};

/**
 * Specifically tracks events related to AI suggestions
 *
 * @param {string} eventType - Type of suggestion event
 * @param {Suggestion} suggestion - Suggestion object
 * @param {string} action - User action on the suggestion (accept/reject/ignore)
 */
export const trackSuggestionEvent = (
  eventType: string, 
  suggestion: Suggestion, 
  action: string
): void => {
  // Calculate position metrics
  const suggestionLength = suggestion.suggestedText.length;
  const originalLength = suggestion.originalText.length;
  const lengthDifference = suggestionLength - originalLength;
  
  // Compile suggestion metadata
  const suggestionData = {
    suggestionId: suggestion.id,
    documentId: suggestion.documentId,
    category: suggestion.category,
    changeType: suggestion.changeType,
    action,
    lengthDifference,
    position: suggestion.position,
    // Don't include the actual content
  };
  
  // Track the suggestion event
  trackAiInteraction(eventType, suggestionData);
  
  // For accept/reject actions, also track the specific metric
  if (action === 'accept' || action === 'reject') {
    trackEvent(METRIC_EVENTS.SUGGESTION_ACCEPTANCE_RATE, {
      suggestionId: suggestion.id,
      category: suggestion.category,
      action,
      accepted: action === 'accept',
    });
  }
};

/**
 * Clears user context on logout or session end
 */
export const clearUserContext = (): void => {
  // Clear user context in Sentry
  Sentry.setUser(null);
  
  // Clear identity in analytics
  analytics.clearUserIdentity();
  
  if (IS_DEV_ENV) {
    console.log('[TRACKING] User context cleared');
  }
};