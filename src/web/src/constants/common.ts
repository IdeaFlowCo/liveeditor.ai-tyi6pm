/**
 * Common constants used throughout the application
 * Contains application settings, keys, messages, and configuration values
 */

// Application information
export const APP_NAME = "AI Writing Enhancement";
export const APP_VERSION = "1.0.0";

// Time durations (in milliseconds)
export const ANONYMOUS_SESSION_DURATION = 86400000; // 24 hours
export const AUTOSAVE_INTERVAL = 30000; // 30 seconds
export const DEFAULT_DEBOUNCE_DELAY = 300; // 300ms
export const MAX_IDLE_TIME = 1800000; // 30 minutes
export const ANONYMOUS_WARNING_THRESHOLD = 900000; // 15 minutes
export const RETRY_DELAY = 1000; // 1 second (base delay before exponential backoff)
export const ANIMATION_DURATION = 200; // 200ms
export const AI_REQUEST_TIMEOUT = 10000; // 10 seconds

// Document limitations
export const DOCUMENT_SIZE_LIMIT = 25000; // Maximum document size in words

// Pagination
export const DEFAULT_PAGE_SIZE = 10;

// API retry strategy
export const MAX_RETRY_ATTEMPTS = 3;

// Accessibility
export const FOCUS_VISIBLE_OUTLINE = "2px solid #2C6ECB";

// Local storage keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: "ai_writing_auth_token",
  REFRESH_TOKEN: "ai_writing_refresh_token",
  USER_PREFERENCES: "ai_writing_user_prefs",
  SESSION_ID: "ai_writing_session_id",
  TEMP_DOCUMENT: "ai_writing_temp_document"
};

// User types
export const USER_TYPES = {
  ANONYMOUS: "anonymous",
  AUTHENTICATED: "authenticated",
  ADMIN: "admin"
};

// HTTP status codes
export const HTTP_STATUS = {
  OK: 200,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  SERVER_ERROR: 500,
  TOO_MANY_REQUESTS: 429
};

// Error messages
export const ERROR_MESSAGES = {
  DEFAULT: "An unexpected error occurred. Please try again later.",
  NETWORK: "Unable to connect to the server. Please check your internet connection.",
  UNAUTHORIZED: "Your session has expired or you don't have permission to perform this action.",
  DOCUMENT_TOO_LARGE: "Document exceeds the maximum size of 25,000 words. Please reduce the content.",
  AI_SERVICE_UNAVAILABLE: "AI service is currently unavailable. Please try again later.",
  SESSION_EXPIRED: "Your session has expired. Please log in again to continue."
};

// Success messages
export const SUCCESS_MESSAGES = {
  DOCUMENT_SAVED: "Document saved successfully.",
  CHANGES_APPLIED: "Changes applied successfully.",
  LOGIN_SUCCESS: "You have been successfully logged in.",
  REGISTRATION_SUCCESS: "Your account has been created successfully. Welcome!"
};

// Date format patterns
export const DATE_FORMATS = {
  SHORT: "MM/DD/YYYY",
  LONG: "MMMM D, YYYY",
  TIME_ONLY: "h:mm A",
  RELATIVE: "relative"
};

// Responsive design breakpoints
export const BREAKPOINTS = {
  MOBILE: 768, // < 768px
  TABLET: 1024, // 768px - 1024px
  DESKTOP: 1025 // > 1024px
};

// Keyboard shortcuts
export const KEYBOARD_SHORTCUTS = {
  SAVE: "Ctrl+S",
  UNDO: "Ctrl+Z",
  ACCEPT_SUGGESTION: "Alt+A",
  REJECT_SUGGESTION: "Alt+R",
  NEXT_SUGGESTION: "Alt+N",
  PREVIOUS_SUGGESTION: "Alt+P"
};

// Color scheme constants
export const COLORS = {
  PRIMARY: "#2C6ECB", // Primary Blue
  SECONDARY: "#20B2AA", // Secondary Teal
  NEUTRAL: "#F5F7FA", // Neutral Gray
  SUCCESS: "#28A745", // Success Green
  WARNING: "#FFC107", // Warning Yellow
  ERROR: "#DC3545", // Error Red
  DELETION: "#FF6B6B", // Red for deletions in track changes
  ADDITION: "#20A779" // Green for additions in track changes
};