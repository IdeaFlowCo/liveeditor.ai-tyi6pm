import diff_match_patch from 'diff-match-patch';

/**
 * Defines types of changes in a text diff
 * @version 1.0.0
 */
export enum DiffChangeType {
  ADDITION = 'addition',
  DELETION = 'deletion',
  UNCHANGED = 'unchanged'
}

/**
 * Represents a single change in a text diff
 * @version 1.0.0
 */
export interface DiffChange {
  /** Unique identifier for the change */
  id: string;
  /** Type of change (addition, deletion, unchanged) */
  type: DiffChangeType;
  /** The text content of this change */
  content: string;
  /** Starting position of this change in the original text */
  position: number;
  /** Length of the content in characters */
  length: number;
}

/**
 * Complete diff result structure containing all changes
 * @version 1.0.0
 */
export interface DiffResult {
  /** Array of all changes detected */
  changes: DiffChange[];
  /** The original text before changes */
  originalText: string;
  /** The suggested text with changes */
  suggestedText: string;
  /** Additional metadata about the diff */
  metadata: {
    /** When the diff was computed */
    timestamp: string;
    /** Options used for the diff algorithm */
    options: DiffOptions;
  };
}

/**
 * Configuration options for the diff algorithm
 * @version 1.0.0
 */
export interface DiffOptions {
  /** Cost of an edit operation for the diff algorithm (default: 4) */
  editCost?: number;
  /** Whether to perform semantic cleanup of the diff (default: true) */
  semanticCleanup?: boolean;
  /** Additional custom options */
  [key: string]: any;
}

/**
 * Computes the difference between original text and suggested text using the diff-match-patch algorithm
 * 
 * @param originalText The original text before any changes
 * @param suggestedText The suggested text with AI improvements
 * @param options Configuration options for the diff algorithm
 * @returns Structured diff result with change operations
 */
export function computeTextDiff(
  originalText: string,
  suggestedText: string,
  options: DiffOptions = {}
): DiffResult {
  // Input validation
  if (typeof originalText !== 'string' || typeof suggestedText !== 'string') {
    throw new Error('Both originalText and suggestedText must be strings');
  }
  
  const dmp = new diff_match_patch();
  
  // Set algorithm options if provided
  if (options.editCost !== undefined) {
    dmp.Diff_EditCost = options.editCost;
  }
  
  // Compute the diff between the texts
  const diff = dmp.diff_main(originalText, suggestedText);
  
  // Perform cleanup to make the diff more semantically meaningful
  if (options.semanticCleanup !== false) {
    dmp.diff_cleanupSemantic(diff);
  }
  
  // Convert library diff format to our structured format
  let position = 0;
  const changes: DiffChange[] = [];
  
  for (const [type, text] of diff) {
    if (text.length === 0) continue; // Skip empty segments
    
    // Map library diff type to our enum
    let changeType: DiffChangeType;
    switch (type) {
      case -1: // DIFF_DELETE
        changeType = DiffChangeType.DELETION;
        break;
      case 1: // DIFF_INSERT
        changeType = DiffChangeType.ADDITION;
        break;
      case 0: // DIFF_EQUAL
      default:
        changeType = DiffChangeType.UNCHANGED;
        break;
    }
    
    const change: DiffChange = {
      id: generateChangeId({ type: changeType, content: text, position }),
      type: changeType,
      content: text,
      position,
      length: text.length
    };
    
    changes.push(change);
    
    // Update position counter (only increment for non-additions as they exist in the original text)
    if (changeType !== DiffChangeType.ADDITION) {
      position += text.length;
    }
  }
  
  return {
    changes,
    originalText,
    suggestedText,
    metadata: {
      timestamp: new Date().toISOString(),
      options
    }
  };
}

/**
 * Converts raw diff operations into a structured format suitable for track changes visualization in ProseMirror
 * 
 * @param diffResult The structured diff result to format
 * @returns ProseMirror-compatible representation of changes
 */
