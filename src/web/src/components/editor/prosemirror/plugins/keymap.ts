import { keymap } from 'prosemirror-keymap'; // v1.2.0
import { Plugin, PluginKey, TextSelection, EditorState, Transaction } from 'prosemirror-state'; // v1.4.2
import { baseKeymap, toggleMark, setBlockType, wrapIn } from 'prosemirror-commands'; // v1.5.1

import { schema } from '../schema';
import { trackChangesPluginKey, applyTrackedChange } from './track-changes';
import { KEYBOARD_SHORTCUTS } from '../../../constants/editor';

// Plugin key for accessing keymap plugin state
export const keymapPluginKey = new PluginKey('keymap');

/**
 * Creates a configured keymap plugin with keyboard shortcuts for the editor
 * @param options Configuration options for the keymap plugin
 * @returns Configured keymap plugin with custom keyboard shortcuts
 */
export function createKeymapPlugin(options: { onSave?: (state: EditorState) => void } = {}): Plugin {
  // Start with basic keymap from prosemirror-commands
  const baseKeyBindings = { ...baseKeymap };

  // Add formatting shortcuts
  const formattingKeyBindings = {
    [KEYBOARD_SHORTCUTS.BOLD]: toggleMark(schema.marks.strong),
    [KEYBOARD_SHORTCUTS.ITALIC]: toggleMark(schema.marks.em),
    [KEYBOARD_SHORTCUTS.UNDERLINE]: toggleMark(schema.marks.underline)
  };

  // Add paragraph style shortcuts
  const paragraphKeyBindings = {
    'Shift-Ctrl-1': setBlockType(schema.nodes.heading, { level: 1 }),
    'Shift-Ctrl-2': setBlockType(schema.nodes.heading, { level: 2 }),
    'Shift-Ctrl-3': setBlockType(schema.nodes.heading, { level: 3 }),
    'Shift-Ctrl-[': wrapIn(schema.nodes.bullet_list),
    'Shift-Ctrl-]': wrapIn(schema.nodes.ordered_list),
    'Shift-Ctrl->': wrapIn(schema.nodes.blockquote)
  };

  // Add track changes shortcuts
  const trackChangesKeyBindings = {
    [KEYBOARD_SHORTCUTS.ACCEPT_SUGGESTION]: acceptCurrentSuggestion,
    [KEYBOARD_SHORTCUTS.REJECT_SUGGESTION]: rejectCurrentSuggestion,
    [KEYBOARD_SHORTCUTS.NEXT_SUGGESTION]: navigateToNextSuggestion,
    [KEYBOARD_SHORTCUTS.PREV_SUGGESTION]: navigateToPrevSuggestion
  };

  // Add document-level shortcuts
  const documentKeyBindings: Record<string, any> = {
    'Mod-z': baseKeyBindings['Mod-z'], // Undo
    'Shift-Mod-z': baseKeyBindings['Shift-Mod-z'], // Redo
  };

  // If onSave callback is provided, add save shortcut
  if (options.onSave) {
    documentKeyBindings[KEYBOARD_SHORTCUTS.SAVE] = (state: EditorState, dispatch: ((tr: Transaction) => void) | null) => {
      options.onSave(state);
      return true;
    };
  }

  // Combine all shortcuts
  const allKeyBindings = {
    ...baseKeyBindings,
    ...formattingKeyBindings,
    ...paragraphKeyBindings,
    ...trackChangesKeyBindings,
    ...documentKeyBindings
  };

  // Create and return the keymap plugin
  return keymap(allKeyBindings);
}

/**
 * Command to accept the currently selected or focused suggestion
 * @param state The editor state
 * @param dispatch The dispatch function
 * @param view The editor view
 * @returns Whether the command was executed
 */
