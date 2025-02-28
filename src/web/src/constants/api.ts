/**
 * API Constants
 * 
 * This file contains constants for API endpoints and configuration 
 * used throughout the frontend application for communicating with backend services.
 */

/**
 * Base URL for all API requests, configurable by environment
 */
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

/**
 * Default timeout in milliseconds for API requests
 */
export const API_TIMEOUT = 30000; // 30 seconds

/**
 * API version prefix for endpoint URLs
 */
export const API_VERSION = '/api';

/**
 * HTTP method constants for API requests
 */
export const HTTP_METHODS = {
  GET: 'GET',
  POST: 'POST',
  PUT: 'PUT',
  DELETE: 'DELETE',
  PATCH: 'PATCH'
} as const;

/**
 * Content type constants for API request headers
 */
export const CONTENT_TYPES = {
  JSON: 'application/json',
  FORM_DATA: 'multipart/form-data',
  TEXT: 'text/plain'
} as const;

/**
 * HTTP error code constants for error handling
 */
export const ERROR_CODES = {
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  RATE_LIMITED: 429,
  SERVER_ERROR: 500
} as const;

/**
 * Structured object containing all API endpoint paths organized by feature area
 */
export const ENDPOINTS = {
  /**
   * Authentication-related endpoints
   */
  AUTH: {
    /** User login endpoint */
    LOGIN: '/auth/login',
    /** User registration endpoint */
    REGISTER: '/auth/register',
    /** Token refresh endpoint */
    REFRESH: '/auth/refresh',
    /** User logout endpoint */
    LOGOUT: '/auth/logout',
    /** Email verification endpoint */
    VERIFY: '/auth/verify',
    /** Password reset request endpoint */
    PASSWORD_RESET: '/auth/password-reset',
    /** Password reset confirmation endpoint */
    PASSWORD_RESET_CONFIRM: '/auth/password-reset-confirm'
  },

  /**
   * Document management endpoints
   */
  DOCUMENTS: {
    /** Base documents endpoint */
    BASE: '/documents',
    /** Individual document endpoint (requires ID) */
    DOCUMENT: (id: string) => `/documents/${id}`,
    /** Document versions endpoint (requires document ID) */
    VERSIONS: (id: string) => `/documents/${id}/versions`,
    /** Specific document version endpoint (requires document ID and version ID) */
    VERSION: (id: string, versionId: string) => `/documents/${id}/versions/${versionId}`
  },

  /**
   * AI suggestion endpoints
   */
  SUGGESTIONS: {
    /** Base suggestions endpoint */
    BASE: '/suggestions',
    /** Text improvement suggestions endpoint */
    TEXT: '/suggestions/text',
    /** Style improvement suggestions endpoint */
    STYLE: '/suggestions/style',
    /** Grammar improvement suggestions endpoint */
    GRAMMAR: '/suggestions/grammar'
  },

  /**
   * AI chat-related endpoints
   */
  CHAT: {
    /** Send chat message endpoint */
    MESSAGE: '/chat/message',
    /** Retrieve chat history endpoint */
    HISTORY: '/chat/history'
  },

  /**
   * AI template management endpoints
   */
  TEMPLATES: {
    /** Base templates endpoint */
    BASE: '/templates',
    /** Individual template endpoint (requires ID) */
    TEMPLATE: (id: string) => `/templates/${id}`,
    /** Template categories endpoint */
    CATEGORIES: '/templates/categories'
  },

  /**
   * User-related endpoints
   */
  USERS: {
    /** User profile endpoint */
    PROFILE: '/users/profile',
    /** User preferences endpoint */
    PREFERENCES: '/users/preferences'
  }
};