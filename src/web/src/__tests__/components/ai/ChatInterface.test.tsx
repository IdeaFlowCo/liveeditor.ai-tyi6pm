import React from 'react'; // react ^18.2.0
import { renderWithProviders } from '../../utils/test-utils';
import { server } from '../../mocks/server';
import ChatInterface from '../../../components/ai/ChatInterface';
import { API_ROUTES } from '../../../constants/api';
import { sendChatMessageThunk } from '../../../store/slices/aiSlice';
import { ChatRole, ProcessingStatus } from '../../../types/ai';
import { screen, waitFor, within, fireEvent } from '@testing-library/react'; // @testing-library/react ^14.0.0

// IE2: Import jest for testing framework
// IE2: Import @testing-library/react for React testing utilities
// IE2: Import msw for Mock Service Worker for API mocking
// IE2: Import react for React library for component testing

// S2: Main test suite for ChatInterface component
describe('ChatInterface', () => {
  // S2: Include beforeAll to set up MSW server
  beforeAll(() => server.listen());

  // S2: Include afterEach to reset MSW handlers
  afterEach(() => server.resetHandlers());

  // S2: Include afterAll to clean up MSW server
  afterAll(() => server.close());

  // S2: Individual test case
  it('renders the chat interface correctly', () => {
    // S2: Render the ChatInterface component with renderWithProviders
    renderWithProviders(<ChatInterface />);

    // S2: Verify the chat container is present in the document
    const chatContainer = screen.getByRole('complementary');
    expect(chatContainer).toBeInTheDocument();

    // S2: Verify the message input field is rendered
    const messageInput = screen.getByLabelText('Custom AI Prompt');
    expect(messageInput).toBeInTheDocument();

    // S2: Verify the send button is rendered
    const sendButton = screen.getByRole('button', { name: 'Send' });
    expect(sendButton).toBeInTheDocument();
  });

  // S2: Individual test case
  it('displays initial greeting message', () => {
    // S2: Mock the initial state with a greeting message
    const initialState = {
      ai: {
        processingStatus: ProcessingStatus.IDLE,
        error: null,
        suggestions: [],
        selectedTemplate: null,
        templates: [],
        conversations: {
          'conversation-1': {
            id: 'conversation-1',
            title: 'Test Conversation',
            messages: [
              {
                id: 'message-1',
                conversationId: 'conversation-1',
                role: ChatRole.ASSISTANT,
                content: 'Hello! How can I help you today?',
                timestamp: new Date(),
                metadata: null,
              },
            ],
            createdAt: new Date(),
            updatedAt: new Date(),
            documentId: null,
            userId: null,
            sessionId: null,
          },
        },
        currentConversationId: 'conversation-1',
        availableTokens: 0,
        aiFeatureEnabled: true,
      },
    };

    // S2: Render the ChatInterface component
    renderWithProviders(<ChatInterface />, { preloadedState: initialState });

    // S2: Verify the greeting message is displayed in the chat
    const greetingMessage = screen.getByText('Hello! How can I help you today?');
    expect(greetingMessage).toBeInTheDocument();
  });

  // S2: Individual test case
  it('allows user to type and send a message', async () => {
    // S2: Render the ChatInterface component
    const { store } = renderWithProviders(<ChatInterface />);

    // S2: Find the message input field
    const messageInput = screen.getByLabelText('Custom AI Prompt');

    // S2: Type a test message in the input
    const testMessage = 'This is a test message.';
    fireEvent.change(messageInput, { target: { value: testMessage } });
    expect(messageInput).toHaveValue(testMessage);

    // S2: Click the send button
    const sendButton = screen.getByRole('button', { name: 'Send' });
    fireEvent.click(sendButton);

    // S2: Verify the input is cleared after sending
    await waitFor(() => {
      expect(messageInput).toHaveValue('');
    });

    // S2: Verify the user message appears in the chat
    await waitFor(() => {
      expect(screen.getByText(testMessage)).toBeInTheDocument();
    });
  });

  // S2: Individual test case
  it('displays loading state while waiting for AI response', async () => {
    // S2: Set up mock server to delay response
    server.use(
      rest.post(API_ROUTES.CHAT.MESSAGE, async (req, res, ctx) => {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        return res(ctx.status(200), ctx.json({ response: 'Delayed AI response' }));
      })
    );

    // S2: Render the ChatInterface component
    renderWithProviders(<ChatInterface />);

    // S2: Send a user message
    const messageInput = screen.getByLabelText('Custom AI Prompt');
    const testMessage = 'Test message for loading state.';
    fireEvent.change(messageInput, { target: { value: testMessage } });
    const sendButton = screen.getByRole('button', { name: 'Send' });
    fireEvent.click(sendButton);

    // S2: Verify the loading indicator is displayed
    await waitFor(() => {
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    // S2: Wait for the response to complete
    await waitFor(
      () => {
        expect(screen.getByText('Test message for loading state.')).toBeInTheDocument();
      },
      { timeout: 2000 }
    );

    // S2: Verify loading indicator is removed after response arrives
    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });
  });

  // S2: Individual test case
  it('displays AI response after sending a message', async () => {
    // S2: Mock API response with specific AI message content
    const aiMessageContent = 'This is a mock AI response.';
    server.use(
      rest.post(API_ROUTES.CHAT.MESSAGE, (req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            id: 'ai-message-1',
            conversationId: 'conversation-1',
            role: ChatRole.ASSISTANT,
            content: aiMessageContent,
            timestamp: new Date(),
            metadata: null,
          })
        );
      })
    );

    // S2: Render the ChatInterface component
    renderWithProviders(<ChatInterface />);

    // S2: Send a user message
    const messageInput = screen.getByLabelText('Custom AI Prompt');
    const testMessage = 'Test message to get AI response.';
    fireEvent.change(messageInput, { target: { value: testMessage } });
    const sendButton = screen.getByRole('button', { name: 'Send' });
    fireEvent.click(sendButton);

    // S2: Wait for the response to arrive
    await waitFor(() => {
      expect(screen.getByText(aiMessageContent)).toBeInTheDocument();
    });
  });

  // S2: Individual test case
  it('handles error states when AI service fails', async () => {
    // S2: Mock API to return an error response
    server.use(
      rest.post(API_ROUTES.CHAT.MESSAGE, (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ message: 'AI service failed.' }));
      })
    );

    // S2: Render the ChatInterface component
    renderWithProviders(<ChatInterface />);

    // S2: Send a user message
    const messageInput = screen.getByLabelText('Custom AI Prompt');
    const testMessage = 'Test message to trigger AI error.';
    fireEvent.change(messageInput, { target: { value: testMessage } });
    const sendButton = screen.getByRole('button', { name: 'Send' });
    fireEvent.click(sendButton);

    // S2: Verify error message is displayed to the user
    await waitFor(() => {
      expect(screen.getByText('AI service failed.')).toBeInTheDocument();
    });

    // S2: Verify the interface remains usable after an error
    expect(messageInput).toBeEnabled();
    expect(sendButton).toBeEnabled();
  });

  // S2: Individual test case
  it('allows applying AI suggestions to document', async () => {
    // S2: Mock AI response with an actionable suggestion
    server.use(
      rest.post(API_ROUTES.CHAT.MESSAGE, (req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            id: 'ai-message-1',
            conversationId: 'conversation-1',
            role: ChatRole.ASSISTANT,
            content: 'AI suggests replacing "original" with "improved".',
            timestamp: new Date(),
            metadata: {
              suggestion: 'improved',
            },
          })
        );
      })
    );

    // S2: Render the ChatInterface component with document context
    const { store } = renderWithProviders(<ChatInterface documentContext="This is the original text." />);

    // S2: Send a user message requesting content improvement
    const messageInput = screen.getByLabelText('Custom AI Prompt');
    fireEvent.change(messageInput, { target: { value: 'Improve the text.' } });
    const sendButton = screen.getByRole('button', { name: 'Send' });
    fireEvent.click(sendButton);

    // S2: Verify AI response contains an apply button
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Apply suggestion' })).toBeInTheDocument();
    });

    // S2: Click the apply button
    const applyButton = screen.getByRole('button', { name: 'Apply suggestion' });
    fireEvent.click(applyButton);

    // S2: Verify the application action is dispatched correctly
    // TODO: Implement assertion for dispatched action
  });

  // S2: Individual test case
  it('allows starting a new chat conversation', async () => {
    // S2: Render the ChatInterface component with existing messages
    const initialState = {
      ai: {
        processingStatus: ProcessingStatus.IDLE,
        error: null,
        suggestions: [],
        selectedTemplate: null,
        templates: [],
        conversations: {
          'conversation-1': {
            id: 'conversation-1',
            title: 'Test Conversation',
            messages: [
              {
                id: 'message-1',
                conversationId: 'conversation-1',
                role: ChatRole.ASSISTANT,
                content: 'Hello! How can I help you today?',
                timestamp: new Date(),
                metadata: null,
              },
            ],
            createdAt: new Date(),
            updatedAt: new Date(),
            documentId: null,
            userId: null,
            sessionId: null,
          },
        },
        currentConversationId: 'conversation-1',
        availableTokens: 0,
        aiFeatureEnabled: true,
      },
    };
    const { store } = renderWithProviders(<ChatInterface />, { preloadedState: initialState });

    // S2: Find and click the 'New Chat' button
    // TODO: Implement New Chat button
    // const newChatButton = screen.getByRole('button', { name: 'New Chat' });
    // fireEvent.click(newChatButton);

    // S2: Verify the chat history is cleared
    // TODO: Implement assertion for cleared chat history

    // S2: Verify a new greeting message is displayed
    // TODO: Implement assertion for new greeting message
  });
});