export function acceptCurrentSuggestion(state: EditorState, dispatch: ((tr: Transaction) => void) | null, view?: any): boolean {
  const trackChangesState = trackChangesPluginKey.getState(state);
  if (!trackChangesState) return false;

  const suggestion = getCurrentSuggestion(state);
  if (!suggestion) return false;

  if (dispatch) {
    dispatch(applyTrackedChange(state, suggestion.id, true));
  }
  return true;
}

/**
 * Command to reject the currently selected or focused suggestion
 * @param state The editor state
 * @param dispatch The dispatch function
 * @param view The editor view
 * @returns Whether the command was executed
 */
export function rejectCurrentSuggestion(state: EditorState, dispatch: ((tr: Transaction) => void) | null, view?: any): boolean {
  const trackChangesState = trackChangesPluginKey.getState(state);
  if (!trackChangesState) return false;

  const suggestion = getCurrentSuggestion(state);
  if (!suggestion) return false;

  if (dispatch) {
    dispatch(applyTrackedChange(state, suggestion.id, false));
  }
  return true;
}

/**
 * Command to navigate to the next suggestion in the document
 * @param state The editor state
 * @param dispatch The dispatch function
 * @param view The editor view
 * @returns Whether the command was executed
 */
export function navigateToNextSuggestion(state: EditorState, dispatch: ((tr: Transaction) => void) | null, view?: any): boolean {
  const trackChangesState = trackChangesPluginKey.getState(state);
  if (!trackChangesState) return false;

  const allSuggestions = trackChangesState.getChanges();
  if (!allSuggestions.length) return false;

  const { selection } = state;
  const currentPos = selection.from;
  
  // Find the next suggestion after current position
  const nextSuggestion = allSuggestions.find(suggestion => suggestion.from > currentPos);
  if (!nextSuggestion) return false;

  if (dispatch) {
    const tr = state.tr.setSelection(
      TextSelection.create(state.doc, nextSuggestion.from, nextSuggestion.to)
    );
    dispatch(tr);
    
    // Focus editor if view is available
    if (view) {
      view.focus();
    }
  }
  
  return true;
}

/**
 * Command to navigate to the previous suggestion in the document
 * @param state The editor state
 * @param dispatch The dispatch function
 * @param view The editor view
 * @returns Whether the command was executed
 */
export function navigateToPrevSuggestion(state: EditorState, dispatch: ((tr: Transaction) => void) | null, view?: any): boolean {
  const trackChangesState = trackChangesPluginKey.getState(state);
  if (!trackChangesState) return false;

  const allSuggestions = trackChangesState.getChanges();
  if (!allSuggestions.length) return false;

  const { selection } = state;
  const currentPos = selection.from;
  
  // Find all suggestions before current position, and get the last one
  const prevSuggestions = allSuggestions
    .filter(suggestion => suggestion.to < currentPos)
    .sort((a, b) => b.from - a.from);
  
  const prevSuggestion = prevSuggestions[0];
  if (!prevSuggestion) return false;

  if (dispatch) {
    const tr = state.tr.setSelection(
      TextSelection.create(state.doc, prevSuggestion.from, prevSuggestion.to)
    );
    dispatch(tr);
    
    // Focus editor if view is available
    if (view) {
      view.focus();
    }
  }
  
  return true;
}

/**
 * Helper function to get the current suggestion based on selection or cursor position
 * @param state The editor state
 * @returns The current suggestion or null if none is selected
 */
function getCurrentSuggestion(state: EditorState) {
  const trackChangesState = trackChangesPluginKey.getState(state);
  if (!trackChangesState) return null;

  const { selection } = state;
  const allSuggestions = trackChangesState.getChanges();
  
  // Find a suggestion that overlaps with the current selection
  return allSuggestions.find(suggestion => 
    suggestion.from <= selection.to && suggestion.to >= selection.from
  );
}

export {
  acceptCurrentSuggestion,
  rejectCurrentSuggestion,
  navigateToNextSuggestion,
  navigateToPrevSuggestion
};