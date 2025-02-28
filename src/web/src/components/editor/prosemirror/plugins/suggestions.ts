import { Plugin, PluginKey, EditorState, Transaction } from 'prosemirror-state'; // prosemirror-state v1.4.2
import { Decoration, DecorationSet } from 'prosemirror-view'; // prosemirror-view v1.30.0
import { Schema, Node } from 'prosemirror-model'; // prosemirror-model v1.19.0
import { v4 as uuidv4 } from 'uuid'; // uuid v8.3.2

import { trackChangesPluginKey } from '../../../lib/prosemirror-track-changes';
import { findDiffPositions } from '../../../lib/diffing';
import { computeDiff } from '../../../lib/diffing/text-diff';
import { Suggestion, SuggestionStatus, ChangeType } from '../../../types/suggestion';

/**
 * Plugin key for accessing suggestions plugin state
 */
export const suggestionsPluginKey = new PluginKey('suggestions');

/**
 * Class for managing the state of suggestions in the document
 */
export class SuggestionState {
  /**
   * Map of suggestion IDs to suggestion objects
   */
  suggestions: Map<string, Suggestion>;
  
  /**
   * Whether suggestions are currently active
   */
  active: boolean;

  /**
   * Creates a new SuggestionState instance
   * 
   * @param suggestions Map of suggestion IDs to suggestion objects
   * @param active Whether suggestions are active
   */
  constructor(
    suggestions: Map<string, Suggestion> = new Map(),
    active: boolean = true
  ) {
    this.suggestions = suggestions;
    this.active = active;
  }

  /**
   * Applies document changes to update suggestion positions
   * 
   * @param tr Transaction to apply
   * @returns Updated suggestion state
   */
  apply(tr: Transaction): SuggestionState {
    // Check if transaction has suggestion-specific metadata
    const meta = tr.getMeta(suggestionsPluginKey);
    
    // Handle adding a new suggestion
    if (meta?.addSuggestion) {
      const suggestion = meta.addSuggestion;
      return this.addSuggestion(suggestion.id, suggestion);
    }
    
    // Handle changing a suggestion's status
    if (meta?.updateStatus) {
      const { id, status } = meta.updateStatus;
      return this.updateSuggestionStatus(id, status);
    }
    
    // If document didn't change, return the current state
    if (!tr.docChanged) {
      return this;
    }
    
    // For document changes, we would need to adjust suggestion positions
    // This would be a complex implementation mapping positions through the transaction steps
    // For simplicity, we're returning the current state
    // A production implementation would use tr.mapping to adjust positions
    return this;
  }

  /**
   * Retrieves a suggestion by ID
   * 
   * @param id Suggestion ID
   * @returns The suggestion if found
   */
  getSuggestion(id: string): Suggestion | undefined {
    return this.suggestions.get(id);
  }

  /**
   * Adds a new suggestion to the state
   * 
   * @param id Suggestion ID
   * @param suggestion Suggestion to add
   * @returns Updated state with new suggestion
   */
  addSuggestion(id: string, suggestion: Suggestion): SuggestionState {
    const suggestions = new Map(this.suggestions);
    suggestions.set(id, suggestion);
    return new SuggestionState(suggestions, this.active);
  }

  /**
   * Updates the status of a suggestion
   * 
   * @param id Suggestion ID
   * @param status New status
   * @returns Updated state with new status
   */
  updateSuggestionStatus(id: string, status: SuggestionStatus): SuggestionState {
    const suggestion = this.suggestions.get(id);
    if (!suggestion) return this;
    
    const suggestions = new Map(this.suggestions);
    suggestions.set(id, { ...suggestion, status });
    return new SuggestionState(suggestions, this.active);
  }

  /**
   * Gets all suggestions with PENDING status
   * 
   * @returns Array of pending suggestions
   */
  getPendingSuggestions(): Suggestion[] {
    return Array.from(this.suggestions.values())
      .filter(suggestion => suggestion.status === SuggestionStatus.PENDING);
  }
}

