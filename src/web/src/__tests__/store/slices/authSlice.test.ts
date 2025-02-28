import { configureStore } from '@reduxjs/toolkit'; // @reduxjs/toolkit ^1.9.5
import { describe, it, expect, beforeEach, jest } from 'jest'; // jest ^29.5.0
import {
  authReducer,
  setCredentials,
  clearCredentials,
  setAuthLoading,
  setAuthError,
  clearError,
  loginThunk,
  registerThunk,
  logoutThunk,
  refreshTokenThunk,
  createAnonymousSessionThunk,
  convertAnonymousToRegisteredThunk,
  selectAuth,
  selectUser,
  selectIsAuthenticated,
  selectIsAnonymous,
  selectAuthLoading,
  selectAuthError,
} from '../../../store/slices/authSlice';
import { AuthState, AuthErrorType } from '../../../types/auth';
import { User, AnonymousUser } from '../../../types/user';
import { createTestStore } from '../../utils/test-utils';

// Mock the auth API module to isolate auth slice testing from actual API calls
jest.mock('../../../api/auth', () => ({
  login: jest.fn(),
  register: jest.fn(),
  logout: jest.fn(),
  refreshToken: jest.fn(),
  createAnonymousSession: jest.fn(),
  convertAnonymousToRegistered: jest.fn(),
}));

/**
 * Mocks a successful login API response
 * @param user 
 * @param accessToken 
 * @param refreshToken 
 * @returns Mocked successful login response
 */
const mockLoginSuccess = (user: User, accessToken: string, refreshToken: string): Promise<{user: User, accessToken: string, refreshToken: string}> => {
  return Promise.resolve({ user, accessToken, refreshToken });
};

/**
 * Mocks a failed login API response
 * @param errorMessage 
 * @param errorType 
 * @returns Rejected promise with error message
 */
const mockLoginFailure = (errorMessage: string, errorType: AuthErrorType): Promise<never> => {
  return Promise.reject({ message: errorMessage, type: errorType });
};

/**
 * Mocks a successful registration API response
 * @param user 
 * @param accessToken 
 * @param refreshToken 
 * @returns Mocked successful registration response
 */
const mockRegisterSuccess = (user: User, accessToken: string, refreshToken: string): Promise<{user: User, accessToken: string, refreshToken: string}> => {
  return Promise.resolve({ user, accessToken, refreshToken });
};

/**
 * Mocks a successful logout API response
 * @returns Resolved promise with no data
 */
const mockLogoutSuccess = (): Promise<void> => {
  return Promise.resolve();
};

/**
 * Mocks a successful anonymous session creation API response
 * @param sessionId 
 * @returns Mocked successful anonymous session response
 */
const mockCreateAnonymousSessionSuccess = (sessionId: string): Promise<{sessionId: string, expiresAt: string}> => {
  return Promise.resolve({ sessionId, expiresAt: new Date().toISOString() });
};

/**
 * Creates a mock user object for testing
 * @param overrides 
 * @returns Mock user object
 */
const createMockUser = (overrides: object = {}): User => {
  const defaultUser: User = {
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
    isAnonymous: false
  };
  return { ...defaultUser, ...overrides };
};

/**
 * Creates a mock anonymous user object for testing
 * @param overrides 
 * @returns Mock anonymous user object
 */
const createMockAnonymousUser = (overrides: object = {}): AnonymousUser => {
  const defaultAnonymousUser: AnonymousUser = {
    sessionId: 'test-session-id',
    createdAt: new Date().toISOString(),
    expiresAt: new Date().toISOString(),
    isAnonymous: true
  };
  return { ...defaultAnonymousUser, ...overrides };
};

