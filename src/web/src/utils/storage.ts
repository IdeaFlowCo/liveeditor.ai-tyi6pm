import { Document } from '../types/document';
import { User } from '../types/user';
import * as CryptoJS from 'crypto-js'; // v4.1.1

// Storage version for compatibility checks
export const STORAGE_VERSION = '1.0';

// Storage key constants
export const STORAGE_KEYS = {
  USER: 'ai_writing_user',
  AUTH_TOKEN: 'ai_writing_auth_token',
  CURRENT_DOCUMENT: 'ai_writing_current_document',
  DOCUMENTS: 'ai_writing_documents',
  PREFERENCES: 'ai_writing_preferences',
  ANONYMOUS_SESSION_ID: 'ai_writing_anonymous_session'
};

// Expiration times in milliseconds
const STORAGE_EXPIRY = {
  AUTH_TOKEN: 86400000, // 24 hours
  ANONYMOUS_DOCUMENTS: 604800000 // 7 days
};

// Secret key for encryption - in a production environment, this would be better managed
// and potentially retrieved from a secure environment variable
const ENCRYPTION_KEY = 'ai-writing-enhancement-secret-key';

/**
 * Interface for items with expiration
 */
interface StorageItemWithExpiry<T> {
  value: T;
  expiry: number;
}

/**
 * Stores a value in browser storage with optional expiration
 * 
 * @param key Storage key
 * @param value Value to store
 * @param storageType 'localStorage' or 'sessionStorage'
 * @param expirationMs Optional expiration time in milliseconds
 */
export function setItem<T>(
  key: string,
  value: T,
  storageType: 'localStorage' | 'sessionStorage' = 'localStorage',
  expirationMs?: number
): void {
  try {
    const storage = window[storageType];
    let storageValue: string;

    if (expirationMs) {
      const item: StorageItemWithExpiry<T> = {
        value,
        expiry: Date.now() + expirationMs
      };
      storageValue = JSON.stringify(item);
    } else {
      storageValue = JSON.stringify(value);
    }

    storage.setItem(key, storageValue);
  } catch (error) {
    console.error(`Error storing ${key} in ${storageType}:`, error);
    // Handle quota exceeded or other storage errors
    if (error instanceof DOMException && error.name === 'QuotaExceededError') {
      // Try to clear expired items to make space
      clearExpiredItems();
    }
  }
}

/**
 * Retrieves a value from browser storage, checking for expiration
 * 
 * @param key Storage key
 * @param storageType 'localStorage' or 'sessionStorage'
 * @returns The stored value or null if not found or expired
 */
export function getItem<T>(
  key: string,
  storageType: 'localStorage' | 'sessionStorage' = 'localStorage'
): T | null {
  try {
    const storage = window[storageType];
    const item = storage.getItem(key);

    if (!item) return null;

    const parsedItem = JSON.parse(item);

    // Check if the item has an expiry property
    if (parsedItem && typeof parsedItem === 'object' && parsedItem.expiry) {
      // If current time is past expiry, remove the item and return null
      if (Date.now() > parsedItem.expiry) {
        storage.removeItem(key);
        return null;
      }
      return parsedItem.value as T;
    }

    return parsedItem as T;
  } catch (error) {
    console.error(`Error retrieving ${key} from ${storageType}:`, error);
    return null;
  }
}

/**
 * Removes an item from browser storage
 * 
 * @param key Storage key
 * @param storageType 'localStorage' or 'sessionStorage'
 */
export function removeItem(
  key: string,
  storageType: 'localStorage' | 'sessionStorage' = 'localStorage'
): void {
  try {
    const storage = window[storageType];
    storage.removeItem(key);
  } catch (error) {
    console.error(`Error removing ${key} from ${storageType}:`, error);
  }
}

/**
 * Clears all items from browser storage or specific items by prefix
 * 
 * @param storageType 'localStorage' or 'sessionStorage'
 * @param keyPrefix Optional prefix to only clear matching keys
 */
