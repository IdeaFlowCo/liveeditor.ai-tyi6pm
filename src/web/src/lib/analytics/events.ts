/**
 * Analytics Event Constants
 * 
 * This file defines constants for analytics events tracked throughout the application.
 * Use these constants when logging events to ensure consistency in event naming.
 * 
 * These events support the Business Metrics Dashboard requirements outlined in the 
 * technical specifications.
 */

/**
 * Event categories for organizing analytics data
 */
export const EVENT_CATEGORY = {
  USER: 'user',
  DOCUMENT: 'document',
  AI: 'ai',
  NAVIGATION: 'navigation',
  PERFORMANCE: 'performance'
};

/**
 * Events related to user authentication and account management
 */
export const USER_EVENTS = {
  LOGIN: 'user_login',
  LOGOUT: 'user_logout',
  REGISTER: 'user_register',
  CONVERT_TO_REGISTERED: 'user_convert_to_registered',
  PROFILE_UPDATE: 'user_profile_update'
};

/**
 * Events related to document lifecycle and operations
 */
export const DOCUMENT_EVENTS = {
  CREATE: 'document_create',
  EDIT: 'document_edit',
  SAVE: 'document_save',
  DELETE: 'document_delete',
  IMPORT: 'document_import',
  EXPORT: 'document_export',
  FORMAT: 'document_format'
};

/**
 * Events related to AI interaction and suggestion processing
 */
export const AI_EVENTS = {
  REQUEST_SUGGESTION: 'ai_request_suggestion',
  RECEIVE_SUGGESTION: 'ai_receive_suggestion',
  ACCEPT_SUGGESTION: 'ai_accept_suggestion',
  REJECT_SUGGESTION: 'ai_reject_suggestion',
  USE_TEMPLATE: 'ai_use_template',
  CHAT_MESSAGE: 'ai_chat_message',
  ERROR: 'ai_error'
};

/**
 * Events related to user navigation and feature discovery
 */
export const NAVIGATION_EVENTS = {
  PAGE_VIEW: 'navigation_page_view',
  FEATURE_DISCOVERY: 'navigation_feature_discovery',
  SIDEBAR_TOGGLE: 'navigation_sidebar_toggle'
};

/**
 * Events related to application performance and responsiveness
 */
export const PERFORMANCE_EVENTS = {
  PAGE_LOAD: 'performance_page_load',
  AI_RESPONSE_TIME: 'performance_ai_response_time',
  EDITOR_INIT_TIME: 'performance_editor_init_time',
  API_LATENCY: 'performance_api_latency'
};

/**
 * Events for tracking key business metrics and KPIs
 */
export const METRIC_EVENTS = {
  WORD_COUNT: 'metric_word_count',
  SUGGESTION_COUNT: 'metric_suggestion_count',
  SUGGESTION_ACCEPTANCE_RATE: 'metric_suggestion_acceptance_rate',
  SESSION_DURATION: 'metric_session_duration',
  FEATURE_USAGE: 'metric_feature_usage'
};