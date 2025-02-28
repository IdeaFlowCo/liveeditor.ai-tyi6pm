// Import MSW server for API request interception during tests
import server from '../mocks/server';

// @testing-library/jest-dom version ^5.16.5
import '@testing-library/jest-dom';

// Configure global test timeout threshold (30 seconds)
jest.setTimeout(30000);

// Set timezone to ensure consistent date testing
process.env.TZ = 'UTC';

/**
 * Global setup function executed before all tests run
 * This function initializes the testing environment and MSW for API mocking
 */
beforeAll(() => {
  // Start MSW server to intercept API requests
  server.listen({
    onUnhandledRequest: 'warn', // Warn for unhandled requests to help identify missing handlers
  });

  // Mock window.matchMedia which isn't available in Jest DOM environment
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });

  // Silence React Developer Tools console warning
  const originalConsoleError = console.error;
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('React does not recognize the') ||
        args[0].includes('Warning: React.createElement') ||
        args[0].includes('ReactDOM.render is no longer supported'))
    ) {
      return;
    }
    originalConsoleError(...args);
  };

  // Mock ResizeObserver which isn't available in Jest DOM environment
  global.ResizeObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
  }));
});

/**
 * Cleanup function executed after each test to ensure test isolation
 * Resets handlers and cleans up component-specific mocks
 */
afterEach(() => {
  // Reset any runtime request handlers added during tests
  server.resetHandlers();

  // Clean up any component-specific mocks
  jest.clearAllMocks();

  // Reset any modified global state that might affect other tests
  jest.restoreAllMocks();
});

/**
 * Global teardown function executed after all tests complete
 * Cleans up the test environment
 */
afterAll(() => {
  // Stop MSW server from intercepting network requests
  server.close();

  // Clean up the window.matchMedia mock
  delete window.matchMedia;

  // Clean up the ResizeObserver mock
  delete global.ResizeObserver;
});