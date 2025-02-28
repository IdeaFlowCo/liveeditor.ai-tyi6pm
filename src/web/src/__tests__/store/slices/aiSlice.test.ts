import { describe, it, expect, beforeEach } from '@jest/globals'; // ^29.5.0
import { configureStore } from '@reduxjs/toolkit'; // ^1.9.5
import {
  aiReducer, initialState, 
  startSuggestion, completeSuggestion, suggestionError,
  startChat, messageReceived, chatError, resetAiState,
  selectAiState, selectSuggestions, selectChat, selectIsLoading, selectError
} from '../../../store/slices/aiSlice';
import { RootState } from '../../../store';
import { AiSuggestion, ChatMessage } from '../../../types/ai';

/**
 * Helper function to create a Redux store with the AI slice for testing
 * @returns Redux store instance with AI slice configured
 */
const createTestStore = () => {
  return configureStore({
    reducer: {
      ai: aiReducer
    }
  });
};

describe('AI Slice Reducer', () => {
  // Test that the initial state is correct
  it('should return the initial state', () => {
    const store = createTestStore();
    const state = store.getState();
    expect(state.ai).toEqual(initialState);
  });

  // Test startSuggestion action
  it('should handle startSuggestion', () => {
    const store = createTestStore();
    store.dispatch(startSuggestion());
    const state = store.getState();
    expect(state.ai.isLoading).toBe(true);
    expect(state.ai.error).toBe(null);
  });

  // Test completeSuggestion action
  it('should handle completeSuggestion', () => {
    const store = createTestStore();
    
    // Create mock suggestions data
    const mockSuggestions: AiSuggestion[] = [
      {
        id: '1',
        originalText: 'Hello world',
        suggestedText: 'Hello beautiful world',
        explanation: 'Added an adjective',
        position: { from: 0, to: 11 }
      }
    ];
    
    store.dispatch(completeSuggestion(mockSuggestions));
    const state = store.getState();
    
    expect(state.ai.isLoading).toBe(false);
    expect(state.ai.suggestions).toEqual(mockSuggestions);
    expect(state.ai.error).toBe(null);
  });

  // Test suggestionError action
  it('should handle suggestionError', () => {
    const store = createTestStore();
    const errorMessage = 'Failed to get suggestions';
    
    store.dispatch(suggestionError(errorMessage));
    const state = store.getState();
    
    expect(state.ai.isLoading).toBe(false);
    expect(state.ai.error).toBe(errorMessage);
  });

  // Test startChat action
  it('should handle startChat', () => {
    const store = createTestStore();
    const userMessage = 'Can you help me improve this text?';
    
    store.dispatch(startChat(userMessage));
    const state = store.getState();
    
    expect(state.ai.isLoading).toBe(true);
    expect(state.ai.chat).toContainEqual({
      role: 'user',
      content: userMessage
    });
    expect(state.ai.error).toBe(null);
  });

  // Test messageReceived action
  it('should handle messageReceived', () => {
    const store = createTestStore();
    const aiMessage = 'I can help you improve your text. What would you like to change?';
    
    store.dispatch(messageReceived(aiMessage));
    const state = store.getState();
    
    expect(state.ai.isLoading).toBe(false);
    expect(state.ai.chat).toContainEqual({
      role: 'assistant',
      content: aiMessage
    });
    expect(state.ai.error).toBe(null);
  });

  // Test chatError action
  it('should handle chatError', () => {
    const store = createTestStore();
    const errorMessage = 'Failed to send message';
    
    store.dispatch(chatError(errorMessage));
    const state = store.getState();
    
    expect(state.ai.isLoading).toBe(false);
    expect(state.ai.error).toBe(errorMessage);
  });

  // Test resetAiState action
  it('should handle resetAiState', () => {
    const store = createTestStore();
    
    // First, modify the state with various actions
    store.dispatch(startSuggestion());
    store.dispatch(completeSuggestion([
      {
        id: '1',
        originalText: 'Hello world',
        suggestedText: 'Hello beautiful world',
        explanation: 'Added an adjective',
        position: { from: 0, to: 11 }
      }
    ]));
    store.dispatch(startChat('Can you help me?'));
    
    // Then reset the state
    store.dispatch(resetAiState());
    const state = store.getState();
    
    // Check that state is reset to initial state
    expect(state.ai).toEqual(initialState);
  });
});

describe('AI Slice Selectors', () => {
  // Test selectAiState selector
  it('selectAiState should return the entire AI state', () => {
    const store = createTestStore();
    const state = store.getState() as RootState;
    const aiState = selectAiState(state);
    
    expect(aiState).toEqual(state.ai);
  });

  // Test selectSuggestions selector
  it('selectSuggestions should return only the suggestions part of the state', () => {
    const store = createTestStore();
    
    // Create a state containing suggestions
    const mockSuggestions: AiSuggestion[] = [
      {
        id: '1',
        originalText: 'Hello world',
        suggestedText: 'Hello beautiful world',
        explanation: 'Added an adjective',
        position: { from: 0, to: 11 }
      }
    ];
    
    store.dispatch(completeSuggestion(mockSuggestions));
    const state = store.getState() as RootState;
    const suggestions = selectSuggestions(state);
    
    expect(suggestions).toEqual(mockSuggestions);
  });

  // Test selectChat selector
  it('selectChat should return only the chat messages part of the state', () => {
    const store = createTestStore();
    
    // Create a state containing chat messages
    store.dispatch(startChat('User message'));
    store.dispatch(messageReceived('AI response'));
    
    const state = store.getState() as RootState;
    const chat = selectChat(state);
    
    expect(chat).toHaveLength(2);
    expect(chat[0]).toEqual(expect.objectContaining({
      role: 'user',
      content: 'User message'
    }));
    expect(chat[1]).toEqual(expect.objectContaining({
      role: 'assistant',
      content: 'AI response'
    }));
  });

  // Test selectIsLoading selector
  it('selectIsLoading should return the loading state', () => {
    const store = createTestStore();
    
    // Initially should not be loading
    expect(selectIsLoading(store.getState() as RootState)).toBe(false);
    
    // Update the store to set isLoading to true
    store.dispatch(startSuggestion());
    expect(selectIsLoading(store.getState() as RootState)).toBe(true);
    
    // Update the store to set isLoading to false
    store.dispatch(completeSuggestion([]));
    expect(selectIsLoading(store.getState() as RootState)).toBe(false);
  });

  // Test selectError selector
  it('selectError should return the error state', () => {
    const store = createTestStore();
    const errorMessage = 'Test error message';
    
    // Create a state with an error message
    store.dispatch(suggestionError(errorMessage));
    expect(selectError(store.getState() as RootState)).toBe(errorMessage);
    
    // Update the store to clear the error
    store.dispatch(startSuggestion());
    expect(selectError(store.getState() as RootState)).toBe(null);
  });
});