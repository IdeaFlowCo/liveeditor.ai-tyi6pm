/**
 * Core analytics module for tracking user interactions and application performance.
 * 
 * Provides a flexible analytics framework that supports both anonymous and
 * authenticated user tracking throughout the application.
 * 
 * @module analytics
 * @version 1.0.0 
 */

import { v4 as uuidv4 } from 'uuid'; // uuid ^9.0.0
import { 
  EVENT_CATEGORY, 
  USER_EVENTS, 
  DOCUMENT_EVENTS, 
  AI_EVENTS, 
  NAVIGATION_EVENTS, 
  PERFORMANCE_EVENTS, 
  METRIC_EVENTS 
} from './events';
import { post } from '../../utils/api';

// Constants
const SESSION_ID_KEY = 'ai_writing_session_id';
const DEBUG_ANALYTICS = process.env.NODE_ENV === 'development';
const ANALYTICS_ENDPOINT = '/api/analytics/events';
const FLUSH_INTERVAL = 30000; // 30 seconds
const MAX_QUEUE_SIZE = 20;

// Types
interface AnalyticsConfig {
  debug?: boolean;
  endpoint?: string;
  flushInterval?: number;
  maxQueueSize?: number;
  disableTracking?: boolean;
}

interface UserProperties {
  accountType?: string;
  creationDate?: string;
  [key: string]: any;
}

interface PerformanceMeasurement {
  stop: () => void;
}

/**
 * Represents a structured analytics event with standardized properties
 */
class AnalyticsEvent {
  category: string;
  action: string;
  timestamp: number;
  sessionId: string;
  userId: string | null;
  data: Record<string, any>;
  
  /**
   * Creates a new analytics event
   * 
   * @param category - Event category (user, document, ai, etc.)
   * @param action - Specific action being tracked
   * @param data - Additional event data
   */
  constructor(category: string, action: string, data: Record<string, any> = {}) {
    this.category = category;
    this.action = action;
    this.timestamp = Date.now();
    this.sessionId = getSessionId();
    this.userId = userId;
    this.data = data;
  }
  
  /**
   * Converts the event to a JSON-serializable object
   * 
   * @returns JSON representation of the event
   */
  toJSON(): Record<string, any> {
    const result: Record<string, any> = {
      category: this.category,
      action: this.action,
      timestamp: this.timestamp,
      sessionId: this.sessionId
    };
    
    if (this.userId) {
      result.userId = this.userId;
    }
    
    if (Object.keys(this.data).length > 0) {
      result.data = this.data;
    }
    
    return result;
  }
}

// Module state
let config: AnalyticsConfig = {
  debug: DEBUG_ANALYTICS,
  endpoint: ANALYTICS_ENDPOINT,
  flushInterval: FLUSH_INTERVAL,
  maxQueueSize: MAX_QUEUE_SIZE,
  disableTracking: false
};

let eventQueue: AnalyticsEvent[] = [];
let flushIntervalId: number | null = null;
let userId: string | null = null;
let userProps: UserProperties | null = null;

/**
 * Initializes the analytics module with configuration options
 *
 * @param config - Configuration options for the analytics module
 */
function initialize(userConfig: AnalyticsConfig = {}): void {
  config = { ...config, ...userConfig };
  
  // Generate or retrieve session ID
  getSessionId();
  
  // Set up flush interval
  if (flushIntervalId !== null) {
    clearInterval(flushIntervalId);
  }
  
  flushIntervalId = window.setInterval(() => {
    flushEvents(true);
  }, config.flushInterval);
  
  // Ensure events are flushed before page unload
  window.addEventListener('beforeunload', () => {
    flushEvents(false);
  });
  
  if (config.debug) {
    console.log('Analytics initialized with config:', config);
  }
}

/**
 * Records an analytics event for later sending to the backend
 *
 * @param category - Event category (user, document, ai, etc.)
 * @param action - Specific action being tracked
 * @param data - Additional event data
 */
