/**
 * Central Redux store configuration for the AI Writing Enhancement application
 * 
 * Configures Redux store with reducers from all feature slices, sets up middleware
 * including localStorage persistence, and provides typed hooks for accessing the store.
 * 
 * @module store
 * @version 1.0.0
 */

import { configureStore, combineReducers } from '@reduxjs/toolkit'; // ^1.9.5
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux'; // ^8.1.1

// Import reducers from feature slices
import authReducer from './slices/authSlice';
import documentReducer from './slices/documentSlice';
import aiReducer from './slices/aiSlice';
import uiReducer from './slices/uiSlice';

// Import custom middleware
import apiMiddleware from './middleware/api';

/**
 * Loads persisted state from localStorage
 * 
 * @returns The persisted state or undefined if none exists
 */
const loadStateFromLocalStorage = (): object | undefined => {
  try {
    const serializedState = localStorage.getItem('reduxState');
    if (!serializedState) return undefined;
    return JSON.parse(serializedState);
  } catch (error) {
    console.error('Error loading state from localStorage:', error);
    return undefined;
  }
};

/**
 * Creates middleware that persists specific parts of state to localStorage
 * 
 * @param stateSelectors - Object containing functions to select parts of state to persist
 * @returns Redux middleware function
 */
const createLocalStorageMiddleware = (stateSelectors: Record<string, (state: any) => any>) => {
  return (store: any) => (next: any) => (action: any) => {
    const result = next(action);
    
    // Get current state after action is processed
    const state = store.getState();
    
    // Extract the parts of the state to persist
    const stateToPersist: Record<string, any> = {};
    for (const key in stateSelectors) {
      stateToPersist[key] = stateSelectors[key](state);
    }
    
    // Persist to localStorage
    try {
      const serializedState = JSON.stringify(stateToPersist);
      localStorage.setItem('reduxState', serializedState);
    } catch (error) {
      console.error('Error saving state to localStorage:', error);
    }
    
    return result;
  };
};

/**
 * Configures and creates the Redux store with all reducers and middleware
 * 
 * @param preloadedState - Optional initial state to preload the store with
 * @returns Configured Redux store instance
 */
export const configureAppStore = (preloadedState = {}) => {
  // Combine all reducers
  const rootReducer = combineReducers({
    auth: authReducer,
    document: documentReducer,
    ai: aiReducer,
    ui: uiReducer
  });

  // Create selectors for localStorage persistence
  const stateSelectors = {
    auth: (state: any) => ({
      user: state.auth.user,
      isAuthenticated: state.auth.isAuthenticated,
      isAnonymous: state.auth.isAnonymous,
      token: state.auth.token,
      // Don't persist sensitive information like refreshToken
    }),
    document: (state: any) => ({
      documentList: state.document.documentList,
      // Only persist metadata, not the full document content
    }),
    ui: (state: any) => ({
      theme: state.ui.theme,
      // Persist user preferences like theme
    })
    // Don't persist AI state as it's ephemeral
  };

  // Create localStorage middleware
  const localStorageMiddleware = createLocalStorageMiddleware(stateSelectors);

  // Configure the store with reducers, preloaded state, and middleware
  const store = configureStore({
    reducer: rootReducer,
    preloadedState,
    middleware: (getDefaultMiddleware) => 
      getDefaultMiddleware({
        serializableCheck: {
          // Ignore certain paths for serializability checks
          ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
          ignoredPaths: ['auth.refreshToken']
        }
      })
      .concat(apiMiddleware, localStorageMiddleware),
    devTools: process.env.NODE_ENV !== 'production'
  });

  return store;
};

/**
 * Sets up the store with persisted state from localStorage
 * 
 * @returns Redux store initialized with persisted state
 */
export const setupStore = () => {
  const persistedState = loadStateFromLocalStorage();
  return configureAppStore(persistedState);
};

// Create the store instance
export const store = setupStore();

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

/**
 * Custom typed hook to get the dispatch function
 * 
 * @returns Typed dispatch function
 */
export const useAppDispatch = () => useDispatch<AppDispatch>();

/**
 * Custom typed hook to select from the store state
 * 
 * @template T The return type of the selector function
 * @param selector Function that extracts data from the store state
 * @returns Value returned by the selector
 */
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;