import { Document } from './document';
import { SuggestionType } from './ai';

/**
 * Defines the different types of text changes that can be suggested
 * @version 1.0.0
 */
export enum ChangeType {
  ADDITION = 'addition',
  DELETION = 'deletion',
  REPLACEMENT = 'replacement',
  FORMATTING = 'formatting'
}

/**
 * Defines the possible review statuses of a suggestion
 * @version 1.0.0
 */
export enum SuggestionStatus {
  PENDING = 'pending',
  ACCEPTED = 'accepted',
  REJECTED = 'rejected'
}

/**
 * Represents a selected portion of text in the document
 * @version 1.0.0
 */
export interface TextSelection {
  /** Starting position of the selection */
  from: number;
  /** Ending position of the selection */
  to: number;
  /** The selected text content */
  text: string;
}

/**
 * Represents a position range in the document where a suggestion applies
 * @version 1.0.0
 */
export interface Position {
  /** Starting position of the suggestion */
  from: number;
  /** Ending position of the suggestion */
  to: number;
}

/**
 * Core interface representing a single document suggestion
 * @version 1.0.0
 */
export interface Suggestion {
  /** Unique identifier for the suggestion */
  id: string;
  /** ID of the document this suggestion applies to */
  documentId: string;
  /** Type of change (addition, deletion, etc.) */
  changeType: ChangeType;
  /** Current status of the suggestion (pending, accepted, rejected) */
  status: SuggestionStatus;
  /** Category of the suggestion based on improvement type */
  category: SuggestionType;
  /** Position information for the suggestion */
  position: Position;
  /** The original text that was analyzed */
  originalText: string;
  /** The text suggested by the AI */
  suggestedText: string;
  /** Explanation of why the change was suggested */
  explanation: string;
  /** When the suggestion was created */
  createdAt: Date;
}

/**
 * Extended suggestion interface with detailed diff information for display
 * @version 1.0.0
 */
export interface SuggestionWithDiff {
  /** The base suggestion object */
  suggestion: Suggestion;
  /** HTML representation of the difference for display */
  diffHtml: string;
  /** Detailed operations for the diff */
  diffOperations: Array<{ type: 'insert' | 'delete' | 'equal'; text: string }>;
}

/**
 * Represents a group of related suggestions from a single AI response
 * @version 1.0.0
 */
export interface SuggestionGroup {
  /** Unique identifier for the group */
  id: string;
  /** ID of the document these suggestions apply to */
  documentId: string;
  /** Category of suggestions in this group */
  category: SuggestionType;
  /** The prompt that was used to generate these suggestions */
  prompt: string;
  /** Array of suggestions in this group */
  suggestions: Suggestion[];
  /** When the suggestion group was created */
  createdAt: Date;
}

/**
 * Statistics about suggestion status counts for tracking and display
 * @version 1.0.0
 */
export interface SuggestionStats {
  /** Total number of suggestions */
  total: number;
  /** Number of accepted suggestions */
  accepted: number;
  /** Number of rejected suggestions */
  rejected: number;
  /** Number of pending suggestions */
  pending: number;
  /** Counts by suggestion category */
  byCategory: Record<string, number>;
}

/**
 * Parameters for requesting suggestions from the AI service
 * @version 1.0.0
 */
export interface SuggestionRequest {
  /** ID of the document to analyze */
  documentId: string;
  /** Content of the document to analyze */
  content: string;
  /** Optional text selection for targeted improvements */
  selection: TextSelection | null;
  /** Category of improvement to apply */
  category: SuggestionType;
  /** Optional custom prompt text for specific instructions */
  customPrompt: string | null;
}

/**
 * Response from the AI service containing generated suggestions
 * @version 1.0.0
 */
export interface SuggestionResponse {
  /** ID of the suggestion group created */
  suggestionGroupId: string;
  /** Array of suggestions generated */
  suggestions: Suggestion[];
  /** The prompt that was used for generation */
  promptUsed: string;
  /** Time taken to process the suggestions in milliseconds */
  processingTime: number;
}

/**
 * Request containing multiple suggestion requests to be processed as a batch
 * @version 1.0.0
 */
export interface SuggestionBatchRequest {
  /** Array of suggestion requests to process */
  requests: SuggestionRequest[];
}

/**
 * Request for processing user decisions on accepting or rejecting suggestions
 * @version 1.0.0
 */
export interface SuggestionAcceptRejectRequest {
  /** ID of the document being updated */
  documentId: string;
  /** Array of suggestion IDs to accept */
  acceptedSuggestionIds: string[];
  /** Array of suggestion IDs to reject */
  rejectedSuggestionIds: string[];
}

/**
 * Request for submitting user feedback on suggestion quality
 * @version 1.0.0
 */
export interface SuggestionFeedbackRequest {
  /** ID of the suggestion being rated */
  suggestionId: string;
  /** User rating (typically 1-5) */
  rating: number;
  /** Optional comment about the suggestion quality */
  comment: string | null;
}

/**
 * Redux state structure for managing suggestions and track changes
 * @version 1.0.0
 */
export interface SuggestionState {
  /** Map of suggestion group IDs to suggestion groups */
  groups: Record<string, SuggestionGroup>;
  /** Map of suggestion IDs to suggestions */
  suggestions: Record<string, Suggestion>;
  /** ID of the currently selected suggestion, or null if none selected */
  currentSuggestionId: string | null;
  /** Whether suggestions are currently being loaded */
  loading: boolean;
  /** Error message if suggestion loading failed */
  error: string | null;
  /** Suggestion statistics */
  stats: SuggestionStats;
}