import React from 'react'; // React v18.2.0
import { rest } from 'msw'; // msw v1.0.0
import {
  renderWithProviders,
  screen,
  waitFor,
  within,
  userEvent,
  fireEvent,
} from '../utils/test-utils';
import EditorPage from '../../pages/Editor';
import server from '../mocks/server';
import handlers from '../mocks/handlers';
import useDocument from '../../hooks/useDocument';
import useAi from '../../hooks/useAi';
import { Suggestion } from '../../types';
import { SuggestionStatus } from '../../types/suggestion';
import { act } from 'react-dom/test-utils';
import { authLoginHandler } from '../mocks/handlers';
import { documentsGetHandler } from '../mocks/handlers';
import { documentsListHandler } from '../mocks/handlers';
import { suggestionsHandler } from '../mocks/handlers';
import { chatHandler } from '../mocks/handlers';
import { templatesHandler } from '../mocks/handlers';
import { Mock } from 'node:test';
import { MockedFunction } from 'jest-mock';
import { configureAppStore } from '../../store';
import { Provider } from 'react-redux';

// Define global setup and teardown functions for MSW server
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Define a type for the mock implementation of the useDocument hook
type MockUseDocument = {
  documentContent?: string;
  isLoading?: boolean;
  isError?: boolean;
  loadDocument?: MockedFunction<any>;
  saveDocumentChanges?: MockedFunction<any>;
  updateDocumentContent?: MockedFunction<any>;
};

// Define a type for the mock implementation of the useAi hook
type MockUseAi = {
  isProcessing?: boolean;
  suggestions?: Suggestion[];
  generateSuggestion?: MockedFunction<any>;
  acceptSuggestion?: MockedFunction<any>;
  rejectSuggestion?: MockedFunction<any>;
};

// Define a mock implementation of the useDocument hook
const mockUseDocument = (overrides: MockUseDocument = {}) => {
  const defaultValues = {
    documentContent: 'Initial document content',
    isLoading: false,
    isError: false,
    loadDocument: jest.fn(),
    saveDocumentChanges: jest.fn(),
    updateDocumentContent: jest.fn(),
  };
  return { ...defaultValues, ...overrides };
};

// Define a mock implementation of the useAi hook
const mockUseAi = (overrides: MockUseAi = {}) => {
  const defaultValues = {
    isProcessing: false,
    suggestions: [],
    generateSuggestion: jest.fn(),
    acceptSuggestion: jest.fn(),
    rejectSuggestion: jest.fn(),
  };
  return { ...defaultValues, ...overrides };
};

