import { Node, Mark, Fragment, Schema } from 'prosemirror-model'; // prosemirror-model v1.19.0
import { Transaction, EditorState } from 'prosemirror-state'; // prosemirror-state v1.4.2
import { Step, StepResult, ReplaceStep } from 'prosemirror-transform'; // prosemirror-transform v1.7.0
import { Decoration, DecorationSet } from 'prosemirror-view'; // prosemirror-view v1.30.0
import { markForDeletion, markForAddition, isChangeNode, getChangeAttrs } from './utils';
import { compareText } from '../diffing/text-diff';

/**
 * Interface representing an individual tracked change
 */
export interface ChangeType {
  id: string;
  type: string; // 'addition', 'deletion', 'modification'
  from: number;
  to: number;
  text: string;
  author: string;
  timestamp: number;
}

/**
 * Interface representing a set of tracked changes
 */
export interface ChangeSetType {
  changes: Array<ChangeType>;
  metadata: {
    author: string;
    timestamp: number;
    source: string;
  };
}

// Constants for change types
const CHANGE_TYPES = {
  ADDITION: 'addition',
  DELETION: 'deletion',
  MODIFICATION: 'modification'
};

/**
 * Creates a set of tracked changes from original and modified text
 * 
 * Compares the original document with the modified document to identify
 * additions, deletions, and modifications between them.
 * 
 * @param originalDoc The original document
 * @param modifiedDoc The modified document with changes
 * @param schema The ProseMirror schema
 * @returns A change set containing all detected changes
 */
export function createChangeSet(
  originalDoc: Node,
  modifiedDoc: Node,
  schema: Schema
): ChangeSetType {
  // Extract text content from both documents
  const originalText = originalDoc.textContent;
  const modifiedText = modifiedDoc.textContent;
  
  // Compare the texts using the diff utility
  const diffResult = compareText(originalText, modifiedText);
  
  // Convert the diff result to a change set
  const changes: ChangeType[] = [];
  const timestamp = Date.now();
  const author = "AI Assistant"; // Default author for AI suggestions
  
  // Process the diff result into changes
  diffResult.forEach((diff: any, index: number) => {
    const id = `change-${index}`;
    
    if (diff.added) {
      changes.push({
        id,
        type: CHANGE_TYPES.ADDITION,
        from: diff.position,
        to: diff.position + diff.value.length,
        text: diff.value,
        author,
        timestamp
      });
    } else if (diff.removed) {
      changes.push({
        id,
        type: CHANGE_TYPES.DELETION,
        from: diff.position,
        to: diff.position + diff.value.length,
        text: diff.value,
        author,
        timestamp
      });
    }
    // Unchanged text doesn't need to be tracked
  });
  
  // Process adjacent addition/deletion pairs into modifications
  // This is important for tracking replaced text correctly
  for (let i = 0; i < changes.length - 1; i++) {
    const current = changes[i];
    const next = changes[i + 1];
    
    if (current.type === CHANGE_TYPES.DELETION && 
        next.type === CHANGE_TYPES.ADDITION && 
        current.to === next.from) {
      
      // Replace the pair with a single modification
      changes.splice(i, 2, {
        id: `change-mod-${i}`,
        type: CHANGE_TYPES.MODIFICATION,
        from: current.from,
        to: next.to,
        text: next.text, // The new text
        author,
        timestamp
      });
      
      // Adjust index since we removed an element
      i--;
    }
  }
  
  return {
    changes,
    metadata: {
      author,
      timestamp,
      source: 'AI Suggestion'
    }
  };
}

/**
 * Applies a set of tracked changes to a document
 * 
 * Takes a set of changes and applies them to the document state,
 * marking additions and deletions appropriately for visual display.
 * 
 * @param state The current editor state
 * @param changeSet The set of changes to apply
 * @returns A transaction with the changes applied
 */