export function clear(
  storageType: 'localStorage' | 'sessionStorage' = 'localStorage',
  keyPrefix?: string
): void {
  try {
    const storage = window[storageType];
    
    if (keyPrefix) {
      // Remove only items that start with the prefix
      const keysToRemove: string[] = [];
      
      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        if (key && key.startsWith(keyPrefix)) {
          keysToRemove.push(key);
        }
      }
      
      // Remove the items after collecting all keys
      // (to avoid issues with changing storage length during iteration)
      keysToRemove.forEach(key => storage.removeItem(key));
    } else {
      // Clear all items
      storage.clear();
    }
  } catch (error) {
    console.error(`Error clearing ${storageType}:`, error);
  }
}

/**
 * Saves authenticated user data to persistent storage
 * 
 * @param user The user object to store
 */
export function saveUserData(user: User): void {
  setItem(STORAGE_KEYS.USER, user, 'localStorage');
}

/**
 * Retrieves authenticated user data from storage
 * 
 * @returns The stored user data or null if not found or expired
 */
export function getUserData(): User | null {
  return getItem<User>(STORAGE_KEYS.USER, 'localStorage');
}

/**
 * Removes user data and authentication tokens from storage on logout
 */
export function clearUserData(): void {
  removeItem(STORAGE_KEYS.USER, 'localStorage');
  removeItem(STORAGE_KEYS.AUTH_TOKEN, 'localStorage');
}

/**
 * Saves authentication token with appropriate expiration
 * 
 * @param token Authentication token
 */
export function saveAuthToken(token: string): void {
  try {
    const encryptedToken = encryptData(token);
    setItem(
      STORAGE_KEYS.AUTH_TOKEN,
      encryptedToken,
      'localStorage',
      STORAGE_EXPIRY.AUTH_TOKEN
    );
  } catch (error) {
    console.error('Error saving authentication token:', error);
  }
}

/**
 * Retrieves the authentication token if not expired
 * 
 * @returns The authentication token or null if not found or expired
 */
export function getAuthToken(): string | null {
  try {
    const encryptedToken = getItem<string>(STORAGE_KEYS.AUTH_TOKEN, 'localStorage');
    if (!encryptedToken) return null;
    
    return decryptData(encryptedToken);
  } catch (error) {
    console.error('Error retrieving authentication token:', error);
    return null;
  }
}

/**
 * Saves the current document to appropriate storage based on user authentication status
 * 
 * @param document Document to save
 * @param isAuthenticated Whether the user is authenticated
 */
export function saveCurrentDocument(document: Document, isAuthenticated: boolean): void {
  try {
    if (isAuthenticated) {
      // For authenticated users, save to localStorage without expiration
      setItem(STORAGE_KEYS.CURRENT_DOCUMENT, document, 'localStorage');
    } else {
      // For anonymous users, save to sessionStorage with expiration
      setItem(
        STORAGE_KEYS.CURRENT_DOCUMENT,
        document,
        'sessionStorage',
        STORAGE_EXPIRY.ANONYMOUS_DOCUMENTS
      );
    }
  } catch (error) {
    console.error('Error saving current document:', error);
  }
}

/**
 * Retrieves the current document from storage
 * 
 * @returns The current document or null if not found
 */
export function getCurrentDocument(): Document | null {
  // Try localStorage first (for authenticated users)
  let document = getItem<Document>(STORAGE_KEYS.CURRENT_DOCUMENT, 'localStorage');
  
  // If not found, try sessionStorage (for anonymous users)
  if (!document) {
    document = getItem<Document>(STORAGE_KEYS.CURRENT_DOCUMENT, 'sessionStorage');
  }
  
  return document;
}

/**
 * Generates and saves a unique session ID for anonymous users
 * 
 * @returns The generated session ID
 */
