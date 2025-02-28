import { useState, useEffect, useCallback, useMemo, useRef } from 'react'; // react ^18.2.0
import { useAppDispatch, useAppSelector } from '../store';
import {
  ProcessingStatus,
  SuggestionType,
  PromptTemplate,
  ChatMessage,
  ChatRequest,
  SuggestionRequest,
  SuggestionResponse,
  AiState,
  AiError
} from '../types/ai';
import {
  generateSuggestions,
  generateTextSuggestions,
  generateStyleSuggestions,
  generateGrammarSuggestions,
  processSuggestionDecisions
} from '../api/suggestions';
import {
  sendChatMessage,
  createNewConversation,
  getChatHistory
} from '../api/chat';
import {
  setProcessingStatus,
  clearError,
  setError,
  selectTemplate,
  clearSelectedTemplate,
  addChatMessage,
  clearChat,
  clearSuggestions,
  selectAiState,
  selectProcessingStatus,
  selectSuggestions,
  selectCurrentConversation,
  selectSelectedTemplate,
  selectTemplates,
  fetchTemplates as fetchTemplatesThunk,
  sendChatMessage as sendChatMessageThunk,
  applySuggestionsToDocument
} from '../store/slices/aiSlice';
import {
  AI_PROCESSING_STATES,
  SUGGESTION_TYPES,
  DEFAULT_PROMPT_TEMPLATES
} from '../constants/ai';
import useDocument from './useDocument';

/**
 * Custom hook that provides AI functionality for working with document content
 * @returns AI state and functions for interacting with AI capabilities
 */
