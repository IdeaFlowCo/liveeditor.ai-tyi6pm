import { useState, useEffect, useCallback, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { RootState } from '../store';
import {
  login,
  register,
  logout,
  createAnonymousSession,
  convertAnonymousToRegistered,
  refreshToken,
  setCredentials,
  clearError
} from '../store/slices/authSlice';
import {
  selectAuth,
  selectUser,
  selectIsAuthenticated,
  selectIsAnonymous,
  selectAuthLoading,
  selectAuthError
} from '../store/slices/authSlice';
import { User, AnonymousUser } from '../types/user';
import { LoginCredentials, RegisterCredentials, ConvertAnonymousRequest } from '../types/auth';
import {
  isAuthenticated,
  hasAnonymousSession,
  shouldRefreshToken,
  initializeAuthState
} from '../utils/auth';

/**
 * Custom React hook that provides authentication functionality to components.
 * Abstracts the interaction with Redux state and API calls for auth operations.
 * Supports both authenticated and anonymous sessions with smooth transition.
 * 
 * @returns Object containing authentication state and methods
 */
export function useAuth() {
  // Access the auth state from Redux
  const auth = useSelector(selectAuth);
  const user = useSelector(selectUser);
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const isAnonymous = useSelector(selectIsAnonymous);
  const isLoading = useSelector(selectAuthLoading);
  const error = useSelector(selectAuthError);
  
  // Get dispatch function for Redux actions
  const dispatch = useDispatch();
  
  // Local state for redirect URL after authentication
  const [redirectUrl, setRedirectUrlState] = useState<string | null>(null);
  
  // Reference for token refresh interval
  const refreshIntervalRef = useRef<number | null>(null);
  
  /**
   * Logs in a user with email and password
   * 
   * @param credentials - User login credentials (email, password, rememberMe)
   * @returns Promise resolving to login result
   */
  const loginUser = useCallback(
    async (credentials: LoginCredentials) => {
      try {
        return await dispatch(login(credentials)).unwrap();
      } catch (error) {
        console.error('Login error:', error);
        throw error;
      }
    },
    [dispatch]
  );
  
  /**
   * Registers a new user
   * 
   * @param userData - User registration data
   * @returns Promise resolving to registration result
   */
  const registerUser = useCallback(
    async (userData: RegisterCredentials) => {
      try {
        return await dispatch(register(userData)).unwrap();
      } catch (error) {
        console.error('Registration error:', error);
        throw error;
      }
    },
    [dispatch]
  );
  
  /**
   * Logs out the current user
   * 
   * @returns Promise resolving when logout is complete
   */
  const logoutUser = useCallback(
    async () => {
      try {
        await dispatch(logout());
        // Clear token refresh interval if it exists
        if (refreshIntervalRef.current) {
          window.clearInterval(refreshIntervalRef.current);
          refreshIntervalRef.current = null;
        }
      } catch (error) {
        console.error('Logout error:', error);
        throw error;
      }
    },
    [dispatch]
  );
  
  /**
   * Creates an anonymous session for users without an account
   * 
   * @returns Promise resolving to the created anonymous session
   */
  const createAnonymousUser = useCallback(
    async () => {
      try {
        return await dispatch(createAnonymousSession()).unwrap();
      } catch (error) {
        console.error('Create anonymous session error:', error);
        throw error;
      }
    },
    [dispatch]
  );
  
  /**
   * Converts an anonymous user to a registered user
   * 
   * @param conversionData - Data for converting anonymous session to registered user
   * @returns Promise resolving to conversion result
   */
  const convertToRegisteredUser = useCallback(
    async (conversionData: ConvertAnonymousRequest) => {
      try {
        return await dispatch(convertAnonymousToRegistered(conversionData)).unwrap();
      } catch (error) {
        console.error('Convert to registered error:', error);
        throw error;
      }
    },
    [dispatch]
  );
  
  /**
   * Refreshes the authentication token when needed
   * 
   * @returns Promise resolving to refresh result
   */
  const refreshUserToken = useCallback(
    async () => {
      try {
        if (auth.refreshToken) {
          return await dispatch(refreshToken(auth.refreshToken)).unwrap();
        } else {
          throw new Error('No refresh token available');
        }
      } catch (error) {
        console.error('Token refresh error:', error);
        throw error;
      }
    },
    [dispatch, auth.refreshToken]
  );
  
  /**
   * Clears any authentication error state
   */
  const clearAuthError = useCallback(
    () => {
      dispatch(clearError());
    },
    [dispatch]
  );
  
  /**
   * Sets a URL to redirect to after authentication
   * 
   * @param url - URL to redirect to
   */
  const setRedirectUrl = useCallback(
    (url: string) => {
      setRedirectUrlState(url);
    },
    []
  );
  
  /**
   * Gets the stored redirect URL and clears it
   * 
   * @returns The stored redirect URL or null if none is set
   */
  const getRedirectUrl = useCallback(
    (): string | null => {
      const url = redirectUrl;
      setRedirectUrlState(null);
      return url;
    },
    [redirectUrl]
  );
  
  // Effect to check authentication status on mount
  useEffect(() => {
    // If not authenticated and not anonymous, check if we have stored credentials
    if (!isAuthenticated && !isAnonymous) {
      if (isAuthenticated()) {
        // There is a valid token in storage, update redux state
        const authState = initializeAuthState();
        if (authState.user) {
          dispatch(setCredentials({
            user: authState.user,
            token: authState.token,
            refreshToken: authState.refreshToken
          }));
        }
      } else if (hasAnonymousSession()) {
        // There is an anonymous session in storage, initialize it
        createAnonymousUser().catch(err => {
          console.error('Error initializing anonymous session:', err);
        });
      }
    }
  }, [isAuthenticated, isAnonymous, dispatch, createAnonymousUser]);
  
  // Effect to set up token refresh interval
  useEffect(() => {
    // Function to clear refresh interval
    const clearRefreshInterval = () => {
      if (refreshIntervalRef.current) {
        window.clearInterval(refreshIntervalRef.current);
        refreshIntervalRef.current = null;
      }
    };

    // If user is authenticated and has a token
    if (isAuthenticated && auth.token) {
      // Check if token needs refreshing immediately
      if (shouldRefreshToken()) {
        refreshUserToken().catch(err => {
          console.error('Error refreshing token on initialization:', err);
        });
      }
      
      // Set up interval for future checks (only if not already set)
      if (!refreshIntervalRef.current) {
        refreshIntervalRef.current = window.setInterval(() => {
          if (shouldRefreshToken()) {
            refreshUserToken().catch(err => {
              console.error('Error refreshing token:', err);
              // If refresh fails with token expired error, log out
              if (err?.type === 'TOKEN_EXPIRED') {
                logoutUser().catch(logoutErr => {
                  console.error('Error logging out after failed token refresh:', logoutErr);
                });
              }
            });
          }
        }, 60000); // Check every minute
      }
    } else {
      // Not authenticated or no token, clear any existing interval
      clearRefreshInterval();
    }
    
    // Clean up interval on unmount
    return clearRefreshInterval;
  }, [isAuthenticated, auth.token, refreshUserToken, logoutUser]);
  
  // Return auth state and methods
  return {
    // Auth state
    user,
    isAuthenticated,
    isAnonymous,
    isLoading,
    error,
    
    // Auth methods
    login: loginUser,
    register: registerUser,
    logout: logoutUser,
    createAnonymousSession: createAnonymousUser,
    convertToRegistered: convertToRegisteredUser,
    refreshUserToken,
    clearError: clearAuthError,
    
    // Redirect URL management
    setRedirectUrl,
    getRedirectUrl
  };
}