/**
 * Creates a ProseMirror plugin for managing and displaying AI-generated suggestions
 * in the document editor
 * 
 * @param options Configuration options
 * @returns Configured ProseMirror plugin for suggestions
 */
export function createSuggestionsPlugin(options = {}): Plugin {
  return new Plugin({
    key: suggestionsPluginKey,
    
    state: {
      init() {
        return new SuggestionState();
      },
      apply(tr, pluginState, oldState, newState) {
        return pluginState.apply(tr);
      }
    },
    
    props: {
      decorations(state) {
        return getSuggestionDecorations(state);
      }
    },
    
    view(editorView) {
      return {
        update: (view, prevState) => {
          // Refresh decorations when document changes
          if (view.state.doc !== prevState.doc) {
            // The track changes plugin might need to update when our suggestions change
            const trackChangesState = trackChangesPluginKey.getState(view.state);
            if (trackChangesState) {
              view.updateState(view.state);
            }
          }
        }
      };
    }
  });
}

/**
 * Applies a suggestion to the document, accepting the suggested change
 * 
 * @param state Editor state
 * @param suggestionId ID of the suggestion to apply
 * @returns Transaction that applies the suggestion
 */
export function applySuggestion(state: EditorState, suggestionId: string): Transaction {
  const pluginState = suggestionsPluginKey.getState(state) as SuggestionState;
  const suggestion = pluginState.getSuggestion(suggestionId);
  
  if (!suggestion) {
    console.warn(`Suggestion with ID ${suggestionId} not found`);
    return state.tr;
  }
  
  let tr = state.tr;
  const { from, to } = suggestion.position;
  
  // Replace original text with suggested text
  tr.replaceWith(from, to, state.schema.text(suggestion.suggestedText));
  
  // Update suggestion status
  tr.setMeta(suggestionsPluginKey, {
    updateStatus: {
      id: suggestionId,
      status: SuggestionStatus.ACCEPTED
    }
  });
  
  return tr;
}

/**
 * Rejects a suggestion, removing it from the document without applying changes
 * 
 * @param state Editor state
 * @param suggestionId ID of the suggestion to reject
 * @returns Transaction that rejects the suggestion
 */
export function rejectSuggestion(state: EditorState, suggestionId: string): Transaction {
  const pluginState = suggestionsPluginKey.getState(state) as SuggestionState;
  const suggestion = pluginState.getSuggestion(suggestionId);
  
  if (!suggestion) {
    console.warn(`Suggestion with ID ${suggestionId} not found`);
    return state.tr;
  }
  
  let tr = state.tr;
  
  // Update suggestion status
  tr.setMeta(suggestionsPluginKey, {
    updateStatus: {
      id: suggestionId,
      status: SuggestionStatus.REJECTED
    }
  });
  
  return tr;
}

/**
 * Creates decorations for displaying suggestions in the editor
 * 
 * @param state Editor state
 * @returns Set of decorations for all active suggestions
 */