describe('Editor Page Component', () => {
  it('renders editor with loading state initially', async () => {
    // Mock the useDocument hook to simulate a loading state
    (useDocument as jest.Mock) = jest.fn().mockReturnValue(mockUseDocument({ isLoading: true }));

    // Render the EditorPage component with providers
    renderWithProviders(<EditorPage />);

    // Verify that the loading spinner is displayed
    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    // Verify that the loading message is displayed
    expect(screen.getByText(/Loading document/i)).toBeInTheDocument();
  });

  it('renders editor with document content when loaded', async () => {
    // Mock the useDocument hook to simulate a loaded document
    (useDocument as jest.Mock) = jest.fn().mockReturnValue(mockUseDocument({ documentContent: 'Loaded document content' }));

    // Render the EditorPage component with providers
    renderWithProviders(<EditorPage />);

    // Verify that the document content is rendered correctly
    expect(screen.getByText(/Loaded document content/i)).toBeInTheDocument();

    // Verify that the editor toolbar is present
    expect(screen.getByRole('toolbar')).toBeInTheDocument();

    // Verify that the AI sidebar is present
    expect(screen.getByRole('complementary')).toBeInTheDocument();
  });

  it('handles document not found error', async () => {
    // Mock the useDocument hook to simulate a document not found error
    (useDocument as jest.Mock) = jest.fn().mockReturnValue(mockUseDocument({ isError: true }));

    // Render the EditorPage component with providers
    renderWithProviders(<EditorPage />);

    // Verify that the error message is displayed
    expect(screen.getByText(/Failed to load document/i)).toBeInTheDocument();

    // Verify that the option to create a new document is available
    expect(screen.getByRole('button', { name: /New Document/i })).toBeInTheDocument();
  });

  it('allows typing in the editor', async () => {
    // Mock the useDocument hook to simulate a loaded document and update function
    const updateDocumentContent = jest.fn();
    (useDocument as jest.Mock) = jest.fn().mockReturnValue(mockUseDocument({ documentContent: '', updateDocumentContent }));

    // Render the EditorPage component with providers
    renderWithProviders(<EditorPage />);

    // Find the editor element
    const editorElement = screen.getByRole('textbox');

    // Simulate typing in the editor
    await userEvent.type(editorElement, 'Typed text');

    // Verify that the user input is reflected in the editor
    expect(editorElement).toHaveTextContent('Typed text');

    // Verify that the document state is updated on input
    expect(updateDocumentContent).toHaveBeenCalledTimes(10);
  });

  it('processes AI suggestions correctly', async () => {
    // Mock the useDocument hook to simulate a loaded document
    (useDocument as jest.Mock) = jest.fn().mockReturnValue(mockUseDocument({ documentContent: 'Original text' }));

    // Mock the useAi hook to simulate AI suggestions
    const generateSuggestion = jest.fn();
    const acceptSuggestion = jest.fn();
    const rejectSuggestion = jest.fn();
    (useAi as jest.Mock) = jest.fn().mockReturnValue(mockUseAi({ generateSuggestion, acceptSuggestion, rejectSuggestion }));

    // Render the EditorPage component with providers
    renderWithProviders(<EditorPage />);

    // Find the "Make it shorter" button
    const makeItShorterButton = screen.getByRole('button', { name: /Make it shorter/i });

    // Simulate clicking the "Make it shorter" button
    await userEvent.click(makeItShorterButton);

    // Verify that the AI suggestion request is sent
    expect(generateSuggestion).toHaveBeenCalledTimes(1);

    // Find the "Accept" button
    const acceptButton = screen.getByRole('button', { name: /Accept/i });

    // Simulate clicking the "Accept" button
    await userEvent.click(acceptButton);

    // Verify that the user can accept suggestions
    expect(acceptSuggestion).toHaveBeenCalledTimes(1);

    // Find the "Reject" button
    const rejectButton = screen.getByRole('button', { name: /Reject/i });

    // Simulate clicking the "Reject" button
    await userEvent.click(rejectButton);

    // Verify that the user can reject suggestions
    expect(rejectSuggestion).toHaveBeenCalledTimes(1);
  });

  it('shows save prompt for anonymous users', async () => {
    // Mock the useAuth hook to simulate an anonymous user
    (useAuth as jest.Mock) = jest.fn().mockReturnValue({
      isAuthenticated: false,
      isAnonymous: true,
      user: { sessionId: 'session-123', isAnonymous: true },
    });

    // Mock the useDocument hook to simulate a loaded document and save function
    const saveDocumentChanges = jest.fn();
    (useDocument as jest.Mock) = jest.fn().mockReturnValue(mockUseDocument({ documentContent: 'Test content', saveDocumentChanges }));

    // Render the EditorPage component with providers
    renderWithProviders(<EditorPage />);

    // Find the "Save" button
    const saveButton = screen.getByRole('button', { name: /Save/i });

    // Simulate clicking the "Save" button
    await userEvent.click(saveButton);

    // Verify that the save prompt appears for anonymous users
    expect(screen.getByRole('dialog', { name: /Save Your Document/i })).toBeInTheDocument();

    // Find the "Continue Anonymously" button
    const continueAnonymouslyButton = screen.getByRole('button', { name: /Continue Anonymously/i });

    // Simulate clicking the "Continue Anonymously" button
    await userEvent.click(continueAnonymouslyButton);

    // Verify that the user can continue without saving
    expect(saveDocumentChanges).toHaveBeenCalledTimes(1);
  });

  it('saves document automatically for authenticated users', async () => {
    // Mock the useAuth hook to simulate an authenticated user
    (useAuth as jest.Mock) = jest.fn().mockReturnValue({
      isAuthenticated: true,
      isAnonymous: false,
      user: { id: 'user-123', isAnonymous: false },
    });

    // Mock the useDocument hook to simulate a loaded document and save function
    const saveDocumentChanges = jest.fn();
    (useDocument as jest.Mock) = jest.fn().mockReturnValue(mockUseDocument({ documentContent: 'Test content', saveDocumentChanges }));

    // Render the EditorPage component with providers
    renderWithProviders(<EditorPage />);

    // Find the "Save" button
    const saveButton = screen.getByRole('button', { name: /Save/i });

    // Simulate clicking the "Save" button
    await userEvent.click(saveButton);

    // Verify that the document is saved to the server for authenticated users
    expect(saveDocumentChanges).toHaveBeenCalledTimes(1);

    // Verify that a success notification is shown after save
    //expect(screen.getByText(/Document saved successfully/i)).toBeInTheDocument();
  });

  it('allows chat interaction with AI', async () => {
    // Mock the useDocument hook to simulate a loaded document
    (useDocument as jest.Mock) = jest.fn().mockReturnValue(mockUseDocument({ documentContent: 'Test content' }));

    // Mock the useAi hook to simulate chat functionality
    const sendMessage = jest.fn();
    (useAi as jest.Mock) = jest.fn().mockReturnValue(mockUseAi({ sendMessage }));

    // Render the EditorPage component with providers
    renderWithProviders(<EditorPage />);

    // Find the "Chat" button
    const chatButton = screen.getByRole('button', { name: /Chat/i });

    // Simulate clicking the "Chat" button
    await userEvent.click(chatButton);

    // Find the chat input field
    const chatInput = screen.getByRole('textbox', { name: /Enter custom prompt/i });

    // Simulate typing a message in the chat input
    await userEvent.type(chatInput, 'Test message');

    // Simulate pressing Enter to send the message
    await fireEvent.keyDown(chatInput, { key: 'Enter' });

    // Verify that the message is sent to the AI service
    expect(sendMessage).toHaveBeenCalledTimes(1);
  });
});