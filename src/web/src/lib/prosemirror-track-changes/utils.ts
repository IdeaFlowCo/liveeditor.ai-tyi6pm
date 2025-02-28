import { Suggestion, SuggestionStatus, Position } from '../../../types/suggestion';
import { computeDiff } from '../../diffing/text-diff';
import { Schema, Mark, Node, Fragment, MarkType } from 'prosemirror-model'; // prosemirror-model v1.19.0
import { EditorState, Transaction } from 'prosemirror-state'; // prosemirror-state v1.4.2
import { Decoration, DecorationSet } from 'prosemirror-view'; // prosemirror-view v1.30.2
import { v4 as uuidv4 } from 'uuid'; // uuid v8.3.2

// Constants
export const SUGGESTION_MARK_TYPE = 'suggestion';
const DELETION_CLASS = 'suggestion-deletion';
const ADDITION_CLASS = 'suggestion-addition';

/**
 * Creates a ProseMirror mark for a suggestion with the appropriate attributes
 * 
 * @param schema The ProseMirror schema containing mark types
 * @param suggestion The suggestion data to store in the mark
 * @returns A ProseMirror mark with suggestion attributes
 */
export function createSuggestionMark(schema: Schema, suggestion: Suggestion): Mark {
  const suggestionMarkType = schema.marks[SUGGESTION_MARK_TYPE];
  if (!suggestionMarkType) {
    throw new Error(`Mark type '${SUGGESTION_MARK_TYPE}' not found in schema`);
  }
  
  return suggestionMarkType.create({
    id: suggestion.id,
    originalText: suggestion.originalText,
    suggestedText: suggestion.suggestedText,
    status: suggestion.status
  });
}

/**
 * Finds all suggestion marks in a document or document fragment
 * 
 * @param docOrFrag The document or fragment to search for suggestion marks
 * @returns Array of suggestion marks with their positions
 */
export function findSuggestionMarks(
  docOrFrag: Node | Fragment
): Array<{ mark: Mark, from: number, to: number }> {
  const result: Array<{ mark: Mark, from: number, to: number }> = [];
  
  if (docOrFrag instanceof Node) {
    docOrFrag.descendants((node, pos) => {
      // Check if the node has any suggestion marks
      const suggestionMarks = node.marks.filter(mark => 
        mark.type.name === SUGGESTION_MARK_TYPE
      );
      
      if (suggestionMarks.length > 0) {
        for (const mark of suggestionMarks) {
          result.push({
            mark,
            from: pos,
            to: pos + node.nodeSize
          });
        }
      }
      
      return true; // Continue traversal
    });
  } else {
    // For fragments, we need to process each node
    let pos = 0;
    docOrFrag.forEach((node, offset) => {
      node.descendants((childNode, childPos) => {
        const absolutePos = pos + offset + childPos;
        
        const suggestionMarks = childNode.marks.filter(mark => 
          mark.type.name === SUGGESTION_MARK_TYPE
        );
        
        if (suggestionMarks.length > 0) {
          for (const mark of suggestionMarks) {
            result.push({
              mark,
              from: absolutePos,
              to: absolutePos + childNode.nodeSize
            });
          }
        }
        
        return true;
      });
      pos += node.nodeSize;
    });
  }
  
  return result;
}

/**
 * Finds nodes in the document that have suggestion marks, representing changes
 * 
 * @param state The editor state containing the document
 * @returns Array of changed nodes with their suggestion marks and positions
 */
export function findChangedNodes(
  state: EditorState
): Array<{ node: Node, mark: Mark, from: number, to: number }> {
  const result: Array<{ node: Node, mark: Mark, from: number, to: number }> = [];
  const { doc } = state;
  
  doc.descendants((node, pos) => {
    // Find all suggestion marks on this node
    const suggestionMarks = node.marks.filter(mark => 
      mark.type.name === SUGGESTION_MARK_TYPE
    );
    
    if (suggestionMarks.length > 0) {
      for (const mark of suggestionMarks) {
        result.push({
          node,
          mark,
          from: pos,
          to: pos + node.nodeSize
        });
      }
    }
    
    return true; // Continue traversal
  });
  
  return result;
}

