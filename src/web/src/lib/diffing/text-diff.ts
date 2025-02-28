import { DiffChangeType, DiffChange, DiffResult, DiffOptions } from '../../types/suggestion';
import { v4 as uuidv4 } from 'uuid'; // uuid v8.3.2
import * as diff_match_patch from 'diff-match-patch'; // diff-match-patch v1.0.5

/**
 * Default configuration options for the diff algorithm
 */
export const DEFAULT_DIFF_OPTIONS: DiffOptions = {
  ignoreCase: false,
  ignoreWhitespace: false,
  semanticCleanup: true,
  efficientCleanup: true,
  wordGranularity: false,
  changeThreshold: 0.4
};

/**
 * Compares original and modified text to generate a structured diff result
 * 
 * @param originalText The baseline text for comparison
 * @param modifiedText The modified text to compare against the original
 * @param options Configuration options for the diff algorithm
 * @returns Structured representation of text differences
 */
export function computeDiff(
  originalText: string, 
  modifiedText: string, 
  options: DiffOptions = DEFAULT_DIFF_OPTIONS
): DiffResult {
  // Initialize diff_match_patch instance
  const dmp = new diff_match_patch();
  
  // Apply options to customize diff behavior
  let processedOriginal = originalText;
  let processedModified = modifiedText;
  
  if (options.ignoreCase) {
    processedOriginal = processedOriginal.toLowerCase();
    processedModified = processedModified.toLowerCase();
  }
  
  if (options.ignoreWhitespace) {
    // Replace all whitespace with a single space
    processedOriginal = processedOriginal.replace(/\s+/g, ' ');
    processedModified = processedModified.replace(/\s+/g, ' ');
  }
  
  // Compute the diff
  let rawDiff;
  
  if (options.wordGranularity) {
    // Split text into words and generate the diff at word level
    const wordSeparator = /\s+|[,.!?;:'"()\[\]{}]/;
    const originalWords = processedOriginal.split(wordSeparator).filter(Boolean);
    const modifiedWords = processedModified.split(wordSeparator).filter(Boolean);
    
    // Join words with a marker character that won't appear in normal text
    const separator = '\u0001';
    const originalWordText = originalWords.join(separator);
    const modifiedWordText = modifiedWords.join(separator);
    
    rawDiff = dmp.diff_main(originalWordText, modifiedWordText);
    
    // Convert the word-level diff back to character representation
    rawDiff = rawDiff.map(([op, text]) => {
      const words = text.split(separator);
      return [op, words.join(' ')];
    });
  } else {
    // Character-level diff
    rawDiff = dmp.diff_main(processedOriginal, processedModified);
  }
  
  // Apply cleanup to improve diff readability
  if (options.semanticCleanup) {
    dmp.diff_cleanupSemantic(rawDiff);
  }
  
  if (options.efficientCleanup) {
    dmp.diff_cleanupEfficiency(rawDiff);
  }
  
  // Process the raw diff into structured format
  const changes = _processRawDiff(rawDiff, originalText, modifiedText);
  
  // Group adjacent changes of the same type for better readability
  const groupedChanges = _groupAdjacentChanges(changes);
  
  // Generate unique IDs for each change using uuidv4
  const changesWithIds = groupedChanges.map(change => ({
    ...change,
    id: generateChangeId()
  }));
  
  // Return complete DiffResult with changes and metadata
  return {
    changes: changesWithIds,
    originalText,
    modifiedText
  };
}

/**
 * Converts a diff result to HTML with appropriate styling for additions and deletions
 * 
 * @param diffResult The diff result to convert to HTML
 * @param options Optional configuration for HTML rendering
 * @returns HTML representation of the diff with styling
 */
export function formatDiffAsHTML(
  diffResult: DiffResult, 
  options: {
    addedClass?: string;
    deletedClass?: string;
    unchangedClass?: string;
    addedPrefix?: string;
    addedSuffix?: string;
    deletedPrefix?: string;
    deletedSuffix?: string;
  } = {}
): string {
  const { 
    addedClass = 'addition', 
    deletedClass = 'deletion', 
    unchangedClass = '',
    addedPrefix = '',
    addedSuffix = '',
    deletedPrefix = '',
    deletedSuffix = ''
  } = options;

  const { changes } = diffResult;
  let html = '';

  // Build HTML string by iterating through changes
  for (const change of changes) {
    const escapedText = _escapeHTML(change.text);
    
    switch (change.type) {
      case DiffChangeType.ADDITION:
        html += `<span class="${addedClass}">${addedPrefix}${escapedText}${addedSuffix}</span>`;
        break;
      case DiffChangeType.DELETION:
        html += `<span class="${deletedClass}">${deletedPrefix}${escapedText}${deletedSuffix}</span>`;
        break;
      case DiffChangeType.UNCHANGED:
        html += unchangedClass 
          ? `<span class="${unchangedClass}">${escapedText}</span>` 
          : escapedText;
        break;
    }
  }

  return html;
}

/**
 * Formats diff result for integration with ProseMirror editor's track changes functionality
 * 
 * @param diffResult The diff result to format for editor integration
 * @returns Editor-compatible diff format
 */
export function formatDiffForEditor(diffResult: DiffResult): object {
  // Convert DiffResult to format compatible with ProseMirror schema
  const editorChanges = diffResult.changes.map(change => {
    return {
      id: change.id,
      type: change.type,
      text: change.text,
      // Transform change positions to editor-specific coordinate system
      from: change.originalStart,
      to: change.originalEnd,
      // Include metadata required for track changes UI components
      meta: {
        explanation: '',  // To be filled in by the calling code
        timestamp: new Date().toISOString(),
        originalText: change.type === DiffChangeType.DELETION ? change.text : '',
        suggestedText: change.type === DiffChangeType.ADDITION ? change.text : ''
      }
    };
  });
  
  // Return editor-compatible representation of changes
  return {
    changes: editorChanges,
    documentId: '', // To be filled in by the calling code
    timestamp: new Date().toISOString()
  };
}

/**
 * Applies selected changes from a diff result to transform original text
 * 
 * @param originalText The original text to transform
 * @param diffResult The diff result containing changes
 * @param selectedChangeIds Array of change IDs to apply
 * @returns Text with selected changes applied
 */
export function applyChangesToText(
  originalText: string, 
  diffResult: DiffResult, 
  selectedChangeIds: string[] = []
): string {
  // Extract changes from diff result
  const { changes } = diffResult;
  
  // Filter changes to only those with IDs in selectedChangeIds
  const changesToApply = selectedChangeIds.length === 0 
    ? changes.filter(change => change.type === DiffChangeType.ADDITION) // Default to only additions if no IDs specified
    : changes.filter(change => selectedChangeIds.includes(change.id));
  
  // Sort changes by position in reverse order to prevent position shifts
  const sortedChanges = [...changesToApply].sort((a, b) => {
    // For deletions, we want to apply later ones first to avoid position shifts
    if (a.type === DiffChangeType.DELETION && b.type === DiffChangeType.DELETION) {
      return b.originalStart - a.originalStart;
    }
    
    // Apply deletions before additions to avoid position confusion
    if (a.type === DiffChangeType.DELETION && b.type !== DiffChangeType.DELETION) {
      return -1;
    }
    
    if (a.type !== DiffChangeType.DELETION && b.type === DiffChangeType.DELETION) {
      return 1;
    }
    
    // For additions, process from start to end
    return a.originalStart - b.originalStart;
  });
  
  // Apply each selected change to the original text
  let result = originalText;
  let offset = 0;  // Track position shifts due to applied changes
  
  for (const change of sortedChanges) {
    const adjustedStart = change.originalStart + offset;
    
    switch (change.type) {
      case DiffChangeType.ADDITION:
        // For additions, insert new text at specified position
        result = result.slice(0, adjustedStart) + change.text + result.slice(adjustedStart);
        offset += change.text.length;
        break;
        
      case DiffChangeType.DELETION:
        // For deletions, remove text at specified position
        const adjustedEnd = change.originalEnd + offset;
        result = result.slice(0, adjustedStart) + result.slice(adjustedEnd);
        offset -= (change.originalEnd - change.originalStart);
        break;
        
      // Unchanged text doesn't need modification
      case DiffChangeType.UNCHANGED:
        break;
    }
  }
  
  return result;
}

/**
 * Converts diff result to plain text, optionally including or excluding deletions
 * 
 * @param diffResult The diff result to convert
 * @param includeDeletedText Whether to include deleted text in the output
 * @returns Plain text representation of the diff
 */
export function diffToPlainText(
  diffResult: DiffResult, 
  includeDeletedText: boolean = false
): string {
  let text = '';
  
  for (const change of diffResult.changes) {
    switch (change.type) {
      case DiffChangeType.ADDITION:
      case DiffChangeType.UNCHANGED:
        text += change.text;
        break;
      case DiffChangeType.DELETION:
        if (includeDeletedText) {
          text += change.text;
        }
        break;
    }
  }
  
  return text;
}

/**
 * Calculates statistics about the changes identified in a diff result
 * 
 * @param diffResult The diff result to analyze
 * @returns Statistics including counts and percentages of changes
 */
export function getChangeStatistics(diffResult: DiffResult): {
  totalCharacters: number;
  charactersChanged: number;
  percentageChanged: number;
  additions: number;
  deletions: number;
  changeBlocks: number;
} {
  let totalOriginal = 0;
  let totalAdded = 0;
  let totalDeleted = 0;
  let additionBlocks = 0;
  let deletionBlocks = 0;
  
  for (const change of diffResult.changes) {
    switch (change.type) {
      case DiffChangeType.ADDITION:
        totalAdded += change.text.length;
        additionBlocks++;
        break;
      case DiffChangeType.DELETION:
        totalDeleted += change.text.length;
        deletionBlocks++;
        break;
      case DiffChangeType.UNCHANGED:
        totalOriginal += change.text.length;
        break;
    }
  }
  
  // Original text includes unchanged + deleted
  const totalOriginalChars = totalOriginal + totalDeleted;
  const totalChangedChars = totalAdded + totalDeleted;
  const percentageChanged = totalOriginalChars > 0 
    ? (totalChangedChars / totalOriginalChars) * 100 
    : 0;
  
  return {
    totalCharacters: totalOriginalChars,
    charactersChanged: totalChangedChars,
    percentageChanged: Number(percentageChanged.toFixed(2)),
    additions: additionBlocks,
    deletions: deletionBlocks,
    changeBlocks: additionBlocks + deletionBlocks
  };
}

/**
 * Finds the change that affects a specific position in the original text
 * 
 * @param diffResult The diff result to search
 * @param position Position in the original text
 * @returns Change affecting the specified position, or null if none found
 */
export function findChangeAtPosition(
  diffResult: DiffResult, 
  position: number
): DiffChange | null {
  for (const change of diffResult.changes) {
    // Filter changes to find those whose range includes the specified position
    if (change.type !== DiffChangeType.ADDITION) {
      if (position >= change.originalStart && position < change.originalEnd) {
        return change;
      }
    }
  }
  
  return null;
}

/**
 * Generates a unique identifier for a change
 * 
 * @returns Unique identifier
 */
export function generateChangeId(): string {
  return uuidv4();
}

/**
 * Internal function to process raw diff_match_patch output into structured format
 * 
 * @param rawDiff Raw diff from diff_match_patch
 * @param originalText Original text that was compared
 * @param modifiedText Modified text that was compared
 * @returns Array of structured diff changes
 */
function _processRawDiff(
  rawDiff: Array<[number, string]>, 
  originalText: string, 
  modifiedText: string
): DiffChange[] {
  const changes: DiffChange[] = [];
  let originalPos = 0;
  let modifiedPos = 0;
  
  for (const [operation, text] of rawDiff) {
    let type: DiffChangeType;
    let originalStart = originalPos;
    let originalEnd = originalPos;
    let modifiedStart = modifiedPos;
    let modifiedEnd = modifiedPos;
    
    // Map diff_match_patch operations to our DiffChangeType
    // diff_match_patch uses: -1 for deletion, 0 for equality, 1 for insertion
    switch (operation) {
      case -1: // Deletion
        type = DiffChangeType.DELETION;
        originalEnd += text.length;
        originalPos += text.length;
        break;
      case 0: // Equality
        type = DiffChangeType.UNCHANGED;
        originalEnd += text.length;
        modifiedEnd += text.length;
        originalPos += text.length;
        modifiedPos += text.length;
        break;
      case 1: // Insertion
        type = DiffChangeType.ADDITION;
        modifiedEnd += text.length;
        modifiedPos += text.length;
        break;
      default:
        throw new Error(`Unknown diff operation: ${operation}`);
    }
    
    changes.push({
      id: '',  // Will be populated later with unique ID
      type,
      text,
      originalStart,
      originalEnd,
      modifiedStart,
      modifiedEnd
    });
  }
  
  return changes;
}

/**
 * Internal function to group adjacent changes of the same type
 * 
 * @param changes Array of diff changes
 * @returns Array of grouped changes
 */
function _groupAdjacentChanges(changes: DiffChange[]): DiffChange[] {
  if (changes.length <= 1) {
    return changes;
  }
  
  const result: DiffChange[] = [];
  let current = changes[0];
  
  for (let i = 1; i < changes.length; i++) {
    const next = changes[i];
    
    // Check if the current and next changes are of the same type and adjacent
    const sameType = current.type === next.type;
    const adjacentOriginal = current.originalEnd === next.originalStart;
    const adjacentModified = current.modifiedEnd === next.modifiedStart;
    
    if (sameType && (adjacentOriginal || adjacentModified)) {
      // Merge the changes
      current = {
        ...current,
        text: current.text + next.text,
        originalEnd: next.originalEnd,
        modifiedEnd: next.modifiedEnd
      };
    } else {
      // Add the current change to the result and start a new current
      result.push(current);
      current = next;
    }
  }
  
  // Add the last current change
  result.push(current);
  
  return result;
}

/**
 * Helper function to escape HTML special characters
 * 
 * @param text Text to escape
 * @returns Escaped text safe for HTML insertion
 */
function _escapeHTML(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}