/**
 * Redux middleware that persists selected parts of the application state to localStorage
 * 
 * This middleware watches for state changes and persists the selected parts to
 * localStorage or sessionStorage based on the configuration provided.
 * It supports both anonymous and authenticated user sessions with different storage
 * strategies and implements debouncing to prevent performance issues.
 * 
 * @module store/middleware/localStorage
 */

import { Middleware, AnyAction } from 'redux'; // ^4.2.1
import { isEqual } from 'lodash'; // ^4.17.21
import { RootState } from '../index';
import { setItem, getItem, STORAGE_KEYS } from '../../utils/storage';

// Debounce time for storage operations in milliseconds
const STORAGE_DEBOUNCE_TIME = 1000;

// Action type constant for hydrating the store from storage
export const HYDRATE_FROM_STORAGE = 'HYDRATE_FROM_STORAGE';

/**
 * Configuration interface for localStorage middleware
 */
export interface StorageConfig {
  /**
   * Keys to persist to storage
   */
  keys: string[];
  
  /**
   * Selector functions to extract data from the state
   */
  selectors: Record<string, (state: RootState) => any>;
}

/**
 * Creates a Redux middleware that persists selected parts of the state to localStorage
 * 
 * @param config - Configuration object with keys and selectors
 * @returns Configured Redux middleware
 */
export const createLocalStorageMiddleware = (config: StorageConfig): Middleware => {
  // Store last values and debounce timers for each key
  const lastValues: Record<string, any> = {};
  const debounceTimers: Record<string, number> = {};
  
  return store => next => (action: AnyAction) => {
    // Run the action first
    const result = next(action);
    
    // Skip storage operations for the hydrate action to prevent loops
    if (action.type === HYDRATE_FROM_STORAGE) {
      return result;
    }
    
    // Get the current state
    const state = store.getState();
    
    // Check if we need to persist any values
    for (const key of config.keys) {
      const selector = config.selectors[key];
      if (!selector) continue;
      
      const value = selector(state);
      
      // Only persist if the value has changed (deep comparison)
      if (!isEqual(value, lastValues[key])) {
        // Update the last value cache
        lastValues[key] = JSON.parse(JSON.stringify(value)); // Deep clone
        
        // Clear existing debounce timer
        if (debounceTimers[key]) {
          clearTimeout(debounceTimers[key]);
        }
        
        // Set new debounce timer
        debounceTimers[key] = window.setTimeout(() => {
          // Use the appropriate storage key from constants
          const storageKey = STORAGE_KEYS[key] || key;
          
          // Determine storage type based on authentication status and key
          let storageType: 'localStorage' | 'sessionStorage' = 'localStorage';
          
          // For auth and user data, use appropriate storage based on authentication status
          if (key === 'auth' || key === 'user') {
            const isAuthenticated = state.auth?.isAuthenticated || false;
            
            // Authenticated users use localStorage, anonymous users use sessionStorage
            storageType = isAuthenticated ? 'localStorage' : 'sessionStorage';
          }
          
          // For documents, use appropriate storage based on authentication status
          else if (key === 'document' || key === 'documents') {
            const isAuthenticated = state.auth?.isAuthenticated || false;
            
            // Authenticated users use localStorage, anonymous users use sessionStorage
            storageType = isAuthenticated ? 'localStorage' : 'sessionStorage';
          }
          
          // Use the storage utility to save the value
          setItem(storageKey, value, storageType);
        }, STORAGE_DEBOUNCE_TIME);
      }
    }
    
    return result;
  };
};

/**
 * Loads persisted state from localStorage for hydrating the Redux store
 * 
 * @returns State object to hydrate the store
 */
export const loadStateFromLocalStorage = (): Partial<RootState> => {
  const state: Partial<RootState> = {};
  
  // Load auth state
  const authState = getAuthStateFromStorage();
  if (authState) {
    state.auth = authState;
  }
  
  // Load document state
  const documentState = getDocumentStateFromStorage();
  if (documentState) {
    state.document = documentState;
  }

  // Load UI preferences (like theme) if available
  const uiPreferences = getItem(STORAGE_KEYS.PREFERENCES);
  if (uiPreferences) {
    state.ui = {
      ...state.ui,
      theme: uiPreferences.theme
    };
  }
  
  return state;
};

/**
 * Helper function to load authentication state from storage
 * 
 * @returns Authentication state from storage
 */
const getAuthStateFromStorage = () => {
  // Try to get user data from localStorage
  const userData = getItem(STORAGE_KEYS.USER, 'localStorage');
  const authToken = getItem(STORAGE_KEYS.AUTH_TOKEN, 'localStorage');
  
  // Try to get anonymous session ID from sessionStorage
  const anonymousSessionId = getItem(STORAGE_KEYS.ANONYMOUS_SESSION_ID, 'sessionStorage');
  
  // If no user data, auth token, or anonymous session, return null
  if (!userData && !authToken && !anonymousSessionId) {
    return null;
  }
  
  // Determine authentication status
  const isAuthenticated = !!authToken && !!userData;
  const isAnonymous = !isAuthenticated && !!anonymousSessionId;
  
  // Return auth state object
  return {
    user: userData || (isAnonymous && anonymousSessionId ? { 
      sessionId: anonymousSessionId, 
      isAnonymous: true,
      createdAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // 24 hours
    } : null),
    token: authToken,
    isAuthenticated,
    isAnonymous,
    loading: false,
    error: null,
    errorType: null,
    // Refresh token is never stored client-side for security
    refreshToken: null
  };
};

/**
 * Helper function to load document state from storage
 * 
 * @returns Document state from storage
 */
const getDocumentStateFromStorage = () => {
  // Try to get document data from localStorage (authenticated users)
  let currentDocument = getItem(STORAGE_KEYS.CURRENT_DOCUMENT, 'localStorage');
  let documentList = getItem(STORAGE_KEYS.DOCUMENTS, 'localStorage');
  
  // If not found in localStorage, try sessionStorage (anonymous users)
  if (!currentDocument) {
    currentDocument = getItem(STORAGE_KEYS.CURRENT_DOCUMENT, 'sessionStorage');
  }
  
  if (!documentList) {
    documentList = getItem(STORAGE_KEYS.DOCUMENTS, 'sessionStorage');
  }
  
  // If no document data, return null
  if (!currentDocument && !documentList) {
    return null;
  }
  
  // Return document state object
  return {
    document: currentDocument,
    documentList: documentList || [],
    documentVersions: [],
    suggestions: [],
    loading: false,
    error: null,
    dirty: false,
    hasChanges: false
  };
};