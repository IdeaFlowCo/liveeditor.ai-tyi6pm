// jest: ^27.0.0
import { renderHook, act } from '@testing-library/react-hooks'; // @testing-library/react-hooks: ^8.0.1
import { waitFor } from '@testing-library/react'; // @testing-library/react: ^14.0.0
import { useAuth } from '../../hooks/useAuth';
import { renderWithProviders, createTestStore } from '../utils/test-utils';
import server from '../mocks/server';
import { rest } from 'msw'; // msw: ^1.0.0
import { ENDPOINTS } from '../../constants/api';
import { LoginCredentials, RegisterCredentials, ConvertAnonymousRequest } from '../../types/auth';

/**
 * Main test suite for the useAuth hook
 */
describe('useAuth hook', () => {
  /**
   * Setup before each test
   */
  beforeEach(() => {
    server.resetHandlers(); // Reset any mock handlers to their default implementations
    localStorage.clear(); // Clear localStorage to ensure clean auth state
    // Set up any common test data needed across tests
  });

  /**
   * Cleanup after each test
   */
  afterEach(() => {
    localStorage.clear(); // Reset localStorage to clean state
    server.resetHandlers(); // Reset any server handlers that might have been modified
  });

  /**
   * Tests for initial hook state
   */
  describe('initial state', () => {
    /**
     * Tests the initial state values of the hook
     */
    it('should return initial authentication state', () => {
      // Render the useAuth hook using renderWithProviders
      const { result } = renderHook(() => useAuth(), { wrapper: renderWithProviders });

      // Verify initial state has user as null
      expect(result.current.user).toBeNull();
      // Verify isAuthenticated is false
      expect(result.current.isAuthenticated).toBe(false);
      // Verify isAnonymous is true
      expect(result.current.isAnonymous).toBe(true);
      // Verify isLoading is false
      expect(result.current.isLoading).toBe(false);
      // Verify error is null
      expect(result.current.error).toBeNull();
    });
  });

  /**
   * Tests for the login functionality
   */
  describe('login functionality', () => {
    /**
     * Tests successful login operation
     */
    it('should handle successful login', async () => {
      // Mock successful login API response with test user data and tokens
      const testUser = {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        profileImage: null,
        role: 'user',
        emailVerified: true,
        createdAt: new Date().toISOString(),
        lastLoginAt: new Date().toISOString(),
        preferences: null,
        isAnonymous: false,
      };
      const testToken = 'test-jwt-token';
      const testRefreshToken = 'test-refresh-token';

      server.use(
        rest.post(ENDPOINTS.AUTH.LOGIN, (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json({
              user: testUser,
              token: testToken,
              refreshToken: testRefreshToken,
              expiresIn: 3600,
            })
          );
        })
      );

      // Render the useAuth hook using renderWithProviders
      const { result } = renderHook(() => useAuth(), { wrapper: renderWithProviders });

      // Call the login function with test credentials
      const credentials: LoginCredentials = {
        email: 'test@example.com',
        password: 'password123',
        rememberMe: false,
      };

      let loginError: any = null;
      act(() => {
        result.current.login(credentials).catch(e => loginError = e);
      });

      // Wait for the operation to complete
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Verify isLoading state transitions (true during operation, false after)
      expect(result.current.isLoading).toBe(false);
      // Verify user data is updated correctly
      expect(result.current.user).toEqual(testUser);
      // Verify isAuthenticated is set to true
      expect(result.current.isAuthenticated).toBe(true);
      // Verify isAnonymous is set to false
      expect(result.current.isAnonymous).toBe(false);
      // Verify error remains null
      expect(result.current.error).toBeNull();
      expect(loginError).toBeNull();
    });

    /**
     * Tests login failure handling
     */
    it('should handle login failure', async () => {
      // Mock failed login API response with appropriate error
      const testError = 'Invalid credentials';
      server.use(
        rest.post(ENDPOINTS.AUTH.LOGIN, (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ message: testError })
          );
        })
      );

      // Render the useAuth hook using renderWithProviders
      const { result } = renderHook(() => useAuth(), { wrapper: renderWithProviders });

      // Call the login function with test credentials
      const credentials: LoginCredentials = {
        email: 'test@example.com',
        password: 'wrongpassword',
        rememberMe: false,
      };

      let loginError: any = null;
      act(() => {
        result.current.login(credentials).catch(e => loginError = e);
      });

      // Wait for the operation to complete
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Verify isLoading state transitions (true during operation, false after)
      expect(result.current.isLoading).toBe(false);
      // Verify user remains null
      expect(result.current.user).toBeNull();
      // Verify isAuthenticated remains false
      expect(result.current.isAuthenticated).toBe(false);
      // Verify error state contains the expected error message
      expect(result.current.error).toBe(testError);
      // Verify isAnonymous remains true
      expect(result.current.isAnonymous).toBe(true);
      expect(loginError.message).toBe(testError);
    });
  });

  /**
   * Tests for the registration functionality
   */
  describe('registration functionality', () => {
    /**
     * Tests successful user registration
     */
    it('should handle successful registration', async () => {
      // Mock successful registration API response with user data and tokens
      const testUser = {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        profileImage: null,
        role: 'user',
        emailVerified: true,
        createdAt: new Date().toISOString(),
        lastLoginAt: new Date().toISOString(),
        preferences: null,
        isAnonymous: false,
      };
      const testToken = 'test-jwt-token';
      const testRefreshToken = 'test-refresh-token';

      server.use(
        rest.post(ENDPOINTS.AUTH.REGISTER, (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json({
              user: testUser,
              token: testToken,
              refreshToken: testRefreshToken,
              expiresIn: 3600,
            })
          );
        })
      );

      // Render the useAuth hook using renderWithProviders
      const { result } = renderHook(() => useAuth(), { wrapper: renderWithProviders });

      // Call the register function with test registration data
      const registerData: RegisterCredentials = {
        email: 'test@example.com',
        password: 'password123',
        confirmPassword: 'password123',
        firstName: 'Test',
        lastName: 'User',
        agreeToTerms: true,
      };

      let registerError: any = null;
      act(() => {
        result.current.register(registerData).catch(e => registerError = e);
      });

      // Wait for the operation to complete
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Verify isLoading state transitions
      expect(result.current.isLoading).toBe(false);
      // Verify user data is updated correctly
      expect(result.current.user).toEqual(testUser);
      // Verify isAuthenticated is set to true
      expect(result.current.isAuthenticated).toBe(true);
      // Verify isAnonymous is set to false
      expect(result.current.isAnonymous).toBe(false);
      // Verify error remains null
      expect(result.current.error).toBeNull();
      expect(registerError).toBeNull();
    });

    /**
     * Tests registration failure handling
     */
    it('should handle registration failure', async () => {
      // Mock failed registration API response with appropriate error
      const testError = 'Email already exists';
      server.use(
        rest.post(ENDPOINTS.AUTH.REGISTER, (req, res, ctx) => {
          return res(
            ctx.status(400),
            ctx.json({ message: testError })
          );
        })
      );

      // Render the useAuth hook using renderWithProviders
      const { result } = renderHook(() => useAuth(), { wrapper: renderWithProviders });

      // Call the register function with test registration data
      const registerData: RegisterCredentials = {
        email: 'test@example.com',
        password: 'password123',
        confirmPassword: 'password123',
        firstName: 'Test',
        lastName: 'User',
        agreeToTerms: true,
      };

      let registerError: any = null;
      act(() => {
        result.current.register(registerData).catch(e => registerError = e);
      });

      // Wait for the operation to complete
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Verify isLoading state transitions
      expect(result.current.isLoading).toBe(false);
      // Verify user remains null
      expect(result.current.user).toBeNull();
      // Verify isAuthenticated remains false
      expect(result.current.isAuthenticated).toBe(false);
      // Verify error state contains the expected error message
      expect(result.current.error).toBe(testError);
      // Verify isAnonymous remains true
      expect(result.current.isAnonymous).toBe(true);
      expect(registerError.message).toBe(testError);
    });
  });

  /**
   * Tests for the logout functionality
   */
  describe('logout functionality', () => {
    /**
     * Tests successful logout operation
     */
    it('should handle logout successfully', async () => {
      // Set up authenticated state with a mock user and tokens
      const testUser = {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        profileImage: null,
        role: 'user',
        emailVerified: true,
        createdAt: new Date().toISOString(),
        lastLoginAt: new Date().toISOString(),
        preferences: null,
        isAnonymous: false,
      };
      const testToken = 'test-jwt-token';
      localStorage.setItem('auth_access_token', testToken);

      // Mock successful logout API response
      server.use(
        rest.post(ENDPOINTS.AUTH.LOGOUT, (req, res, ctx) => {
          return res(ctx.status(204));
        })
      );

      // Render the useAuth hook using renderWithProviders with authenticated state
      const { result } = renderHook(() => useAuth(), {
        wrapper: renderWithProviders,
        initialProps: {
          preloadedState: {
            auth: {
              user: testUser,
              isAuthenticated: true,
              isAnonymous: false,
              token: testToken,
              refreshToken: 'test-refresh-token',
              loading: false,
              error: null,
            },
          },
        },
      });

      // Call the logout function
      act(() => {
        result.current.logout();
      });

      // Wait for the operation to complete
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Verify user is set to null
      expect(result.current.user).toBeNull();
      // Verify isAuthenticated is set to false
      expect(result.current.isAuthenticated).toBe(false);
      // Verify isAnonymous is set to true
      expect(result.current.isAnonymous).toBe(true);
      // Verify local storage tokens are cleared
      expect(localStorage.getItem('auth_access_token')).toBeNull();
    });
  });

  /**
   * Tests for anonymous session operations
   */
  describe('anonymous session functionality', () => {
    /**
     * Tests creating an anonymous session
     */
    it('should create anonymous session', async () => {
      // Mock successful anonymous session creation API response
      const testSessionId = 'test-session-id';
      const testExpiresAt = new Date(Date.now() + 3600000).toISOString(); // Expires in 1 hour
      server.use(
        rest.post('/auth/anonymous', (req, res, ctx) => {
          return res(
            ctx.status(201),
            ctx.json({
              sessionId: testSessionId,
              expiresAt: testExpiresAt,
            })
          );
        })
      );

      // Render the useAuth hook using renderWithProviders
      const { result } = renderHook(() => useAuth(), { wrapper: renderWithProviders });

      // Call the createAnonymousSession function
      act(() => {
        result.current.createAnonymousSession();
      });

      // Wait for the operation to complete
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Verify isLoading state transitions
      expect(result.current.isLoading).toBe(false);
      // Verify isAnonymous is set to true
      expect(result.current.isAnonymous).toBe(true);
      // Verify isAuthenticated remains false
      expect(result.current.isAuthenticated).toBe(false);
      // Verify anonymous user data is set correctly
      expect(result.current.user).toEqual({
        sessionId: testSessionId,
        createdAt: expect.any(String),
        expiresAt: testExpiresAt,
        isAnonymous: true,
      });
      // Verify error remains null
      expect(result.current.error).toBeNull();
    });

    /**
     * Tests converting anonymous session to registered account
     */
    it('should convert anonymous session to registered account', async () => {
      // Set up anonymous session state with sessionId
      const testSessionId = 'test-session-id';
      localStorage.setItem('ai_writing_anonymous_session', testSessionId);

      // Mock successful conversion API response with user data and tokens
      const testUser = {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        profileImage: null,
        role: 'user',
        emailVerified: true,
        createdAt: new Date().toISOString(),
        lastLoginAt: new Date().toISOString(),
        preferences: null,
        isAnonymous: false,
      };
      const testToken = 'test-jwt-token';
      const testRefreshToken = 'test-refresh-token';

      server.use(
        rest.post('/auth/convert-anonymous', (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json({
              user: testUser,
              token: testToken,
              refreshToken: testRefreshToken,
              expiresIn: 3600,
            })
          );
        })
      );

      // Render the useAuth hook using renderWithProviders with anonymous state
      const { result } = renderHook(() => useAuth(), {
        wrapper: renderWithProviders,
        initialProps: {
          preloadedState: {
            auth: {
              user: {
                sessionId: testSessionId,
                createdAt: new Date().toISOString(),
                expiresAt: new Date(Date.now() + 3600000).toISOString(),
                isAnonymous: true,
              },
              isAuthenticated: false,
              isAnonymous: true,
              token: null,
              refreshToken: null,
              loading: false,
              error: null,
            },
          },
        },
      });

      // Call the convertToRegistered function with registration data
      const conversionData: ConvertAnonymousRequest = {
        sessionId: testSessionId,
        email: 'test@example.com',
        password: 'password123',
        firstName: 'Test',
        lastName: 'User',
        agreeToTerms: true,
      };

      let convertError: any = null;
      act(() => {
        result.current.convertToRegistered(conversionData).catch(e => convertError = e);
      });

      // Wait for the operation to complete
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Verify isLoading state transitions
      expect(result.current.isLoading).toBe(false);
      // Verify user data is updated correctly
      expect(result.current.user).toEqual(testUser);
      // Verify isAuthenticated is set to true
      expect(result.current.isAuthenticated).toBe(true);
      // Verify isAnonymous is set to false
      expect(result.current.isAnonymous).toBe(false);
      // Verify error remains null
      expect(result.current.error).toBeNull();
      expect(convertError).toBeNull();
    });
  });

  /**
   * Tests for token refresh operations
   */
  describe('token refresh functionality', () => {
    /**
     * Tests successful token refresh
     */
    it('should refresh auth token successfully', async () => {
      // Set up authenticated state with a mock user and tokens including refresh token
      const testUser = {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        profileImage: null,
        role: 'user',
        emailVerified: true,
        createdAt: new Date().toISOString(),
        lastLoginAt: new Date().toISOString(),
        preferences: null,
        isAnonymous: false,
      };
      const testToken = 'test-jwt-token';
      const testRefreshToken = 'test-refresh-token';
      const newTestToken = 'new-test-jwt-token';
      const newTestRefreshToken = 'new-test-refresh-token';

      server.use(
        rest.post(ENDPOINTS.AUTH.REFRESH, (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json({
              accessToken: newTestToken,
              refreshToken: newTestRefreshToken,
              expiresIn: 3600,
            })
          );
        })
      );

      // Render the useAuth hook using renderWithProviders with authenticated state
      const { result } = renderHook(() => useAuth(), {
        wrapper: renderWithProviders,
        initialProps: {
          preloadedState: {
            auth: {
              user: testUser,
              isAuthenticated: true,
              isAnonymous: false,
              token: testToken,
              refreshToken: testRefreshToken,
              loading: false,
              error: null,
            },
          },
        },
      });

      // Call the refreshUserToken function
      act(() => {
        result.current.refreshUserToken();
      });

      // Wait for the operation to complete
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Verify tokens are updated with new values
      expect(result.current.user).toEqual(testUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.token).toBe(newTestToken);
      expect(result.current.refreshToken).toBe(newTestRefreshToken);
      // Verify authenticated state is maintained
      expect(result.current.isAnonymous).toBe(false);
      // Verify error remains null
      expect(result.current.error).toBeNull();
    });

    /**
     * Tests token refresh failure handling
     */
    it('should handle token refresh failure', async () => {
      // Set up authenticated state with a mock user and tokens including refresh token
      const testUser = {
        id: 'test-user-id',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        profileImage: null,
        role: 'user',
        emailVerified: true,
        createdAt: new Date().toISOString(),
        lastLoginAt: new Date().toISOString(),
        preferences: null,
        isAnonymous: false,
      };
      const testToken = 'test-jwt-token';
      const testRefreshToken = 'test-refresh-token';
      const testError = 'Token expired';

      server.use(
        rest.post(ENDPOINTS.AUTH.REFRESH, (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ message: testError })
          );
        })
      );

      // Render the useAuth hook using renderWithProviders with authenticated state
      const { result } = renderHook(() => useAuth(), {
        wrapper: renderWithProviders,
        initialProps: {
          preloadedState: {
            auth: {
              user: testUser,
              isAuthenticated: true,
              isAnonymous: false,
              token: testToken,
              refreshToken: testRefreshToken,
              loading: false,
              error: null,
            },
          },
        },
      });

      // Call the refreshUserToken function
      act(() => {
        result.current.refreshUserToken();
      });

      // Wait for the operation to complete
      await waitFor(() => expect(result.current.isLoading).toBe(false));

      // Verify user is set to null on token refresh failure
      expect(result.current.user).toBeNull();
      // Verify isAuthenticated is set to false
      expect(result.current.isAuthenticated).toBe(false);
      // Verify error state contains the expected error message
      expect(result.current.error).toBe(testError);
      // Verify local storage tokens are cleared
      expect(localStorage.getItem('auth_access_token')).toBeNull();
    });
  });

  /**
   * Tests for error handling functionality
   */
  describe('error handling', () => {
    /**
     * Tests error clearing functionality
     */
    it('should clear authentication errors', () => {
      // Set up state with an authentication error
      const testError = 'Test error message';
      const { result } = renderHook(() => useAuth(), {
        wrapper: renderWithProviders,
        initialProps: {
          preloadedState: {
            auth: {
              user: null,
              isAuthenticated: false,
              isAnonymous: true,
              token: null,
              refreshToken: null,
              loading: false,
              error: testError,
            },
          },
        },
      });

      // Call the clearError function
      act(() => {
        result.current.clearError();
      });

      // Verify error is cleared to null
      expect(result.current.error).toBeNull();
    });
  });

  /**
   * Tests for redirect URL handling
   */
  describe('redirect url functionality', () => {
    /**
     * Tests setting and retrieving redirect URLs
     */
    it('should set and get redirect URL correctly', () => {
      // Render the useAuth hook using renderWithProviders
      const { result } = renderHook(() => useAuth(), { wrapper: renderWithProviders });

      // Call setRedirectUrl with a test URL
      const testUrl = '/test-redirect-url';
      act(() => {
        result.current.setRedirectUrl(testUrl);
      });

      // Call getRedirectUrl and verify it returns the correct URL
      let retrievedUrl: string | null = null;
      act(() => {
        retrievedUrl = result.current.getRedirectUrl();
      });
      expect(retrievedUrl).toBe(testUrl);
    });
  });
});