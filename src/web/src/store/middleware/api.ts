/**
 * Redux middleware for API request handling
 * 
 * Intercepts actions with API request configurations and manages the full
 * request lifecycle including authentication, loading states, success responses,
 * and error handling.
 *
 * @module api-middleware
 * @version 1.0.0
 */

import { Middleware, isRejectedWithValue, createAction, isFulfilled, isPending } from '@reduxjs/toolkit'; // ^1.9.5
import { Action, MiddlewareAPI } from 'redux'; // ^4.2.1
import { makeRequest, ApiMethod } from '../../utils/api';
import { handleApiError } from '../../utils/error-handling';
import { getAuthToken } from '../../utils/auth';

// Symbol to identify API actions
export const API_REQUEST = Symbol('API_REQUEST');

/**
 * Configuration for an API request
 */
export interface ApiRequest {
  /** API endpoint path */
  endpoint: string;
  /** HTTP method (GET, POST, etc.) */
  method: ApiMethod;
  /** Request payload for POST, PUT, PATCH */
  data?: any;
  /** Whether the request requires authentication */
  authenticated?: boolean;
  /** Additional request headers */
  headers?: Record<string, string>;
  /** Whether to include credentials in the request */
  withCredentials?: boolean;
  /** AbortSignal for cancelling the request */
  signal?: AbortSignal;
  /** Request timeout in milliseconds */
  timeout?: number;
  /** Whether to retry failed requests */
  retry?: boolean;
  /** Number of retry attempts */
  retryAttempts?: number;
}

/**
 * Action types for the API request cycle
 */
export interface ApiActionTypes {
  /** Action type for request initiation */
  request: string;
  /** Action type for successful response */
  success: string;
  /** Action type for request failure */
  failure: string;
}

/**
 * Optional callbacks for API request lifecycle
 */
export interface ApiActionCallbacks {
  /** Called when request is initiated */
  onRequest?: (dispatch: any, getState: any, action: ApiAction) => void;
  /** Called on successful response */
  onSuccess?: (dispatch: any, getState: any, response: any, action: ApiAction) => void;
  /** Called on request failure */
  onFailure?: (dispatch: any, getState: any, error: any, action: ApiAction) => void;
}

/**
 * Configuration for creating an API action
 */
export interface ApiActionConfig {
  /** Base action type */
  type: string;
  /** API request configuration */
  request: ApiRequest;
  /** Action types for request lifecycle */
  types: ApiActionTypes;
  /** Optional callbacks for request lifecycle */
  callbacks?: ApiActionCallbacks;
  /** Additional payload data */
  payload?: any;
  /** Whether to show error toast on failure */
  showErrorToast?: boolean;
  /** Custom error message */
  errorMessage?: string;
}

/**
 * Redux action with API request configuration
 */
export interface ApiAction {
  /** Action type */
  type: string;
  /** Symbol marking this as an API action */
  [API_REQUEST]: true;
  /** API request configuration */
  request: ApiRequest;
  /** Action types for request lifecycle */
  types: ApiActionTypes;
  /** Optional callbacks for request lifecycle */
  callbacks?: ApiActionCallbacks;
  /** Additional payload data */
  payload?: any;
  /** Whether to show error toast on failure */
  showErrorToast?: boolean;
  /** Custom error message */
  errorMessage?: string;
}

/**
 * Helper function to create a properly formatted API action
 * 
 * @param config - API action configuration
 * @returns Properly formatted API action
 */
export const createApiAction = (config: ApiActionConfig): ApiAction => {
  // Validate required properties
  if (!config.type) {
    throw new Error('Action type is required');
  }
  
  if (!config.request || !config.request.endpoint || !config.request.method) {
    throw new Error('API request configuration is incomplete');
  }
  
  if (!config.types || !config.types.request || !config.types.success || !config.types.failure) {
    throw new Error('API action types are required');
  }
  
  // Return formatted action
  return {
    type: config.type,
    [API_REQUEST]: true,
    request: config.request,
    types: config.types,
    callbacks: config.callbacks,
    payload: config.payload,
    showErrorToast: config.showErrorToast !== undefined ? config.showErrorToast : true,
    errorMessage: config.errorMessage,
  };
};

/**
 * Type guard to check if an action is an API action
 * 
 * @param action - Action to check
 * @returns True if the action is an API action
 */
export const isApiAction = (action: Action): action is ApiAction => {
  return Boolean(action && (action as ApiAction)[API_REQUEST]);
};

/**
 * Processes an API request based on the action configuration
 * 
 * @param action - API action to process
 * @param dispatch - Redux dispatch function
 * @param getState - Redux getState function
 * @param next - Next middleware function
 * @returns Promise resolving to the API response data
 */
const processApiRequest = async (
  action: ApiAction,
  dispatch: any,
  getState: any,
  next: any
): Promise<any> => {
  const { request, types, callbacks, payload, showErrorToast, errorMessage } = action;
  const { endpoint, method, data, authenticated = true, ...options } = request;
  
  // Dispatch the request action to indicate loading state
  dispatch({ type: types.request, payload });
  
  // Call onRequest callback if it exists
  if (callbacks?.onRequest) {
    callbacks.onRequest(dispatch, getState, action);
  }
  
  try {
    // Get authentication token if the request requires authentication
    const token = authenticated ? getAuthToken() : null;
    
    // Make the API request
    const response = await makeRequest(
      endpoint,
      method,
      data,
      {
        ...options,
        headers: {
          ...options.headers,
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      }
    );
    
    // Dispatch success action
    dispatch({ type: types.success, payload: response, meta: { originalPayload: payload } });
    
    // Call onSuccess callback if it exists
    if (callbacks?.onSuccess) {
      callbacks.onSuccess(dispatch, getState, response, action);
    }
    
    return response;
  } catch (error) {
    // Handle API error
    const processedError = handleApiError(error as Error, {
      showNotification: showErrorToast,
      customMessage: errorMessage,
      context: { endpoint, method }
    });
    
    // Dispatch failure action
    dispatch({ 
      type: types.failure, 
      error: true, 
      payload: processedError,
      meta: { originalPayload: payload }
    });
    
    // Call onFailure callback if it exists
    if (callbacks?.onFailure) {
      callbacks.onFailure(dispatch, getState, processedError, action);
    }
    
    // Re-throw the error for the caller to handle
    throw processedError;
  }
};

/**
 * Redux middleware for API request handling
 * 
 * @param store - Redux store
 * @returns Next middleware function
 */
const apiMiddleware: Middleware = (store: MiddlewareAPI<any>) => (next) => (action) => {
  // If not an API action, pass it through
  if (!isApiAction(action)) {
    return next(action);
  }
  
  // Process the API request
  return processApiRequest(
    action,
    store.dispatch,
    store.getState,
    next
  );
};

export default apiMiddleware;