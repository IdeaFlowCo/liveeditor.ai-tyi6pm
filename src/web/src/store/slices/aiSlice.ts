import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import {
  AiState,
  ProcessingStatus,
  SuggestionType,
  PromptTemplate,
  ChatMessage,
  ChatRole,
  ChatConversation,
  AiError
} from '../types/ai';
import {
  SuggestionResponse,
  SuggestionRequest
} from '../types/suggestion';
import {
  generateSuggestions,
  processSuggestionDecisions,
  submitSuggestionFeedback
} from '../api/suggestions';
import {
  sendChatMessage,
  createNewConversation,
  getChatHistory,
  deleteConversation
} from '../api/chat';
import {
  getTemplates,
  getTemplateById
} from '../api/templates';

/**
 * Async thunk that sends a request to generate AI suggestions for document content
 */
export const requestSuggestions = createAsyncThunk(
  'ai/requestSuggestions',
  async (request: SuggestionRequest, { rejectWithValue }) => {
    try {
      // Log the suggestion request for analytics
      console.log('Requesting suggestions:', request);
      const response = await generateSuggestions(request);
      return response;
    } catch (error) {
      console.error('Error requesting suggestions:', error);
      return rejectWithValue({
        message: error instanceof Error ? error.message : 'Failed to generate suggestions',
        code: 'SUGGESTION_ERROR',
        details: error,
        retry: true
      });
    }
  }
);

/**
 * Async thunk that accepts a specific suggestion and applies it to the document
 */
export const acceptSuggestion = createAsyncThunk(
  'ai/acceptSuggestion',
  async ({ suggestionId, documentId }: { suggestionId: string, documentId: string }, { rejectWithValue }) => {
    try {
      const response = await processSuggestionDecisions({
        documentId,
        acceptedSuggestionIds: [suggestionId],
        rejectedSuggestionIds: []
      });
      return { success: response.success, suggestionId };
    } catch (error) {
      console.error('Error accepting suggestion:', error);
      return rejectWithValue({
        message: error instanceof Error ? error.message : 'Failed to accept suggestion',
        code: 'ACCEPT_SUGGESTION_ERROR',
        details: error,
        retry: true
      });
    }
  }
);

/**
 * Async thunk that rejects a specific suggestion
 */
export const rejectSuggestion = createAsyncThunk(
  'ai/rejectSuggestion',
  async ({ suggestionId, documentId }: { suggestionId: string, documentId: string }, { rejectWithValue }) => {
    try {
      const response = await processSuggestionDecisions({
        documentId,
        acceptedSuggestionIds: [],
        rejectedSuggestionIds: [suggestionId]
      });
      return { success: response.success, suggestionId };
    } catch (error) {
      console.error('Error rejecting suggestion:', error);
      return rejectWithValue({
        message: error instanceof Error ? error.message : 'Failed to reject suggestion',
        code: 'REJECT_SUGGESTION_ERROR',
        details: error,
        retry: true
      });
    }
  }
);

/**
 * Async thunk that submits user feedback on suggestion quality
 */
export const rateSuggestion = createAsyncThunk(
  'ai/rateSuggestion',
  async ({ suggestionId, rating, feedback }: { suggestionId: string, rating: number, feedback?: string }, { rejectWithValue }) => {
    try {
      const response = await submitSuggestionFeedback({
        suggestionId,
        rating,
        comment: feedback || null
      });
      return { success: response.success, suggestionId };
    } catch (error) {
      console.error('Error rating suggestion:', error);
      return rejectWithValue({
        message: error instanceof Error ? error.message : 'Failed to submit feedback',
        code: 'RATE_SUGGESTION_ERROR',
        details: error,
        retry: false
      });
    }
  }
);

/**
 * Async thunk that fetches all available prompt templates
 */
export const fetchTemplates = createAsyncThunk(
  'ai/fetchTemplates',
  async (_, { rejectWithValue }) => {
    try {
      const templates = await getTemplates();
      return templates;
    } catch (error) {
      console.error('Error fetching templates:', error);
      return rejectWithValue({
        message: error instanceof Error ? error.message : 'Failed to fetch templates',
        code: 'FETCH_TEMPLATES_ERROR',
        details: error,
        retry: true
      });
    }
  }
);

