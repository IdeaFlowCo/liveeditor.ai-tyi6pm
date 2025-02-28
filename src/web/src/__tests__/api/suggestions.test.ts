/**
 * Test file for the suggestions API module
 * 
 * This file contains tests for the functions in the suggestions API module that handle
 * generating AI-powered writing improvement suggestions, processing user decisions on 
 * suggestions, and managing feedback on suggestion quality.
 */
import { 
  generateSuggestions,
  generateTextSuggestions, 
  generateStyleSuggestions, 
  generateGrammarSuggestions,
  processSuggestionDecisions,
  submitSuggestionFeedback,
  getSuggestionById,
  getSuggestionsForDocument,
  generateSuggestionDiff
} from '../../api/suggestions';

import {
  SuggestionRequest,
  SuggestionResponse,
  SuggestionAcceptRejectRequest,
  SuggestionFeedbackRequest,
  Suggestion,
  SuggestionWithDiff
} from '../../types/suggestion';

import { SuggestionType } from '../../types/ai';
import { post, get, put } from '../../utils/api';
import { ENDPOINTS } from '../../constants/api';
import { rest } from 'msw';
import { server } from '../mocks/server';

// Set up mock server
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Mock the API functions
jest.mock('../../utils/api', () => ({
  post: jest.fn(),
  get: jest.fn(),
  put: jest.fn(),
}));

/**
 * Helper function to create a mock suggestion request object for testing
 * 
 * @param overrides - Optional fields to override default values
 * @returns A valid suggestion request object
 */
const createMockSuggestionRequest = (overrides = {}): SuggestionRequest => {
  return {
    documentId: 'test-document-id',
    content: 'This is test document content that needs improvement.',
    selection: null,
    category: SuggestionType.PROFESSIONAL,
    customPrompt: null,
    ...overrides
  };
};

/**
 * Helper function to create a mock suggestion object for testing
 * 
 * @param overrides - Optional fields to override default values
 * @returns A valid suggestion object
 */
const createMockSuggestion = (overrides = {}): Suggestion => {
  return {
    id: 'test-suggestion-id',
    documentId: 'test-document-id',
    changeType: 'replacement',
    status: 'pending',
    category: SuggestionType.PROFESSIONAL,
    position: { from: 10, to: 20 },
    originalText: 'needs improvement',
    suggestedText: 'requires enhancement',
    explanation: 'More professional wording',
    createdAt: new Date(),
    ...overrides
  };
};

describe('generateSuggestions function', () => {
  test('should make a POST request to the suggestions endpoint', async () => {
    // Mock successful response
    const mockResponse: SuggestionResponse = {
      suggestionGroupId: 'group-123',
      suggestions: [
        {
          id: 'suggestion-1',
          originalText: 'needs improvement',
          suggestedText: 'requires enhancement',
          explanation: 'More professional wording',
          position: { start: 10, end: 20 }
        }
      ],
      promptUsed: 'Make it more professional',
      processingTime: 420
    };
    
    (post as jest.Mock).mockResolvedValue(mockResponse);
    
    // Create request and call function
    const request = createMockSuggestionRequest();
    const result = await generateSuggestions(request);
    
    // Verify post was called correctly
    expect(post).toHaveBeenCalledWith(ENDPOINTS.SUGGESTIONS.BASE, request);
    
    // Verify result
    expect(result).toEqual(mockResponse);
  });
  
  test('should throw an error if request validation fails', async () => {
    // Create invalid request (missing content)
    const invalidRequest = createMockSuggestionRequest({ content: '' });
    
    // Verify function throws error
    await expect(generateSuggestions(invalidRequest)).rejects.toThrow(
      'Document content is required for generating suggestions'
    );
    
    // Verify post was not called
    expect(post).not.toHaveBeenCalled();
  });
  
  test('should handle API errors correctly', async () => {
    // Mock API error
    const errorMessage = 'API error occurred';
    (post as jest.Mock).mockRejectedValue(new Error(errorMessage));
    
    // Create request and call function
    const request = createMockSuggestionRequest();
    
    // Verify error is propagated
    await expect(generateSuggestions(request)).rejects.toThrow(errorMessage);
  });
});

describe('generateTextSuggestions function', () => {
  test('should make a POST request to the text suggestions endpoint', async () => {
    // Mock successful response
    const mockResponse: SuggestionResponse = {
      suggestionGroupId: 'group-123',
      suggestions: [
        {
          id: 'suggestion-1',
          originalText: 'complicated wording',
          suggestedText: 'simpler text',
          explanation: 'Clearer text',
          position: { start: 10, end: 30 }
        }
      ],
      promptUsed: 'Make it clearer',
      processingTime: 350
    };
    
    (post as jest.Mock).mockResolvedValue(mockResponse);
    
    // Create request and call function
    const request = createMockSuggestionRequest({ category: SuggestionType.CLARITY });
    const result = await generateTextSuggestions(request);
    
    // Verify post was called correctly
    expect(post).toHaveBeenCalledWith(ENDPOINTS.SUGGESTIONS.TEXT, request);
    
    // Verify result
    expect(result).toEqual(mockResponse);
  });
});