/**
 * Creates a transaction to apply a suggestion to the document,
 * replacing the original text with the suggested text
 * 
 * @param state The editor state
 * @param suggestion The suggestion to apply
 * @returns A transaction that applies the suggestion
 */
export function applySuggestionToDocument(
  state: EditorState,
  suggestion: Suggestion
): Transaction {
  const { from, to } = suggestion.position;
  let tr = state.tr;
  
  // Delete the original text in the specified range
  tr.delete(from, to);
  
  // Insert the suggested text at the same position
  tr.insertText(suggestion.suggestedText, from);
  
  // Update the suggestion status to ACCEPTED
  const updatedSuggestion = {
    ...suggestion,
    status: SuggestionStatus.ACCEPTED
  };
  
  // Store the updated suggestion state in the transaction metadata
  tr.setMeta('suggestionUpdate', updatedSuggestion);
  
  return tr;
}

/**
 * Creates a transaction to reject a suggestion by removing its markup
 * while keeping the original text
 * 
 * @param state The editor state
 * @param suggestion The suggestion to reject
 * @returns A transaction that rejects the suggestion
 */
export function rejectSuggestion(
  state: EditorState,
  suggestion: Suggestion
): Transaction {
  const { from, to } = suggestion.position;
  let tr = state.tr;
  
  // Find the mark type in the schema
  const suggestionMarkType = state.schema.marks[SUGGESTION_MARK_TYPE];
  if (!suggestionMarkType) {
    throw new Error(`Mark type '${SUGGESTION_MARK_TYPE}' not found in schema`);
  }
  
  // Remove the suggestion mark from the specified range
  tr.removeMark(from, to, suggestionMarkType);
  
  // Update the suggestion status to REJECTED
  const updatedSuggestion = {
    ...suggestion,
    status: SuggestionStatus.REJECTED
  };
  
  // Store the updated suggestion state in the transaction metadata
  tr.setMeta('suggestionUpdate', updatedSuggestion);
  
  return tr;
}

/**
 * Generates a character-level diff between original and suggested text
 * using the computeDiff utility
 * 
 * @param originalText The original text before changes
 * @param suggestedText The suggested text with changes
 * @returns Array of diff operations
 */
export function diffTexts(
  originalText: string,
  suggestedText: string
): Array<{value: string, added?: boolean, removed?: boolean}> {
  const diff = computeDiff(originalText, suggestedText);
  const result: Array<{value: string, added?: boolean, removed?: boolean}> = [];
  
  // Transform the diff result into a standard format
  for (const part of diff) {
    if (part.type === 'addition') {
      result.push({ value: part.text, added: true });
    } else if (part.type === 'deletion') {
      result.push({ value: part.text, removed: true });
    } else { // unchanged
      result.push({ value: part.text });
    }
  }
  
  return result;
}

/**
 * Finds a suggestion at the given document position
 * 
 * @param state The editor state
 * @param pos The position in the document to check
 * @returns Suggestion at the position or null if none found
 */