/**
 * Async thunk that sends a user message to the AI chat assistant
 */
export const sendChatMessageThunk = createAsyncThunk(
  'ai/sendChatMessage',
  async ({ message, conversationId, documentId, documentContext }: 
    { message: string, conversationId?: string, documentId?: string, documentContext?: string }, 
    { dispatch, rejectWithValue }
  ) => {
    try {
      // Create a new conversation if conversationId is not provided
      let activeConversationId = conversationId;
      
      if (!activeConversationId) {
        const newConversation = await createNewConversation(documentId || null, documentContext || null);
        activeConversationId = newConversation.id;
        
        // Update the current conversation in the state
        dispatch(setCurrentConversation(newConversation));
      }
      
      // Send the message to the active conversation
      const response = await sendChatMessage({
        message,
        conversationId: activeConversationId,
        documentId: documentId || null,
        documentContext: documentContext || null
      });
      
      return response;
    } catch (error) {
      console.error('Error sending chat message:', error);
      return rejectWithValue({
        message: error instanceof Error ? error.message : 'Failed to send chat message',
        code: 'CHAT_MESSAGE_ERROR',
        details: error,
        retry: true
      });
    }
  }
);

/**
 * Async thunk that creates a new chat conversation
 */
export const createConversation = createAsyncThunk(
  'ai/createConversation',
  async ({ documentId, initialContext }: { documentId?: string, initialContext?: string }, { rejectWithValue }) => {
    try {
      const conversation = await createNewConversation(
        documentId || null, 
        initialContext || null
      );
      
      return {
        conversationId: conversation.id,
        conversation,
        welcomeMessage: conversation.messages[0] || null
      };
    } catch (error) {
      console.error('Error creating conversation:', error);
      return rejectWithValue({
        message: error instanceof Error ? error.message : 'Failed to create conversation',
        code: 'CREATE_CONVERSATION_ERROR',
        details: error,
        retry: true
      });
    }
  }
);

/**
 * Async thunk that loads message history for a conversation
 */
export const loadConversationHistory = createAsyncThunk(
  'ai/loadConversationHistory',
  async (conversationId: string, { rejectWithValue }) => {
    try {
      const conversations = await getChatHistory(conversationId);
      if (conversations.length === 0) {
        return [];
      }
      return conversations[0].messages;
    } catch (error) {
      console.error('Error loading conversation history:', error);
      return rejectWithValue({
        message: error instanceof Error ? error.message : 'Failed to load conversation history',
        code: 'LOAD_CONVERSATION_ERROR',
        details: error,
        retry: true
      });
    }
  }
);

/**
 * Async thunk that deletes a chat conversation
 */
export const deleteConversationThunk = createAsyncThunk(
  'ai/deleteConversation',
  async (conversationId: string, { rejectWithValue }) => {
    try {
      const response = await deleteConversation(conversationId);
      return { success: response.success, conversationId };
    } catch (error) {
      console.error('Error deleting conversation:', error);
      return rejectWithValue({
        message: error instanceof Error ? error.message : 'Failed to delete conversation',
        code: 'DELETE_CONVERSATION_ERROR',
        details: error,
        retry: true
      });
    }
  }
);

// Initial state for the AI slice
const initialState: AiState = {
  processingStatus: ProcessingStatus.IDLE,
  error: null,
  suggestions: [],
  selectedTemplate: null,
  templates: [],
  conversations: {},
  currentConversationId: null,
  availableTokens: 0,
  aiFeatureEnabled: true
};

