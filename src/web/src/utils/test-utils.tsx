/**
 * Utility functions and components for testing React components with all necessary providers.
 * Enables comprehensive unit and integration testing of the application's frontend components.
 *
 * @module test-utils
 * @version 1.0.0
 */

import React, { ReactElement, ReactNode } from 'react'; // react ^18.2.0
import { render, RenderOptions, RenderResult } from '@testing-library/react'; // @testing-library/react ^14.0.0
import userEvent from '@testing-library/user-event'; // @testing-library/user-event ^14.0.0
import { Provider } from 'react-redux'; // react-redux ^8.1.1
import { BrowserRouter, MemoryRouter, Routes, Route } from 'react-router-dom'; // react-router-dom ^6.15.0
import { PreloadedState } from '@reduxjs/toolkit'; // @reduxjs/toolkit ^1.9.5

import { setupStore, RootState, AppDispatch } from '../store';
import { AuthProvider } from '../contexts/AuthContext';
import { ThemeProvider } from '../contexts/ThemeContext';
import { EditorProvider } from '../contexts/EditorContext';

/**
 * Renders a React component wrapped with all necessary providers for testing (Redux, Router, Auth, Theme, Editor).
 *
 * @param ui - The React component to render.
 * @param options - Custom render options to merge with default options.
 * @param preloadedState - Optional preloaded state for the Redux store.
 * @param initialEntries - Optional initial entries for the Router.
 * @returns Enhanced render result with store and user event utilities.
 */
const renderWithProviders = (
  ui: ReactElement,
  options: RenderOptions = {},
  preloadedState?: Partial<RootState>,
  initialEntries?: string[]
): RenderResult & { store: ReturnType<typeof setupStore>; user: ReturnType<typeof userEvent.setup> } => {
  // LD1: Create a test Redux store using setupStore with provided preloaded state
  const store = setupStore(preloadedState);

  // LD1: Set up user event instance for simulating user interactions
  const user = userEvent.setup();

  // LD1: Create a wrapper component that composes all providers (Redux, Router, Auth, Theme, Editor)
  const AllTheProviders = ({ children }: { children?: ReactNode }) => (
    // IE1: Wrap with Redux Provider using the test store
    <Provider store={store}>
      {/* IE1: Wrap with Router provider with initial entries if provided */}
      <MemoryRouter initialEntries={initialEntries}>
        {/* IE1: Wrap with AuthProvider for authentication context */}
        <AuthProvider>
          {/* IE1: Wrap with ThemeProvider for theme context */}
          <ThemeProvider>
            {/* IE1: Wrap with EditorProvider for editor context */}
            <EditorProvider>
              {children}
            </EditorProvider>
          </ThemeProvider>
        </AuthProvider>
      </MemoryRouter>
    </Provider>
  );

  // LD1: Handle custom render options and merge with default options
  const renderOptions = {
    wrapper: AllTheProviders,
    ...options,
  };

  // LD1: Render the UI component with all providers wrapped around it
  const renderResult = render(ui, renderOptions);

  // LD1: Return render result enhanced with store and user event utilities
  return {
    ...renderResult,
    store,
    user,
  };
};

/**
 * Creates a configured Redux store with test state for testing purposes.
 *
 * @param preloadedState - Optional preloaded state for the Redux store.
 * @returns Configured Redux store.
 */
const createTestStore = (preloadedState?: Partial<RootState>): ReturnType<typeof setupStore> => {
  // LD1: Call setupStore with the provided preloaded state
  // LD1: Return the configured store instance
  return setupStore(preloadedState);
};

/**
 * Creates a wrapper component with all providers for testing.
 *
 * @param store - Configured Redux store.
 * @param initialEntries - Optional initial entries for the Router.
 * @returns Provider wrapper component.
 */
const createWrapper = (store: ReturnType<typeof setupStore>, initialEntries?: string[]): React.FC => {
  // LD1: Return a function component that wraps children with all necessary providers
  const ProviderWrapper: React.FC<{ children?: ReactNode }> = ({ children }) => (
    // IE1: Wrap with Redux Provider using the test store
    <Provider store={store}>
      {/* IE1: Wrap with Router provider with initial entries if provided */}
      <MemoryRouter initialEntries={initialEntries}>
        {/* IE1: Wrap with AuthProvider for authentication context */}
        <AuthProvider>
          {/* IE1: Wrap with ThemeProvider for theme context */}
          <ThemeProvider>
            {/* IE1: Wrap with EditorProvider for editor context */}
            <EditorProvider>
              {children}
            </EditorProvider>
          </ThemeProvider>
        </AuthProvider>
      </MemoryRouter>
    </Provider>
  );
  return ProviderWrapper;
};

// IE3: Be generous about your exports so long as it doesn't create a security risk
export * from '@testing-library/react';
export { renderWithProviders, createTestStore, createWrapper };