export function getSuggestionAt(
  state: EditorState,
  pos: number
): Suggestion | null {
  const { doc } = state;
  const $pos = doc.resolve(pos);
  
  // Check if we're directly at a node with a suggestion mark
  const node = doc.nodeAt(pos);
  if (node) {
    const suggestionMarks = node.marks.filter(mark => 
      mark.type.name === SUGGESTION_MARK_TYPE
    );
    
    if (suggestionMarks.length > 0) {
      const mark = suggestionMarks[0];
      return {
        id: mark.attrs.id,
        originalText: mark.attrs.originalText,
        suggestedText: mark.attrs.suggestedText,
        position: {
          from: pos,
          to: pos + node.nodeSize
        },
        status: mark.attrs.status
      };
    }
  }
  
  // Check if the position is between nodes with suggestion marks
  // Try the node before the position
  const nodeBefore = $pos.nodeBefore;
  if (nodeBefore) {
    const suggestionMarks = nodeBefore.marks.filter(mark => 
      mark.type.name === SUGGESTION_MARK_TYPE
    );
    
    if (suggestionMarks.length > 0) {
      const mark = suggestionMarks[0];
      const from = pos - nodeBefore.nodeSize;
      
      return {
        id: mark.attrs.id,
        originalText: mark.attrs.originalText,
        suggestedText: mark.attrs.suggestedText,
        position: {
          from,
          to: pos
        },
        status: mark.attrs.status
      };
    }
  }
  
  // Try the node after the position
  const nodeAfter = $pos.nodeAfter;
  if (nodeAfter) {
    const suggestionMarks = nodeAfter.marks.filter(mark => 
      mark.type.name === SUGGESTION_MARK_TYPE
    );
    
    if (suggestionMarks.length > 0) {
      const mark = suggestionMarks[0];
      
      return {
        id: mark.attrs.id,
        originalText: mark.attrs.originalText,
        suggestedText: mark.attrs.suggestedText,
        position: {
          from: pos,
          to: pos + nodeAfter.nodeSize
        },
        status: mark.attrs.status
      };
    }
  }
  
  return null;
}

/**
 * Extracts all suggestions from the document
 * 
 * @param state The editor state containing the document
 * @returns Array of all suggestions in the document
 */
export function getAllSuggestions(state: EditorState): Array<Suggestion> {
  const { doc } = state;
  const suggestions: Suggestion[] = [];
  const seenIds = new Set<string>(); // To avoid duplicates
  
  // Find all suggestion marks in the document
  const marksWithPos = findSuggestionMarks(doc);
  
  // Convert marks to suggestion objects
  for (const { mark, from, to } of marksWithPos) {
    const id = mark.attrs.id;
    
    // Skip if we've already processed this suggestion
    if (seenIds.has(id)) {
      continue;
    }
    
    seenIds.add(id);
    
    // Create a suggestion object from the mark's attributes
    suggestions.push({
      id,
      originalText: mark.attrs.originalText,
      suggestedText: mark.attrs.suggestedText,
      position: { from, to },
      status: mark.attrs.status
    });
  }
  
  return suggestions;
}

/**
 * Finds all suggestions within a given document range
 * 
 * @param state The editor state
 * @param from Start position of the range
 * @param to End position of the range
 * @returns Array of suggestions within the range
 */
export function findSuggestionsInRange(
  state: EditorState,
  from: number,
  to: number
): Array<Suggestion> {
  const { doc } = state;
  const suggestions: Suggestion[] = [];
  const seenIds = new Set<string>(); // To avoid duplicates
  
  // Create a slice of the document for the specified range
  const slice = doc.slice(from, to);
  
  // Find suggestion marks in the slice
  const marksWithPos = findSuggestionMarks(slice.content);
  
  // Convert marks to suggestion objects, adjusting positions relative to the range start
  for (const { mark, from: markFrom, to: markTo } of marksWithPos) {
    const id = mark.attrs.id;
    
    // Skip if we've already processed this suggestion
    if (seenIds.has(id)) {
      continue;
    }
    
    seenIds.add(id);
    
    // Adjust positions to be relative to the original document
    const adjustedFrom = from + markFrom;
    const adjustedTo = from + markTo;
    
    // Create a suggestion object from the mark's attributes
    suggestions.push({
      id,
      originalText: mark.attrs.originalText,
      suggestedText: mark.attrs.suggestedText,
      position: { from: adjustedFrom, to: adjustedTo },
      status: mark.attrs.status
    });
  }
  
  return suggestions;
}

/**
 * Creates a transaction to accept all suggestions in the document
 * 
 * @param state The editor state
 * @returns A transaction that accepts all suggestions
 */
