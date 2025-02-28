import { renderHook, act } from '@testing-library/react-hooks'; // @testing-library/react-hooks ^8.0.1
import { Provider } from 'react-redux'; // react-redux ^8.0.5
import { configureStore } from '@reduxjs/toolkit'; // @reduxjs/toolkit ^1.9.5
import useAi from '../../hooks/useAi';
import { rootReducer } from '../../store';
import { server } from '../mocks/server';
import { API_ENDPOINTS } from '../../constants/api';
import { rest } from 'msw'; // msw ^1.2.1
import { generateSuggestions, sendChatMessage, clearSuggestions, clearChatHistory, loadTemplates } from '../../store/slices/aiSlice';

// Mock server setup for API endpoints
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Redux store factory for testing
const createTestStore = (preloadedState = {}) => {
  return configureStore({
    reducer: rootReducer,
    preloadedState,
  });
};

describe('useAi hook', () => {
  describe('Suggestions', () => {
    it('should generate suggestions successfully', async () => {
      const store = createTestStore();
      const { result } = renderHook(() => useAi(), {
        wrapper: ({ children }) => (
          <Provider store={store}>{children}</Provider>
        ),
      });

      await act(async () => {
        // Mock document content for testing
        const documentContent = 'This is a test document.';
        // Call generateSuggestion with a mock prompt type
        await result.current.generateSuggestion('grammar');
      });

      // Assert that the processing status is completed
      expect(store.getState().ai.processingStatus).toBe('completed');
      // Assert that suggestions are generated
      expect(store.getState().ai.suggestions.length).toBeGreaterThan(0);
    });

    it('should handle suggestion generation errors', async () => {
      server.use(
        rest.post(API_ENDPOINTS.SUGGESTIONS.BASE, (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ message: 'Suggestion generation failed' }));
        })
      );

      const store = createTestStore();
      const { result } = renderHook(() => useAi(), {
        wrapper: ({ children }) => (
          <Provider store={store}>{children}</Provider>
        ),
      });

      await act(async () => {
        // Mock document content for testing
        const documentContent = 'This is a test document.';
        // Call generateSuggestion with a mock prompt type
        await result.current.generateSuggestion('grammar');
      });

      // Assert that the processing status is error
      expect(store.getState().ai.processingStatus).toBe('error');
      // Assert that an error message is set
      expect(store.getState().ai.error).not.toBeNull();
    });

    it('should clear suggestions', async () => {
      const store = createTestStore({
        ai: {
          processingStatus: 'completed',
          error: null,
          suggestions: [{
            suggestions: [{
              id: '1',
              originalText: 'test',
              suggestedText: 'test',
              explanation: 'test',
              position: { start: 0, end: 0 },
              status: 'pending'
            }],
            suggestionGroupId: '1',
            promptUsed: 'test',
            processingTime: 0
          }],
          selectedTemplate: null,
          templates: [],
          conversations: {},
          currentConversationId: null,
          availableTokens: 0,
          aiFeatureEnabled: true
        }
      });
      const { result } = renderHook(() => useAi(), {
        wrapper: ({ children }) => (
          <Provider store={store}>{children}</Provider>
        ),
      });

      await act(async () => {
        // Call clearSuggestions
        result.current.clearSuggestions();
      });

      // Assert that suggestions are cleared
      expect(store.getState().ai.suggestions).toEqual([]);
    });
  });

  describe('Chat', () => {
    it('should send chat messages successfully', async () => {
      const store = createTestStore();
      const { result } = renderHook(() => useAi(), {
        wrapper: ({ children }) => (
          <Provider store={store}>{children}</Provider>
        ),
      });

      await act(async () => {
        // Call sendMessage with a mock message
        await result.current.sendMessage('Hello, AI!');
      });

      // Assert that the processing status is completed
      expect(store.getState().ai.processingStatus).toBe('completed');
      // Assert that a chat message is added
      expect(Object.keys(store.getState().ai.conversations).length).toBeGreaterThan(0);
    });

    it('should handle chat errors', async () => {
      server.use(
        rest.post(API_ENDPOINTS.CHAT.MESSAGE, (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ message: 'Chat message failed' }));
        })
      );

      const store = createTestStore();
      const { result } = renderHook(() => useAi(), {
        wrapper: ({ children }) => (
          <Provider store={store}>{children}</Provider>
        ),
      });

      await act(async () => {
        // Call sendMessage with a mock message
        await result.current.sendMessage('Hello, AI!');
      });

      // Assert that the processing status is error
      expect(store.getState().ai.processingStatus).toBe('error');
      // Assert that an error message is set
      expect(store.getState().ai.error).not.toBeNull();
    });

    it('should clear chat history', async () => {
      const store = createTestStore({
        ai: {
          processingStatus: 'completed',
          error: null,
          suggestions: [],
          selectedTemplate: null,
          templates: [],
          conversations: {
            '1': {
              id: '1',
              title: 'Test Conversation',
              messages: [{
                id: '1',
                conversationId: '1',
                role: 'user',
                content: 'test',
                timestamp: new Date()
              }],
              createdAt: new Date(),
              updatedAt: new Date(),
              documentId: null,
              userId: null,
              sessionId: null
            }
          },
          currentConversationId: '1',
          availableTokens: 0,
          aiFeatureEnabled: true
        }
      });
      const { result } = renderHook(() => useAi(), {
        wrapper: ({ children }) => (
          <Provider store={store}>{children}</Provider>
        ),
      });

      await act(async () => {
        // Call clearChatHistory
        result.current.clearChatHistory();
      });

      // Assert that chat history is cleared
      expect(store.getState().ai.conversations).toEqual({});
      expect(store.getState().ai.currentConversationId).toBeNull();
    });
  });

  describe('Templates', () => {
    it('should load templates', async () => {
      const store = createTestStore();
      const { result } = renderHook(() => useAi(), {
        wrapper: ({ children }) => (
          <Provider store={store}>{children}</Provider>
        ),
      });

      // Assert that templates are loaded
      expect(store.getState().ai.templates.length).toBeGreaterThan(0);
    });

    it('should access templates from state', async () => {
      const store = createTestStore({
        ai: {
          processingStatus: 'completed',
          error: null,
          suggestions: [],
          selectedTemplate: null,
          templates: [{
            id: '1',
            name: 'Test Template',
            description: 'Test Template',
            category: 'test',
            promptText: 'test',
            isSystem: true
          }],
          conversations: {},
          currentConversationId: null,
          availableTokens: 0,
          aiFeatureEnabled: true
        }
      });
      const { result } = renderHook(() => useAi(), {
        wrapper: ({ children }) => (
          <Provider store={store}>{children}</Provider>
        ),
      });

      // Assert that templates are accessible from state
      expect(result.current.templates.length).toBeGreaterThan(0);
    });
  });

  describe('Integration', () => {
    it('should handle full workflow - generate suggestions then clear', async () => {
      const store = createTestStore();
      const { result } = renderHook(() => useAi(), {
        wrapper: ({ children }) => (
          <Provider store={store}>{children}</Provider>
        ),
      });

      await act(async () => {
        // Mock document content for testing
        const documentContent = 'This is a test document.';
        // Call generateSuggestion with a mock prompt type
        await result.current.generateSuggestion('grammar');
        // Call clearSuggestions
        result.current.clearSuggestions();
      });

      // Assert that the processing status is completed
      expect(store.getState().ai.processingStatus).toBe('completed');
      // Assert that suggestions are cleared
      expect(store.getState().ai.suggestions).toEqual([]);
    });

    it('should handle full chat workflow - send message then clear', async () => {
      const store = createTestStore();
      const { result } = renderHook(() => useAi(), {
        wrapper: ({ children }) => (
          <Provider store={store}>{children}</Provider>
        ),
      });

      await act(async () => {
        // Call sendMessage with a mock message
        await result.current.sendMessage('Hello, AI!');
        // Call clearChatHistory
        result.current.clearChatHistory();
      });

      // Assert that the processing status is completed
      expect(store.getState().ai.processingStatus).toBe('completed');
      // Assert that chat history is cleared
      expect(store.getState().ai.conversations).toEqual({});
      expect(store.getState().ai.currentConversationId).toBeNull();
    });
  });
});