export function saveAnonymousSessionId(): string {
  // Check if a session ID already exists
  let sessionId = getAnonymousSessionId();
  
  if (!sessionId) {
    // Generate a new ID if none exists
    sessionId = `anon-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
    setItem(STORAGE_KEYS.ANONYMOUS_SESSION_ID, sessionId, 'sessionStorage');
  }
  
  return sessionId;
}

/**
 * Retrieves the anonymous session ID if it exists
 * 
 * @returns The session ID or null if not found
 */
export function getAnonymousSessionId(): string | null {
  return getItem<string>(STORAGE_KEYS.ANONYMOUS_SESSION_ID, 'sessionStorage');
}

/**
 * Migrates anonymous user data to authenticated user storage after login/registration
 * 
 * @param userId The ID of the authenticated user
 * @returns Success status of the migration
 */
export function migrateAnonymousData(userId: string): boolean {
  try {
    // Retrieve the current document from anonymous session
    const currentDocument = getItem<Document>(STORAGE_KEYS.CURRENT_DOCUMENT, 'sessionStorage');
    
    if (currentDocument) {
      // Update document with user ID and clear session ID
      currentDocument.userId = userId;
      currentDocument.sessionId = null;
      currentDocument.isAnonymous = false;
      
      // Save to authenticated storage
      setItem(STORAGE_KEYS.CURRENT_DOCUMENT, currentDocument, 'localStorage');
      
      // Clean up the anonymous document
      removeItem(STORAGE_KEYS.CURRENT_DOCUMENT, 'sessionStorage');
    }
    
    // Get any other anonymous documents and migrate them
    // (This is a simplified version - in a real app, there might be more data to migrate)
    
    // Clear the anonymous session ID
    removeItem(STORAGE_KEYS.ANONYMOUS_SESSION_ID, 'sessionStorage');
    
    return true;
  } catch (error) {
    console.error('Error migrating anonymous data:', error);
    return false;
  }
}

/**
 * Saves a list of document metadata for the user
 * 
 * @param documents Array of document metadata
 */
export function saveDocumentList(documents: Document[]): void {
  setItem(STORAGE_KEYS.DOCUMENTS, documents, 'localStorage');
}

/**
 * Retrieves the list of documents for the user
 * 
 * @returns Array of document metadata or empty array if none found
 */
export function getDocumentList(): Document[] {
  const documents = getItem<Document[]>(STORAGE_KEYS.DOCUMENTS, 'localStorage');
  return documents || [];
}

/**
 * Utility function to clear all expired items from storage
 */
export function clearExpiredItems(): void {
  try {
    // Check localStorage
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key) {
        const item = localStorage.getItem(key);
        if (item) {
          try {
            const parsedItem = JSON.parse(item);
            if (parsedItem && typeof parsedItem === 'object' && parsedItem.expiry) {
              if (Date.now() > parsedItem.expiry) {
                localStorage.removeItem(key);
              }
            }
          } catch (e) {
            // Skip items that can't be parsed as JSON
          }
        }
      }
    }
    
    // Check sessionStorage
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key) {
        const item = sessionStorage.getItem(key);
        if (item) {
          try {
            const parsedItem = JSON.parse(item);
            if (parsedItem && typeof parsedItem === 'object' && parsedItem.expiry) {
              if (Date.now() > parsedItem.expiry) {
                sessionStorage.removeItem(key);
              }
            }
          } catch (e) {
            // Skip items that can't be parsed as JSON
          }
        }
      }
    }
  } catch (error) {
    console.error('Error clearing expired items:', error);
  }
}

/**
 * Encrypts sensitive data before storing
 * 
 * @param data String data to encrypt
 * @returns Encrypted string
 */
export function encryptData(data: string): string {
  return CryptoJS.AES.encrypt(data, ENCRYPTION_KEY).toString();
}

/**
 * Decrypts sensitive data after retrieval
 * 
 * @param encryptedData Encrypted string to decrypt
 * @returns Decrypted string
 */
export function decryptData(encryptedData: string): string {
  const bytes = CryptoJS.AES.decrypt(encryptedData, ENCRYPTION_KEY);
  return bytes.toString(CryptoJS.enc.Utf8);
}

/**
 * Checks if a specific storage type is available and working
 * 
 * @param storageType 'localStorage' or 'sessionStorage'
 * @returns Whether storage is available
 */
export function isStorageAvailable(storageType: 'localStorage' | 'sessionStorage'): boolean {
  try {
    const storage = window[storageType];
    const testKey = '__storage_test__';
    storage.setItem(testKey, 'test');
    storage.removeItem(testKey);
    return true;
  } catch (e) {
    return false;
  }
}