export function formatDiffForTrackChanges(diffResult: DiffResult): object {
  if (!diffResult || !Array.isArray(diffResult.changes)) {
    throw new Error('Invalid diffResult provided');
  }
  
  // Create decorations for ProseMirror
  const decorations = [];
  let positionInOriginal = 0;
  let positionInSuggested = 0;
  
  for (const change of diffResult.changes) {
    switch (change.type) {
      case DiffChangeType.DELETION:
        // Deleted text exists in the original but not in the suggested
        decorations.push({
          type: 'deletion',
          from: positionInOriginal,
          to: positionInOriginal + change.content.length,
          attrs: {
            id: change.id,
            content: change.content
          }
        });
        positionInOriginal += change.content.length;
        break;
        
      case DiffChangeType.ADDITION:
        // Added text exists in the suggested but not in the original
        decorations.push({
          type: 'addition',
          from: positionInOriginal,
          to: positionInOriginal,
          attrs: {
            id: change.id,
            content: change.content
          }
        });
        positionInSuggested += change.content.length;
        break;
        
      case DiffChangeType.UNCHANGED:
        // Unchanged text exists in both versions
        positionInOriginal += change.content.length;
        positionInSuggested += change.content.length;
        break;
    }
  }
  
  return {
    decorations,
    original: {
      text: diffResult.originalText,
      length: diffResult.originalText.length
    },
    suggested: {
      text: diffResult.suggestedText,
      length: diffResult.suggestedText.length
    }
  };
}

/**
 * Applies accepted changes to the original text, creating a new version with accepted modifications
 * 
 * @param originalText The original text before any changes
 * @param acceptedChanges Array of changes that have been accepted
 * @returns Text with accepted changes applied
 */
export function applyAcceptedChanges(
  originalText: string,
  acceptedChanges: Array<DiffChange>
): string {
  if (!originalText || !Array.isArray(acceptedChanges)) {
    return originalText || '';
  }
  
  // Sort changes by position in descending order to avoid position shifts
  // when applying changes from end to start
  const sortedChanges = [...acceptedChanges].sort((a, b) => b.position - a.position);
  
  let result = originalText;
  
  for (const change of sortedChanges) {
    try {
      if (change.type === DiffChangeType.ADDITION) {
        // For additions, insert the new content at the specified position
        result = result.substring(0, change.position) + change.content + result.substring(change.position);
      } else if (change.type === DiffChangeType.DELETION) {
        // For deletions, remove the specified content
        result = result.substring(0, change.position) + result.substring(change.position + change.length);
      }
      // No action needed for unchanged content
    } catch (error) {
      console.error(`Error applying change at position ${change.position}:`, error);
      // Continue with the next change instead of breaking completely
    }
  }
  
  return result;
}

/**
 * Removes rejected changes from the suggested text, reverting to original in those sections
 * 
 * @param suggestedText The suggested text with all changes
 * @param rejectedChanges Array of changes that have been rejected
 * @param originalText The original text before any changes
 * @returns Text with rejected changes reverted
 */
export function applyRejectedChanges(
  suggestedText: string,
  rejectedChanges: Array<DiffChange>,
  originalText: string
): string {
  if (!suggestedText || !originalText || !Array.isArray(rejectedChanges)) {
    return suggestedText || '';
  }
  
  if (rejectedChanges.length === 0) {
    return suggestedText; // No changes to reject
  }
  
  // For a more accurate implementation, we need to recompute the diff
  // This is because positions in suggestedText don't directly map to those in the original diff
  const dmp = new diff_match_patch();
  const diff = dmp.diff_main(originalText, suggestedText);
  dmp.diff_cleanupSemantic(diff);
  
  // Create a map of rejected change IDs for quick lookup
  const rejectedIds = new Set(rejectedChanges.map(change => change.id));
  
  // Build the result by keeping only non-rejected changes
  let position = 0;
  const acceptedChanges: DiffChange[] = [];
  
  for (const [type, text] of diff) {
    if (text.length === 0) continue; // Skip empty segments
    
    let changeType: DiffChangeType;
    switch (type) {
      case -1: // DIFF_DELETE
        changeType = DiffChangeType.DELETION;
        break;
      case 1: // DIFF_INSERT
        changeType = DiffChangeType.ADDITION;
        break;
      case 0: // DIFF_EQUAL
      default:
        changeType = DiffChangeType.UNCHANGED;
        break;
    }
    
    const changeId = generateChangeId({ type: changeType, content: text, position });
    
    // Only include the change if it's not rejected and not unchanged
    // Unchanged text is automatically included in the original
    if (!rejectedIds.has(changeId) && changeType !== DiffChangeType.UNCHANGED) {
      acceptedChanges.push({
        id: changeId,
        type: changeType,
        content: text,
        position,
        length: text.length
      });
    }
    
    // Update position counter (only increment for non-additions)
    if (changeType !== DiffChangeType.ADDITION) {
      position += text.length;
    }
  }
  
  // Apply the accepted changes to the original text
  return applyAcceptedChanges(originalText, acceptedChanges);
}