describe('generateStyleSuggestions function', () => {
  test('should make a POST request to the style suggestions endpoint', async () => {
    // Mock successful response
    const mockResponse: SuggestionResponse = {
      suggestionGroupId: 'group-123',
      suggestions: [
        {
          id: 'suggestion-1',
          originalText: 'I think',
          suggestedText: 'It is suggested that',
          explanation: 'More formal academic tone',
          position: { start: 5, end: 12 }
        }
      ],
      promptUsed: 'Make it more academic',
      processingTime: 380
    };
    
    (post as jest.Mock).mockResolvedValue(mockResponse);
    
    // Create request and call function
    const request = createMockSuggestionRequest({ category: SuggestionType.ACADEMIC });
    const result = await generateStyleSuggestions(request);
    
    // Verify post was called correctly
    expect(post).toHaveBeenCalledWith(ENDPOINTS.SUGGESTIONS.STYLE, request);
    
    // Verify result
    expect(result).toEqual(mockResponse);
  });
});

describe('generateGrammarSuggestions function', () => {
  test('should make a POST request to the grammar suggestions endpoint', async () => {
    // Mock successful response
    const mockResponse: SuggestionResponse = {
      suggestionGroupId: 'group-123',
      suggestions: [
        {
          id: 'suggestion-1',
          originalText: 'they was',
          suggestedText: 'they were',
          explanation: 'Subject-verb agreement',
          position: { start: 20, end: 28 }
        }
      ],
      promptUsed: 'Fix grammar',
      processingTime: 290
    };
    
    (post as jest.Mock).mockResolvedValue(mockResponse);
    
    // Create request and call function
    const request = createMockSuggestionRequest({ category: SuggestionType.GRAMMAR });
    const result = await generateGrammarSuggestions(request);
    
    // Verify post was called correctly
    expect(post).toHaveBeenCalledWith(ENDPOINTS.SUGGESTIONS.GRAMMAR, request);
    
    // Verify result
    expect(result).toEqual(mockResponse);
  });
});

describe('processSuggestionDecisions function', () => {
  test('should make a PUT request with accept/reject decisions', async () => {
    // Mock successful response
    const mockResponse = {
      success: true,
      acceptedCount: 2,
      rejectedCount: 1
    };
    
    (put as jest.Mock).mockResolvedValue(mockResponse);
    
    // Create request and call function
    const request: SuggestionAcceptRejectRequest = {
      documentId: 'test-document-id',
      acceptedSuggestionIds: ['suggestion-1', 'suggestion-2'],
      rejectedSuggestionIds: ['suggestion-3']
    };
    
    const result = await processSuggestionDecisions(request);
    
    // Verify put was called correctly
    expect(put).toHaveBeenCalledWith(
      `${ENDPOINTS.SUGGESTIONS.BASE}/decisions`,
      request
    );
    
    // Verify result
    expect(result).toEqual(mockResponse);
  });
  
  test('should throw an error if request validation fails', async () => {
    // Create invalid request (missing suggestion IDs)
    const invalidRequest: SuggestionAcceptRejectRequest = {
      documentId: 'test-document-id',
      acceptedSuggestionIds: [],
      rejectedSuggestionIds: []
    };
    
    // Verify function throws error
    await expect(processSuggestionDecisions(invalidRequest)).rejects.toThrow(
      'At least one suggestion ID must be provided for acceptance or rejection'
    );
    
    // Verify put was not called
    expect(put).not.toHaveBeenCalled();
  });
});

describe('submitSuggestionFeedback function', () => {
  test('should make a POST request with feedback data', async () => {
    // Mock successful response
    const mockResponse = {
      success: true
    };
    
    (post as jest.Mock).mockResolvedValue(mockResponse);
    
    // Create request and call function
    const request: SuggestionFeedbackRequest = {
      suggestionId: 'test-suggestion-id',
      rating: 4,
      comment: 'Good suggestion but could be better'
    };
    
    const result = await submitSuggestionFeedback(request);
    
    // Verify post was called correctly
    expect(post).toHaveBeenCalledWith(
      `${ENDPOINTS.SUGGESTIONS.BASE}/feedback`,
      request
    );
    
    // Verify result
    expect(result).toEqual(mockResponse);
  });
});

