import { useEffect, useCallback } from 'react'; // React 18.2.0
import { useDispatch, useSelector } from 'react-redux'; // React-Redux 8.1.1
import useMediaQuery from './useMediaQuery';
import {
  setSidebarOpen,
  setSidebarMode,
  selectSidebarOpen,
  selectSidebarMode
} from '../store/slices/uiSlice';

/**
 * Custom hook to detect if the current viewport is mobile-sized
 * Uses the useMediaQuery hook with a mobile breakpoint
 * @returns boolean indicating if the viewport is mobile-sized
 */
function useIsMobile(): boolean {
  return useMediaQuery('(max-width: 768px)');
}

/**
 * Custom hook that provides sidebar state and control functions for the AI assistant sidebar
 * @returns Object containing sidebar state and functions to control it
 */
function useSidebar() {
  // Get current sidebar state from Redux store
  const isOpen = useSelector(selectSidebarOpen);
  const mode = useSelector(selectSidebarMode);
  const dispatch = useDispatch();
  const isMobile = useIsMobile();

  /**
   * Toggle sidebar open/closed state
   */
  const toggleSidebar = useCallback(() => {
    dispatch({ type: 'ui/toggleSidebar' });
  }, [dispatch]);

  /**
   * Close the sidebar
   */
  const closeSidebar = useCallback(() => {
    dispatch({ type: 'ui/setSidebarClosed' });
  }, [dispatch]);

  /**
   * Open the sidebar
   */
  const openSidebar = useCallback(() => {
    dispatch(setSidebarOpen());
  }, [dispatch]);

  /**
   * Set the active sidebar mode/tab
   * @param newMode The new mode to set
   */
  const setMode = useCallback((newMode: string) => {
    dispatch(setSidebarMode(newMode));
  }, [dispatch]);

  // Automatically close sidebar on mobile when screen size changes
  useEffect(() => {
    if (isMobile && isOpen) {
      closeSidebar();
    }
  }, [isMobile, isOpen, closeSidebar]);

  return {
    isOpen,
    mode,
    toggleSidebar,
    closeSidebar,
    openSidebar,
    setMode
  };
}

export default useSidebar;