import { User } from './user';

/**
 * Represents the status of asynchronous operations for document management
 * @version 1.0.0
 */
export enum AsyncStatus {
  IDLE = 'idle',
  LOADING = 'loading',
  SUCCESS = 'success',
  ERROR = 'error'
}

/**
 * Represents different states a document can be in during its lifecycle
 * @version 1.0.0
 */
export enum DocumentState {
  DRAFT = 'draft',
  SAVED = 'saved',
  PROCESSING = 'processing',
  MODIFIED = 'modified',
  REVIEWING = 'reviewing',
  READONLY = 'readonly'
}

/**
 * Represents the status of track changes suggestions
 * @version 1.0.0
 */
export enum ChangeStatus {
  PENDING = 'pending',
  ACCEPTED = 'accepted',
  REJECTED = 'rejected'
}

/**
 * Supported document formats for import/export operations
 * @version 1.0.0
 */
export enum DocumentFormat {
  TEXT = 'text',
  HTML = 'html',
  MARKDOWN = 'markdown',
  DOCX = 'docx',
  PDF = 'pdf'
}

/**
 * Different display modes for track changes
 * @version 1.0.0
 */
export enum TrackChangesMode {
  SHOW_ALL = 'showAll',
  SHOW_PENDING = 'showPending',
  HIDE_ALL = 'hideAll',
  FINAL = 'final',
  ORIGINAL = 'original'
}

/**
 * Statistics and metrics for a document
 * @version 1.0.0
 */
export interface DocumentStats {
  /** Total number of words in the document */
  wordCount: number;
  /** Total number of characters in the document */
  characterCount: number;
  /** Number of paragraphs in the document */
  paragraphCount: number;
  /** Estimated reading time in minutes */
  readingTime: number;
  /** Total number of AI suggestions */
  suggestionCount: number;
  /** Number of suggestions that have been accepted */
  acceptedSuggestions: number;
  /** Number of suggestions that have been rejected */
  rejectedSuggestions: number;
  /** Number of suggestions that are still pending review */
  pendingSuggestions: number;
}

/**
 * Metadata associated with a document
 * @version 1.0.0
 */
export interface DocumentMetadata {
  /** Document title */
  title: string;
  /** User-defined tags for categorization */
  tags: string[];
  /** Date the document was created */
  createdAt: Date;
  /** Date the document was last updated */
  updatedAt: Date;
  /** Date the document was last accessed */
  lastAccessedAt: Date;
  /** Whether the document has been archived */
  isArchived: boolean;
  /** Document format (TEXT, HTML, etc.) */
  format: DocumentFormat;
}

/**
 * Position of a change within a document
 * @version 1.0.0
 */
export interface DocumentChangePosition {
  /** Starting position of the change */
  from: number;
  /** Ending position of the change */
  to: number;
}

/**
 * A suggested change from the AI in a document
 * @version 1.0.0
 */
export interface DocumentChange {
  /** Unique identifier for the change */
  id: string;
  /** Position information for the change */
  position: DocumentChangePosition;
  /** The original text that was modified */
  originalText: string;
  /** The text suggested by the AI */
  suggestedText: string;
  /** Explanation of why the change was suggested */
  explanation: string;
  /** Current status of the change (pending, accepted, rejected) */
  status: ChangeStatus;
  /** When the suggestion was created */
  timestamp: Date;
  /** Source of the suggestion (template name, chat, etc.) */
  sourceType: string;
  /** Additional context or properties for the change */
  metadata: Record<string, any>;
}

/**
 * Represents a version of a document in version history
 * @version 1.0.0
 */
export interface DocumentVersion {
  /** Unique identifier for the version */
  id: string;
  /** ID of the document this version belongs to */
  documentId: string;
  /** Sequential version number */
  versionNumber: number;
  /** Document content at this version */
  content: string;
  /** When this version was created */
  createdAt: Date;
  /** User ID or system identifier that created this version */
  createdBy: string;
  /** Description of changes in this version */
  changeDescription: string;
  /** ID of the previous version, or null if this is the first version */
  previousVersionId: string | null;
}

/**
 * Core interface representing a document with its content, metadata, and track changes
 * @version 1.0.0
 */
export interface Document {
  /** Unique identifier for the document */
  id: string;
  /** ID of the user who owns the document, or null for anonymous documents */
  userId: string | null;
  /** Session ID for anonymous documents, or null for authenticated documents */
  sessionId: string | null;
  /** Main content of the document */
  content: string;
  /** Document metadata */
  metadata: DocumentMetadata;
  /** Current state of the document */
  state: DocumentState;
  /** Array of suggested changes */
  changes: DocumentChange[];
  /** Document statistics */
  stats: DocumentStats;
  /** ID of the current version, or null if no versions exist */
  currentVersionId: string | null;
  /** Whether this is an anonymous document */
  isAnonymous: boolean;
}

/**
 * Data transfer object for creating a new document
 * @version 1.0.0
 */
export interface DocumentCreateDTO {
  /** Document title */
  title: string;
  /** Initial document content */
  content: string;
  /** Optional tags for categorization */
  tags?: string[];
  /** Optional document format */
  format?: DocumentFormat;
  /** Optional session ID for anonymous documents */
  sessionId?: string;
}

/**
 * Data transfer object for updating an existing document
 * @version 1.0.0
 */
export interface DocumentUpdateDTO {
  /** Updated document content (optional) */
  content?: string;
  /** Updated document title (optional) */
  title?: string;
  /** Updated document tags (optional) */
  tags?: string[];
  /** Updated document changes (optional) */
  changes?: DocumentChange[];
  /** Updated archive status (optional) */
  isArchived?: boolean;
}

/**
 * Interface for filtering documents in listings and searches
 * @version 1.0.0
 */
export interface DocumentFilter {
  /** Filter by user ID */
  userId?: string;
  /** Filter by session ID (for anonymous documents) */
  sessionId?: string;
  /** Filter by document title (partial match) */
  title?: string;
  /** Filter by tags (any match) */
  tags?: string[];
  /** Filter by archive status */
  isArchived?: boolean;
  /** Filter for documents created/updated after this date */
  fromDate?: Date;
  /** Filter for documents created/updated before this date */
  toDate?: Date;
}

/**
 * Interface for paginated document list responses
 * @version 1.0.0
 */
export interface DocumentListResponse {
  /** Array of documents in the current page */
  documents: Document[];
  /** Total number of documents matching the filter */
  total: number;
  /** Current page number (1-based) */
  page: number;
  /** Number of documents per page */
  pageSize: number;
  /** Total number of pages */
  totalPages: number;
}

/**
 * Interface for document export configuration options
 * @version 1.0.0
 */
export interface DocumentExportOptions {
  /** Target format for export */
  format: DocumentFormat;
  /** Whether to include track changes in the export */
  includeTrackChanges: boolean;
  /** Optional filename for the exported document */
  fileName?: string;
  /** Additional format-specific export options */
  options?: Record<string, any>;
}

/**
 * Interface for document import configuration options
 * @version 1.0.0
 */
export interface DocumentImportOptions {
  /** Source format of the document */
  format?: DocumentFormat;
  /** Whether to automatically detect the document format */
  autoDetectFormat: boolean;
  /** Additional format-specific import options */
  options?: Record<string, any>;
}