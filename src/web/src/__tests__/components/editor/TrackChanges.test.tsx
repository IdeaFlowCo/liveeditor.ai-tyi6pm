import React from 'react'; // React v18.2.0
import { render, screen, fireEvent, waitFor } from '@testing-library/react'; // @testing-library/react ^14.0.0
import { act } from 'react-dom/test-utils'; // react-dom/test-utils ^18.2.0
import '@testing-library/jest-dom'; // @testing-library/jest-dom ^5.16.5

import { TrackChanges } from '../../../components/editor/TrackChanges';
import { renderWithProviders } from '../../utils/test-utils';
import { SuggestionInline } from '../../../components/editor/SuggestionInline';

// Mock Redux state with document content and suggestions
const mockReduxState = {
  document: {
    document: {
      id: 'test-doc-id',
      userId: 'test-user-id',
      sessionId: null,
      content: 'The quick brown fox jumps over the lazy dog.',
      metadata: {
        title: 'Test Document',
        tags: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        lastAccessedAt: new Date(),
        isArchived: false,
        format: 'text',
      },
      state: 'saved',
      changes: [
        {
          id: 'suggestion-1',
          position: { from: 4, to: 9 },
          originalText: 'quick',
          suggestedText: 'fast',
          explanation: 'More appropriate word',
          status: 'pending',
          timestamp: new Date(),
          sourceType: 'template',
          metadata: {},
        },
        {
          id: 'suggestion-2',
          position: { from: 16, to: 21 },
          originalText: 'jumps',
          suggestedText: 'leaps',
          explanation: 'More vivid verb',
          status: 'pending',
          timestamp: new Date(),
          sourceType: 'template',
          metadata: {},
        },
      ],
      stats: {
        wordCount: 9,
        characterCount: 44,
        paragraphCount: 1,
        readingTime: 1,
        suggestionCount: 2,
        acceptedSuggestions: 0,
        rejectedSuggestions: 0,
        pendingSuggestions: 2,
      },
      currentVersionId: null,
      isAnonymous: false,
    },
  },
};

// Mock suggestions data
const mockSuggestions = [
  {
    id: 'suggestion-1',
    position: { from: 4, to: 9 },
    originalText: 'quick',
    suggestedText: 'fast',
    explanation: 'More appropriate word',
    status: 'pending',
    timestamp: new Date(),
    sourceType: 'template',
    metadata: {},
  },
  {
    id: 'suggestion-2',
    position: { from: 16, to: 21 },
    originalText: 'jumps',
    suggestedText: 'leaps',
    explanation: 'More vivid verb',
    status: 'pending',
    timestamp: new Date(),
    sourceType: 'template',
    metadata: {},
  },
];

describe('TrackChanges component', () => {
  let mockStore: any;

  beforeEach(() => {
    mockStore = {
      getState: () => mockReduxState,
      dispatch: jest.fn(),
      subscribe: jest.fn(),
    };
  });

  it('should render the track changes component', async () => {
    renderWithProviders(<TrackChanges isVisible={true} isReviewMode={true} showExplanations={true} />, {
      preloadedState: mockReduxState,
    });

    expect(screen.getByText('Original Text')).toBeInTheDocument();
    expect(screen.getByText('Suggested Change')).toBeInTheDocument();
  });

  it('should display suggestions with proper formatting', async () => {
    renderWithProviders(<TrackChanges isVisible={true} isReviewMode={true} showExplanations={true} />, {
      preloadedState: mockReduxState,
    });

    expect(screen.getByText('Original Text')).toBeInTheDocument();
    expect(screen.getByText('Suggested Change')).toBeInTheDocument();
  });

  it('should navigate between suggestions', async () => {
    renderWithProviders(<TrackChanges isVisible={true} isReviewMode={true} showExplanations={true} />, {
      preloadedState: mockReduxState,
    });

    const nextButton = screen.getByText('Next >');
    fireEvent.click(nextButton);

    expect(screen.getByText('Original Text')).toBeInTheDocument();
    expect(screen.getByText('Suggested Change')).toBeInTheDocument();
  });

  it('should accept a suggestion when accept button is clicked', async () => {
    renderWithProviders(<TrackChanges isVisible={true} isReviewMode={true} showExplanations={true} />, {
      preloadedState: mockReduxState,
    });

    const acceptButton = screen.getByText('Accept');
    fireEvent.click(acceptButton);

    expect(screen.getByText('Original Text')).toBeInTheDocument();
    expect(screen.getByText('Suggested Change')).toBeInTheDocument();
  });

  it('should reject a suggestion when reject button is clicked', async () => {
    renderWithProviders(<TrackChanges isVisible={true} isReviewMode={true} showExplanations={true} />, {
      preloadedState: mockReduxState,
    });

    const rejectButton = screen.getByText('Reject');
    fireEvent.click(rejectButton);

    expect(screen.getByText('Original Text')).toBeInTheDocument();
    expect(screen.getByText('Suggested Change')).toBeInTheDocument();
  });

  it('should accept all suggestions when accept all button is clicked', async () => {
    renderWithProviders(<TrackChanges isVisible={true} isReviewMode={true} showExplanations={true} />, {
      preloadedState: mockReduxState,
    });

    const acceptAllButton = screen.getByText('Accept All');
    fireEvent.click(acceptAllButton);

    expect(screen.getByText('Original Text')).toBeInTheDocument();
    expect(screen.getByText('Suggested Change')).toBeInTheDocument();
  });

  it('should reject all suggestions when reject all button is clicked', async () => {
    renderWithProviders(<TrackChanges isVisible={true} isReviewMode={true} showExplanations={true} />, {
      preloadedState: mockReduxState,
    });

    const rejectAllButton = screen.getByText('Reject All');
    fireEvent.click(rejectAllButton);

    expect(screen.getByText('Original Text')).toBeInTheDocument();
    expect(screen.getByText('Suggested Change')).toBeInTheDocument();
  });

  it('should display explanation for suggestions', async () => {
    renderWithProviders(<TrackChanges isVisible={true} isReviewMode={true} showExplanations={true} />, {
      preloadedState: mockReduxState,
    });

    expect(screen.getByText('More appropriate word')).toBeInTheDocument();
  });

  it('should update document content when suggestions are accepted', async () => {
    renderWithProviders(<TrackChanges isVisible={true} isReviewMode={true} showExplanations={true} />, {
      preloadedState: mockReduxState,
    });

    const acceptButton = screen.getByText('Accept');
    fireEvent.click(acceptButton);

    expect(screen.getByText('Original Text')).toBeInTheDocument();
    expect(screen.getByText('Suggested Change')).toBeInTheDocument();
  });
});