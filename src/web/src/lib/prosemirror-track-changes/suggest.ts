import { 
  Plugin, 
  PluginKey, 
  Transaction, 
  EditorState 
} from 'prosemirror-state'; // prosemirror-state v1.4.2

import { 
  Decoration, 
  DecorationSet, 
  EditorView 
} from 'prosemirror-view'; // prosemirror-view v1.30.2

import { 
  Fragment, 
  Mark, 
  Node, 
  Slice 
} from 'prosemirror-model'; // prosemirror-model v1.19.0

import { 
  Step, 
  ReplaceStep 
} from 'prosemirror-transform'; // prosemirror-transform v1.7.2

import { 
  findChangedNodes, 
  applyChange, 
  rejectChange 
} from './utils';

import { 
  TrackChangesState, 
  trackChangesPlugin 
} from './track-changes';

import { 
  Suggestion 
} from '../../types/suggestion';

// Constants for marks used in tracking changes
export const SUGGESTION_MARK = 'suggestion';

// Plugin key for accessing suggestion state
export const suggestionPluginKey = new PluginKey('suggestions');

/**
 * Class representing the state of suggestions in the editor
 */
export class SuggestionState {
  /**
   * Map of suggestion IDs to suggestion objects
   */
  suggestions: Map<string, Suggestion>;
  
  /**
   * Decorations for visualizing suggestions in the editor
   */
  decorations: DecorationSet;

  /**
   * Creates a new suggestion state
   * 
   * @param suggestions Map of suggestion IDs to suggestion objects
   * @param decorations Decoration set for visualizing suggestions
   */
  constructor(
    suggestions: Map<string, Suggestion> = new Map(),
    decorations: DecorationSet = DecorationSet.empty
  ) {
    this.suggestions = suggestions;
    this.decorations = decorations;
  }

  /**
   * Updates the suggestion state based on a transaction
   * 
   * @param tr Transaction to apply
   * @param state Editor state
   * @returns Updated suggestion state
   */
  apply(tr: Transaction, state: EditorState): SuggestionState {
    // Map decorations through document changes
    let decorations = this.decorations.map(tr.mapping, tr.doc);
    
    // Check if this transaction has suggestion-related metadata
    const suggestUpdate = tr.getMeta('suggestion');
    if (suggestUpdate) {
      // Create a new map to avoid mutating the existing one
      const suggestions = new Map(this.suggestions);
      
      // Update or delete the suggestion based on its status
      if (suggestUpdate.id) {
        if (suggestUpdate.deleted) {
          suggestions.delete(suggestUpdate.id);
        } else {
          suggestions.set(suggestUpdate.id, suggestUpdate);
        }
      }
      
      return new SuggestionState(suggestions, decorations);
    }

    // If the transaction doesn't change the document, return with mapped decorations
    if (!tr.docChanged) {
      return new SuggestionState(this.suggestions, decorations);
    }

    // For document changes, just update decorations and keep suggestions
    return new SuggestionState(this.suggestions, decorations);
  }

  /**
   * Adds a new suggestion to the state
   * 
   * @param suggestion The suggestion to add
   * @param from Starting position in the document
   * @param to Ending position in the document
   * @param doc The document to add the decoration to
   * @returns Updated suggestion state
   */
  addSuggestion(suggestion: Suggestion, from: number, to: number, doc: Node): SuggestionState {
    // Create a new map to avoid mutating the existing one
    const suggestions = new Map(this.suggestions);
    suggestions.set(suggestion.id, suggestion);
    
    // Create a decoration for the suggestion
    const decoration = createDecorationForSuggestion(suggestion, from, to);
    
    // Add the decoration to the set
    const decorations = this.decorations.add(doc, [decoration]);
    
    return new SuggestionState(suggestions, decorations);
  }

  /**
   * Removes a suggestion from the state
   * 
   * @param suggestionId ID of the suggestion to remove
   * @returns Updated suggestion state
   */
  removeSuggestion(suggestionId: string): SuggestionState {
    // Create a new map to avoid mutating the existing one
    const suggestions = new Map(this.suggestions);
    
    // Check if the suggestion exists before trying to delete it
    if (suggestions.has(suggestionId)) {
      suggestions.delete(suggestionId);
    
      // Remove decorations associated with this suggestion
      const decorations = this.decorations.remove(
        this.decorations.find(null, null, spec => spec['data-suggestion-id'] === suggestionId)
      );
      
      return new SuggestionState(suggestions, decorations);
    }
    
    // If the suggestion doesn't exist, return the current state
    return this;
  }

  /**
   * Gets a suggestion by ID
   * 
   * @param suggestionId ID of the suggestion to get
   * @returns The suggestion if found, otherwise undefined
   */
  getSuggestion(suggestionId: string): Suggestion | undefined {
    return this.suggestions.get(suggestionId);
  }
}

/**
 * Creates a new suggestion based on the provided text and metadata
 * 
 * @param text Text content for the suggestion
 * @param metadata Additional metadata for the suggestion
 * @returns A new suggestion object
 */
