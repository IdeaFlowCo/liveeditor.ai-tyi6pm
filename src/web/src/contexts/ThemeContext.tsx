/**
 * Theme Context Provider for the AI writing enhancement application
 * 
 * This context handles theme management with support for:
 * - Light theme
 * - Dark theme
 * - System preference detection
 * - Theme persistence across sessions
 * 
 * @module ThemeContext
 * @version 1.0.0
 */

import React, { createContext, useState, useEffect, useContext, ReactNode } from 'react'; // React 18.2.0
import { AppTheme } from '../types';
import useMediaQuery from '../hooks/useMediaQuery';
import { getItem, setItem } from '../utils/storage';

/**
 * Storage key for persisting theme preference
 */
const THEME_STORAGE_KEY = 'app-theme';

/**
 * Default theme when no preference is stored
 */
const DEFAULT_THEME: AppTheme = 'system';

/**
 * Interface defining the shape of the theme context value
 */
interface ThemeContextType {
  /** Current theme preference ('light', 'dark', or 'system') */
  theme: AppTheme;
  /** The actual theme being applied ('light' or 'dark') */
  effectiveTheme: string;
  /** Whether dark mode is currently active */
  isDarkMode: boolean;
  /** Function to change the theme */
  setTheme: (theme: AppTheme) => void;
  /** Function to cycle through themes */
  toggleTheme: () => void;
}

/**
 * Props interface for the ThemeProvider component
 */
interface ThemeProviderProps {
  /** React children */
  children: ReactNode;
}

/**
 * Context that provides theme state and functions to components
 */
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/**
 * Provider component that manages theme state for the application
 * 
 * Handles theme detection, persistence, and toggle functionality.
 */
const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  // Initialize theme from localStorage or use default
  const [theme, setThemeState] = useState<AppTheme>(() => {
    const savedTheme = getItem<AppTheme>(THEME_STORAGE_KEY);
    return savedTheme || DEFAULT_THEME;
  });

  // Detect system preference for dark mode
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');

  // Determine effective theme based on selected theme and system preference
  const effectiveTheme = theme === 'system' 
    ? (prefersDarkMode ? 'dark' : 'light') 
    : theme;
  
  const isDarkMode = effectiveTheme === 'dark';

  // Update theme and save to localStorage
  const setTheme = (newTheme: AppTheme) => {
    setThemeState(newTheme);
    setItem(THEME_STORAGE_KEY, newTheme);
  };

  // Toggle between light, dark, and system themes
  const toggleTheme = () => {
    const themeOrder: AppTheme[] = ['light', 'dark', 'system'];
    const currentIndex = themeOrder.indexOf(theme);
    const nextIndex = (currentIndex + 1) % themeOrder.length;
    setTheme(themeOrder[nextIndex]);
  };

  // Apply theme to document by setting a data attribute
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', effectiveTheme);
  }, [effectiveTheme]);

  // Create the context value
  const contextValue: ThemeContextType = {
    theme,
    effectiveTheme,
    isDarkMode,
    setTheme,
    toggleTheme
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

/**
 * Custom hook that provides access to the theme context throughout the application
 * 
 * @returns The current theme state and theme control functions
 * @throws Error if used outside of ThemeProvider
 */
const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  
  return context;
};

export { ThemeContext, ThemeProvider, useTheme };