// Create the AI slice
export const aiSlice = createSlice({
  name: 'ai',
  initialState,
  reducers: {
    setSelectedTemplate: (state, action: PayloadAction<PromptTemplate | null>) => {
      state.selectedTemplate = action.payload;
    },
    clearSuggestions: (state) => {
      state.suggestions = [];
    },
    setCurrentConversation: (state, action: PayloadAction<ChatConversation>) => {
      const conversation = action.payload;
      state.conversations[conversation.id] = conversation;
      state.currentConversationId = conversation.id;
    },
    clearAiError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    // requestSuggestions reducers
    builder
      .addCase(requestSuggestions.pending, (state) => {
        state.processingStatus = ProcessingStatus.REQUESTING;
        state.error = null;
      })
      .addCase(requestSuggestions.fulfilled, (state, action) => {
        state.processingStatus = ProcessingStatus.COMPLETED;
        state.suggestions.push(action.payload);
      })
      .addCase(requestSuggestions.rejected, (state, action) => {
        state.processingStatus = ProcessingStatus.ERROR;
        state.error = action.payload as AiError;
      });

    // acceptSuggestion reducers
    builder
      .addCase(acceptSuggestion.pending, (state) => {
        state.processingStatus = ProcessingStatus.PROCESSING;
      })
      .addCase(acceptSuggestion.fulfilled, (state, action) => {
        state.processingStatus = ProcessingStatus.COMPLETED;
        // Update suggestion status in our state
        state.suggestions.forEach(suggestionResponse => {
          suggestionResponse.suggestions.forEach(suggestion => {
            if (suggestion.id === action.payload.suggestionId) {
              suggestion.status = 'accepted';
            }
          });
        });
      })
      .addCase(acceptSuggestion.rejected, (state, action) => {
        state.processingStatus = ProcessingStatus.ERROR;
        state.error = action.payload as AiError;
      });

    // rejectSuggestion reducers
    builder
      .addCase(rejectSuggestion.pending, (state) => {
        state.processingStatus = ProcessingStatus.PROCESSING;
      })
      .addCase(rejectSuggestion.fulfilled, (state, action) => {
        state.processingStatus = ProcessingStatus.COMPLETED;
        // Update suggestion status in our state
        state.suggestions.forEach(suggestionResponse => {
          suggestionResponse.suggestions.forEach(suggestion => {
            if (suggestion.id === action.payload.suggestionId) {
              suggestion.status = 'rejected';
            }
          });
        });
      })
      .addCase(rejectSuggestion.rejected, (state, action) => {
        state.processingStatus = ProcessingStatus.ERROR;
        state.error = action.payload as AiError;
      });

    // rateSuggestion reducers
    builder
      .addCase(rateSuggestion.pending, (state) => {
        state.processingStatus = ProcessingStatus.PROCESSING;
      })
      .addCase(rateSuggestion.fulfilled, (state) => {
        state.processingStatus = ProcessingStatus.COMPLETED;
        // Rating doesn't require a state update since it's just feedback
      })
      .addCase(rateSuggestion.rejected, (state, action) => {
        state.processingStatus = ProcessingStatus.ERROR;
        state.error = action.payload as AiError;
      });

    // fetchTemplates reducers
    builder
      .addCase(fetchTemplates.pending, (state) => {
        state.processingStatus = ProcessingStatus.REQUESTING;
      })
      .addCase(fetchTemplates.fulfilled, (state, action) => {
        state.processingStatus = ProcessingStatus.COMPLETED;
        state.templates = action.payload;
        // Clear any previous template selection if the template no longer exists
        if (state.selectedTemplate) {
          if (!action.payload.find(template => template.id === state.selectedTemplate?.id)) {
            state.selectedTemplate = null;
          }
        }
      })
      .addCase(fetchTemplates.rejected, (state, action) => {
        state.processingStatus = ProcessingStatus.ERROR;
        state.error = action.payload as AiError;
      });

    // sendChatMessageThunk reducers
    builder
      .addCase(sendChatMessageThunk.pending, (state) => {
        state.processingStatus = ProcessingStatus.PROCESSING;
      })
      .addCase(sendChatMessageThunk.fulfilled, (state, action) => {
        state.processingStatus = ProcessingStatus.COMPLETED;
        const message = action.payload;
        if (state.currentConversationId && message.conversationId === state.currentConversationId) {
          // Ensure the conversation exists in the state
          if (!state.conversations[message.conversationId]) {
            state.conversations[message.conversationId] = {
              id: message.conversationId,
              title: "New Conversation",
              messages: [],
              createdAt: new Date(),
              updatedAt: new Date(),
              documentId: null,
              userId: null,
              sessionId: null
            };
          }
          
          // Add the new message to the conversation
          state.conversations[message.conversationId].messages.push(message);
          state.conversations[message.conversationId].updatedAt = new Date();
        }
      })
      .addCase(sendChatMessageThunk.rejected, (state, action) => {
        state.processingStatus = ProcessingStatus.ERROR;
        state.error = action.payload as AiError;
      });

    // createConversation reducers
    builder
      .addCase(createConversation.pending, (state) => {
        state.processingStatus = ProcessingStatus.PROCESSING;
      })
      .addCase(createConversation.fulfilled, (state, action) => {
        state.processingStatus = ProcessingStatus.COMPLETED;
        const { conversationId, conversation } = action.payload;
        state.conversations[conversationId] = conversation;
        state.currentConversationId = conversationId;
      })
      .addCase(createConversation.rejected, (state, action) => {
        state.processingStatus = ProcessingStatus.ERROR;
        state.error = action.payload as AiError;
      });

    // loadConversationHistory reducers
    builder
      .addCase(loadConversationHistory.pending, (state) => {
        state.processingStatus = ProcessingStatus.REQUESTING;
      })
      .addCase(loadConversationHistory.fulfilled, (state, action) => {
        state.processingStatus = ProcessingStatus.COMPLETED;
        if (state.currentConversationId && action.payload.length > 0) {
          // Ensure the conversation exists in the state
          if (!state.conversations[state.currentConversationId]) {
            state.conversations[state.currentConversationId] = {
              id: state.currentConversationId,
              title: "Conversation",
              messages: [],
              createdAt: new Date(),
              updatedAt: new Date(),
              documentId: null,
              userId: null,
              sessionId: null
            };
          }
          
          // Update the conversation with the loaded messages
          state.conversations[state.currentConversationId].messages = action.payload;
        }
      })
      .addCase(loadConversationHistory.rejected, (state, action) => {
        state.processingStatus = ProcessingStatus.ERROR;
        state.error = action.payload as AiError;
      });

    // deleteConversationThunk reducers
    builder
      .addCase(deleteConversationThunk.pending, (state) => {
        state.processingStatus = ProcessingStatus.PROCESSING;
      })
      .addCase(deleteConversationThunk.fulfilled, (state, action) => {
        state.processingStatus = ProcessingStatus.COMPLETED;
        const { conversationId } = action.payload;
        
        // Remove the conversation from state
        delete state.conversations[conversationId];
        
        // Reset current conversation ID if it matches the deleted one
        if (state.currentConversationId === conversationId) {
          state.currentConversationId = null;
        }
      })
      .addCase(deleteConversationThunk.rejected, (state, action) => {
        state.processingStatus = ProcessingStatus.ERROR;
        state.error = action.payload as AiError;
      });
  }
});

// Export actions and reducer
export const { setSelectedTemplate, clearSuggestions, setCurrentConversation, clearAiError } = aiSlice.actions;
export const aiReducer = aiSlice.reducer;

// Selectors
/**
 * Selector for the entire AI state
 */
export const selectAiState = (state: { ai: AiState }): AiState => state.ai;

/**
 * Selector for the current AI processing status
 */
export const selectProcessingStatus = (state: { ai: AiState }): ProcessingStatus => state.ai.processingStatus;

/**
 * Selector for getting current AI suggestions
 */
export const selectSuggestions = (state: { ai: AiState }): SuggestionResponse[] => state.ai.suggestions;

/**
 * Selector for getting available prompt templates
 */
export const selectTemplates = (state: { ai: AiState }): PromptTemplate[] => state.ai.templates;

/**
 * Selector for getting the current chat conversation
 */
export const selectCurrentConversation = (state: { ai: AiState }): ChatConversation | null => {
  return state.ai.currentConversationId 
    ? state.ai.conversations[state.ai.currentConversationId] || null 
    : null;
};

/**
 * Selector for getting any AI-related errors
 */
export const selectAiError = (state: { ai: AiState }): AiError | null => state.ai.error;