export function acceptAllChanges(state: EditorState): Transaction {
  const suggestions = getAllSuggestions(state);
  
  // Start with a new transaction
  let tr = state.tr;
  
  // Process suggestions in reverse order to maintain positions
  // (from last to first in the document)
  const sortedSuggestions = [...suggestions].sort(
    (a, b) => b.position.from - a.position.from
  );
  
  for (const suggestion of sortedSuggestions) {
    // Only process pending suggestions
    if (suggestion.status !== SuggestionStatus.PENDING) {
      continue;
    }
    
    const { from, to } = suggestion.position;
    
    // Delete the original text and insert the suggested text
    tr.delete(from, to);
    tr.insertText(suggestion.suggestedText, from);
    
    // Update the suggestion status
    const updatedSuggestion = {
      ...suggestion,
      status: SuggestionStatus.ACCEPTED
    };
    
    // Store the updated suggestion status
    tr.setMeta('suggestionUpdate', updatedSuggestion);
  }
  
  return tr;
}

/**
 * Creates a transaction to reject all suggestions in the document
 * 
 * @param state The editor state
 * @returns A transaction that rejects all suggestions
 */
export function rejectAllChanges(state: EditorState): Transaction {
  const suggestions = getAllSuggestions(state);
  const suggestionMarkType = state.schema.marks[SUGGESTION_MARK_TYPE];
  
  if (!suggestionMarkType) {
    throw new Error(`Mark type '${SUGGESTION_MARK_TYPE}' not found in schema`);
  }
  
  // Start with a new transaction
  let tr = state.tr;
  
  // Process suggestions in reverse order to maintain positions
  const sortedSuggestions = [...suggestions].sort(
    (a, b) => b.position.from - a.position.from
  );
  
  for (const suggestion of sortedSuggestions) {
    // Only process pending suggestions
    if (suggestion.status !== SuggestionStatus.PENDING) {
      continue;
    }
    
    const { from, to } = suggestion.position;
    
    // Remove the suggestion mark, keeping the original text
    tr.removeMark(from, to, suggestionMarkType);
    
    // Update the suggestion status
    const updatedSuggestion = {
      ...suggestion,
      status: SuggestionStatus.REJECTED
    };
    
    // Store the updated suggestion status
    tr.setMeta('suggestionUpdate', updatedSuggestion);
  }
  
  return tr;
}

/**
 * Creates visual decorations for rendering suggestions in the editor
 * 
 * @param state The editor state
 * @returns Set of decorations for all suggestions
 */
export function createSuggestionDecorations(state: EditorState): DecorationSet {
  const { doc } = state;
  const decorations: Decoration[] = [];
  
  // Find all suggestion marks in the document
  const changedNodes = findChangedNodes(state);
  
  // Create decorations for each suggestion
  for (const { mark, from, to } of changedNodes) {
    // Skip decorations for accepted or rejected suggestions
    if (mark.attrs.status !== SuggestionStatus.PENDING) {
      continue;
    }
    
    const originalText = mark.attrs.originalText;
    const suggestedText = mark.attrs.suggestedText;
    const suggestionId = mark.attrs.id;
    
    // If original and suggested text are the same, nothing to show
    if (originalText === suggestedText) {
      continue;
    }
    
    // For deletions: original text with deletion styling
    decorations.push(
      Decoration.inline(from, to, {
        class: DELETION_CLASS,
        'data-suggestion-id': suggestionId
      })
    );
    
    // For additions: suggested text with addition styling
    decorations.push(
      Decoration.widget(to, (view) => {
        const span = document.createElement('span');
        span.className = ADDITION_CLASS;
        span.setAttribute('data-suggestion-id', suggestionId);
        span.textContent = suggestedText;
        return span;
      })
    );
  }
  
  return DecorationSet.create(doc, decorations);
}

/**
 * Creates a suggestion object from original text, suggested text, and position
 * 
 * @param originalText The original text
 * @param suggestedText The suggested replacement text
 * @param position The position in the document where the suggestion applies
 * @returns A new suggestion object
 */
export function createSuggestionFromDiff(
  originalText: string,
  suggestedText: string,
  position: Position
): Suggestion {
  // Generate a unique ID for the suggestion
  const id = uuidv4();
  
  // Create a suggestion object with original text, suggested text, and position
  return {
    id,
    originalText,
    suggestedText,
    position,
    status: SuggestionStatus.PENDING
  };
}