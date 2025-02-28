/**
 * Application route paths
 * Centralized route definitions to prevent hardcoding URLs throughout the application
 * This enables consistent navigation and easier route updates across the entire app
 */
export const ROUTES = {
  /**
   * Landing page route
   */
  HOME: '/',

  /**
   * Document editor route
   * Used for both creating new documents and editing existing ones
   */
  EDITOR: '/editor',

  /**
   * User login page
   */
  LOGIN: '/login',

  /**
   * User registration page
   */
  REGISTER: '/register',

  /**
   * User dashboard showing overview and recent documents
   */
  DASHBOARD: '/dashboard',

  /**
   * Document management page for listing and managing user documents
   */
  DOCUMENTS: '/documents',

  /**
   * User settings and preferences page
   */
  SETTINGS: '/settings',

  /**
   * Forgot password request page
   */
  FORGOT_PASSWORD: '/forgot-password',

  /**
   * Reset password page (used with token)
   */
  RESET_PASSWORD: '/reset-password',

  /**
   * 404 Not found page
   */
  NOT_FOUND: '/404'
};

/**
 * Generates a route to the editor with a specific document ID
 * @param documentId - The ID of the document to edit
 * @returns The complete URL path to the specified document in the editor
 */
export const getEditorRoute = (documentId: string): string => {
  return `${ROUTES.EDITOR}/${documentId}`;
};

/**
 * Generates a route to the reset password page with a token
 * @param token - The password reset token
 * @returns The complete URL path to the reset password page with token
 */
export const getResetPasswordRoute = (token: string): string => {
  return `${ROUTES.RESET_PASSWORD}?token=${token}`;
};