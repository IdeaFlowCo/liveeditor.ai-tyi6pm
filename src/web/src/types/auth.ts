import { User, AnonymousUser } from './user';

/**
 * Represents the authentication state in the application
 * @version 1.0.0
 */
export interface AuthState {
  /** Whether the user is authenticated with valid credentials */
  isAuthenticated: boolean;
  /** Whether the user is in an anonymous session */
  isAnonymous: boolean;
  /** The current user object, which could be authenticated, anonymous, or null if not yet determined */
  user: User | AnonymousUser | null;
  /** The JWT access token for authenticated users */
  token: string | null;
  /** The refresh token used to obtain new access tokens */
  refreshToken: string | null;
  /** Whether an authentication operation is in progress */
  loading: boolean;
  /** Error message if authentication failed */
  error: string | null;
  /** Categorized error type for more specific error handling */
  errorType: AuthErrorType | null;
}

/**
 * Defines the types of authentication actions for tracking and analytics
 * @version 1.0.0
 */
export enum AuthActionType {
  LOGIN = 'LOGIN',
  REGISTER = 'REGISTER',
  LOGOUT = 'LOGOUT',
  REFRESH_TOKEN = 'REFRESH_TOKEN',
  CREATE_ANONYMOUS = 'CREATE_ANONYMOUS',
  CONVERT_ANONYMOUS = 'CONVERT_ANONYMOUS'
}

/**
 * Categorizes authentication error types for better error handling
 * @version 1.0.0
 */
export enum AuthErrorType {
  INVALID_CREDENTIALS = 'INVALID_CREDENTIALS',
  EMAIL_EXISTS = 'EMAIL_EXISTS',
  TOKEN_EXPIRED = 'TOKEN_EXPIRED',
  INVALID_TOKEN = 'INVALID_TOKEN',
  UNAUTHORIZED = 'UNAUTHORIZED',
  NETWORK_ERROR = 'NETWORK_ERROR',
  SERVER_ERROR = 'SERVER_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR'
}

/**
 * Represents credentials for user login
 * @version 1.0.0
 */
export interface LoginCredentials {
  /** User's email address */
  email: string;
  /** User's password */
  password: string;
  /** Whether to extend the session beyond the default duration */
  rememberMe: boolean;
}

/**
 * Represents data required for new user registration
 * @version 1.0.0
 */
export interface RegisterCredentials {
  /** User's email address */
  email: string;
  /** User's chosen password */
  password: string;
  /** Password confirmation to prevent typos */
  confirmPassword: string;
  /** User's first name */
  firstName: string;
  /** User's last name */
  lastName: string;
  /** Whether the user has accepted the terms of service */
  agreeToTerms: boolean;
}

/**
 * Represents the response from authentication endpoints
 * @version 1.0.0
 */
export interface AuthResponse {
  /** Authenticated user information */
  user: User;
  /** JWT access token for API requests */
  accessToken: string;
  /** Token used to refresh the access token when it expires */
  refreshToken: string;
  /** Time in seconds until the access token expires */
  expiresIn: number;
}

/**
 * Represents the response from anonymous session creation
 * @version 1.0.0
 */
export interface AnonymousAuthResponse {
  /** Unique identifier for the anonymous session */
  sessionId: string;
  /** ISO timestamp of when the session expires */
  expiresAt: string;
}

/**
 * Represents the request to refresh an authentication token
 * @version 1.0.0
 */
export interface TokenRefreshRequest {
  /** Current refresh token */
  refreshToken: string;
}

/**
 * Represents the response from token refresh endpoint
 * @version 1.0.0
 */
export interface TokenRefreshResponse {
  /** New JWT access token */
  accessToken: string;
  /** New refresh token (token rotation) */
  refreshToken: string;
  /** Time in seconds until the new access token expires */
  expiresIn: number;
}

/**
 * Represents the request to initiate password reset
 * @version 1.0.0
 */
export interface ForgotPasswordRequest {
  /** Email address associated with the account */
  email: string;
}

/**
 * Represents the request to reset password with token
 * @version 1.0.0
 */
export interface ResetPasswordRequest {
  /** Password reset token received via email */
  token: string;
  /** New password */
  password: string;
  /** Confirmation of new password */
  confirmPassword: string;
}

/**
 * Represents the request to verify user email
 * @version 1.0.0
 */
export interface VerifyEmailRequest {
  /** Email verification token received via email */
  token: string;
}

/**
 * Represents the request to convert anonymous session to registered user
 * @version 1.0.0
 */
export interface ConvertAnonymousRequest {
  /** Anonymous session ID to convert */
  sessionId: string;
  /** User's email address for new account */
  email: string;
  /** User's chosen password */
  password: string;
  /** User's first name */
  firstName: string;
  /** User's last name */
  lastName: string;
  /** Whether the user has accepted the terms of service */
  agreeToTerms: boolean;
}

/**
 * Defines supported OAuth providers for social login
 * @version 1.0.0
 */
export enum OAuthProvider {
  GOOGLE = 'GOOGLE',
  MICROSOFT = 'MICROSOFT'
}

/**
 * Represents the request for OAuth authentication
 * @version 1.0.0
 */
export interface OAuthRequest {
  /** OAuth provider to authenticate with */
  provider: OAuthProvider;
  /** Authorization code returned from OAuth provider */
  code: string;
  /** URI the OAuth provider should redirect to after authentication */
  redirectUri: string;
}

/**
 * Represents a standardized authentication error
 * @version 1.0.0
 */
export interface AuthError {
  /** Categorized error type */
  type: AuthErrorType;
  /** Human-readable error message */
  message: string;
  /** Specific field related to the error, if applicable */
  field: string | null;
}