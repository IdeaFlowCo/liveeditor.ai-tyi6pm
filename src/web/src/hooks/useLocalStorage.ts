import { useState, useEffect, useCallback, useRef, Dispatch, SetStateAction } from 'react'; // react@18.2.0

/**
 * Utility function to check if localStorage is available and accessible
 * @returns {boolean} True if localStorage is available and working, false otherwise
 */
export function isStorageAvailable(): boolean {
  try {
    // Check if running in a browser environment
    if (typeof window === 'undefined') {
      return false;
    }
    
    // Test localStorage by setting and removing a test item
    const testKey = '__storage_test__';
    window.localStorage.setItem(testKey, testKey);
    window.localStorage.removeItem(testKey);
    return true;
  } catch (e) {
    // localStorage might be unavailable due to:
    // - Browser's privacy mode (e.g., Safari private browsing)
    // - Storage quota exceeded
    // - Cookies/storage disabled in browser settings
    return false;
  }
}

/**
 * Helper function to safely retrieve and parse a value from localStorage
 * @param {string} key - The localStorage key to retrieve
 * @param {T | (() => T)} initialValue - The default value or function that returns the default value
 * @returns {T} The parsed value from localStorage or the initialValue
 */
function getStorageValue<T>(key: string, initialValue: T | (() => T)): T {
  // Check if localStorage is available
  if (!isStorageAvailable()) {
    // If initialValue is a function, call it to get the actual value
    return typeof initialValue === 'function' 
      ? (initialValue as () => T)() 
      : initialValue;
  }

  try {
    // Get the item from localStorage
    const item = window.localStorage.getItem(key);
    
    // Parse stored json if item exists
    if (item !== null) {
      return JSON.parse(item);
    }
    
    // If item doesn't exist in localStorage, return initialValue
    return typeof initialValue === 'function' 
      ? (initialValue as () => T)() 
      : initialValue;
  } catch (error) {
    // If parsing fails or another error occurs, return initialValue
    console.error(`Error reading localStorage key "${key}":`, error);
    return typeof initialValue === 'function' 
      ? (initialValue as () => T)() 
      : initialValue;
  }
}

/**
 * A custom React hook that provides a typed interface for using localStorage,
 * with features like serialization, error handling, and cross-tab synchronization.
 * 
 * @param {string} key - The key to store the value under in localStorage
 * @param {T | (() => T)} initialValue - The initial value or function that returns the initial value
 * @returns {[T, Dispatch<SetStateAction<T>>, () => void, boolean]} A tuple containing:
 *   - The stored value
 *   - A function to update the value
 *   - A function to remove the value
 *   - A boolean indicating if storage is available
 */
export function useLocalStorage<T>(
  key: string, 
  initialValue: T | (() => T)
): [T, Dispatch<SetStateAction<T>>, () => void, boolean] {
  // Track storage availability
  const [storageAvailable, setStorageAvailable] = useState<boolean>(isStorageAvailable());
  
  // Initialize state with value from localStorage or initialValue
  const [storedValue, setStoredValue] = useState<T>(() => 
    getStorageValue<T>(key, initialValue)
  );
  
  // Use a ref to keep track of the current key for storage event handling
  const keyRef = useRef<string>(key);
  useEffect(() => {
    keyRef.current = key;
  }, [key]);

  // Update localStorage whenever the state changes
  const setValue: Dispatch<SetStateAction<T>> = useCallback((value: SetStateAction<T>) => {
    try {
      // Allow value to be a function so we have the same API as useState
      const valueToStore = value instanceof Function 
        ? value(storedValue) 
        : value;
      
      // Save state
      setStoredValue(valueToStore);
      
      // Save to localStorage if available
      if (storageAvailable) {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      console.error(`Error saving to localStorage key "${key}":`, error);
      // Update storage availability if we encounter an error
      setStorageAvailable(isStorageAvailable());
    }
  }, [key, storedValue, storageAvailable]);

  // Function to remove the value from localStorage
  const removeValue = useCallback(() => {
    try {
      // Remove from localStorage
      if (storageAvailable) {
        window.localStorage.removeItem(key);
      }
      
      // Reset state to initialValue
      setStoredValue(
        typeof initialValue === 'function' 
          ? (initialValue as () => T)() 
          : initialValue
      );
    } catch (error) {
      console.error(`Error removing localStorage key "${key}":`, error);
      setStorageAvailable(isStorageAvailable());
    }
  }, [key, initialValue, storageAvailable]);

  // Listen for changes to localStorage made from other tabs/windows
  useEffect(() => {
    // Only attach listener if localStorage is available
    if (!storageAvailable) return;

    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === keyRef.current) {
        try {
          // Update state if our key changed in another tab
          const newValue = event.newValue 
            ? JSON.parse(event.newValue) 
            : (typeof initialValue === 'function' 
                ? (initialValue as () => T)() 
                : initialValue);
          
          setStoredValue(newValue);
        } catch (error) {
          console.error(`Error processing storage event for key "${keyRef.current}":`, error);
        }
      }
    };

    // Add event listener for storage events
    window.addEventListener('storage', handleStorageChange);

    // Clean up event listener on unmount
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [initialValue, storageAvailable]);

  return [storedValue, setValue, removeValue, storageAvailable];
}