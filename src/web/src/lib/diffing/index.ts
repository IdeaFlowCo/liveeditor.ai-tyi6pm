/**
 * Text differencing utilities for the track changes functionality
 * 
 * This module re-exports functions and types from the text-diff module to provide
 * a clean interface for comparing original text with AI-suggested modifications.
 * @module diffing
 */

// Re-export all required functions and constants from text-diff.ts
export {
  computeDiff,
  formatDiffAsHTML,
  formatDiffForEditor,
  applyChangesToText,
  diffToPlainText,
  getChangeStatistics,
  findChangeAtPosition,
  generateChangeId,
  DEFAULT_DIFF_OPTIONS
} from './text-diff';

// Note: We only re-export what's needed by the public API
// Types are automatically exported with their respective functions