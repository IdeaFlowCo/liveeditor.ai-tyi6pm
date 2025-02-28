import React from 'react'; // react ^18.2.0
import { Provider } from 'react-redux'; // react-redux ^8.1.1
import AppRoutes from './routes';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';
import store from './store';
import ErrorBoundary from './components/common/ErrorBoundary';

/**
 * Root component that wraps the entire application with necessary providers and routes
 * @returns {JSX.Element} The full application component tree
 */
function App() {
  // Wrap the entire application with an ErrorBoundary to catch any unhandled errors
  return (
    <ErrorBoundary name="App">
      {/* Provide the Redux store using Provider from react-redux */}
      <Provider store={store}>
        {/* Set up ThemeProvider to manage application theming */}
        <ThemeProvider>
          {/* Set up AuthProvider to manage authentication state */}
          <AuthProvider>
            {/* Render the AppRoutes component which contains all application routes */}
            <AppRoutes />
          </AuthProvider>
        </ThemeProvider>
      </Provider>
    </ErrorBoundary>
  );
  // Ensure proper nesting order of providers to make dependencies available to child components
}

// Export the App component as the default export to be used as the application entry point
export default App;