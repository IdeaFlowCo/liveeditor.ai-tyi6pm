/**
 * Entry point for the ProseMirror track changes module
 * 
 * This module provides Microsoft Word-style track changes functionality for
 * the ProseMirror editor, enabling visualization and review of text changes.
 * It's designed specifically for reviewing, accepting, and rejecting AI-suggested
 * improvements in the document editor.
 * 
 * @module prosemirror-track-changes
 * @version 1.0.0
 */

// Import all from track-changes module
import * as trackChanges from './track-changes';

// Import all from utils module
import * as utils from './utils';

// Import all from suggest module
import * as suggest from './suggest';

// Re-export the core track changes functionality
export const trackChangesPlugin = trackChanges.trackChangesPlugin;
export const TrackChangesState = trackChanges.TrackChangesState;

// Re-export change management functions
export const createChangeSet = trackChanges.createChangeSet;
export const applyChangeSet = trackChanges.applyChangeSet;
export const acceptChange = trackChanges.acceptChange;
export const rejectChange = trackChanges.rejectChange;
export const acceptAllChanges = trackChanges.acceptAllChanges;
export const rejectAllChanges = trackChanges.rejectAllChanges;
export const findChangesInRange = trackChanges.findChangesInRange;
export const createChangeDecorations = trackChanges.createChangeDecorations;

// Re-export suggestion related functionality
export const suggestionPlugin = suggest.suggestionPlugin();
export const SuggestionState = suggest.SuggestionState;
export const createSuggestion = suggest.createSuggestion;
export const applySuggestionToDoc = suggest.applySuggestionToDoc;
export const rejectSuggestionFromDoc = suggest.rejectSuggestionFromDoc;
export const findSuggestionsInRange = suggest.findSuggestionsInRange;

// Re-export important constants
export const SUGGESTION_MARK_TYPE = utils.SUGGESTION_MARK_TYPE;

// Re-export types and interfaces
export type { ChangeType } from './track-changes';