function useAi() {
  // Initialize Redux dispatch and selectors for AI state
  const dispatch = useAppDispatch();
  const aiState = useAppSelector(selectAiState);
  const processingStatus = useAppSelector(selectProcessingStatus);
  const suggestions = useAppSelector(selectSuggestions);
  const currentConversation = useAppSelector(selectCurrentConversation);
  const selectedTemplate = useAppSelector(selectSelectedTemplate);
  const templates = useAppSelector(selectTemplates);

  // Get document state from useDocument hook
  const { documentContent } = useDocument();

  // Set up local state for selected text and chat input
  const [selectedText, setSelectedText] = useState<string>('');
  const [chatInput, setChatInput] = useState<string>('');

  // Implement useEffect to load templates on initial render
  useEffect(() => {
    dispatch(fetchTemplatesThunk());
  }, [dispatch]);

  /**
   * Implement generateSuggestion function to request AI suggestions for text
   * @param promptType - The type of suggestion to generate
   */
  const generateSuggestion = useCallback(async (promptType: SuggestionType | null, customPrompt: string | null = null) => {
    if (!documentContent) {
      dispatch(setError({ message: 'Document content is required to generate suggestions.', code: 'NO_DOCUMENT_CONTENT', details: null, retry: false }));
      return;
    }

    dispatch(setProcessingStatus(ProcessingStatus.REQUESTING));
    dispatch(clearError());

    const suggestionRequest: SuggestionRequest = {
      documentId: null, // TODO: Implement document ID
      documentContent: documentContent,
      selection: selectedText
        ? {
          startPosition: 0, // TODO: Implement start position
          endPosition: selectedText.length, // TODO: Implement end position
          selectedText: selectedText,
        }
        : null,
      promptType: promptType,
      customPrompt: customPrompt,
      templateId: selectedTemplate ? selectedTemplate.id : null,
      options: null,
    };

    try {
      const response = await dispatch(generateSuggestions(suggestionRequest)).unwrap();
      console.log('AI Suggestion Response:', response);
      dispatch(setProcessingStatus(ProcessingStatus.COMPLETED));
    } catch (error: any) {
      console.error('Error generating suggestion:', error);
      dispatch(setProcessingStatus(ProcessingStatus.ERROR));
      dispatch(setError({ message: error.message, code: error.code, details: error.details, retry: error.retry }));
    }
  }, [documentContent, selectedText, selectedTemplate, dispatch]);

  /**
   * Implement handleTemplateSelect function to process template selections
   * @param template - The template to select
   */
  const handleTemplateSelect = useCallback((template: PromptTemplate) => {
    dispatch(selectTemplate(template));
    // Automatically generate suggestion when a template is selected
    generateSuggestion(template.templateType, template.promptText);
  }, [dispatch, generateSuggestion]);

  /**
   * Implement acceptSuggestion function to accept AI suggestions
   * @param suggestionId - The ID of the suggestion to accept
   */
  const acceptSuggestion = useCallback(async (suggestionId: string) => {
    // TODO: Implement accept suggestion logic
    console.log('Accepting suggestion:', suggestionId);
  }, []);

  /**
   * Implement rejectSuggestion function to reject AI suggestions
   * @param suggestionId - The ID of the suggestion to reject
   */
  const rejectSuggestion = useCallback(async (suggestionId: string) => {
    // TODO: Implement reject suggestion logic
    console.log('Rejecting suggestion:', suggestionId);
  }, []);

  /**
   * Implement acceptAllSuggestions function to accept all suggestions at once
   */
  const acceptAllSuggestions = useCallback(async () => {
    // TODO: Implement accept all suggestions logic
    console.log('Accepting all suggestions');
  }, []);

  /**
   * Implement rejectAllSuggestions function to reject all suggestions at once
   */
  const rejectAllSuggestions = useCallback(async () => {
    // TODO: Implement reject all suggestions logic
    console.log('Rejecting all suggestions');
  }, []);

  /**
   * Implement clearSuggestionsState function to reset suggestion state
   */
  const clearSuggestionsState = useCallback(() => {
    dispatch(clearSuggestions());
    dispatch(clearSelectedTemplate());
  }, [dispatch]);

  /**
   * Implement sendMessage function for chat interface
   * @param message - The message to send
   */
  const sendMessage = useCallback(async (message: string) => {
    if (!message) {
      dispatch(setError({ message: 'Message content is required to send a message.', code: 'NO_MESSAGE_CONTENT', details: null, retry: false }));
      return;
    }

    dispatch(setProcessingStatus(ProcessingStatus.REQUESTING));
    dispatch(clearError());

    const chatRequest: ChatRequest = {
      message: message,
      conversationId: currentConversation ? currentConversation.id : null,
      documentId: null, // TODO: Implement document ID
      documentContext: documentContent,
      selectedText: selectedText,
    };

    try {
      await dispatch(sendChatMessageThunk(chatRequest)).unwrap();
      setChatInput('');
      dispatch(setProcessingStatus(ProcessingStatus.COMPLETED));
    } catch (error: any) {
      console.error('Error sending chat message:', error);
      dispatch(setProcessingStatus(ProcessingStatus.ERROR));
      dispatch(setError({ message: error.message, code: error.code, details: error.details, retry: error.retry }));
    }
  }, [currentConversation, documentContent, selectedText, dispatch]);

  /**
   * Implement startNewChat function to begin new chat conversations
   */
  const startNewChat = useCallback(async () => {
    dispatch(clearChat());
    // TODO: Implement start new chat logic
    console.log('Starting new chat');
  }, [dispatch]);

  /**
   * Implement clearChatHistory function to reset chat state
   */
  const clearChatHistory = useCallback(() => {
    dispatch(clearChat());
  }, [dispatch]);

  /**
   * Implement applyGeneratedContent function to apply AI suggestions to document
   */
  const applyGeneratedContent = useCallback(async () => {
    // TODO: Implement apply generated content logic
    console.log('Applying generated content');
  }, []);

  // Return AI state and all functions in a single object
  return {
    processingStatus: aiState.processingStatus,
    isProcessing: aiState.processingStatus === ProcessingStatus.PROCESSING || aiState.processingStatus === ProcessingStatus.REQUESTING,
    error: aiState.error,
    suggestions: suggestions,
    selectedTemplate: aiState.selectedTemplate,
    templates: aiState.templates,
    currentChat: aiState.currentConversationId ? aiState.conversations[aiState.currentConversationId] : null,
    chatInput,
    setChatInput,
    selectedText,
    setSelectedText,
    generateSuggestion,
    handleTemplateSelect,
    acceptSuggestion,
    rejectSuggestion,
    acceptAllSuggestions,
    rejectAllSuggestions,
    clearSuggestions: clearSuggestionsState,
    sendMessage,
    startNewChat,
    clearChatHistory,
    applyGeneratedContent
  };
}

export default useAi;