/**
 * Locates a specific change by its ID within a diff result
 * 
 * @param diffResult The diff result containing changes
 * @param changeId The ID of the change to find
 * @returns The specific change object if found, null otherwise
 */
export function findChangeById(
  diffResult: DiffResult,
  changeId: string
): DiffChange | null {
  if (!diffResult || !diffResult.changes || !changeId) {
    return null;
  }
  
  for (const change of diffResult.changes) {
    if (change.id === changeId) {
      return change;
    }
  }
  return null;
}

/**
 * Generates a unique ID for a change based on its content and position
 * 
 * @param change The change object requiring an ID
 * @returns Unique identifier for the change
 */
export function generateChangeId(change: Pick<DiffChange, 'type' | 'content' | 'position'>): string {
  if (!change || !change.type || change.content === undefined || change.position === undefined) {
    throw new Error('Invalid change object provided');
  }
  
  // Create a string that combines the properties
  const idBase = `${change.type}-${change.position}-${change.content}`;
  
  // Use a simple hash function to generate a shorter ID
  // In a production environment, consider using a more robust hashing algorithm
  let hash = 0;
  for (let i = 0; i < idBase.length; i++) {
    const char = idBase.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0; // Convert to 32bit integer
  }
  
  // Convert to a positive hex string
  return Math.abs(hash).toString(16);
}

/**
 * Converts a diff result to plain text with markers for additions and deletions
 * 
 * @param diffResult The diff result to convert
 * @param options Configuration options for the output format
 * @returns Plain text representation of changes with markup
 */
export function diffToPlainText(
  diffResult: DiffResult,
  options: {
    additionMarkers?: [string, string];
    deletionMarkers?: [string, string];
  } = {}
): string {
  if (!diffResult || !Array.isArray(diffResult.changes)) {
    return '';
  }
  
  const addMarkers = options.additionMarkers || ['{+', '+}'];
  const delMarkers = options.deletionMarkers || ['[-', '-]'];
  
  let result = '';
  
  for (const change of diffResult.changes) {
    switch (change.type) {
      case DiffChangeType.ADDITION:
        result += `${addMarkers[0]}${change.content}${addMarkers[1]}`;
        break;
      case DiffChangeType.DELETION:
        result += `${delMarkers[0]}${change.content}${delMarkers[1]}`;
        break;
      case DiffChangeType.UNCHANGED:
        result += change.content;
        break;
    }
  }
  
  return result;
}

/**
 * Calculates statistics about the changes in a diff result
 * 
 * @param diffResult The diff result to analyze
 * @returns Statistics including counts of additions, deletions, and total changes
 */
export function getChangeStats(diffResult: DiffResult): object {
  if (!diffResult || !Array.isArray(diffResult.changes)) {
    return {
      additions: 0,
      deletions: 0,
      unchanged: 0,
      total: 0,
      addedCharacters: 0,
      deletedCharacters: 0,
      unchangedCharacters: 0,
      totalCharacters: 0,
      percentageChanged: 0
    };
  }
  
  const stats = {
    additions: 0,
    deletions: 0,
    unchanged: 0,
    total: diffResult.changes.length,
    addedCharacters: 0,
    deletedCharacters: 0,
    unchangedCharacters: 0,
    totalCharacters: diffResult.originalText ? diffResult.originalText.length : 0,
    percentageChanged: 0
  };
  
  for (const change of diffResult.changes) {
    switch (change.type) {
      case DiffChangeType.ADDITION:
        stats.additions++;
        stats.addedCharacters += change.content.length;
        break;
      case DiffChangeType.DELETION:
        stats.deletions++;
        stats.deletedCharacters += change.content.length;
        break;
      case DiffChangeType.UNCHANGED:
        stats.unchanged++;
        stats.unchangedCharacters += change.content.length;
        break;
    }
  }
  
  // Calculate percentage of the document that was changed
  const changedCharacters = stats.addedCharacters + stats.deletedCharacters;
  const totalCharactersWithAdditions = stats.totalCharacters + stats.addedCharacters;
  
  if (totalCharactersWithAdditions > 0) {
    stats.percentageChanged = (changedCharacters / totalCharactersWithAdditions) * 100;
  }
  
  return stats;
}