/**
 * API functions for managing user data in the AI writing enhancement application
 * 
 * This module provides methods for interacting with user-related API endpoints,
 * including profile management, preference settings, and account operations for
 * both authenticated and anonymous users.
 * 
 * @module api/user
 * @version 1.0.0
 */

import { get, put, post, delete as del } from '../utils/api';
import { ENDPOINTS } from '../constants/api';
import { 
  UserProfile, 
  UserPreferences, 
  UserUpdateRequest, 
  UserPreferencesUpdateRequest, 
  ChangeEmailRequest, 
  ChangePasswordRequest 
} from '../types/user';

/**
 * Fetches the current user's profile information
 * 
 * @returns Promise resolving to the user profile data
 * @throws ApiError if the request fails
 */
export const getUserProfile = async (): Promise<UserProfile> => {
  try {
    return await get<UserProfile>(ENDPOINTS.USERS.PROFILE);
  } catch (error) {
    console.error('Failed to fetch user profile:', error);
    throw error;
  }
};

/**
 * Updates the current user's profile information
 * 
 * @param profileData - Data containing the fields to update
 * @returns Promise resolving to the updated user profile
 * @throws ApiError if the request fails
 */
export const updateUserProfile = async (profileData: UserUpdateRequest): Promise<UserProfile> => {
  try {
    return await put<UserProfile>(ENDPOINTS.USERS.PROFILE, profileData);
  } catch (error) {
    console.error('Failed to update user profile:', error);
    throw error;
  }
};

/**
 * Fetches the current user's preference settings
 * 
 * @returns Promise resolving to the user preferences
 * @throws ApiError if the request fails
 */
export const getUserPreferences = async (): Promise<UserPreferences> => {
  try {
    return await get<UserPreferences>(ENDPOINTS.USERS.PREFERENCES);
  } catch (error) {
    console.error('Failed to fetch user preferences:', error);
    throw error;
  }
};

/**
 * Updates the current user's preference settings
 * 
 * @param preferences - Preference settings to update
 * @returns Promise resolving to the updated user preferences
 * @throws ApiError if the request fails
 */
export const updateUserPreferences = async (preferences: UserPreferencesUpdateRequest): Promise<UserPreferences> => {
  try {
    return await put<UserPreferences>(ENDPOINTS.USERS.PREFERENCES, preferences);
  } catch (error) {
    console.error('Failed to update user preferences:', error);
    throw error;
  }
};

/**
 * Changes the user's email address
 * 
 * @param emailData - Object containing new email and password verification
 * @returns Promise resolving to a success message
 * @throws ApiError if the request fails
 */
export const changeEmail = async (emailData: ChangeEmailRequest): Promise<{ message: string }> => {
  try {
    return await post<{ message: string }>(`${ENDPOINTS.USERS.PROFILE}/email`, emailData);
  } catch (error) {
    console.error('Failed to change email:', error);
    throw error;
  }
};

/**
 * Changes the user's password
 * 
 * @param passwordData - Object containing current and new password
 * @returns Promise resolving to a success message
 * @throws ApiError if the request fails
 */
export const changePassword = async (passwordData: ChangePasswordRequest): Promise<{ message: string }> => {
  try {
    return await post<{ message: string }>(`${ENDPOINTS.USERS.PROFILE}/password`, passwordData);
  } catch (error) {
    console.error('Failed to change password:', error);
    throw error;
  }
};

/**
 * Uploads a new profile image for the user
 * 
 * @param imageData - FormData containing the image file
 * @returns Promise resolving to the URL of the uploaded image
 * @throws ApiError if the request fails
 */
export const uploadProfileImage = async (imageData: FormData): Promise<{ imageUrl: string }> => {
  try {
    return await post<{ imageUrl: string }>(
      `${ENDPOINTS.USERS.PROFILE}/image`,
      imageData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );
  } catch (error) {
    console.error('Failed to upload profile image:', error);
    throw error;
  }
};

/**
 * Permanently deletes the user's account
 * 
 * @param credentials - Object containing password for verification
 * @returns Promise resolving to a success message
 * @throws ApiError if the request fails
 */
export const deleteAccount = async (credentials: { password: string }): Promise<{ message: string }> => {
  try {
    return await del<{ message: string }>(ENDPOINTS.USERS.PROFILE, {
      data: credentials
    });
  } catch (error) {
    console.error('Failed to delete account:', error);
    throw error;
  }
};