export function applyChangeSet(
  state: EditorState,
  changeSet: ChangeSetType
): Transaction {
  let tr = state.tr;
  const { schema, doc } = state;
  
  // Apply changes in reverse order to avoid position shifting
  const sortedChanges = [...changeSet.changes].sort((a, b) => b.from - a.from);
  
  for (const change of sortedChanges) {
    switch (change.type) {
      case CHANGE_TYPES.ADDITION:
        // Create a node with the added text
        const addNode = schema.text(change.text);
        
        // Mark it as an addition
        const markedAddNode = markForAddition(addNode, schema, {
          id: change.id,
          author: change.author,
          timestamp: change.timestamp
        });
        
        // Insert the marked node
        tr = tr.insert(change.from, markedAddNode);
        break;
        
      case CHANGE_TYPES.DELETION:
        // Get the actual text at this range
        const delText = doc.textBetween(change.from, change.to);
        
        // Create a node with the text to be deleted
        const delNode = schema.text(delText);
        
        // Mark it as a deletion
        const markedDelNode = markForDeletion(delNode, schema, {
          id: change.id,
          author: change.author,
          timestamp: change.timestamp
        });
        
        // Replace the original with the marked deletion
        tr = tr.replaceWith(change.from, change.to, markedDelNode);
        break;
        
      case CHANGE_TYPES.MODIFICATION:
        // Handle as a deletion followed by an addition
        
        // First, get the original text
        const origText = doc.textBetween(change.from, change.to);
        
        // Create a node with the original text
        const modDelNode = schema.text(origText);
        
        // Mark it as a deletion
        const markedModDelNode = markForDeletion(modDelNode, schema, {
          id: `${change.id}-del`,
          author: change.author,
          timestamp: change.timestamp
        });
        
        // Replace the original with the marked deletion
        tr = tr.replaceWith(change.from, change.to, markedModDelNode);
        
        // Create a node with the new text
        const modAddNode = schema.text(change.text);
        
        // Mark it as an addition
        const markedModAddNode = markForAddition(modAddNode, schema, {
          id: `${change.id}-add`,
          author: change.author,
          timestamp: change.timestamp
        });
        
        // Insert the marked addition
        tr = tr.insert(change.to, markedModAddNode);
        break;
    }
  }
  
  return tr;
}

/**
 * Accepts a specific change, incorporating it into the document
 * 
 * For additions: Keeps the content but removes the addition mark
 * For deletions: Removes the content marked for deletion
 * For modifications: Keeps the new content and removes any change marks
 * 
 * @param state The current editor state
 * @param changeId The ID of the change to accept
 * @returns A transaction with the change accepted
 */
export function acceptChange(
  state: EditorState,
  changeId: string
): Transaction {
  const { doc, schema } = state;
  let tr = state.tr;
  let changeFound = false;
  
  // Find the change with the given ID
  doc.descendants((node, pos) => {
    if (!isChangeNode(node)) return true;
    
    const attrs = getChangeAttrs(node);
    if (attrs.id !== changeId) return true;
    
    changeFound = true;
    
    if (attrs.type === CHANGE_TYPES.ADDITION) {
      // For additions, keep the content but remove the mark
      tr = tr.removeMark(pos, pos + node.nodeSize, schema.marks.addition);
    } else if (attrs.type === CHANGE_TYPES.DELETION) {
      // For deletions, remove the node entirely
      tr = tr.delete(pos, pos + node.nodeSize);
    } else if (attrs.type === CHANGE_TYPES.MODIFICATION) {
      // For modifications, we need to handle both parts
      if (attrs.id.endsWith('-del')) {
        // Delete the deletion part
        tr = tr.delete(pos, pos + node.nodeSize);
      } else if (attrs.id.endsWith('-add')) {
        // Keep the addition but remove the mark
        tr = tr.removeMark(pos, pos + node.nodeSize, schema.marks.addition);
      }
    }
    
    return false; // Stop traversal after processing
  });
  
  if (!changeFound) {
    console.warn(`Change with ID ${changeId} not found`);
  }
  
  return tr;
}

/**
 * Rejects a specific change, reverting to the original content
 * 
 * For additions: Removes the added content
 * For deletions: Keeps the original content by removing the deletion mark
 * For modifications: Reverts to the original content
 * 
 * @param state The current editor state
 * @param changeId The ID of the change to reject
 * @returns A transaction with the change rejected
 */
export function rejectChange(
  state: EditorState,
  changeId: string
): Transaction {
  const { doc, schema } = state;
  let tr = state.tr;
  let changeFound = false;
  
  // Find the change with the given ID
  doc.descendants((node, pos) => {
    if (!isChangeNode(node)) return true;
    
    const attrs = getChangeAttrs(node);
    if (attrs.id !== changeId) return true;
    
    changeFound = true;
    
    if (attrs.type === CHANGE_TYPES.ADDITION) {
      // For additions, delete the node entirely
      tr = tr.delete(pos, pos + node.nodeSize);
    } else if (attrs.type === CHANGE_TYPES.DELETION) {
      // For deletions, keep the content but remove the mark
      tr = tr.removeMark(pos, pos + node.nodeSize, schema.marks.deletion);
    } else if (attrs.type === CHANGE_TYPES.MODIFICATION) {
      // For modifications, we need to handle both parts
      if (attrs.id.endsWith('-del')) {
        // Keep the deletion part but remove the mark
        tr = tr.removeMark(pos, pos + node.nodeSize, schema.marks.deletion);
      } else if (attrs.id.endsWith('-add')) {
        // Delete the addition part
        tr = tr.delete(pos, pos + node.nodeSize);
      }
    }
    
    return false; // Stop traversal after processing
  });
  
  if (!changeFound) {
    console.warn(`Change with ID ${changeId} not found`);
  }
  
  return tr;
}

