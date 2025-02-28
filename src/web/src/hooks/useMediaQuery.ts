import { useState, useEffect } from 'react'; // React 18.2.0

/**
 * Custom hook that checks if a provided media query string matches the current viewport
 * @param query CSS media query string to check against
 * @returns boolean indicating if the query currently matches
 */
function useMediaQuery(query: string): boolean {
  // Define state variable with initial value based on current match
  const [matches, setMatches] = useState<boolean>(() => {
    // Check if window is defined (to prevent SSR issues)
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false; // Default to false for server-side rendering
  });

  useEffect(() => {
    // Ensure we're in a browser environment
    if (typeof window === 'undefined') return;
    
    // Create MediaQueryList object using window.matchMedia(query)
    const mediaQueryList = window.matchMedia(query);
    
    // Function to evaluate the media query and update state
    const handleChange = () => {
      setMatches(mediaQueryList.matches);
    };

    // Add event listener for changes to the media query state
    if (mediaQueryList.addEventListener) {
      mediaQueryList.addEventListener('change', handleChange);
    } else {
      // For older browsers
      mediaQueryList.addListener(handleChange);
    }

    // Return cleanup function to remove the event listener on unmount
    return () => {
      if (mediaQueryList.removeEventListener) {
        mediaQueryList.removeEventListener('change', handleChange);
      } else {
        // For older browsers
        mediaQueryList.removeListener(handleChange);
      }
    };
  }, [query]); // Re-run effect if the query changes

  // Return the current match state boolean value
  return matches;
}

export default useMediaQuery;