describe('authSlice', () => {
  it('should return the initial state', () => {
    const store = createTestStore();
    expect(selectAuth(store.getState())).toEqual({
      user: null,
      isAuthenticated: false,
      isAnonymous: true,
      token: null,
      refreshToken: null,
      loading: false,
      error: null,
      errorType: null
    });
  });

  it('setCredentials should update auth state correctly', () => {
    const store = createTestStore();
    const mockUser = createMockUser();
    store.dispatch(setCredentials({ user: mockUser, token: 'test-token', refreshToken: 'test-refresh-token' }));
    expect(selectUser(store.getState())).toEqual(mockUser);
    expect(selectIsAuthenticated(store.getState())).toBe(true);
  });

  it('setCredentials should handle anonymous user correctly', () => {
    const store = createTestStore();
    const mockAnonymousUser = createMockAnonymousUser();
    store.dispatch(setCredentials({ user: mockAnonymousUser }));
    expect(selectUser(store.getState())).toEqual(mockAnonymousUser);
    expect(selectIsAuthenticated(store.getState())).toBe(false);
    expect(selectIsAnonymous(store.getState())).toBe(true);
  });

  it('clearCredentials should reset auth state', () => {
    const store = createTestStore({
      auth: {
        user: createMockUser(),
        isAuthenticated: true,
        isAnonymous: false,
        token: 'test-token',
        refreshToken: 'test-refresh-token',
        loading: false,
        error: 'test-error',
        errorType: AuthErrorType.UNKNOWN_ERROR
      }
    });
    store.dispatch(clearCredentials());
    expect(selectUser(store.getState())).toBeNull();
    expect(selectIsAuthenticated(store.getState())).toBe(false);
    expect(selectIsAnonymous(store.getState())).toBe(true);
    expect(selectAuthLoading(store.getState())).toBe(false);
    expect(selectAuthError(store.getState())).toBeNull();
  });

  it('setAuthLoading should update loading state', () => {
    const store = createTestStore();
    store.dispatch(setAuthLoading(true));
    expect(selectAuthLoading(store.getState())).toBe(true);
    store.dispatch(setAuthLoading(false));
    expect(selectAuthLoading(store.getState())).toBe(false);
  });

  it('setAuthError should update error state', () => {
    const store = createTestStore();
    store.dispatch(setAuthError({ message: 'test-error', type: AuthErrorType.INVALID_CREDENTIALS }));
    expect(selectAuthError(store.getState())).toBe('test-error');
    expect(store.getState().auth.errorType).toBe(AuthErrorType.INVALID_CREDENTIALS);
    expect(selectAuthLoading(store.getState())).toBe(false);
  });

  it('clearError should reset error state', () => {
    const store = createTestStore({
      auth: {
        user: null,
        isAuthenticated: false,
        isAnonymous: true,
        token: null,
        refreshToken: null,
        loading: false,
        error: 'test-error',
        errorType: AuthErrorType.INVALID_CREDENTIALS
      }
    });
    store.dispatch(clearError());
    expect(selectAuthError(store.getState())).toBeNull();
    expect(store.getState().auth.errorType).toBeNull();
  });
});

describe('authSlice thunks', () => {
  it('loginThunk should update state on successful login', async () => {
    const mockUser = createMockUser();
    const mockAccessToken = 'mocked-access-token';
    const mockRefreshToken = 'mocked-refresh-token';
    (require('../../../api/auth').login as jest.Mock).mockImplementation(() => mockLoginSuccess(mockUser, mockAccessToken, mockRefreshToken));

    const store = createTestStore();
    const loginCredentials = { email: 'test@example.com', password: 'password123' };
    const loginPromise = store.dispatch(loginThunk(loginCredentials as any));

    expect(selectAuthLoading(store.getState())).toBe(true);

    await loginPromise;

    expect(selectUser(store.getState())).toEqual(mockUser);
    expect(selectIsAuthenticated(store.getState())).toBe(true);
    expect(selectAuthLoading(store.getState())).toBe(false);
  });

  it('loginThunk should set error on failed login', async () => {
    const mockErrorMessage = 'Invalid credentials';
    const mockErrorType = AuthErrorType.INVALID_CREDENTIALS;
    (require('../../../api/auth').login as jest.Mock).mockImplementation(() => mockLoginFailure(mockErrorMessage, mockErrorType));

    const store = createTestStore();
    const loginCredentials = { email: 'test@example.com', password: 'wrong-password' };
    const loginPromise = store.dispatch(loginThunk(loginCredentials as any));

    await loginPromise.catch(() => {});

    expect(selectAuthError(store.getState())).toBe(mockErrorMessage);
    expect(store.getState().auth.errorType).toBe(mockErrorType);
    expect(selectAuthLoading(store.getState())).toBe(false);
  });

  it('registerThunk should update state on successful registration', async () => {
    const mockUser = createMockUser();
    const mockAccessToken = 'mocked-access-token';
    const mockRefreshToken = 'mocked-refresh-token';
    (require('../../../api/auth').register as jest.Mock).mockImplementation(() => mockRegisterSuccess(mockUser, mockAccessToken, mockRefreshToken));

    const store = createTestStore();
    const registerData = { email: 'test@example.com', password: 'password123', firstName: 'Test', lastName: 'User' };
    const registerPromise = store.dispatch(registerThunk(registerData as any));

    await registerPromise;

    expect(selectUser(store.getState())).toEqual(mockUser);
    expect(selectIsAuthenticated(store.getState())).toBe(true);
    expect(selectAuthLoading(store.getState())).toBe(false);
  });

  it('logoutThunk should clear auth state', async () => {
    (require('../../../api/auth').logout as jest.Mock).mockImplementation(() => mockLogoutSuccess());

    const store = createTestStore({
      auth: {
        user: createMockUser(),
        isAuthenticated: true,
        isAnonymous: false,
        token: 'test-token',
        refreshToken: 'test-refresh-token',
        loading: false,
        error: null,
        errorType: null
      }
    });
    const logoutPromise = store.dispatch(logoutThunk());

    await logoutPromise;

    expect(selectUser(store.getState())).toBeNull();
    expect(selectIsAuthenticated(store.getState())).toBe(false);
    expect(selectIsAnonymous(store.getState())).toBe(true);
    expect(selectAuthLoading(store.getState())).toBe(false);
  });

  it('createAnonymousSessionThunk should set anonymous state', async () => {
    const mockSessionId = 'mocked-session-id';
    (require('../../../api/auth').createAnonymousSession as jest.Mock).mockImplementation(() => mockCreateAnonymousSessionSuccess(mockSessionId));

    const store = createTestStore();
    const createAnonymousSessionPromise = store.dispatch(createAnonymousSessionThunk());

    await createAnonymousSessionPromise;

    const user = selectUser(store.getState());
    expect(selectIsAnonymous(store.getState())).toBe(true);
    expect(selectIsAuthenticated(store.getState())).toBe(false);
    expect((user as AnonymousUser)?.sessionId).toBe(mockSessionId);
  });

  it('convertAnonymousToRegisteredThunk should update from anonymous to authenticated', async () => {
    const mockUser = createMockUser();
    const mockAccessToken = 'mocked-access-token';
    const mockRefreshToken = 'mocked-refresh-token';
    (require('../../../api/auth').convertAnonymousToRegistered as jest.Mock).mockImplementation(() => mockRegisterSuccess(mockUser, mockAccessToken, mockRefreshToken));

    const store = createTestStore({
      auth: {
        user: createMockAnonymousUser(),
        isAuthenticated: false,
        isAnonymous: true,
        token: null,
        refreshToken: null,
        loading: false,
        error: null,
        errorType: null
      }
    });
    const conversionData = { sessionId: 'test-session-id', email: 'test@example.com', password: 'password123', firstName: 'Test', lastName: 'User', agreeToTerms: true };
    const convertPromise = store.dispatch(convertAnonymousToRegisteredThunk(conversionData as any));

    await convertPromise;

    expect(selectUser(store.getState())).toEqual(mockUser);
    expect(selectIsAuthenticated(store.getState())).toBe(true);
    expect(selectIsAnonymous(store.getState())).toBe(false);
  });
});