/**
 * Accepts all changes in the document
 * 
 * Processes all changes in the document in the correct order to maintain
 * document integrity when accepting multiple changes at once.
 * 
 * @param state The current editor state
 * @returns A transaction with all changes accepted
 */
export function acceptAllChanges(
  state: EditorState
): Transaction {
  const { doc, schema } = state;
  let tr = state.tr;
  
  // First, find all changes in the document
  const additions: {pos: number, node: Node}[] = [];
  const deletions: {pos: number, node: Node}[] = [];
  
  // Collect all changes
  doc.descendants((node, pos) => {
    if (!isChangeNode(node)) return true;
    
    const attrs = getChangeAttrs(node);
    
    if (attrs.type === CHANGE_TYPES.ADDITION) {
      additions.push({ pos, node });
    } else if (attrs.type === CHANGE_TYPES.DELETION) {
      deletions.push({ pos, node });
    } else if (attrs.type === CHANGE_TYPES.MODIFICATION) {
      if (attrs.id.endsWith('-del')) {
        deletions.push({ pos, node });
      } else if (attrs.id.endsWith('-add')) {
        additions.push({ pos, node });
      }
    }
    
    return true;
  });
  
  // Process additions first (remove marks but keep content)
  for (const { pos, node } of additions) {
    tr = tr.removeMark(pos, pos + node.nodeSize, schema.marks.addition);
  }
  
  // Process deletions in reverse order to avoid position shifts
  deletions.sort((a, b) => b.pos - a.pos);
  
  for (const { pos, node } of deletions) {
    tr = tr.delete(pos, pos + node.nodeSize);
  }
  
  return tr;
}

/**
 * Rejects all changes in the document
 * 
 * Processes all changes in the document in the correct order to maintain
 * document integrity when rejecting multiple changes at once.
 * 
 * @param state The current editor state
 * @returns A transaction with all changes rejected
 */
export function rejectAllChanges(
  state: EditorState
): Transaction {
  const { doc, schema } = state;
  let tr = state.tr;
  
  // First, find all changes in the document
  const additions: {pos: number, node: Node}[] = [];
  const deletions: {pos: number, node: Node}[] = [];
  
  // Collect all changes
  doc.descendants((node, pos) => {
    if (!isChangeNode(node)) return true;
    
    const attrs = getChangeAttrs(node);
    
    if (attrs.type === CHANGE_TYPES.ADDITION) {
      additions.push({ pos, node });
    } else if (attrs.type === CHANGE_TYPES.DELETION) {
      deletions.push({ pos, node });
    } else if (attrs.type === CHANGE_TYPES.MODIFICATION) {
      if (attrs.id.endsWith('-del')) {
        deletions.push({ pos, node });
      } else if (attrs.id.endsWith('-add')) {
        additions.push({ pos, node });
      }
    }
    
    return true;
  });
  
  // Process deletions first (remove marks but keep content)
  for (const { pos, node } of deletions) {
    tr = tr.removeMark(pos, pos + node.nodeSize, schema.marks.deletion);
  }
  
  // Process additions in reverse order to avoid position shifts
  additions.sort((a, b) => b.pos - a.pos);
  
  for (const { pos, node } of additions) {
    tr = tr.delete(pos, pos + node.nodeSize);
  }
  
  return tr;
}

/**
 * Finds all changes within a specific document range
 * 
 * Identifies nodes and marks that represent tracked changes within the
 * given document range and collects metadata about each change.
 * 
 * @param state The current editor state
 * @param from Starting position in the document
 * @param to Ending position in the document
 * @returns Array of changes in the specified range
 */
