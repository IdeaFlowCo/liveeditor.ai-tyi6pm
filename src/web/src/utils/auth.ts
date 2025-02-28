import { User, AnonymousUser, UserSession } from '../types/user';
import {
  AuthState,
  AuthResponse,
  AnonymousAuthResponse,
  TokenRefreshResponse,
  AuthErrorType,
  AuthError
} from '../types/auth';
import {
  saveUserData,
  getUserData,
  clearUserData,
  saveAuthToken,
  getAuthToken,
  saveAnonymousSessionId,
  getAnonymousSessionId
} from './storage';
import jwt_decode from 'jwt-decode'; // v3.1.2

// Buffer time before token expiration to trigger refresh (5 minutes)
export const AUTH_TOKEN_EXPIRATION_BUFFER_MS = 300000;

/**
 * Initializes the authentication state from storage
 * 
 * @returns Initial authentication state based on storage
 */
export function initializeAuthState(): AuthState {
  const token = getAuthToken();
  const user = getUserData();
  const anonymousSessionId = getAnonymousSessionId();
  
  // If we have a valid token and user data, the user is authenticated
  if (token && user && !isTokenExpired(token)) {
    return {
      isAuthenticated: true,
      isAnonymous: false,
      user,
      token,
      refreshToken: null, // Refresh token is not stored in browser
      loading: false,
      error: null,
      errorType: null
    };
  }
  
  // If we have an anonymous session, the user is anonymous
  if (anonymousSessionId) {
    const anonymousUser: AnonymousUser = {
      sessionId: anonymousSessionId,
      createdAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24 hours from now
      isAnonymous: true
    };
    
    return {
      isAuthenticated: false,
      isAnonymous: true,
      user: anonymousUser,
      token: null,
      refreshToken: null,
      loading: false,
      error: null,
      errorType: null
    };
  }
  
  // Default state: not authenticated, not anonymous
  return {
    isAuthenticated: false,
    isAnonymous: false,
    user: null,
    token: null,
    refreshToken: null,
    loading: false,
    error: null,
    errorType: null
  };
}

/**
 * Checks if a JWT token is expired
 * 
 * @param token - JWT token to check
 * @returns True if token is expired or invalid, false otherwise
 */
export function isTokenExpired(token: string): boolean {
  try {
    const expiration = getTokenExpiration(token);
    
    if (!expiration) {
      return true; // If we can't determine expiration, consider it expired
    }
    
    // Compare expiration with current time
    const currentTime = Date.now();
    return expiration <= currentTime;
  } catch (error) {
    console.error('Error checking token expiration:', error);
    return true; // Treat invalid tokens as expired
  }
}

/**
 * Checks if a JWT token will expire soon and should be refreshed
 * 
 * @param token - JWT token to check
 * @param bufferTimeMs - Buffer time in milliseconds (default: 5 minutes)
 * @returns True if token will expire soon, false otherwise
 */
export function isTokenExpiringSoon(
  token: string,
  bufferTimeMs: number = AUTH_TOKEN_EXPIRATION_BUFFER_MS
): boolean {
  try {
    const expiration = getTokenExpiration(token);
    
    if (!expiration) {
      return true; // If we can't determine expiration, consider it expiring soon
    }
    
    // Compare expiration with current time plus buffer
    const currentTime = Date.now();
    return expiration <= (currentTime + bufferTimeMs);
  } catch (error) {
    console.error('Error checking if token is expiring soon:', error);
    return true; // Treat invalid tokens as expiring soon
  }
}

/**
 * Extracts the expiration time from a JWT token
 * 
 * @param token - JWT token to decode
 * @returns Token expiration timestamp in milliseconds, or null if invalid
 */
export function getTokenExpiration(token: string): number | null {
  try {
    const decoded: any = jwt_decode(token);
    
    if (!decoded || !decoded.exp) {
      return null; // Invalid token or missing expiration claim
    }
    
    // JWT exp claim is in seconds, convert to milliseconds
    return decoded.exp * 1000;
  } catch (error) {
    console.error('Error extracting token expiration:', error);
    return null;
  }
}

/**
 * Extracts the user ID from a JWT token
 * 
 * @param token - JWT token to decode
 * @returns User ID from token, or null if invalid
 */
export function getUserIdFromToken(token: string): string | null {
  try {
    const decoded: any = jwt_decode(token);
    
    if (!decoded || !decoded.sub) {
      return null; // Invalid token or missing subject claim
    }
    
    return decoded.sub;
  } catch (error) {
    console.error('Error extracting user ID from token:', error);
    return null;
  }
}

/**
 * Processes an authentication response and saves credentials to storage
 * 
 * @param response - Authentication response from API
 */
export function processAuthResponse(response: AuthResponse): void {
  try {
    // Save user data
    saveUserData(response.user);
    
    // Save access token
    saveAuthToken(response.accessToken);
    
    // Note: We don't store refresh token in browser storage for security
    // It should only be used in the current session
  } catch (error) {
    console.error('Error processing authentication response:', error);
    throw error;
  }
}

