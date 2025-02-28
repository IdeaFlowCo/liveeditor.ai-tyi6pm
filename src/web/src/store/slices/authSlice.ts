import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import {
  AuthState,
  LoginCredentials,
  RegisterCredentials,
  AuthResponse,
  TokenRefreshResponse,
  AuthErrorType,
  ConvertAnonymousRequest,
  AnonymousAuthResponse
} from '../../types/auth';
import { User, AnonymousUser } from '../../types/user';
import {
  login,
  register,
  logout,
  refreshToken,
  createAnonymousSession,
  convertAnonymousToRegistered,
  verifyEmail,
  forgotPassword,
  resetPassword,
  authenticateWithOAuth
} from '../../api/auth';
import { parseAuthError } from '../../utils/auth';

/**
 * Initial state for the auth slice
 */
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isAnonymous: true,
  token: null,
  refreshToken: null,
  loading: false,
  error: null,
  errorType: null
};

/**
 * Async thunk for user login with email and password
 */
export const loginThunk = createAsyncThunk(
  'auth/login',
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      const response = await login(credentials);
      return response;
    } catch (error) {
      const parsedError = parseAuthError(error);
      return rejectWithValue({
        message: parsedError.message,
        type: parsedError.type
      });
    }
  }
);

/**
 * Async thunk for user registration
 */
export const registerThunk = createAsyncThunk(
  'auth/register',
  async (userData: RegisterCredentials, { rejectWithValue }) => {
    try {
      const response = await register(userData);
      return response;
    } catch (error) {
      const parsedError = parseAuthError(error);
      return rejectWithValue({
        message: parsedError.message,
        type: parsedError.type
      });
    }
  }
);

/**
 * Async thunk for user logout
 */
export const logoutThunk = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await logout();
      return;
    } catch (error) {
      // Log the error but don't reject the promise
      console.error('Logout error:', error);
    }
  }
);

/**
 * Async thunk for refreshing authentication token
 */
export const refreshTokenThunk = createAsyncThunk(
  'auth/refreshToken',
  async (refreshTokenValue: string, { rejectWithValue }) => {
    try {
      const response = await refreshToken({ refreshToken: refreshTokenValue });
      return response;
    } catch (error) {
      const parsedError = parseAuthError(error);
      return rejectWithValue({
        message: parsedError.message,
        type: parsedError.type
      });
    }
  }
);

/**
 * Async thunk for creating anonymous user session
 */
export const createAnonymousSessionThunk = createAsyncThunk(
  'auth/createAnonymousSession',
  async (_, { rejectWithValue }) => {
    try {
      const response = await createAnonymousSession();
      return response;
    } catch (error) {
      const parsedError = parseAuthError(error);
      return rejectWithValue({
        message: parsedError.message,
        type: parsedError.type
      });
    }
  }
);

/**
 * Async thunk for converting anonymous session to registered account
 */
export const convertAnonymousToRegisteredThunk = createAsyncThunk(
  'auth/convertAnonymousToRegistered',
  async (conversionData: ConvertAnonymousRequest, { rejectWithValue }) => {
    try {
      const response = await convertAnonymousToRegistered(conversionData);
      return response;
    } catch (error) {
      const parsedError = parseAuthError(error);
      return rejectWithValue({
        message: parsedError.message,
        type: parsedError.type
      });
    }
  }
);

/**
 * Async thunk for verifying user email with token
 */
export const verifyEmailThunk = createAsyncThunk(
  'auth/verifyEmail',
  async (token: string, { rejectWithValue }) => {
    try {
      await verifyEmail({ token });
      return { success: true };
    } catch (error) {
      const parsedError = parseAuthError(error);
      return rejectWithValue({
        message: parsedError.message,
        type: parsedError.type
      });
    }
  }
);

/**
 * Async thunk for requesting password reset
 */
export const requestPasswordResetThunk = createAsyncThunk(
  'auth/requestPasswordReset',
  async (email: string, { rejectWithValue }) => {
    try {
      await forgotPassword({ email });
      return { success: true };
    } catch (error) {
      const parsedError = parseAuthError(error);
      return rejectWithValue({
        message: parsedError.message,
        type: parsedError.type
      });
    }
  }
);

