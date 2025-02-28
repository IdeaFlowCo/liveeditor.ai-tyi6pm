import { 
  LoginCredentials, 
  RegisterCredentials, 
  AuthResponse, 
  AnonymousAuthResponse, 
  TokenRefreshRequest, 
  TokenRefreshResponse, 
  ForgotPasswordRequest, 
  ResetPasswordRequest, 
  VerifyEmailRequest, 
  ConvertAnonymousRequest, 
  OAuthRequest,
  AuthError
} from '../types/auth';
import { post, get } from '../utils/api';
import { ENDPOINTS } from '../constants/api';
import { 
  parseAuthError, 
  processAuthResponse, 
  processAnonymousAuthResponse, 
  processTokenRefreshResponse,
  clearAuthStorage
} from '../utils/auth';
import { AxiosError } from 'axios'; // ^1.4.0

/**
 * Authenticates a user with their credentials and returns a token and user information
 * 
 * @param credentials - User login credentials (email, password, rememberMe)
 * @returns Promise resolving to user data with authentication tokens
 */
export const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
  try {
    const response = await post<AuthResponse>(ENDPOINTS.AUTH.LOGIN, credentials);
    processAuthResponse(response);
    return response;
  } catch (error) {
    throw parseAuthError(error);
  }
};

/**
 * Creates a new user account with the provided registration data
 * 
 * @param userData - Registration data including email, password, name
 * @returns Promise resolving to new user data with authentication token
 */
export const register = async (userData: RegisterCredentials): Promise<AuthResponse> => {
  try {
    const response = await post<AuthResponse>(ENDPOINTS.AUTH.REGISTER, userData);
    processAuthResponse(response);
    return response;
  } catch (error) {
    throw parseAuthError(error);
  }
};

/**
 * Logs out the current user by invalidating their authentication token
 * 
 * @returns Promise resolving when logout is complete
 */
export const logout = async (): Promise<void> => {
  try {
    await post(ENDPOINTS.AUTH.LOGOUT);
    clearAuthStorage(); // Clear local authentication data
  } catch (error) {
    console.error('Logout error:', error);
    clearAuthStorage(); // Still clear auth data on error
  }
};

/**
 * Refreshes the authentication token using a refresh token
 * 
 * @param refreshData - Object containing the refresh token
 * @returns Promise resolving to new access and refresh tokens
 */
export const refreshToken = async (refreshData: TokenRefreshRequest): Promise<TokenRefreshResponse> => {
  try {
    const response = await post<TokenRefreshResponse>(ENDPOINTS.AUTH.REFRESH, refreshData);
    processTokenRefreshResponse(response);
    return response;
  } catch (error) {
    throw parseAuthError(error);
  }
};

/**
 * Initiates the password reset process by requesting a reset link be sent to the user's email
 * 
 * @param data - Object containing the user's email
 * @returns Promise resolving to a success message
 */
export const forgotPassword = async (data: ForgotPasswordRequest): Promise<{ message: string }> => {
  try {
    return await post<{ message: string }>(ENDPOINTS.AUTH.PASSWORD_RESET, data);
  } catch (error) {
    throw parseAuthError(error);
  }
};

/**
 * Resets the user's password using a reset token
 * 
 * @param data - Object containing the reset token and new password
 * @returns Promise resolving to a success message
 */
export const resetPassword = async (data: ResetPasswordRequest): Promise<{ message: string }> => {
  try {
    return await post<{ message: string }>(ENDPOINTS.AUTH.PASSWORD_RESET_CONFIRM, data);
  } catch (error) {
    throw parseAuthError(error);
  }
};

/**
 * Verifies a user's email address using a verification token
 * 
 * @param data - Object containing the verification token
 * @returns Promise resolving to a success message
 */
export const verifyEmail = async (data: VerifyEmailRequest): Promise<{ message: string }> => {
  try {
    return await post<{ message: string }>(ENDPOINTS.AUTH.VERIFY, data);
  } catch (error) {
    throw parseAuthError(error);
  }
};

/**
 * Validates the current user session by checking the token with the server
 * 
 * @returns Promise resolving to user data if session is valid
 */
export const validateSession = async (): Promise<AuthResponse> => {
  try {
    // Assuming session validation endpoint
    const response = await get<AuthResponse>('/auth/session');
    processAuthResponse(response);
    return response;
  } catch (error) {
    throw parseAuthError(error);
  }
};

/**
 * Creates an anonymous session for users who haven't logged in
 * 
 * @returns Promise resolving to anonymous session identifier and expiration
 */
export const createAnonymousSession = async (): Promise<AnonymousAuthResponse> => {
  try {
    // Assuming anonymous session creation endpoint
    const response = await post<AnonymousAuthResponse>('/auth/anonymous');
    processAnonymousAuthResponse(response);
    return response;
  } catch (error) {
    throw parseAuthError(error);
  }
};

/**
 * Converts an anonymous session to a registered user account
 * 
 * @param data - Registration data including the anonymous session ID
 * @returns Promise resolving to new user data with authentication token
 */
export const convertAnonymousToRegistered = async (data: ConvertAnonymousRequest): Promise<AuthResponse> => {
  try {
    // Assuming anonymous conversion endpoint
    const response = await post<AuthResponse>('/auth/convert-anonymous', data);
    processAuthResponse(response);
    return response;
  } catch (error) {
    throw parseAuthError(error);
  }
};

/**
 * Authenticates a user using an OAuth provider
 * 
 * @param data - OAuth provider, code, and redirect URI
 * @returns Promise resolving to user data with authentication token
 */
export const authenticateWithOAuth = async (data: OAuthRequest): Promise<AuthResponse> => {
  try {
    // Assuming OAuth authentication endpoint
    const response = await post<AuthResponse>('/auth/oauth', data);
    processAuthResponse(response);
    return response;
  } catch (error) {
    throw parseAuthError(error);
  }
};