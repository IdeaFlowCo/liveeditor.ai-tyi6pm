import {
  EditorState,
  Plugin,
  PluginKey,
  Transaction
} from 'prosemirror-state'; // v1.4.2
import {
  Decoration,
  DecorationSet
} from 'prosemirror-view'; // v1.30.2
import {
  Fragment,
  Slice
} from 'prosemirror-model'; // v1.19.0
import {
  Mapping,
  Step
} from 'prosemirror-transform'; // v1.7.1
import { v4 as uuidv4 } from 'uuid'; // v9.0.0

import { schema } from '../schema';
import { TextDiff } from '../../../../lib/diffing/text-diff';
import { TRACK_CHANGES_CLASSNAMES } from '../../../../constants/editor';
import { SuggestionType } from '../../../../types/suggestion';

/**
 * Plugin key for accessing the track changes plugin state
 */
export const trackChangesPluginKey = new PluginKey<TrackChangesState>('trackChanges');

/**
 * Represents a single tracked change in the document
 */
export class Change {
  /** Unique identifier for the change */
  id: string;
  /** Starting position of the change in the document */
  from: number;
  /** Ending position of the change in the document */
  to: number;
  /** The original text before the change */
  originalText: string;
  /** The suggested text for the change */
  suggestedText: string;
  /** Type of change (addition, deletion, modification) */
  type: SuggestionType;
  /** Additional metadata about the change */
  metadata: Record<string, any>;

  /**
   * Creates a new change object
   */
  constructor({
    id = uuidv4(),
    from,
    to,
    originalText,
    suggestedText,
    type = SuggestionType.CUSTOM,
    metadata = {}
  }: {
    id?: string;
    from: number;
    to: number;
    originalText: string;
    suggestedText: string;
    type?: SuggestionType;
    metadata?: Record<string, any>;
  }) {
    this.id = id;
    this.from = from;
    this.to = to;
    this.originalText = originalText;
    this.suggestedText = suggestedText;
    this.type = type;
    this.metadata = metadata;
  }

  /**
   * Checks if the change is within a specified range
   */
  isInRange(from: number, to: number): boolean {
    return this.from < to && this.to > from;
  }

  /**
   * Maps the change positions according to document transformations
   */
  map(mapping: Mapping): Change {
    const from = mapping.map(this.from);
    const to = mapping.map(this.to);
    
    return new Change({
      id: this.id,
      from,
      to,
      originalText: this.originalText,
      suggestedText: this.suggestedText,
      type: this.type,
      metadata: this.metadata
    });
  }

  /**
   * Generates a human-readable description of the change
   */
  getDescription(): string {
    if (!this.originalText && this.suggestedText) {
      return `Added: "${this.suggestedText}"`;
    } else if (this.originalText && !this.suggestedText) {
      return `Deleted: "${this.originalText}"`;
    } else {
      return `Changed: "${this.originalText}" to "${this.suggestedText}"`;
    }
  }
}

/**
 * Manages the state of track changes within the editor
 */
export class TrackChangesState {
  /** Map of change IDs to Change objects */
  changes: Map<string, Change>;
  /** Set of decorations for visualizing changes */
  decorations: DecorationSet;
  /** Whether track changes is enabled */
  enabled: boolean;

  /**
   * Creates a new track changes state
   */
  constructor(
    changes: Map<string, Change> = new Map(),
    decorations: DecorationSet = DecorationSet.empty,
    enabled: boolean = true
  ) {
    this.changes = changes;
    this.decorations = decorations;
    this.enabled = enabled;
  }

  /**
   * Adds a new tracked change to the state
   */
  addChange(change: Change): TrackChangesState {
    const newChanges = new Map(this.changes);
    newChanges.set(change.id, change);
    
    // Add decorations for this change
    const decorations = createChangeDecoration(change, null);
    const newDecorations = this.decorations.add(null, decorations);
    
    return new TrackChangesState(newChanges, newDecorations, this.enabled);
  }

  /**
   * Removes a tracked change from the state
   */
  removeChange(changeId: string): TrackChangesState {
    const newChanges = new Map(this.changes);
    newChanges.delete(changeId);
    
    // Remove decorations for this change
    const newDecorations = this.decorations.remove(
      this.decorations.find(null, null, spec => spec.id === changeId)
    );
    
    return new TrackChangesState(newChanges, newDecorations, this.enabled);
  }