describe('getSuggestionById function', () => {
  test('should make a GET request for a specific suggestion', async () => {
    // Mock suggestion response
    const mockSuggestion = createMockSuggestion();
    
    (get as jest.Mock).mockResolvedValue(mockSuggestion);
    
    // Call function
    const result = await getSuggestionById('test-suggestion-id');
    
    // Verify get was called correctly
    expect(get).toHaveBeenCalledWith(
      `${ENDPOINTS.SUGGESTIONS.BASE}/test-suggestion-id`
    );
    
    // Verify result
    expect(result).toEqual(mockSuggestion);
  });
  
  test('should throw an error if suggestion ID is invalid', async () => {
    // Call function with empty ID
    await expect(getSuggestionById('')).rejects.toThrow(
      'Suggestion ID is required'
    );
    
    // Verify get was not called
    expect(get).not.toHaveBeenCalled();
  });
});

describe('getSuggestionsForDocument function', () => {
  test('should make a GET request for document suggestions', async () => {
    // Mock suggestions array
    const mockSuggestions = [
      createMockSuggestion({ id: 'suggestion-1' }),
      createMockSuggestion({ id: 'suggestion-2' })
    ];
    
    (get as jest.Mock).mockResolvedValue(mockSuggestions);
    
    // Call function
    const result = await getSuggestionsForDocument('test-document-id');
    
    // Verify get was called correctly
    expect(get).toHaveBeenCalledWith(
      `${ENDPOINTS.SUGGESTIONS.BASE}/document/test-document-id`
    );
    
    // Verify result
    expect(result).toEqual(mockSuggestions);
  });
});

describe('generateSuggestionDiff function', () => {
  test('should make a POST request to calculate suggestion diff', async () => {
    // Mock suggestion and diff result
    const mockSuggestion = createMockSuggestion();
    const mockDiffResult: SuggestionWithDiff = {
      suggestion: mockSuggestion,
      diffHtml: '<span class="deleted">needs improvement</span><span class="added">requires enhancement</span>',
      diffOperations: [
        { type: 'delete', text: 'needs improvement' },
        { type: 'insert', text: 'requires enhancement' }
      ]
    };
    
    (post as jest.Mock).mockResolvedValue(mockDiffResult);
    
    // Call function
    const result = await generateSuggestionDiff(mockSuggestion);
    
    // Verify post was called correctly
    expect(post).toHaveBeenCalledWith(
      `${ENDPOINTS.SUGGESTIONS.BASE}/diff`,
      { suggestion: mockSuggestion }
    );
    
    // Verify result
    expect(result).toEqual(mockDiffResult);
  });
});

describe('Integration with MSW server', () => {
  // Temporarily restore the actual API functions for this test
  beforeEach(() => {
    jest.restoreAllMocks();
  });
  
  // Re-mock them after
  afterEach(() => {
    jest.mock('../../utils/api', () => ({
      post: jest.fn(),
      get: jest.fn(),
      put: jest.fn(),
    }));
  });
  
  test('should handle entire suggestion flow with mocked API', async () => {
    // Set up MSW server handlers
    server.use(
      rest.post(`${ENDPOINTS.SUGGESTIONS.BASE}`, (req, res, ctx) => {
        return res(
          ctx.json<SuggestionResponse>({
            suggestionGroupId: 'group-123',
            suggestions: [
              {
                id: 'suggestion-1',
                originalText: 'needs improvement',
                suggestedText: 'requires enhancement',
                explanation: 'More professional wording',
                position: { start: 10, end: 20 }
              }
            ],
            promptUsed: 'Make it more professional',
            processingTime: 420
          })
        );
      }),
      
      rest.put(`${ENDPOINTS.SUGGESTIONS.BASE}/decisions`, (req, res, ctx) => {
        return res(
          ctx.json({
            success: true,
            acceptedCount: 1,
            rejectedCount: 0
          })
        );
      })
    );
    
    // Create document content and request
    const documentContent = 'This is test document content that needs improvement.';
    const request = createMockSuggestionRequest({ content: documentContent });
    
    // Generate suggestions
    const suggestionResponse = await generateSuggestions(request);
    
    // Verify response
    expect(suggestionResponse.suggestions.length).toBe(1);
    expect(suggestionResponse.suggestions[0].originalText).toBe('needs improvement');
    
    // Process suggestion decisions
    const decisionRequest: SuggestionAcceptRejectRequest = {
      documentId: 'test-document-id',
      acceptedSuggestionIds: [suggestionResponse.suggestions[0].id],
      rejectedSuggestionIds: []
    };
    
    const decisionResult = await processSuggestionDecisions(decisionRequest);
    
    // Verify decisions were processed
    expect(decisionResult.success).toBe(true);
    expect(decisionResult.acceptedCount).toBe(1);
    expect(decisionResult.rejectedCount).toBe(0);
  });
});