/**
 * Processes an anonymous authentication response and saves session info
 * 
 * @param response - Anonymous authentication response from API
 */
export function processAnonymousAuthResponse(response: AnonymousAuthResponse): void {
  try {
    // Save anonymous session ID to storage
    // The saveAnonymousSessionId function will automatically generate a session ID if none exists
    const sessionId = saveAnonymousSessionId();
    
    // Note: In a production environment, we would also save the expiration timestamp
    // For now, this is handled within the storage utility
  } catch (error) {
    console.error('Error processing anonymous authentication response:', error);
    throw error;
  }
}

/**
 * Processes a token refresh response and updates stored tokens
 * 
 * @param response - Token refresh response from API
 */
export function processTokenRefreshResponse(response: TokenRefreshResponse): void {
  try {
    // Save new access token
    saveAuthToken(response.accessToken);
    
    // Note: We don't store refresh token in browser storage for security
    // It should only be used in the current session
  } catch (error) {
    console.error('Error processing token refresh response:', error);
    throw error;
  }
}

/**
 * Clears all authentication data from storage on logout
 */
export function clearAuthStorage(): void {
  try {
    // Clear user data and tokens
    clearUserData();
    
    // Note: We intentionally don't clear the anonymous session
    // This allows users to maintain their anonymous session after logging out
  } catch (error) {
    console.error('Error clearing authentication storage:', error);
    throw error;
  }
}

/**
 * Checks if the user is authenticated with a valid token
 * 
 * @returns True if user is authenticated, false otherwise
 */
export function isAuthenticated(): boolean {
  try {
    const token = getAuthToken();
    
    if (!token) {
      return false;
    }
    
    return !isTokenExpired(token);
  } catch (error) {
    console.error('Error checking authentication status:', error);
    return false;
  }
}

/**
 * Checks if the user has an active anonymous session
 * 
 * @returns True if anonymous session exists, false otherwise
 */
export function hasAnonymousSession(): boolean {
  try {
    const sessionId = getAnonymousSessionId();
    return !!sessionId;
  } catch (error) {
    console.error('Error checking anonymous session:', error);
    return false;
  }
}

/**
 * Parses API error responses into a structured authentication error
 * 
 * @param error - Error from API request
 * @returns Standardized authentication error object
 */
export function parseAuthError(error: any): AuthError {
  try {
    // Default error response
    let authError: AuthError = {
      type: AuthErrorType.UNKNOWN_ERROR,
      message: 'An unknown error occurred',
      field: null
    };
    
    // Check if it's an Axios error with a response
    if (error.response && error.response.data) {
      const { data } = error.response;
      
      // Extract error message
      authError.message = data.message || 'Authentication failed';
      
      // Map backend error codes to frontend error types
      if (data.code) {
        switch (data.code) {
          case 'INVALID_CREDENTIALS':
            authError.type = AuthErrorType.INVALID_CREDENTIALS;
            authError.field = 'password'; // Assume password is incorrect
            break;
          case 'EMAIL_EXISTS':
            authError.type = AuthErrorType.EMAIL_EXISTS;
            authError.field = 'email';
            break;
          case 'TOKEN_EXPIRED':
            authError.type = AuthErrorType.TOKEN_EXPIRED;
            break;
          case 'INVALID_TOKEN':
            authError.type = AuthErrorType.INVALID_TOKEN;
            break;
          case 'UNAUTHORIZED':
            authError.type = AuthErrorType.UNAUTHORIZED;
            break;
          default:
            authError.type = AuthErrorType.SERVER_ERROR;
        }
      }
      
      // Extract specific field if provided
      if (data.field) {
        authError.field = data.field;
      }
    } else if (error.request) {
      // Request was made but no response received
      authError.type = AuthErrorType.NETWORK_ERROR;
      authError.message = 'Network error. Please check your connection.';
    }
    
    return authError;
  } catch (err) {
    console.error('Error parsing authentication error:', err);
    return {
      type: AuthErrorType.UNKNOWN_ERROR,
      message: 'Failed to process error response',
      field: null
    };
  }
}

/**
 * Determines if the current token should be refreshed based on expiration
 * 
 * @returns True if token needs refreshing, false otherwise
 */
export function shouldRefreshToken(): boolean {
  try {
    const token = getAuthToken();
    
    if (!token) {
      return false; // No token to refresh
    }
    
    return isTokenExpiringSoon(token);
  } catch (error) {
    console.error('Error checking if token should be refreshed:', error);
    return false;
  }
}

/**
 * Returns the current session status (authenticated, anonymous, or none)
 * 
 * @returns Session status: 'authenticated', 'anonymous', or 'none'
 */
export function getSessionStatus(): string {
  if (isAuthenticated()) {
    return 'authenticated';
  }
  
  if (hasAnonymousSession()) {
    return 'anonymous';
  }
  
  return 'none';
}