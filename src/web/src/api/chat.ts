/**
 * API client module for AI chat services
 * 
 * Handles communication with the backend AI chat services, providing functions for
 * sending chat messages, creating conversations, managing chat history, and
 * contextual chat processing with document content.
 *
 * @module api/chat
 * @version 1.0.0
 */

import { post, get } from '../utils/api';
import { ENDPOINTS } from '../constants/api';
import { 
  ChatRequest, 
  ChatMessage, 
  ChatConversation, 
  ChatRole 
} from '../types/ai';

/**
 * Sends a chat message to the AI assistant and returns the assistant's response
 * 
 * @param request - The chat request containing message and context information
 * @returns Promise resolving to the AI assistant's response message
 * @throws Error if the message content is empty or if the API request fails
 */
export const sendChatMessage = async (request: ChatRequest): Promise<ChatMessage> => {
  // Validate request has required message content
  if (!request.message || request.message.trim() === '') {
    throw new Error('Message content is required');
  }

  try {
    // Format request with conversation context if available
    const requestPayload = {
      ...request,
      // Ensure the message is trimmed
      message: request.message.trim(),
    };

    // Make POST request to chat message endpoint
    const response = await post<{ message: ChatMessage }>(
      ENDPOINTS.CHAT.MESSAGE,
      requestPayload
    );

    // Process and return the assistant response
    return response.message;
  } catch (error) {
    console.error('Error sending chat message:', error);
    throw error;
  }
};

/**
 * Creates a new chat conversation with optional document context
 * 
 * @param documentId - Optional ID of the document to associate with the conversation
 * @param documentContext - Optional document content to provide context to the AI
 * @param initialMessage - Optional initial message to start the conversation
 * @returns Promise resolving to the newly created conversation
 * @throws Error if the API request fails
 */
export const createNewConversation = async (
  documentId: string | null = null,
  documentContext: string | null = null,
  initialMessage: string | null = null
): Promise<ChatConversation> => {
  try {
    // Build conversation initialization request with provided parameters
    const requestPayload = {
      documentId,
      documentContext,
      initialMessage,
    };

    // Make POST request to create a new conversation
    const response = await post<ChatConversation>(
      '/chat/conversation/new',
      requestPayload
    );

    // Return the created conversation with initial system message
    return response;
  } catch (error) {
    console.error('Error creating new conversation:', error);
    throw error;
  }
};

/**
 * Retrieves chat history for a specific conversation or document
 * 
 * @param conversationId - Optional ID of the conversation to retrieve
 * @param documentId - Optional ID of the document to get associated conversations
 * @returns Promise resolving to an array of chat conversations
 * @throws Error if no ID is provided or if the API request fails
 */
export const getChatHistory = async (
  conversationId: string | null = null,
  documentId: string | null = null
): Promise<ChatConversation[]> => {
  // Validate that at least one parameter is provided
  if (!conversationId && !documentId) {
    throw new Error('Either conversationId or documentId must be provided');
  }

  try {
    // Build query parameters based on provided IDs
    const params: Record<string, string> = {};
    if (conversationId) {
      params.conversationId = conversationId;
    }
    if (documentId) {
      params.documentId = documentId;
    }

    // Make GET request to chat history endpoint
    const response = await get<{ conversations: ChatConversation[] }>(
      ENDPOINTS.CHAT.HISTORY,
      params
    );

    // Return the retrieved conversations
    return response.conversations;
  } catch (error) {
    console.error('Error fetching chat history:', error);
    throw error;
  }
};

/**
 * Retrieves a specific chat conversation by ID
 * 
 * @param conversationId - ID of the conversation to retrieve
 * @returns Promise resolving to the requested conversation
 * @throws Error if the conversation ID is not provided or if the API request fails
 */
export const getChatConversation = async (
  conversationId: string
): Promise<ChatConversation> => {
  // Validate the conversation ID is provided
  if (!conversationId) {
    throw new Error('Conversation ID is required');
  }

  try {
    // Make GET request to specific conversation endpoint
    const response = await get<ChatConversation>(
      `/chat/conversation/${conversationId}`
    );

    // Return the conversation data with messages
    return response;
  } catch (error) {
    console.error(`Error fetching conversation ${conversationId}:`, error);
    throw error;
  }
};

/**
 * Creates a context-aware prompt based on document content for improved AI responses
 * 
 * @param documentContent - The document content to create context from
 * @param selectedText - Optional text selection to focus the context on
 * @returns Promise resolving to optimized context prompt
 * @throws Error if document content is empty or if the API request fails
 */
export const generateDocumentContextPrompt = async (
  documentContent: string,
  selectedText: string | null = null
): Promise<string> => {
  // Validate document content is provided
  if (!documentContent || documentContent.trim() === '') {
    throw new Error('Document content is required for context generation');
  }

  try {
    // Format the document content into a condensed context
    // Highlight the selected text if provided
    const requestPayload = {
      documentContent: documentContent.trim(),
      selectedText: selectedText ? selectedText.trim() : null,
    };

    // Make POST request to context generation endpoint
    const response = await post<{ contextPrompt: string }>(
      '/chat/context',
      requestPayload
    );

    // Return the optimized context prompt
    return response.contextPrompt;
  } catch (error) {
    console.error('Error generating document context prompt:', error);
    throw error;
  }
};

/**
 * Deletes a specific chat conversation
 * 
 * @param conversationId - ID of the conversation to delete
 * @returns Promise resolving to success status
 * @throws Error if the conversation ID is not provided or if the API request fails
 */
export const deleteConversation = async (
  conversationId: string
): Promise<{ success: boolean }> => {
  // Validate conversation ID is provided
  if (!conversationId) {
    throw new Error('Conversation ID is required');
  }

  try {
    // Make POST request with delete action since 'del' is not imported
    const response = await post<{ success: boolean }>(
      `/chat/conversation/${conversationId}/delete`,
      { conversationId }
    );

    // Return success status from API
    return response;
  } catch (error) {
    console.error(`Error deleting conversation ${conversationId}:`, error);
    throw error;
  }
};