describe('authSlice selectors', () => {
  it('selectAuth should return the complete auth state', () => {
    const mockState = {
      auth: {
        user: createMockUser(),
        isAuthenticated: true,
        isAnonymous: false,
        token: 'test-token',
        refreshToken: 'test-refresh-token',
        loading: false,
        error: null,
        errorType: null
      }
    };
    const store = createTestStore(mockState);
    expect(selectAuth(store.getState())).toEqual(mockState.auth);
  });

  it('selectUser should return the current user', () => {
    const mockUser = createMockUser();
    const mockState = {
      auth: {
        user: mockUser,
        isAuthenticated: true,
        isAnonymous: false,
        token: 'test-token',
        refreshToken: 'test-refresh-token',
        loading: false,
        error: null,
        errorType: null
      }
    };
    const store = createTestStore(mockState);
    expect(selectUser(store.getState())).toEqual(mockUser);

    const emptyState = createTestStore();
    expect(selectUser(emptyState.getState())).toBeNull();
  });

  it('selectIsAuthenticated should return authentication status', () => {
    const authenticatedState = createTestStore({
      auth: {
        user: createMockUser(),
        isAuthenticated: true,
        isAnonymous: false,
        token: 'test-token',
        refreshToken: 'test-refresh-token',
        loading: false,
        error: null,
        errorType: null
      }
    });
    expect(selectIsAuthenticated(authenticatedState.getState())).toBe(true);

    const unauthenticatedState = createTestStore();
    expect(selectIsAuthenticated(unauthenticatedState.getState())).toBe(false);
  });

  it('selectIsAnonymous should return anonymous status', () => {
    const anonymousState = createTestStore({
      auth: {
        user: createMockAnonymousUser(),
        isAuthenticated: false,
        isAnonymous: true,
        token: null,
        refreshToken: null,
        loading: false,
        error: null,
        errorType: null
      }
    });
    expect(selectIsAnonymous(anonymousState.getState())).toBe(true);

    const authenticatedState = createTestStore({
      auth: {
        user: createMockUser(),
        isAuthenticated: true,
        isAnonymous: false,
        token: 'test-token',
        refreshToken: 'test-refresh-token',
        loading: false,
        error: null,
        errorType: null
      }
    });
    expect(selectIsAnonymous(authenticatedState.getState())).toBe(false);
  });

  it('selectAuthLoading should return loading status', () => {
    const loadingState = createTestStore({
      auth: {
        user: null,
        isAuthenticated: false,
        isAnonymous: true,
        token: null,
        refreshToken: null,
        loading: true,
        error: null,
        errorType: null
      }
    });
    expect(selectAuthLoading(loadingState.getState())).toBe(true);

    const notLoadingState = createTestStore();
    expect(selectAuthLoading(notLoadingState.getState())).toBe(false);
  });

  it('selectAuthError should return error message', () => {
    const errorState = createTestStore({
      auth: {
        user: null,
        isAuthenticated: false,
        isAnonymous: true,
        token: null,
        refreshToken: null,
        loading: false,
        error: 'test-error',
        errorType: null
      }
    });
    expect(selectAuthError(errorState.getState())).toBe('test-error');

    const noErrorState = createTestStore();
    expect(selectAuthError(noErrorState.getState())).toBeNull();
  });
});