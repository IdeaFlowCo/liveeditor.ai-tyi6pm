// msw: ^1.2.2
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

/**
 * Creates a Mock Service Worker (MSW) server for intercepting API requests during testing.
 * This server allows tests to run without making actual network requests,
 * providing consistent and controlled responses for reliable testing.
 * 
 * Usage:
 * - Call server.listen() before tests
 * - Call server.resetHandlers() between tests (if needed)
 * - Call server.close() after tests
 * 
 * @example
 * // In setupTests.js or similar setup file:
 * beforeAll(() => server.listen())
 * afterEach(() => server.resetHandlers())
 * afterAll(() => server.close())
 */
export const server = setupServer(...handlers);