import React, { ReactElement, ReactNode } from 'react'; // react ^18.2.0
import { render, screen, waitFor, within, fireEvent } from '@testing-library/react'; // @testing-library/react ^14.0.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.4.3
import { Provider } from 'react-redux'; // react-redux ^8.1.1
import { BrowserRouter, MemoryRouter, Routes, Route } from 'react-router-dom'; // react-router-dom ^6.9.0
import { setupServer } from 'msw/node'; // msw/node ^1.0.0
import { rest } from 'msw'; // msw ^1.0.0

import { store, configureAppStore } from '../../store';
import { AuthContext, AuthProvider } from '../../contexts/AuthContext';
import { EditorContext, EditorProvider } from '../../contexts/EditorContext';
import { ThemeContext, ThemeProvider } from '../../contexts/ThemeContext';
import handlers from '../mocks/handlers';

/**
 * Custom render function that wraps components with necessary providers (Redux, Router, Auth, Theme, Editor)
 * @param ui React element to render
 * @param options Options for the render function
 * @returns Returns enhanced render result with additional utilities including store reference
 */
const renderWithProviders = (
  ui: ReactElement,
  options: {
    preloadedState?: object;
    routerOptions?: {
      routes?: ReactElement[];
      initialEntries?: string[];
    };
    authState?: object;
    editorState?: object;
    themeState?: object;
  } = {}
) => {
  // LD1: Merge provided options with default options
  const { preloadedState = {}, routerOptions, authState, editorState, themeState } = options;

  // LD2: Create a test Redux store with initial state if provided
  const testStore = configureAppStore(preloadedState);

  // LD3: Configure router options with routes and initial entries if provided
  const { routes, initialEntries } = routerOptions || {};

  // LD4: Set up authentication mock state if provided
  const MockAuth = ({ children }: { children: ReactNode }) => (
    <AuthContext.Provider value={mockAuthContext(authState)}>
      {children}
    </AuthContext.Provider>
  );

  // LD5: Set up editor mock state if provided
  const MockEditor = ({ children }: { children: ReactNode }) => (
    <EditorContext.Provider value={mockEditorContext(editorState)}>
      {children}
    </EditorContext.Provider>
  );

  // LD6: Set up theme preferences if provided
  const MockTheme = ({ children }: { children: ReactNode }) => (
    <ThemeContext.Provider value={mockThemeContext(themeState)}>
      {children}
    </ThemeContext.Provider>
  );

  // LD7: Wrap the component with all necessary providers (Redux, Router, Auth, Editor, Theme)
  const Wrapper = ({ children }: { children: ReactNode }): JSX.Element => (
    <Provider store={testStore}>
      {routerOptions ? (
        <MemoryRouter initialEntries={initialEntries}>
          {routes ? <Routes>{routes}</Routes> : children}
        </MemoryRouter>
      ) : (
        <BrowserRouter>
          <MockAuth>
            <MockEditor>
              <MockTheme>
                {children}
              </MockTheme>
            </MockEditor>
          </MockAuth>
        </BrowserRouter>
      )}
    </Provider>
  );

  // LD8: Call RTL's render function with the wrapped component
  const renderResult = render(ui, { wrapper: Wrapper });

  // LD9: Return the render result enhanced with store and custom utilities
  return {
    ...renderResult,
    store: testStore,
  };
};

/**
 * Creates a configured Redux store for testing with optional preloaded state
 * @param preloadedState Optional initial state to preload the store with
 * @returns Configured Redux store instance
 */
const createTestStore = (preloadedState = {}) => {
  // LD1: Call configureAppStore with the provided preloaded state
  const testStore = configureAppStore(preloadedState);

  // LD2: Return the configured store instance
  return testStore;
};

/**
 * Renders a component within a MemoryRouter with specified routes and initial entry
 * @param ui React element to render
 * @param options Options for the MemoryRouter
 * @returns Returns render result with router utilities
 */
const renderWithRouter = (
  ui: ReactElement,
  options: {
    initialEntries?: string[];
    routes?: ReactElement[];
  } = {}
) => {
  // LD1: Configure MemoryRouter with initialEntries from options
  const { initialEntries = ['/'] } = options;

  // LD2: Wrap component with MemoryRouter and optional Routes
  const Wrapper = ({ children }: { children: ReactNode }): JSX.Element => (
    <MemoryRouter initialEntries={initialEntries}>
      {options.routes ? <Routes>{options.routes}</Routes> : children}
    </MemoryRouter>
  );

  // LD3: Render the wrapped component
  const renderResult = render(ui, { wrapper: Wrapper });

  // LD4: Return the render result
  return renderResult;
};

