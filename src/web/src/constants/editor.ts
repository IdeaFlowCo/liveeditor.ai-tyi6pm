/**
 * Editor Constants
 * 
 * This file contains constants, enums, and configuration values for the document editor components.
 * These constants are used throughout the application to ensure consistent behavior, styling,
 * and operation of the document editing and AI suggestion features.
 */

/**
 * Defines the possible interaction modes for the editor
 */
export const EDITOR_MODES = {
  EDIT: 'edit',            // Regular editing mode
  REVIEW: 'review',        // Review AI suggestions mode
  READ_ONLY: 'read-only'   // View-only mode
} as const;

/**
 * Defines available text formatting options for the editor toolbar
 */
export const FORMATTING_OPTIONS = {
  BOLD: 'bold',
  ITALIC: 'italic',
  UNDERLINE: 'underline',
  HEADING1: 'heading1',
  HEADING2: 'heading2',
  HEADING3: 'heading3',
  BULLET_LIST: 'bulletList',
  ORDERED_LIST: 'orderedList',
  BLOCKQUOTE: 'blockquote',
  CODE_BLOCK: 'codeBlock'
} as const;

/**
 * Defines keyboard shortcuts for common editor actions
 */
export const KEYBOARD_SHORTCUTS = {
  SAVE: 'Ctrl+S',
  BOLD: 'Ctrl+B',
  ITALIC: 'Ctrl+I',
  UNDERLINE: 'Ctrl+U',
  ACCEPT_SUGGESTION: 'Alt+A',
  REJECT_SUGGESTION: 'Alt+R',
  NEXT_SUGGESTION: 'Alt+N',
  PREV_SUGGESTION: 'Alt+P'
} as const;

/**
 * Defines styling colors for track changes feature
 */
export const TRACK_CHANGES_STYLES = {
  DELETION_COLOR: '#FF6B6B',  // Red for deleted text
  ADDITION_COLOR: '#20A779',  // Green for added text
  HIGHLIGHT_COLOR: '#E3F2FD', // Light blue for highlighting
  COMMENT_COLOR: '#F9A826'    // Orange for comments
} as const;

/**
 * Defines possible editor activity states
 */
export const EDITOR_STATES = {
  IDLE: 'idle',             // Default state
  LOADING: 'loading',       // Loading document
  SAVING: 'saving',         // Saving document
  PROCESSING_AI: 'processing-ai', // Processing AI suggestions
  ERROR: 'error'            // Error state
} as const;

/**
 * Defines possible states for AI suggestions
 */
export const SUGGESTION_STATUS = {
  PENDING: 'pending',     // Not yet reviewed
  ACCEPTED: 'accepted',   // Accepted by user
  REJECTED: 'rejected'    // Rejected by user
} as const;

/**
 * Default configuration values for editor appearance
 */
export const DEFAULT_EDITOR_CONFIG = {
  FONT_FAMILY: "'Source Serif Pro', serif",
  FONT_SIZE: '16px',
  LINE_HEIGHT: '1.6',
  PARAGRAPH_SPACING: '16px',
  PLACEHOLDER_TEXT: 'Start typing or paste your text here...'
} as const;

/**
 * Time interval in milliseconds for auto-save functionality
 * 30 seconds = 30,000 milliseconds
 */
export const AUTOSAVE_INTERVAL = 30000;

/**
 * Maximum document size in words that can be processed
 * Based on Technical Specifications F-001-RQ-001 (25,000 words)
 */
export const MAX_DOCUMENT_SIZE = 25000;

/**
 * Supported document import and export formats
 */
export const DOCUMENT_FORMATS = {
  PLAIN_TEXT: 'text/plain',
  RICH_TEXT: 'text/rtf',
  HTML: 'text/html',
  MARKDOWN: 'text/markdown',
  DOCX: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
} as const;

/**
 * Configuration options for track changes behavior
 */
export const TRACK_CHANGES_CONFIG = {
  SHOW_COMMENTS: true,    // Whether to show comments alongside changes
  INLINE_PREVIEW: true,   // Whether to preview changes inline
  AUTO_SCROLL: true       // Whether to auto-scroll to changes
} as const;

/**
 * Event types that can be emitted by the editor
 */
export const EDITOR_EVENTS = {
  DOCUMENT_CHANGE: 'document-change',       // Document content changed
  SELECTION_CHANGE: 'selection-change',     // Text selection changed
  SUGGESTION_ADDED: 'suggestion-added',     // New AI suggestion added
  SUGGESTION_ACCEPTED: 'suggestion-accepted', // Suggestion was accepted
  SUGGESTION_REJECTED: 'suggestion-rejected'  // Suggestion was rejected
} as const;

/**
 * Timeout and debounce durations for editor operations (in milliseconds)
 */
export const EDITOR_TIMEOUT_DURATIONS = {
  DEBOUNCE_SAVE: 2000,      // Debounce time for auto-save (2 seconds)
  DEBOUNCE_CHANGE: 500,     // Debounce time for change events (500ms)
  OPERATION_TIMEOUT: 10000  // Timeout for operations like AI processing (10 seconds)
} as const;