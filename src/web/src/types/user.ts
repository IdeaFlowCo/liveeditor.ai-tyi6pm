/**
 * Defines user roles for authorization in the application
 * @version 1.0.0
 */
export enum UserRole {
  USER = 'user',
  ADMIN = 'admin'
}

/**
 * User preferences for notification delivery
 * @version 1.0.0
 */
export interface NotificationPreferences {
  /** Whether to receive notifications via email */
  email: boolean;
  /** Whether to receive notifications about document updates */
  documentUpdates: boolean;
  /** Whether to receive marketing communications */
  marketing: boolean;
}

/**
 * User-configurable privacy and data sharing preferences
 * @version 1.0.0
 */
export interface PrivacySettings {
  /** Whether to allow collection of usage data */
  dataCollection: boolean;
  /** Whether to allow documents to be used for AI model training */
  aiModelTraining: boolean;
  /** Whether to allow anonymized usage statistics to be shared */
  shareUsageStatistics: boolean;
}

/**
 * User customization preferences for the application
 * @version 1.0.0
 */
export interface UserPreferences {
  /** User interface theme */
  theme: string;
  /** Font size for document editor */
  fontSize: number;
  /** Categories of AI improvement prompts to show by default */
  defaultPromptCategories: string[];
  /** Settings for notification delivery */
  notificationSettings: NotificationPreferences;
  /** User-configurable privacy and data sharing preferences */
  privacySettings: PrivacySettings;
}

/**
 * Represents a registered user in the system
 * @version 1.0.0
 */
export interface User {
  /** Unique identifier for the user */
  id: string;
  /** User's email address (unique) */
  email: string;
  /** User's first name */
  firstName: string;
  /** User's last name */
  lastName: string;
  /** URL to user's profile image (null if not set) */
  profileImage: string | null;
  /** User's role for authorization purposes */
  role: UserRole;
  /** Whether the user's email has been verified */
  emailVerified: boolean;
  /** ISO timestamp of when the account was created */
  createdAt: string;
  /** ISO timestamp of the user's last login (null if never logged in) */
  lastLoginAt: string | null;
  /** User's application preferences (null if not set) */
  preferences: UserPreferences | null;
  /** Flag indicating this is a registered user (false) */
  isAnonymous: boolean;
}

/**
 * Represents an anonymous user session
 * @version 1.0.0
 */
export interface AnonymousUser {
  /** Unique session identifier for the anonymous user */
  sessionId: string;
  /** ISO timestamp of when the session was created */
  createdAt: string;
  /** ISO timestamp of when the session will expire */
  expiresAt: string;
  /** Flag indicating this is an anonymous user (true) */
  isAnonymous: boolean;
}

/**
 * Subset of user data exposed in profile management
 * @version 1.0.0
 */
export interface UserProfile {
  /** User's first name */
  firstName: string;
  /** User's last name */
  lastName: string;
  /** URL to user's profile image (null if not set) */
  profileImage: string | null;
  /** User's email address */
  email: string;
  /** Whether the user's email has been verified */
  emailVerified: boolean;
}

/**
 * Request payload for updating user profile information
 * @version 1.0.0
 */
export interface UserUpdateRequest {
  /** Updated first name */
  firstName: string;
  /** Updated last name */
  lastName: string;
}

/**
 * Request payload for updating user preferences
 * @version 1.0.0
 */
export interface UserPreferencesUpdateRequest {
  /** Updated theme preference (undefined if not changing) */
  theme?: string;
  /** Updated font size preference (undefined if not changing) */
  fontSize?: number;
  /** Updated default prompt categories (undefined if not changing) */
  defaultPromptCategories?: string[];
  /** Updated notification settings (undefined if not changing) */
  notificationSettings?: Partial<NotificationPreferences>;
  /** Updated privacy settings (undefined if not changing) */
  privacySettings?: Partial<PrivacySettings>;
}

/**
 * Request payload for changing user's email address
 * @version 1.0.0
 */
export interface ChangeEmailRequest {
  /** New email address */
  newEmail: string;
  /** Current password for verification */
  password: string;
}

/**
 * Request payload for changing user's password
 * @version 1.0.0
 */
export interface ChangePasswordRequest {
  /** Current password for verification */
  currentPassword: string;
  /** New password */
  newPassword: string;
  /** Confirmation of new password (must match newPassword) */
  confirmPassword: string;
}

/**
 * Represents either an authenticated or anonymous user session
 * @version 1.0.0
 */
export type UserSession = User | AnonymousUser;