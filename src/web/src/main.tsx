import React from 'react'; // react ^18.2.0
import ReactDOM from 'react-dom/client'; // react-dom ^18.2.0
import { BrowserRouter } from 'react-router-dom'; // react-router-dom ^6.15.0
import { Provider } from 'react-redux'; // react-redux ^8.0.5
import App from './App';
import { store } from './store';
import AuthProvider from './contexts/AuthContext';
import ThemeProvider from './contexts/ThemeContext';
import EditorProvider from './contexts/EditorContext';
import ErrorBoundary from './components/common/ErrorBoundary';
import { initAnalytics } from './lib/analytics';
import './assets/styles/tailwind.css';

/**
 * Initializes analytics and renders the root React component with all necessary providers
 */
const main = (): void => {
  // Initialize analytics tracking
  initAnalytics();

  // Create a root element using ReactDOM.createRoot on 'root' DOM element
  const root = ReactDOM.createRoot(
    document.getElementById('root') as HTMLElement
  );

  // Render the App component wrapped in providers (ErrorBoundary, BrowserRouter, Provider, AuthProvider, ThemeProvider, EditorProvider)
  root.render(
    <React.StrictMode>
      <ErrorBoundary name="Root">
        <BrowserRouter>
          <Provider store={store}>
            <AuthProvider>
              <ThemeProvider>
                <EditorProvider>
                  <App />
                </EditorProvider>
              </ThemeProvider>
            </AuthProvider>
          </Provider>
        </BrowserRouter>
      </ErrorBoundary>
    </React.StrictMode>
  );
  // Handle strict mode in development environment
};

// Call the main function to start the application
main();