  /**
   * Updates the state based on document transformations
   */
  applyMapping(mapping: Mapping): TrackChangesState {
    // Map all change positions according to document changes
    const newChanges = new Map();
    for (const [id, change] of this.changes.entries()) {
      newChanges.set(id, change.map(mapping));
    }
    
    // Map decoration positions
    const newDecorations = this.decorations.map(mapping);
    
    return new TrackChangesState(newChanges, newDecorations, this.enabled);
  }

  /**
   * Returns all tracked changes in the current state
   */
  getChanges(): Change[] {
    return Array.from(this.changes.values()).sort((a, b) => a.from - b.from);
  }

  /**
   * Retrieves a specific change by its ID
   */
  getChangeById(changeId: string): Change | undefined {
    return this.changes.get(changeId);
  }
}

/**
 * Creates decorations for visualizing a tracked change in the document
 */
function createChangeDecoration(change: Change, state: EditorState | null): Decoration[] {
  const decorations: Decoration[] = [];
  
  // Determine appearance based on change type
  let className = '';
  const attrs: Record<string, any> = {
    'data-change-id': change.id,
    'data-change-type': change.type,
    'data-original-text': change.originalText,
    'data-suggested-text': change.suggestedText
  };
  
  // Handle the three types of changes differently
  if (!change.originalText && change.suggestedText) {
    // Addition (new text)
    className = 'track-changes-addition';
    attrs.class = className;
    attrs.title = `Suggestion: Add "${change.suggestedText}"`;
    attrs.style = `background-color: #E3FCEF; text-decoration: underline; color: #20A779;`;
    
    decorations.push(
      Decoration.inline(change.from, change.to, attrs, { id: change.id })
    );
    
  } else if (change.originalText && !change.suggestedText) {
    // Deletion (remove text)
    className = 'track-changes-deletion';
    attrs.class = className;
    attrs.title = `Suggestion: Delete "${change.originalText}"`;
    attrs.style = `text-decoration: line-through; color: #FF6B6B;`;
    
    decorations.push(
      Decoration.inline(change.from, change.to, attrs, { id: change.id })
    );
    
  } else if (change.originalText && change.suggestedText) {
    // Modification (replace text)
    className = 'track-changes-modification';
    attrs.class = className;
    attrs.title = `Suggestion: Replace "${change.originalText}" with "${change.suggestedText}"`;
    attrs.style = `text-decoration: line-through; color: #FF6B6B;`;
    
    // Show strike-through for original text
    decorations.push(
      Decoration.inline(change.from, change.to, attrs, { id: change.id + '-delete' })
    );
    
    // Show addition styling for suggested text (handled in UI)
  }
  
  return decorations;
}

/**
 * Creates a ProseMirror plugin that handles track changes functionality
 */
export function createTrackChangesPlugin(options: { enabled?: boolean } = {}): Plugin {
  return new Plugin({
    key: trackChangesPluginKey,
    
    state: {
      init() {
        return new TrackChangesState(
          new Map(),
          DecorationSet.empty,
          options.enabled !== undefined ? options.enabled : true
        );
      },
      
      apply(tr: Transaction, pluginState: TrackChangesState, oldState: EditorState, newState: EditorState) {
        // Apply mapping for document changes
        let state = pluginState;
        if (tr.docChanged) {
          state = state.applyMapping(tr.mapping);
        }
        
        // Handle track changes specific transactions
        const meta = tr.getMeta(trackChangesPluginKey);
        if (meta) {
          if (meta.type === 'addChange') {
            state = state.addChange(meta.change);
          } else if (meta.type === 'removeChange') {
            state = state.removeChange(meta.changeId);
          } else if (meta.type === 'setEnabled') {
            state = new TrackChangesState(state.changes, state.decorations, meta.enabled);
          }
        }
        
        return state;
      }
    },
    
    props: {
      decorations(state) {
        const trackChangesState = this.getState(state);
        return trackChangesState?.enabled ? trackChangesState.decorations : null;
      }
    }
  });
}

/**
 * Applies a tracked change to the document, either accepting or rejecting it
 */
