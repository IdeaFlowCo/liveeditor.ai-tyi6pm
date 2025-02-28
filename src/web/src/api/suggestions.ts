/**
 * API service module for the AI suggestion system
 * 
 * This module provides functions for generating, retrieving, and managing AI-powered
 * writing improvement suggestions. It handles communication with the backend AI services
 * and provides a clean interface for the frontend components to interact with.
 * 
 * @module suggestions
 * @version 1.0.0
 */

import { post, get, put } from '../utils/api';
import { ENDPOINTS } from '../constants/api';
import {
  SuggestionRequest,
  SuggestionResponse,
  SuggestionAcceptRejectRequest,
  SuggestionFeedbackRequest,
  TextSelection,
  Suggestion,
  SuggestionWithDiff
} from '../types/suggestion';
import { SuggestionType } from '../types/ai';

/**
 * Generates AI-powered suggestions for document content
 * 
 * @param request - Suggestion request parameters containing document content and improvement options
 * @returns Promise resolving to suggestion response containing generated improvements
 */
export const generateSuggestions = async (
  request: SuggestionRequest
): Promise<SuggestionResponse> => {
  // Validate the request data
  if (!request.content) {
    throw new Error('Document content is required for generating suggestions');
  }

  // Make POST request to suggestions base endpoint
  return post<SuggestionResponse>(ENDPOINTS.SUGGESTIONS.BASE, request);
};

/**
 * Generates text-focused suggestions like simplification, clarity, or tone improvements
 * 
 * @param request - Suggestion request parameters for text improvements
 * @returns Promise resolving to text-focused improvement suggestions
 */
export const generateTextSuggestions = async (
  request: SuggestionRequest
): Promise<SuggestionResponse> => {
  // Validate the request data
  if (!request.content) {
    throw new Error('Document content is required for generating text suggestions');
  }

  // Make POST request to suggestions text endpoint
  return post<SuggestionResponse>(ENDPOINTS.SUGGESTIONS.TEXT, request);
};

/**
 * Generates style-focused suggestions like professional tone or academic writing
 * 
 * @param request - Suggestion request parameters for style improvements
 * @returns Promise resolving to style-focused improvement suggestions
 */
export const generateStyleSuggestions = async (
  request: SuggestionRequest
): Promise<SuggestionResponse> => {
  // Validate the request data
  if (!request.content) {
    throw new Error('Document content is required for generating style suggestions');
  }

  // Make POST request to suggestions style endpoint
  return post<SuggestionResponse>(ENDPOINTS.SUGGESTIONS.STYLE, request);
};

/**
 * Generates grammar-focused suggestions to correct grammatical errors
 * 
 * @param request - Suggestion request parameters for grammar improvements
 * @returns Promise resolving to grammar-focused improvement suggestions
 */
export const generateGrammarSuggestions = async (
  request: SuggestionRequest
): Promise<SuggestionResponse> => {
  // Validate the request data
  if (!request.content) {
    throw new Error('Document content is required for generating grammar suggestions');
  }

  // Make POST request to suggestions grammar endpoint
  return post<SuggestionResponse>(ENDPOINTS.SUGGESTIONS.GRAMMAR, request);
};

/**
 * Submits user decisions on accepting or rejecting specific suggestions
 * 
 * @param request - Object containing accepted and rejected suggestion IDs
 * @returns Promise resolving to the result of processing the suggestion decisions
 */
export const processSuggestionDecisions = async (
  request: SuggestionAcceptRejectRequest
): Promise<{ success: boolean; acceptedCount: number; rejectedCount: number }> => {
  // Validate the request contains valid document ID and suggestion IDs
  if (!request.documentId) {
    throw new Error('Document ID is required for processing suggestion decisions');
  }
  
  if (!request.acceptedSuggestionIds?.length && !request.rejectedSuggestionIds?.length) {
    throw new Error('At least one suggestion ID must be provided for acceptance or rejection');
  }

  // Make PUT request to suggestions decisions endpoint
  return put<{ success: boolean; acceptedCount: number; rejectedCount: number }>(
    `${ENDPOINTS.SUGGESTIONS.BASE}/decisions`,
    request
  );
};

/**
 * Submits user feedback about suggestion quality to improve AI over time
 * 
 * @param feedback - Object containing feedback details including rating and optional comment
 * @returns Promise resolving to the success status of the feedback submission
 */
export const submitSuggestionFeedback = async (
  feedback: SuggestionFeedbackRequest
): Promise<{ success: boolean }> => {
  // Validate the feedback contains required fields
  if (!feedback.suggestionId) {
    throw new Error('Suggestion ID is required for submitting feedback');
  }
  
  if (feedback.rating < 1 || feedback.rating > 5) {
    throw new Error('Rating must be between 1 and 5');
  }

  // Make POST request to suggestion feedback endpoint
  return post<{ success: boolean }>(
    `${ENDPOINTS.SUGGESTIONS.BASE}/feedback`,
    feedback
  );
};

/**
 * Retrieves a specific suggestion by its ID
 * 
 * @param suggestionId - ID of the suggestion to retrieve
 * @returns Promise resolving to the requested suggestion
 */
export const getSuggestionById = async (
  suggestionId: string
): Promise<Suggestion> => {
  // Validate suggestion ID is provided
  if (!suggestionId) {
    throw new Error('Suggestion ID is required');
  }

  // Make GET request to suggestion endpoint with ID
  return get<Suggestion>(`${ENDPOINTS.SUGGESTIONS.BASE}/${suggestionId}`);
};

/**
 * Retrieves all suggestions generated for a specific document
 * 
 * @param documentId - ID of the document to get suggestions for
 * @returns Promise resolving to an array of suggestions for the document
 */
export const getSuggestionsForDocument = async (
  documentId: string
): Promise<Suggestion[]> => {
  // Validate document ID is provided
  if (!documentId) {
    throw new Error('Document ID is required');
  }

  // Make GET request to document suggestions endpoint
  return get<Suggestion[]>(`${ENDPOINTS.SUGGESTIONS.BASE}/document/${documentId}`);
};

/**
 * Generates detailed difference information between original and suggested text
 * 
 * @param suggestion - The suggestion to generate diff for with original and suggested text
 * @returns Promise resolving to suggestion with detailed diff information for visual display
 */
export const generateSuggestionDiff = async (
  suggestion: Suggestion
): Promise<SuggestionWithDiff> => {
  // Validate suggestion contains original and suggested text
  if (!suggestion.originalText || !suggestion.suggestedText) {
    throw new Error('Original and suggested text are required for generating diff');
  }

  // Make POST request to diff endpoint with the suggestion
  return post<SuggestionWithDiff>(
    `${ENDPOINTS.SUGGESTIONS.BASE}/diff`,
    { suggestion }
  );
};