export function createSuggestion(
  text: string,
  metadata: object
): Suggestion {
  // Generate a unique ID for the suggestion
  const id = Math.random().toString(36).substring(2, 15);
  
  // Create suggestion object with required properties
  return {
    id,
    ...metadata,
    suggestedText: text,
    createdAt: new Date()
  } as Suggestion;
}

/**
 * Applies a suggestion to the document, replacing the target text with the suggested text
 * 
 * @param state The editor state
 * @param suggestion The suggestion to apply
 * @returns A transaction that applies the suggestion
 */
export function applySuggestionToDoc(
  state: EditorState,
  suggestion: Suggestion
): Transaction {
  const { from, to } = suggestion.position;
  let tr = state.tr;
  
  // Delete the original text in the specified range
  tr.delete(from, to);
  
  // Insert the suggested text at the same position
  tr.insertText(suggestion.suggestedText, from);
  
  // Mark the suggestion as accepted in the transaction metadata
  tr.setMeta('suggestion', {
    ...suggestion,
    status: 'accepted'
  });
  
  return tr;
}

/**
 * Rejects a suggestion, removing it from the document
 * 
 * @param state The editor state
 * @param suggestion The suggestion to reject
 * @returns A transaction that rejects the suggestion
 */
export function rejectSuggestionFromDoc(
  state: EditorState,
  suggestion: Suggestion
): Transaction {
  const { from, to } = suggestion.position;
  let tr = state.tr;
  
  // Find the mark type in the schema
  const suggestionMarkType = state.schema.marks[SUGGESTION_MARK];
  if (!suggestionMarkType) {
    throw new Error(`Mark type '${SUGGESTION_MARK}' not found in schema`);
  }
  
  // Remove the suggestion mark from the specified range
  tr.removeMark(from, to, suggestionMarkType);
  
  // Mark the suggestion as rejected in the transaction metadata
  tr.setMeta('suggestion', {
    ...suggestion,
    status: 'rejected'
  });
  
  return tr;
}

/**
 * Finds all suggestions within a given range of the document
 * 
 * @param state The editor state
 * @param from Starting position in the document
 * @param to Ending position in the document
 * @returns Array of suggestions with their positions
 */
export function findSuggestionsInRange(
  state: EditorState,
  from: number,
  to: number
): Array<{suggestion: Suggestion, from: number, to: number}> {
  const result: Array<{suggestion: Suggestion, from: number, to: number}> = [];
  const { doc } = state;
  
  // Traverse the document between the specified positions
  doc.nodesBetween(from, to, (node, pos) => {
    // Check each mark on the node
    node.marks.forEach(mark => {
      if (mark.type.name === SUGGESTION_MARK) {
        // Extract the suggestion data from the mark attributes
        const suggestion = {
          id: mark.attrs.id,
          originalText: mark.attrs.originalText,
          suggestedText: mark.attrs.suggestedText,
          position: {
            from: pos,
            to: pos + node.nodeSize
          },
          status: mark.attrs.status,
          // Include other required fields from the mark attributes or use defaults
          ...mark.attrs
        } as Suggestion;
        
        result.push({
          suggestion,
          from: pos,
          to: pos + node.nodeSize
        });
      }
    });
    
    return true; // Continue traversal
  });
  
  return result;
}

/**
 * Creates ProseMirror decorations to visually display a suggestion
 * 
 * @param suggestion The suggestion to create a decoration for
 * @param from Starting position in the document
 * @param to Ending position in the document
 * @returns A decoration object for the suggestion
 */
export function createDecorationForSuggestion(
  suggestion: Suggestion,
  from: number,
  to: number
): Decoration {
  // Determine the appropriate class based on the suggestion type
  let className = 'suggestion';
  if (suggestion.changeType === 'addition') {
    className += ' suggestion-addition';
  } else if (suggestion.changeType === 'deletion') {
    className += ' suggestion-deletion';
  } else if (suggestion.changeType === 'replacement') {
    className += ' suggestion-replacement';
  }
  
  // Create an inline decoration with appropriate attributes
  return Decoration.inline(from, to, {
    class: className,
    'data-suggestion-id': suggestion.id,
    'data-original-text': suggestion.originalText,
    'data-suggested-text': suggestion.suggestedText,
    'data-status': suggestion.status,
    title: suggestion.explanation || 'Suggested change'
  });
}

/**
 * Creates a ProseMirror plugin for handling suggestions
 * 
 * @returns A new plugin instance
 */
export function suggestionPlugin(): Plugin {
  return new Plugin({
    key: suggestionPluginKey,
    
    state: {
      // Initialize plugin state
      init(config, state) {
        return new SuggestionState();
      },
      
      // Apply changes to plugin state
      apply(tr, pluginState, oldState, newState) {
        return pluginState.apply(tr, newState);
      }
    },
    
    props: {
      // Provide decorations for rendering suggestions
      decorations(state) {
        return this.getState(state).decorations;
      }
    }
  });
}