export function applyTrackedChange(
  state: EditorState,
  changeId: string,
  accept: boolean
): Transaction {
  const pluginState = trackChangesPluginKey.getState(state);
  const change = pluginState?.getChangeById(changeId);
  
  if (!change || !pluginState) {
    return state.tr;
  }
  
  let tr = state.tr;
  
  if (accept) {
    // When accepting a change:
    if (!change.originalText && change.suggestedText) {
      // For additions, the text is already there, nothing to do
    } else if (change.originalText && !change.suggestedText) {
      // For deletions, remove the text
      tr = tr.delete(change.from, change.to);
    } else if (change.originalText && change.suggestedText) {
      // For modifications, replace with suggested text
      tr = tr.replaceWith(
        change.from,
        change.to,
        state.schema.text(change.suggestedText)
      );
    }
  } else {
    // When rejecting a change:
    if (!change.originalText && change.suggestedText) {
      // For additions, remove the added text
      tr = tr.delete(change.from, change.to);
    } else if (change.originalText && !change.suggestedText) {
      // For deletions, the original text stays, nothing to do
    } else if (change.originalText && change.suggestedText) {
      // For modifications, keep the original text
      tr = tr.replaceWith(
        change.from,
        change.to,
        state.schema.text(change.originalText)
      );
    }
  }
  
  // Remove the change from the track changes state
  tr = tr.setMeta(trackChangesPluginKey, {
    type: 'removeChange',
    changeId: change.id
  });
  
  return tr;
}

/**
 * Applies all tracked changes in the document with a single action
 */
export function applyAllChanges(
  state: EditorState,
  accept: boolean
): Transaction {
  const pluginState = trackChangesPluginKey.getState(state);
  
  if (!pluginState) {
    return state.tr;
  }
  
  // Sort changes to avoid position conflicts
  // For accepting, process in forward order
  // For rejecting, process in reverse order to avoid position shifts
  const changes = pluginState.getChanges()
    .sort((a, b) => accept ? a.from - b.from : b.from - a.from);
  
  let tr = state.tr;
  
  // Apply each change in order
  for (const change of changes) {
    if (accept) {
      // When accepting:
      if (!change.originalText && change.suggestedText) {
        // For additions, nothing to do
      } else if (change.originalText && !change.suggestedText) {
        // For deletions, delete the text
        tr = tr.delete(change.from, change.to);
      } else if (change.originalText && change.suggestedText) {
        // For modifications, replace with suggested text
        tr = tr.replaceWith(
          change.from,
          change.to,
          state.schema.text(change.suggestedText)
        );
      }
    } else {
      // When rejecting:
      if (!change.originalText && change.suggestedText) {
        // For additions, delete the text
        tr = tr.delete(change.from, change.to);
      } else if (change.originalText && !change.suggestedText) {
        // For deletions, nothing to do
      } else if (change.originalText && change.suggestedText) {
        // For modifications, keep original text
        tr = tr.replaceWith(
          change.from,
          change.to,
          state.schema.text(change.originalText)
        );
      }
    }
    
    // Remove the change from the track changes state
    tr = tr.setMeta(trackChangesPluginKey, {
      type: 'removeChange',
      changeId: change.id
    });
  }
  
  return tr;
}

/**
 * Finds all tracked changes within a specific document range
 */
export function findChangesInRange(
  state: EditorState,
  from: number,
  to: number
): Change[] {
  const pluginState = trackChangesPluginKey.getState(state);
  
  if (!pluginState) {
    return [];
  }
  
  // Filter changes that overlap with the specified range
  return pluginState.getChanges()
    .filter(change => change.isInRange(from, to))
    .sort((a, b) => a.from - b.from);
}

/**
 * Compares two text versions and generates track changes
 */
export function compareVersions(
  state: EditorState,
  originalText: string,
  suggestedText: string,
  metadata: Record<string, any> = {}
): Transaction {
  let tr = state.tr;
  
  // Use TextDiff to find differences between original and suggested text
  const diffResult = TextDiff.computeDiff(originalText, suggestedText);
  
  if (!diffResult || !diffResult.changes) {
    return tr;
  }
  
  // Convert diff results to Change objects
  for (const diffChange of diffResult.changes) {
    // Skip unchanged sections
    if (diffChange.type === 'unchanged') {
      continue;
    }
    
    // Create a Change object based on the diff type
    let change: Change;
    
    if (diffChange.type === 'addition') {
      // Text was added
      change = new Change({
        from: diffChange.originalStart,
        to: diffChange.originalStart,  // Zero-width for insertions
        originalText: '',
        suggestedText: diffChange.text,
        type: SuggestionType.CUSTOM,
        metadata: {
          ...metadata,
          diffType: 'addition'
        }
      });
    } else if (diffChange.type === 'deletion') {
      // Text was deleted
      change = new Change({
        from: diffChange.originalStart,
        to: diffChange.originalEnd,
        originalText: diffChange.text,
        suggestedText: '',
        type: SuggestionType.CUSTOM,
        metadata: {
          ...metadata,
          diffType: 'deletion'
        }
      });
    } else {
      // Unknown change type, skip
      continue;
    }
    
    // Add the change to the track changes state
    tr = tr.setMeta(trackChangesPluginKey, {
      type: 'addChange',
      change
    });
  }
  
  return tr;
}