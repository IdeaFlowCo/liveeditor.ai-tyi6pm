import { useState, useEffect } from 'react'; // ^18.2.0

/**
 * A custom React hook that delays updating a value until after a specified time
 * has passed without any new updates. This is useful for preventing excessive API calls
 * and state updates during rapid user interactions such as typing.
 *
 * @template T - The type of the value being debounced
 * @param value - The value to debounce
 * @param delay - The delay in milliseconds before the value should update
 * @returns The debounced value that updates only after the specified delay
 * 
 * @example
 * // In a search component:
 * const [searchTerm, setSearchTerm] = useState('');
 * const debouncedSearchTerm = useDebounce(searchTerm, 500);
 * 
 * // Only execute search when debouncedSearchTerm changes
 * useEffect(() => {
 *   if (debouncedSearchTerm) {
 *     searchAPI(debouncedSearchTerm);
 *   }
 * }, [debouncedSearchTerm]);
 */
function useDebounce<T>(value: T, delay: number): T {
  // Initialize a state variable to store the debounced value
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Create a timeout that updates the debounced value after the specified delay
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Return a cleanup function that clears the timeout
    // if the value changes before the delay completes or the component unmounts
    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]); // Re-run the effect when value or delay changes

  // Return the debounced value
  return debouncedValue;
}

export default useDebounce;