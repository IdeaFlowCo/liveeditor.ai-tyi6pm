import { useEffect, RefObject } from 'react'; // React 18.2.0

/**
 * Custom hook that detects clicks outside of the specified element(s) and
 * calls a callback function when such clicks occur. Used for closing modals,
 * dropdowns, sidebars, and other interactive components when a user clicks
 * outside of them.
 *
 * @param callback Function to call when a click outside is detected
 * @param refs A ref or array of refs to elements to detect clicks outside of
 */
export const useClickOutside = (
  callback: () => void,
  refs: RefObject<HTMLElement> | RefObject<HTMLElement>[]
): void => {
  useEffect(() => {
    // Validate input parameters
    if (!callback || typeof callback !== 'function') {
      console.warn('useClickOutside: callback must be a function');
      return;
    }

    if (!refs) {
      console.warn('useClickOutside: refs must be provided');
      return;
    }

    // Normalize refs to always be an array for consistent handling
    const refArray = Array.isArray(refs) ? refs : [refs];

    // Handler function for click/touch events
    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      // Get the element that was clicked
      const target = event.target as Node;

      // Check if the click was not inside any of the ref elements
      const isOutside = !refArray.some((ref) => {
        return ref.current && ref.current.contains(target);
      });

      // If click was outside, call the callback
      if (isOutside) {
        callback();
      }
    };

    // Add event listeners for both mouse and touch events
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);

    // Clean up event listeners on unmount or when dependencies change
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [callback, refs]); // Re-run effect if callback or refs change
};