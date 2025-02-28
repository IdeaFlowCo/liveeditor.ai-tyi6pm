import React from 'react'; // React v18.2.0
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals'; // @jest/globals v29.5.0
import { renderWithProviders, screen, waitFor, userEvent, fireEvent } from '../utils/test-utils';
import Dashboard from '../../pages/Dashboard';
import { ROUTES } from '../../constants/routes';

// Mock the useNavigate hook
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Define a mock navigation function
let mockNavigate: jest.Mock;

/**
 * Setup function for creating a configured userEvent instance
 * @returns Configured userEvent instance
 */
const setup = () => {
  // LD1: Call userEvent.setup() to create a configured instance
  const user = userEvent.setup();
  // LD1: Return the configured instance for use in tests
  return user;
};

/**
 * Helper function to render the Dashboard component with necessary providers and mocks
 * @param {object} options
 * @returns {object} Render result with additional utilities
 */
const renderDashboard = (options: any = {}) => {
  // LD1: Set up default preloadedState with authentication and document state
  const defaultPreloadedState = {
    auth: {
      user: {
        id: 'test-user',
        firstName: 'Test',
        lastName: 'User',
        email: 'test@example.com',
      },
      isAuthenticated: true,
    },
    document: {
      documentList: [],
    },
  };

  // LD2: Merge provided options with defaults
  const preloadedState = {
    ...defaultPreloadedState,
    ...options.preloadedState,
  };

  // LD3: Call renderWithProviders with Dashboard component and configured options
  const renderResult = renderWithProviders(<Dashboard />, { preloadedState });

  // LD4: Return the render result
  return renderResult;
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    mockNavigate = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders welcome message with user name', () => {
    // LD1: Render Dashboard with mock authenticated user
    renderDashboard();

    // LD2: Verify welcome message contains user's name
    expect(screen.getByText(/Welcome, Test!/i)).toBeInTheDocument();
  });

  it('displays loading state while fetching documents', () => {
    // LD1: Render Dashboard with loading state in document slice
    renderDashboard({ preloadedState: { document: { loading: true } } });

    // LD2: Verify loading spinner is displayed
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('displays empty state when no documents exist', () => {
    // LD1: Render Dashboard with empty documents array
    renderDashboard();

    // LD2: Verify empty state message is displayed
    expect(screen.getByText(/No documents yet/i)).toBeInTheDocument();
  });

  it('displays document list when documents exist', () => {
    // LD1: Render Dashboard with documents in the state
    renderDashboard({
      preloadedState: {
        document: {
          documentList: [
            { id: 'doc-1', title: 'Document 1' },
            { id: 'doc-2', title: 'Document 2' },
          ],
        },
      },
    });

    // LD2: Verify document titles are displayed in the list
    expect(screen.getByText(/Document 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Document 2/i)).toBeInTheDocument();
  });

  it("navigates to editor with new document when 'Create New Document' is clicked", async () => {
    // LD1: Render Dashboard with mock navigation function
    renderDashboard();
    const user = setup();

    // LD2: Click the 'Create New Document' button
    const createButton = screen.getByText(/Create New Document/i);
    await user.click(createButton);

    // LD3: Verify navigation is called with editor route and new document ID
    expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining(ROUTES.EDITOR));
  });

  it('navigates to editor when a document is selected', async () => {
    // LD1: Render Dashboard with documents in the state
    renderDashboard({
      preloadedState: {
        document: {
          documentList: [{ id: 'doc-1', title: 'Document 1' }],
        },
      },
    });
    const user = setup();

    // LD2: Click on a document in the list
    const documentLink = screen.getByText(/Document 1/i);
    await user.click(documentLink);

    // LD3: Verify navigation is called with editor route and selected document ID
    expect(mockNavigate).toHaveBeenCalledWith(`${ROUTES.EDITOR}/doc-1`);
  });

  it('shows document statistics correctly', () => {
    // LD1: Render Dashboard with documents containing varied properties in the state
    renderDashboard({
      preloadedState: {
        document: {
          documentList: [
            { id: 'doc-1', title: 'Document 1' , stats: {suggestionCount: 5}},
            { id: 'doc-2', title: 'Document 2', stats: {suggestionCount: 0} },
          ],
        },
      },
    });

    // LD2: Verify statistics cards show correct counts for total documents and AI edited documents
    expect(screen.getByText(/2 Total Documents/i)).toBeInTheDocument();
    expect(screen.getByText(/1 Documents with AI Edits/i)).toBeInTheDocument();
  });

  it('handles error state when document fetching fails', () => {
    // LD1: Render Dashboard with error state in document slice
    renderDashboard({ preloadedState: { document: { loading: false, error: 'Failed to fetch documents' } } });

    // LD2: Verify error message is displayed
    expect(screen.getByText(/Failed to fetch documents/i)).toBeInTheDocument();

    // LD3: Verify retry button is available
    expect(screen.getByText(/Create one to get started!/i)).toBeInTheDocument();
  });
});