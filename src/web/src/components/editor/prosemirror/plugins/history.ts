import { history, undo, redo } from 'prosemirror-history'; // v1.3.0
import { Plugin, PluginKey } from 'prosemirror-state'; // v1.4.2
import { keymap } from 'prosemirror-keymap'; // v1.2.0

import { trackChangesPluginKey } from './track-changes';

/**
 * Plugin key for accessing history plugin state
 */
export const historyPluginKey = new PluginKey('history');

/**
 * Creates a history plugin that integrates with track changes functionality
 * 
 * @param options Configuration options for the history plugin
 * @returns Configured history plugin
 */
export function createHistoryPlugin(options = {}): Plugin {
  // Default options with reasonable values
  const defaultOptions = {
    depth: 100, // Maximum history depth
    newGroupDelay: 500 // Time in ms for changes to be grouped in history
  };

  // Merge default options with provided options
  const finalOptions = { ...defaultOptions, ...options };

  // Create and return configured history plugin
  return history({
    ...finalOptions,
    // Custom function to determine if a new history group should be started
    // This ensures track changes operations are properly grouped
    groupSelectionChanges: false,
    // Function to determine if transaction should be added to history
    addToHistory: (tr) => {
      // Don't add track changes meta transactions to history
      // This prevents undoing the internal track changes state transitions
      if (tr.getMeta(trackChangesPluginKey)) {
        return false;
      }
      
      // Use default behavior for other transactions
      return tr.docChanged && !tr.getMeta("addToHistory") === false;
    }
  });
}

/**
 * Custom undo command that preserves track changes context
 * 
 * @param state Editor state
 * @param dispatch Function to dispatch transactions
 * @param view Editor view
 * @returns Whether the command was executed
 */
export function customUndoCommand(state, dispatch, view) {
  // Get current track changes state
  const trackChangesState = trackChangesPluginKey.getState(state);
  
  // Execute standard undo command
  const result = undo(state, (tr) => {
    if (dispatch) {
      // If track changes is enabled, make sure we preserve its state
      if (trackChangesState && trackChangesState.enabled) {
        // After undo, ensure track changes decorations are preserved
        const newTr = tr.setMeta(trackChangesPluginKey, {
          type: 'preserveDecorations',
          decorations: trackChangesState.decorations
        });
        
        // Dispatch the transaction with preserved track changes state
        dispatch(newTr);
      } else {
        // No track changes to preserve, dispatch as-is
        dispatch(tr);
      }
    }
  }, view);
  
  return result;
}

/**
 * Custom redo command that preserves track changes context
 * 
 * @param state Editor state
 * @param dispatch Function to dispatch transactions
 * @param view Editor view
 * @returns Whether the command was executed
 */
export function customRedoCommand(state, dispatch, view) {
  // Get current track changes state
  const trackChangesState = trackChangesPluginKey.getState(state);
  
  // Execute standard redo command
  const result = redo(state, (tr) => {
    if (dispatch) {
      // If track changes is enabled, make sure we preserve its state
      if (trackChangesState && trackChangesState.enabled) {
        // After redo, ensure track changes decorations are preserved
        const newTr = tr.setMeta(trackChangesPluginKey, {
          type: 'preserveDecorations',
          decorations: trackChangesState.decorations
        });
        
        // Dispatch the transaction with preserved track changes state
        dispatch(newTr);
      } else {
        // No track changes to preserve, dispatch as-is
        dispatch(tr);
      }
    }
  }, view);
  
  return result;
}

/**
 * Keyboard shortcuts for history commands (undo/redo)
 */
export const historyKeymap = keymap({
  'Mod-z': customUndoCommand,
  'Mod-y': customRedoCommand,
  'Shift-Mod-z': customRedoCommand // Standard alternative for redo
});

/**
 * Default configured history plugin ready for use in the editor
 */
export const historyPlugin = createHistoryPlugin();

/**
 * Exports all history-related functionality
 */
export {
  customUndoCommand,
  customRedoCommand,
  createHistoryPlugin,
  historyPluginKey,
  historyKeymap,
  historyPlugin
};