export function findChangesInRange(
  state: EditorState,
  from: number,
  to: number
): Array<ChangeType> {
  const { doc } = state;
  const changes: ChangeType[] = [];
  
  // Find all changes in the specified range
  doc.nodesBetween(from, to, (node, pos) => {
    if (!isChangeNode(node)) return true;
    
    const attrs = getChangeAttrs(node);
    const nodeFrom = pos;
    const nodeTo = pos + node.nodeSize;
    
    // Only include if the node is at least partially within the range
    if (nodeTo > from && nodeFrom < to) {
      changes.push({
        id: attrs.id,
        type: attrs.type,
        from: nodeFrom,
        to: nodeTo,
        text: node.textContent,
        author: attrs.author || 'Unknown',
        timestamp: attrs.timestamp || Date.now()
      });
    }
    
    return true;
  });
  
  return changes;
}

/**
 * Creates decorations to visually highlight tracked changes
 * 
 * Generates appropriate decorations for additions (green underline or background)
 * and deletions (red strikethrough or background).
 * 
 * @param doc The ProseMirror document
 * @returns A set of decorations for the document
 */
export function createChangeDecorations(doc: Node): DecorationSet {
  const decorations: Decoration[] = [];
  
  // Create decorations for all changes in the document
  doc.descendants((node, pos) => {
    if (!isChangeNode(node)) return true;
    
    const attrs = getChangeAttrs(node);
    const from = pos;
    const to = pos + node.nodeSize;
    
    if (attrs.type === CHANGE_TYPES.ADDITION) {
      // Style for additions (typically green)
      decorations.push(Decoration.inline(from, to, {
        class: 'addition-change',
        'data-change-id': attrs.id,
        title: `Added by ${attrs.author || 'Unknown'}`
      }));
    } else if (attrs.type === CHANGE_TYPES.DELETION) {
      // Style for deletions (typically red with strikethrough)
      decorations.push(Decoration.inline(from, to, {
        class: 'deletion-change',
        'data-change-id': attrs.id,
        title: `Deleted by ${attrs.author || 'Unknown'}`
      }));
    } else if (attrs.type === CHANGE_TYPES.MODIFICATION) {
      // Style for modifications (depends on if it's the del or add part)
      if (attrs.id.endsWith('-del')) {
        decorations.push(Decoration.inline(from, to, {
          class: 'deletion-change',
          'data-change-id': attrs.id.replace('-del', ''),
          title: `Modified by ${attrs.author || 'Unknown'}`
        }));
      } else if (attrs.id.endsWith('-add')) {
        decorations.push(Decoration.inline(from, to, {
          class: 'addition-change',
          'data-change-id': attrs.id.replace('-add', ''),
          title: `Modified by ${attrs.author || 'Unknown'}`
        }));
      }
    }
    
    return true;
  });
  
  return DecorationSet.create(doc, decorations);
}

/**
 * Creates change objects from diff results
 * 
 * Processes the diff result to identify changes, converts each diff operation
 * into a change object, and generates unique IDs for each change.
 * 
 * @param diffResult The result of a diff operation
 * @param schema The ProseMirror schema
 * @returns Array of change objects
 */
export function createChangeFromDiff(
  diffResult: any,
  schema: Schema
): Array<ChangeType> {
  const changes: ChangeType[] = [];
  const timestamp = Date.now();
  const author = 'AI Assistant';
  
  // Process the diff result into change objects
  diffResult.forEach((diff: any, index: number) => {
    const id = `diff-${index}`;
    
    if (diff.added) {
      changes.push({
        id,
        type: CHANGE_TYPES.ADDITION,
        from: diff.position,
        to: diff.position + diff.value.length,
        text: diff.value,
        author,
        timestamp
      });
    } else if (diff.removed) {
      changes.push({
        id,
        type: CHANGE_TYPES.DELETION,
        from: diff.position,
        to: diff.position + diff.value.length,
        text: diff.value,
        author,
        timestamp
      });
    }
    // Unchanged segments don't need to be tracked
  });
  
  // Look for adjacent addition/deletion pairs and convert to modifications
  for (let i = 0; i < changes.length - 1; i++) {
    const curr = changes[i];
    const next = changes[i + 1];
    
    if (curr.type === CHANGE_TYPES.DELETION && 
        next.type === CHANGE_TYPES.ADDITION && 
        curr.to === next.from) {
      
      // Replace the pair with a modification
      changes.splice(i, 2, {
        id: `diff-mod-${i}`,
        type: CHANGE_TYPES.MODIFICATION,
        from: curr.from,
        to: next.to,
        text: next.text, // The new text
        author,
        timestamp
      });
      
      // Adjust the index since we removed an element
      i--;
    }
  }
  
  return changes;
}