/**
 * Creates a mock AuthContext provider with specified authentication state
 * @param authState Authentication state to mock
 * @param children React nodes to render within the provider
 * @returns Auth context provider with mocked state
 */
const mockAuthContext = (authState = {}, children?: ReactNode) => {
  // LD1: Create default mock auth state (user, isAuthenticated, isAnonymous, etc.)
  const defaultAuthState = {
    user: null,
    isAuthenticated: false,
    isAnonymous: true,
    isLoading: false,
    error: null,
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    resetPassword: jest.fn(),
    transitionToAuthenticated: jest.fn(),
    setRedirectUrl: jest.fn(),
    getRedirectUrl: jest.fn(),
  };

  // LD2: Merge defaults with provided values to create complete mock state
  const mockContextValue = { ...defaultAuthState, ...authState };

  // LD3: Create mock functions for auth methods (login, register, logout)
  // LD4: Create an AuthContext provider with the mock state and functions
  // LD5: Return the provider wrapping the children
  return mockContextValue;
};

/**
 * Creates a mock EditorContext provider with specified editor state
 * @param editorState Editor state to mock
 * @param children React nodes to render within the provider
 * @returns Editor context provider with mocked state
 */
const mockEditorContext = (editorState = {}, children?: ReactNode) => {
  // LD1: Create default mock editor state (document, suggestions, editorState, etc.)
  const defaultEditorState = {
    editorState: null,
    editorView: null,
    document: null,
    suggestions: [],
    currentSuggestion: null,
    isLoading: false,
    isProcessingAi: false,
    error: null,
    setEditorView: jest.fn(),
    updateEditorState: jest.fn(),
    loadDocument: jest.fn(),
    saveDocument: jest.fn(),
    createDocument: jest.fn(),
    requestAiSuggestions: jest.fn(),
    acceptSuggestion: jest.fn(),
    rejectSuggestion: jest.fn(),
    acceptAllSuggestions: jest.fn(),
    rejectAllSuggestions: jest.fn(),
    getSelectedText: jest.fn(),
    setCurrentSuggestion: jest.fn(),
    getDocumentContent: jest.fn(),
    trackChanges: {
      enabled: true,
      toggle: jest.fn(),
    },
  };

  // LD2: Merge defaults with provided values to create complete mock state
  const mockContextValue = { ...defaultEditorState, ...editorState };

  // LD3: Create mock functions for editor methods (loadDocument, saveDocument, requestAiSuggestions, etc.)
  // LD4: Create an EditorContext provider with the mock state and functions
  // LD5: Return the provider wrapping the children
  return mockContextValue;
};

/**
 * Creates a mock ThemeContext provider with specified theme preferences
 * @param themeState Theme state to mock
 * @param children React nodes to render within the provider
 * @returns Theme context provider with mocked state
 */
const mockThemeContext = (themeState = {}, children?: ReactNode) => {
  // LD1: Create default mock theme state (theme, effectiveTheme, isDarkMode)
  const defaultThemeState = {
    theme: 'light',
    effectiveTheme: 'light',
    isDarkMode: false,
    setTheme: jest.fn(),
    toggleTheme: jest.fn(),
  };

  // LD2: Merge defaults with provided values to create complete mock state
  const mockContextValue = { ...defaultThemeState, ...themeState };

  // LD3: Create mock functions for theme methods (setTheme, toggleTheme)
  // LD4: Create a ThemeContext provider with the mock state and functions
  // LD5: Return the provider wrapping the children
  return mockContextValue;
};

/**
 * Creates a Mock Service Worker server for API mocking in tests
 * @param customHandlers Array of request handlers to use
 * @returns Configured MSW server instance
 */
const createMockServer = (customHandlers = []) => {
  // LD1: Import default handlers from mock handlers module
  // LD2: Combine default handlers with any custom handlers provided
  const allHandlers = [...handlers, ...customHandlers];

  // LD3: Create and return a new MSW server with the combined handlers
  return setupServer(...allHandlers);
};

// Export the custom render function
export { renderWithProviders, createTestStore, renderWithRouter, mockAuthContext, mockEditorContext, mockThemeContext, createMockServer, screen, waitFor, within, userEvent, fireEvent };