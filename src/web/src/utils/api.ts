/**
 * API utility functions for making API calls to the backend
 * 
 * Provides standardized methods for HTTP requests, error handling, and 
 * authentication token management to facilitate communication between 
 * the frontend and backend services.
 * 
 * @module api
 * @version 1.0.0
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios'; // axios ^1.4.0
import { API_BASE_URL, ENDPOINTS, API_TIMEOUT } from '../constants/api';
import { ApiResponse, ApiErrorResponse, HttpMethod } from '../types';

// Storage key for authentication token
const TOKEN_STORAGE_KEY = 'auth_access_token';

/**
 * Custom error class for API-related errors with additional context
 */
export class ApiError extends Error {
  status: number;
  details: any;

  /**
   * Creates a new API Error instance
   * 
   * @param message - Human-readable error message
   * @param status - HTTP status code
   * @param details - Additional error details
   */
  constructor(message: string, status: number = 500, details: any = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
    
    // Fix prototype chain for proper instanceof checks
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/**
 * Creates and configures an Axios instance with default settings
 * 
 * @returns Configured Axios instance for making API requests
 */
export const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  });

  // Request interceptor to add authentication token if available
  client.interceptors.request.use(
    (config) => {
      return addAuthHeader(config);
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor to handle common response processing
  client.interceptors.response.use(
    (response) => {
      return response;
    },
    (error) => {
      return Promise.reject(handleApiError(error));
    }
  );

  return client;
};

/**
 * Generic request function that handles common API request patterns
 * 
 * @param url - API endpoint URL
 * @param method - HTTP method (GET, POST, etc.)
 * @param data - Request payload for POST, PUT, PATCH
 * @param options - Additional Axios request options
 * @returns Promise resolving to the API response data
 */
export const request = async <T = any>(
  url: string,
  method: HttpMethod,
  data?: any,
  options?: AxiosRequestConfig
): Promise<T> => {
  try {
    const client = createApiClient();
    const fullUrl = createUrl(url);
    
    const config: AxiosRequestConfig = {
      ...options,
      method,
      url: fullUrl,
    };

    // Add data to request config based on method
    if (data) {
      if (method === 'GET') {
        config.params = data;
      } else {
        config.data = data;
      }
    }

    const response = await client(config);
    return response.data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw handleApiError(error);
  }
};

/**
 * Convenience function for making GET requests
 * 
 * @param url - API endpoint URL
 * @param params - URL query parameters
 * @param options - Additional Axios request options
 * @returns Promise resolving to the API response data
 */
export const get = <T = any>(
  url: string,
  params?: object,
  options?: AxiosRequestConfig
): Promise<T> => {
  return request<T>(url, 'GET', params, options);
};

/**
 * Convenience function for making POST requests
 * 
 * @param url - API endpoint URL
 * @param data - Request payload
 * @param options - Additional Axios request options
 * @returns Promise resolving to the API response data
 */
export const post = <T = any>(
  url: string,
  data?: any,
  options?: AxiosRequestConfig
): Promise<T> => {
  return request<T>(url, 'POST', data, options);
};

/**
 * Convenience function for making PUT requests
 * 
 * @param url - API endpoint URL
 * @param data - Request payload
 * @param options - Additional Axios request options
 * @returns Promise resolving to the API response data
 */
export const put = <T = any>(
  url: string,
  data?: any,
  options?: AxiosRequestConfig
): Promise<T> => {
  return request<T>(url, 'PUT', data, options);
};

/**
 * Convenience function for making PATCH requests
 * 
 * @param url - API endpoint URL
 * @param data - Request payload
 * @param options - Additional Axios request options
 * @returns Promise resolving to the API response data
 */
export const patch = <T = any>(
  url: string,
  data?: any,
  options?: AxiosRequestConfig
): Promise<T> => {
  return request<T>(url, 'PATCH', data, options);
};

/**
 * Convenience function for making DELETE requests
 * 
 * @param url - API endpoint URL
 * @param options - Additional Axios request options
 * @returns Promise resolving to the API response data
 */
export const del = <T = any>(
  url: string,
  options?: AxiosRequestConfig
): Promise<T> => {
  return request<T>(url, 'DELETE', undefined, options);
};

/**
 * Processes API errors into a standardized format for consistent error handling
 * 
 * @param error - The original error object
 * @returns Standardized API error
 */
export const handleApiError = (error: any): ApiError => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorResponse>;
    const status = axiosError.response?.status || 500;
    
    // Server provided structured error response
    if (axiosError.response?.data) {
      const errorData = axiosError.response.data;
      if (typeof errorData === 'object' && errorData.message) {
        return new ApiError(
          errorData.message,
          status,
          errorData.details || null
        );
      }
    }

    // Network error (no response)
    if (axiosError.code === 'ECONNABORTED' || !axiosError.response) {
      return new ApiError(
        'Unable to reach the server. Please check your internet connection and try again.',
        0,
        { networkError: true }
      );
    }

    // Timeout error
    if (axiosError.code === 'ETIMEDOUT') {
      return new ApiError(
        'Request timed out. Please try again later.',
        408,
        { timeout: true }
      );
    }

    // Generic error with status code
    if (status === 401) {
      return new ApiError('Unauthorized. Please log in again.', status);
    } else if (status === 403) {
      return new ApiError('Access denied. You do not have permission for this action.', status);
    } else if (status === 404) {
      return new ApiError('Resource not found.', status);
    } else if (status === 429) {
      return new ApiError('Too many requests. Please try again later.', status);
    } else if (status >= 500) {
      return new ApiError('Server error. Please try again later.', status);
    }

    // Default axios error
    return new ApiError(
      axiosError.message || 'An unexpected error occurred.',
      status
    );
  }

  // Non-axios error
  return new ApiError(
    error?.message || 'An unexpected error occurred.',
    500,
    { originalError: error }
  );
};

/**
 * Utility to create a full URL by combining endpoint path with base URL
 * 
 * @param endpoint - API endpoint path
 * @returns Complete URL for the API endpoint
 */
export const createUrl = (endpoint: string): string => {
  // Check if endpoint already includes the base URL
  if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
    return endpoint;
  }
  
  // Make sure endpoint starts with a slash
  const formattedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  // Combine base URL with endpoint
  return `${API_BASE_URL}${formattedEndpoint}`;
};

/**
 * Retrieves the authentication token from storage
 * 
 * @returns The authentication token if available, otherwise null
 */
export const getAuthToken = (): string | null => {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch (error) {
    console.error('Error accessing localStorage:', error);
    return null;
  }
};

/**
 * Saves the authentication token to storage
 * 
 * @param token - JWT token string or null to clear
 */
export const setAuthToken = (token: string | null): void => {
  try {
    if (token === null) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    } else {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
    }
  } catch (error) {
    console.error('Error accessing localStorage:', error);
  }
};

/**
 * Removes the authentication token from storage
 */
export const clearAuthToken = (): void => {
  setAuthToken(null);
};

/**
 * Adds authentication header to request config if token is available
 * 
 * @param config - Axios request configuration
 * @returns Updated config object with auth header if token exists
 */
export const addAuthHeader = (config: AxiosRequestConfig): AxiosRequestConfig => {
  const token = getAuthToken();
  
  if (token) {
    config.headers = {
      ...config.headers,
      Authorization: `Bearer ${token}`
    };
  }
  
  return config;
};

// Export additional aliases to maintain backward compatibility
// and align with the file specification
export { del as delete };