export function getSuggestionDecorations(state: EditorState): DecorationSet {
  const pluginState = suggestionsPluginKey.getState(state) as SuggestionState;
  if (!pluginState || !pluginState.active) {
    return DecorationSet.empty;
  }
  
  const { doc } = state;
  const decorations: Decoration[] = [];
  
  // Process each pending suggestion
  for (const suggestion of pluginState.getPendingSuggestions()) {
    const { from, to } = suggestion.position;
    
    switch (suggestion.changeType) {
      case ChangeType.DELETION:
        // Style deleted text with red strikethrough
        decorations.push(Decoration.inline(from, to, {
          class: 'suggestion-deletion',
          'data-suggestion-id': suggestion.id,
          title: `Suggested deletion: ${suggestion.explanation || 'Delete this text'}`
        }));
        break;
        
      case ChangeType.ADDITION:
        // Style added text with green underline
        decorations.push(Decoration.inline(from, to, {
          class: 'suggestion-addition',
          'data-suggestion-id': suggestion.id,
          title: `Suggested addition: ${suggestion.explanation || 'Add this text'}`
        }));
        break;
        
      case ChangeType.REPLACEMENT:
        // Style the original text as deleted
        decorations.push(Decoration.inline(from, to, {
          class: 'suggestion-deletion',
          'data-suggestion-id': suggestion.id,
          title: `Original text: ${suggestion.originalText}`
        }));
        
        // Add a widget to show the suggested replacement
        decorations.push(Decoration.widget(to, (view) => {
          const span = document.createElement('span');
          span.className = 'suggestion-addition suggestion-replacement';
          span.setAttribute('data-suggestion-id', suggestion.id);
          span.setAttribute('title', `Suggested replacement: ${suggestion.explanation || 'Replace with this text'}`);
          span.textContent = suggestion.suggestedText;
          return span;
        }));
        break;
        
      case ChangeType.FORMATTING:
        // Style formatting changes with a highlight
        decorations.push(Decoration.inline(from, to, {
          class: 'suggestion-formatting',
          'data-suggestion-id': suggestion.id,
          title: `Suggested formatting: ${suggestion.explanation || 'Format this text'}`
        }));
        break;
    }
  }
  
  return DecorationSet.create(doc, decorations);
}

/**
 * Adds a new suggestion to the document based on AI recommendation
 * 
 * @param state Editor state
 * @param suggestion Suggestion data
 * @returns Transaction that adds the suggestion
 */
export function addSuggestion(state: EditorState, suggestion: Suggestion): Transaction {
  const tr = state.tr;
  
  // Generate unique ID if not provided
  const suggestionWithId = suggestion.id ? suggestion : {
    ...suggestion,
    id: uuidv4()
  };
  
  // Set metadata for the plugin to process
  tr.setMeta(suggestionsPluginKey, {
    addSuggestion: suggestionWithId
  });
  
  return tr;
}

/**
 * Accepts all pending suggestions in the document
 * 
 * @param state Editor state
 * @returns Transaction that applies all suggestions
 */
export function acceptAllSuggestions(state: EditorState): Transaction {
  const pluginState = suggestionsPluginKey.getState(state) as SuggestionState;
  const pendingSuggestions = pluginState.getPendingSuggestions();
  
  let tr = state.tr;
  
  // Sort suggestions in reverse order by position to avoid position shifts
  // when applying multiple changes
  const sortedSuggestions = [...pendingSuggestions]
    .sort((a, b) => b.position.from - a.position.from);
  
  // Apply each suggestion
  for (const suggestion of sortedSuggestions) {
    const { from, to } = suggestion.position;
    
    // Apply the appropriate change based on suggestion type
    switch (suggestion.changeType) {
      case ChangeType.ADDITION:
      case ChangeType.REPLACEMENT:
      case ChangeType.FORMATTING:
        tr.replaceWith(from, to, state.schema.text(suggestion.suggestedText));
        break;
        
      case ChangeType.DELETION:
        tr.delete(from, to);
        break;
    }
    
    // Update suggestion status
    tr.setMeta(suggestionsPluginKey, {
      updateStatus: {
        id: suggestion.id,
        status: SuggestionStatus.ACCEPTED
      }
    });
  }
  
  return tr;
}

/**
 * Rejects all pending suggestions in the document
 * 
 * @param state Editor state
 * @returns Transaction that rejects all suggestions
 */
export function rejectAllSuggestions(state: EditorState): Transaction {
  const pluginState = suggestionsPluginKey.getState(state) as SuggestionState;
  const pendingSuggestions = pluginState.getPendingSuggestions();
  
  let tr = state.tr;
  
  // Update all suggestions to rejected status
  for (const suggestion of pendingSuggestions) {
    tr.setMeta(suggestionsPluginKey, {
      updateStatus: {
        id: suggestion.id,
        status: SuggestionStatus.REJECTED
      }
    });
  }
  
  return tr;
}