/**
 * Async thunk for resetting password with token
 */
export const resetPasswordThunk = createAsyncThunk(
  'auth/resetPassword',
  async (resetData: { token: string; password: string; confirmPassword: string }, { rejectWithValue }) => {
    try {
      await resetPassword(resetData);
      return { success: true };
    } catch (error) {
      const parsedError = parseAuthError(error);
      return rejectWithValue({
        message: parsedError.message,
        type: parsedError.type
      });
    }
  }
);

/**
 * Redux toolkit slice for authentication state management
 */
export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    /**
     * Sets auth credentials in the state
     */
    setCredentials: (
      state,
      action: PayloadAction<{
        user: User | AnonymousUser;
        token?: string;
        refreshToken?: string;
      }>
    ) => {
      state.user = action.payload.user;
      if (action.payload.token) {
        state.token = action.payload.token;
      }
      if (action.payload.refreshToken) {
        state.refreshToken = action.payload.refreshToken;
      }
      // Set authentication flags based on user type
      if ('isAnonymous' in action.payload.user && action.payload.user.isAnonymous) {
        state.isAuthenticated = false;
        state.isAnonymous = true;
      } else {
        state.isAuthenticated = true;
        state.isAnonymous = false;
      }
      state.error = null;
      state.errorType = null;
    },
    /**
     * Clears all auth credentials from state
     */
    clearCredentials: (state) => {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.isAnonymous = true;
      state.error = null;
      state.errorType = null;
    },
    /**
     * Sets the loading state for auth operations
     */
    setAuthLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    /**
     * Sets an error message in the auth state
     */
    setAuthError: (
      state,
      action: PayloadAction<{ message: string; type?: AuthErrorType }>
    ) => {
      state.error = action.payload.message;
      state.errorType = action.payload.type || null;
      state.loading = false;
    },
    /**
     * Clears any error in the auth state
     */
    clearError: (state) => {
      state.error = null;
      state.errorType = null;
    }
  },
  extraReducers: (builder) => {
    // Login thunk
    builder
      .addCase(loginThunk.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.errorType = null;
      })
      .addCase(loginThunk.fulfilled, (state, action) => {
        state.user = action.payload.user;
        state.token = action.payload.accessToken; // Map from API response field
        state.refreshToken = action.payload.refreshToken;
        state.isAuthenticated = true;
        state.isAnonymous = false;
        state.loading = false;
        state.error = null;
        state.errorType = null;
      })
      .addCase(loginThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message || 'Login failed';
        state.errorType = action.payload?.type || AuthErrorType.UNKNOWN_ERROR;
      });

    // Register thunk
    builder
      .addCase(registerThunk.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.errorType = null;
      })
      .addCase(registerThunk.fulfilled, (state, action) => {
        state.user = action.payload.user;
        state.token = action.payload.accessToken; // Map from API response field
        state.refreshToken = action.payload.refreshToken;
        state.isAuthenticated = true;
        state.isAnonymous = false;
        state.loading = false;
        state.error = null;
        state.errorType = null;
      })
      .addCase(registerThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message || 'Registration failed';
        state.errorType = action.payload?.type || AuthErrorType.UNKNOWN_ERROR;
      });

    // Logout thunk
    builder
      .addCase(logoutThunk.pending, (state) => {
        state.loading = true;
      })
      .addCase(logoutThunk.fulfilled, (state) => {
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        state.isAnonymous = true;
        state.loading = false;
      })
      .addCase(logoutThunk.rejected, (state) => {
        // Even if API logout fails, we still clear the local state
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        state.isAnonymous = true;
        state.loading = false;
      });

    // Token refresh thunk
    builder
      .addCase(refreshTokenThunk.pending, (state) => {
        state.loading = true;
      })
      .addCase(refreshTokenThunk.fulfilled, (state, action) => {
        state.token = action.payload.accessToken; // Map from API response field
        state.refreshToken = action.payload.refreshToken;
        state.loading = false;
      })
      .addCase(refreshTokenThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message || 'Token refresh failed';
        state.errorType = action.payload?.type || AuthErrorType.UNKNOWN_ERROR;
        // If token refresh fails due to expired token, clear credentials
        if (action.payload?.type === AuthErrorType.TOKEN_EXPIRED) {
          state.user = null;
          state.token = null;
          state.refreshToken = null;
          state.isAuthenticated = false;
          state.isAnonymous = true;
        }
      });

    // Anonymous session thunk
    builder
      .addCase(createAnonymousSessionThunk.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.errorType = null;
      })
      .addCase(createAnonymousSessionThunk.fulfilled, (state, action) => {
        const anonymousUser: AnonymousUser = {
          sessionId: action.payload.sessionId,
          createdAt: new Date().toISOString(),
          expiresAt: action.payload.expiresAt,
          isAnonymous: true
        };
        state.user = anonymousUser;
        state.isAuthenticated = false;
        state.isAnonymous = true;
        state.loading = false;
      })
      .addCase(createAnonymousSessionThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message || 'Failed to create anonymous session';
        state.errorType = action.payload?.type || AuthErrorType.UNKNOWN_ERROR;
      });

    // Convert anonymous to registered thunk
    builder
      .addCase(convertAnonymousToRegisteredThunk.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.errorType = null;
      })
      .addCase(convertAnonymousToRegisteredThunk.fulfilled, (state, action) => {
        state.user = action.payload.user;
        state.token = action.payload.accessToken; // Map from API response field
        state.refreshToken = action.payload.refreshToken;
        state.isAuthenticated = true;
        state.isAnonymous = false;
        state.loading = false;
      })
      .addCase(convertAnonymousToRegisteredThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message || 'Failed to convert to registered user';
        state.errorType = action.payload?.type || AuthErrorType.UNKNOWN_ERROR;
      });

    // Email verification thunk
    builder
      .addCase(verifyEmailThunk.pending, (state) => {
        state.loading = true;
      })
      .addCase(verifyEmailThunk.fulfilled, (state) => {
        // Update user's email verification status if successful
        if (state.user && !state.user.isAnonymous) {
          (state.user as User).emailVerified = true;
        }
        state.loading = false;
      })
      .addCase(verifyEmailThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message || 'Email verification failed';
        state.errorType = action.payload?.type || AuthErrorType.UNKNOWN_ERROR;
      });

    // Password reset request thunk
    builder
      .addCase(requestPasswordResetThunk.pending, (state) => {
        state.loading = true;
      })
      .addCase(requestPasswordResetThunk.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(requestPasswordResetThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message || 'Password reset request failed';
        state.errorType = action.payload?.type || AuthErrorType.UNKNOWN_ERROR;
      });

    // Reset password thunk
    builder
      .addCase(resetPasswordThunk.pending, (state) => {
        state.loading = true;
      })
      .addCase(resetPasswordThunk.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(resetPasswordThunk.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload?.message || 'Password reset failed';
        state.errorType = action.payload?.type || AuthErrorType.UNKNOWN_ERROR;
      });
  }
});

/**
 * Selector for the entire auth state
 */
export const selectAuth = (state: { auth: AuthState }) => state.auth;

/**
 * Selector for the current user
 */
export const selectUser = (state: { auth: AuthState }) => state.auth.user;

/**
 * Selector for checking if user is authenticated
 */
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated;

/**
 * Selector for checking if user is in anonymous state
 */
export const selectIsAnonymous = (state: { auth: AuthState }) => state.auth.isAnonymous;

/**
 * Selector for checking if auth operations are loading
 */
export const selectAuthLoading = (state: { auth: AuthState }) => state.auth.loading;

/**
 * Selector for auth errors
 */
export const selectAuthError = (state: { auth: AuthState }) => state.auth.error;

// Export actions
export const {
  setCredentials,
  clearCredentials,
  setAuthLoading,
  setAuthError,
  clearError
} = authSlice.actions;

// Export the reducer
export const authReducer = authSlice.reducer;
export default authReducer;