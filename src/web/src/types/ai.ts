import { Document } from './document';

/**
 * Enum for tracking the current state of AI processing operations
 * @version 1.0.0
 */
export enum ProcessingStatus {
  IDLE = 'idle',
  REQUESTING = 'requesting',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  ERROR = 'error'
}

/**
 * Enum representing different types of AI suggestions and improvement categories
 * @version 1.0.0
 */
export enum SuggestionType {
  SHORTER = 'shorter',
  PROFESSIONAL = 'professional',
  GRAMMAR = 'grammar',
  CLARITY = 'clarity',
  TONE = 'tone',
  STYLE = 'style',
  ACADEMIC = 'academic',
  CREATIVE = 'creative',
  CUSTOM = 'custom'
}

/**
 * Enum representing message sender roles in the chat interface
 * @version 1.0.0
 */
export enum ChatRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system'
}

/**
 * Interface for predefined improvement prompt templates available in the sidebar
 * @version 1.0.0
 */
export interface PromptTemplate {
  /** Unique identifier for the template */
  id: string;
  /** Display name of the template */
  name: string;
  /** Detailed description of what the template does */
  description: string;
  /** The actual prompt text sent to the AI */
  promptText: string;
  /** Category for grouping templates */
  category: string;
  /** Whether this is a system-provided template that cannot be modified */
  isSystem: boolean;
  /** Optional icon identifier for the template */
  icon: string | null;
  /** The type of suggestion this template generates */
  templateType: SuggestionType;
}

/**
 * Interface representing a message in the AI chat interface
 * @version 1.0.0
 */
export interface ChatMessage {
  /** Unique identifier for the message */
  id: string;
  /** ID of the conversation this message belongs to */
  conversationId: string;
  /** Role of the message sender (user, assistant, system) */
  role: ChatRole;
  /** Text content of the message */
  content: string;
  /** When the message was sent */
  timestamp: Date;
  /** Additional metadata for the message */
  metadata: Record<string, any> | null;
}

/**
 * Interface representing a conversation thread in the chat interface
 * @version 1.0.0
 */
export interface ChatConversation {
  /** Unique identifier for the conversation */
  id: string;
  /** User-provided or auto-generated title for the conversation */
  title: string;
  /** Array of messages in the conversation */
  messages: ChatMessage[];
  /** When the conversation was created */
  createdAt: Date;
  /** When the conversation was last updated */
  updatedAt: Date;
  /** Optional ID of the document this conversation is associated with */
  documentId: string | null;
  /** Optional ID of the authenticated user who owns this conversation */
  userId: string | null;
  /** Optional session ID for anonymous users */
  sessionId: string | null;
}

/**
 * Interface for AI suggestion request payloads sent to the backend
 * @version 1.0.0
 */
export interface SuggestionRequest {
  /** Optional ID of the document being improved */
  documentId: string | null;
  /** Content of the document being analyzed */
  documentContent: string;
  /** Optional selection within the document for targeted improvements */
  selection: { 
    startPosition: number; 
    endPosition: number; 
    selectedText: string 
  } | null;
  /** Type of improvement being requested */
  promptType: SuggestionType | null;
  /** Custom prompt text for free-form requests */
  customPrompt: string | null;
  /** ID of the template being used, if applicable */
  templateId: string | null;
  /** Additional options for the AI processing */
  options: Record<string, any> | null;
}

/**
 * Interface for AI suggestion response data from the backend
 * @version 1.0.0
 */
export interface SuggestionResponse {
  /** Unique identifier for the request that generated these suggestions */
  requestId: string;
  /** Array of text improvement suggestions */
  suggestions: Array<{
    /** Unique identifier for this suggestion */
    id: string;
    /** Original text that was analyzed */
    originalText: string;
    /** Improved text suggested by the AI */
    suggestedText: string;
    /** Explanation of why this change was suggested */
    explanation: string;
    /** Position information for the suggestion */
    position: {
      /** Starting position in the document */
      start: number;
      /** Ending position in the document */
      end: number;
    }
  }>;
  /** ID of the document these suggestions apply to */
  documentId: string | null;
  /** The prompt that was used to generate these suggestions */
  promptUsed: string | null;
  /** Status of the suggestion generation process */
  status: string;
  /** Error message if the process failed */
  errorMessage: string | null;
  /** Additional metadata about the suggestions */
  metadata: Record<string, any> | null;
  /** Time taken to process the suggestions in milliseconds */
  processingTime: number;
}

/**
 * Interface for chat message request payloads sent to the backend
 * @version 1.0.0
 */
export interface ChatRequest {
  /** Message content entered by the user */
  message: string;
  /** Optional ID of an existing conversation to continue */
  conversationId: string | null;
  /** Optional ID of the document to provide context */
  documentId: string | null;
  /** Optional document content to provide context */
  documentContext: string | null;
  /** Optional text selection to focus the chat on */
  selectedText: string | null;
  /** Optional session ID for anonymous users */
  sessionId: string | null;
}

/**
 * Interface for AI-specific errors with information about whether to retry
 * @version 1.0.0
 */
export interface AiError {
  /** Error message */
  message: string;
  /** Error code for programmatic handling */
  code: string;
  /** Additional details about the error */
  details: Record<string, any> | null;
  /** Whether the operation can be retried */
  retry: boolean;
}

/**
 * Interface for the complete AI state in the Redux store
 * @version 1.0.0
 */
export interface AiState {
  /** Current status of AI processing */
  processingStatus: ProcessingStatus;
  /** Current error (if any) */
  error: AiError | null;
  /** Array of suggestion responses */
  suggestions: SuggestionResponse[];
  /** Currently selected template */
  selectedTemplate: PromptTemplate | null;
  /** Available prompt templates */
  templates: PromptTemplate[];
  /** Map of conversation IDs to conversations */
  conversations: Record<string, ChatConversation>;
  /** ID of the currently active conversation */
  currentConversationId: string | null;
  /** Number of AI tokens available to the user (for rate limiting) */
  availableTokens: number;
  /** Whether the AI features are enabled for this user */
  aiFeatureEnabled: boolean;
}

/**
 * Enum for the different display modes of the AI sidebar interface
 * @version 1.0.0
 */
export enum AiSidebarMode {
  TEMPLATES = 'templates',
  CHAT = 'chat',
  REVIEW = 'review'
}