function trackEvent(category: string, action: string, data: Record<string, any> = {}): void {
  if (config.disableTracking) return;
  
  const event = new AnalyticsEvent(category, action, data);
  eventQueue.push(event);
  
  if (config.debug) {
    console.log('Analytics event tracked:', event);
  }
  
  // Flush if queue exceeds maximum size
  if (eventQueue.length >= config.maxQueueSize) {
    flushEvents(true);
  }
}

/**
 * Sends queued events to the analytics backend
 *
 * @param async - Whether to use async AJAX (true) or sync navigator.sendBeacon (false)
 * @returns Promise resolving to success status of the flush operation
 */
async function flushEvents(async: boolean = true): Promise<boolean> {
  if (eventQueue.length === 0) return true;
  
  const events = [...eventQueue];
  eventQueue = [];
  
  try {
    if (async) {
      // Use regular AJAX for normal operation
      await post(config.endpoint, { events });
    } else {
      // Use sendBeacon for page unload to ensure delivery
      const blob = new Blob([JSON.stringify({ events })], { type: 'application/json' });
      navigator.sendBeacon(config.endpoint, blob);
    }
    
    if (config.debug) {
      console.log('Analytics events flushed:', events);
    }
    
    return true;
  } catch (error) {
    // Put events back in queue on failure
    eventQueue = [...events, ...eventQueue];
    
    if (config.debug) {
      console.error('Failed to flush analytics events:', error);
    }
    
    return false;
  }
}

/**
 * Retrieves or creates a unique session identifier
 *
 * @returns Unique session identifier
 */
function getSessionId(): string {
  try {
    let sessionId = localStorage.getItem(SESSION_ID_KEY);
    
    if (!sessionId) {
      sessionId = uuidv4();
      localStorage.setItem(SESSION_ID_KEY, sessionId);
      
      if (config.debug) {
        console.log('Created new analytics session ID:', sessionId);
      }
    }
    
    return sessionId;
  } catch (error) {
    // If localStorage is not available, generate a temporary ID
    const tempId = uuidv4();
    
    if (config.debug) {
      console.warn('Unable to access localStorage for session ID, using temporary ID:', tempId);
    }
    
    return tempId;
  }
}

/**
 * Associates analytics events with an authenticated user
 *
 * @param id - Unique user identifier
 * @param properties - Additional user properties
 */
function setUserIdentity(id: string, properties: UserProperties = {}): void {
  userId = id;
  userProps = properties;
  
  // Track identity event to link previous anonymous events with user
  trackEvent(EVENT_CATEGORY.USER, 'identify', {
    userId: id,
    ...properties
  });
  
  if (config.debug) {
    console.log('User identity set:', id, properties);
  }
}

/**
 * Removes user association from analytics, typically on logout
 */
function clearUserIdentity(): void {
  // Flush any pending events before clearing identity
  flushEvents(true);
  
  // Track logout event
  if (userId) {
    trackEvent(EVENT_CATEGORY.USER, 'logout', {
      userId
    });
  }
  
  userId = null;
  userProps = null;
  
  if (config.debug) {
    console.log('User identity cleared');
  }
}

/**
 * Creates a performance measurement with start and end timing
 *
 * @param metricName - Name of the metric to measure
 * @returns Object with stop method to end timing and record metric
 */
function measurePerformance(metricName: string): PerformanceMeasurement {
  const startTime = performance.now();
  
  return {
    stop: () => {
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      trackEvent(EVENT_CATEGORY.PERFORMANCE, metricName, {
        duration,
        startTime,
        endTime
      });
      
      if (config.debug) {
        console.log(`Performance metric [${metricName}]: ${duration.toFixed(2)}ms`);
      }
    }
  };
}

// Default export as an object with all methods
export default {
  initialize,
  trackEvent,
  flushEvents,
  setUserIdentity,
  clearUserIdentity,
  measurePerformance
};

// Named exports for individual functions
export {
  initialize,
  trackEvent,
  flushEvents,
  setUserIdentity,
  clearUserIdentity,
  measurePerformance,
  EVENT_CATEGORY // Re-export from './events'
};