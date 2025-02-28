import React from 'react'; // react ^18.2.0
import ReactDOM from 'react-dom/client'; // react-dom ^18.2.0
import { Provider } from 'react-redux'; // react-redux ^8.0.5
import { BrowserRouter } from 'react-router-dom'; // react-router-dom ^6.15.0
import { createRoot } from 'react-dom/client'; // react-dom/client ^18.2.0

import App from './App';
import { store } from './store';
import './assets/styles/tailwind.css';
import { initAnalytics } from './lib/analytics';

/**
 * The main entry function that initializes the application
 */
function main(): void {
  // Initialize analytics tracking for user insights and performance monitoring
  initAnalytics();

  // Get the DOM element with id 'root' to mount the React application
  const rootElement = document.getElementById('root');

  // Create a root using ReactDOM.createRoot for React 18's concurrent features
  const root = createRoot(rootElement as HTMLElement);

  // Render the application wrapped in necessary providers:
  // - Provider from react-redux for global state management
  // - BrowserRouter for client-side routing
  // - Optional StrictMode in development environment for detecting potential problems
  root.render(
    <React.StrictMode>
      <Provider store={store}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </Provider>
    </React.StrictMode>
  );
}

// Call the main function to start the application
main();