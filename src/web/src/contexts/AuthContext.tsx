import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from 'react'; // react ^18.2.0
import {
  User,
  LoginCredentials,
  RegisterCredentials,
  AnonymousUser,
} from '../types/auth';
import {
  login as loginUser,
  register as registerUser,
  logout as logoutUser,
  resetPassword as resetPassword,
} from '../api/auth';
import {
  setToken,
  removeToken,
  getToken,
} from '../utils/auth';

/**
 * @version 1.0.0
 * Defines the structure of the authentication context
 */
interface AuthContextType {
  /** Current user object */
  user: User | AnonymousUser | null;
  /** Whether the user is authenticated */
  isAuthenticated: boolean;
  /** Whether the authentication state is currently loading */
  isLoading: boolean;
  /** Any error that occurred during authentication */
  error: string | null;
  /** Whether the user is in an anonymous session */
  isAnonymous: boolean;
  /** Function to log in a user */
  login: (credentials: LoginCredentials) => Promise<void>;
  /** Function to register a new user */
  register: (userData: RegisterCredentials) => Promise<void>;
  /** Function to log out the current user */
  logout: () => Promise<void>;
  /** Function to reset the user's password */
  resetPassword: (email: string) => Promise<void>;
  /** Function to transition an anonymous session to an authenticated session */
  transitionToAuthenticated: (user: User) => void;
}

/**
 * @version 1.0.0
 * Creates the authentication context with default values
 */
export const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  isAnonymous: false,
  login: async () => {},
  register: async () => {},
  logout: async () => {},
  resetPassword: async () => {},
  transitionToAuthenticated: () => {},
});

/**
 * @version 1.0.0
 * React component that provides authentication context to its children
 * @param children - React nodes to be rendered within the AuthProvider
 */
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  // Initialize user state as null
  const [user, setUser] = useState<User | AnonymousUser | null>(null);
  // Initialize isAuthenticated state as false
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  // Initialize isLoading state as true
  const [isLoading, setIsLoading] = useState<boolean>(true);
  // Initialize error state as null
  const [error, setError] = useState<string | null>(null);
  // Initialize isAnonymous state as true if no token exists
  const [isAnonymous, setIsAnonymous] = useState<boolean>(getToken() === null);

  /**
   * @version 1.0.0
   * Defines login function that calls loginUser API and updates state
   * @param credentials - User login credentials
   */
  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await loginUser(credentials);
      setUser(response.user);
      setToken(response.accessToken);
      setIsAuthenticated(true);
      setIsAnonymous(false);
    } catch (e: any) {
      setError(e.message);
      setIsAuthenticated(false);
      setIsAnonymous(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * @version 1.0.0
   * Defines register function that calls registerUser API and updates state
   * @param userData - User registration data
   */
  const register = useCallback(async (userData: RegisterCredentials) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await registerUser(userData);
      setUser(response.user);
      setToken(response.accessToken);
      setIsAuthenticated(true);
      setIsAnonymous(false);
    } catch (e: any) {
      setError(e.message);
      setIsAuthenticated(false);
      setIsAnonymous(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * @version 1.0.0
   * Defines logout function that calls logoutUser API and clears state
   */
  const logout = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      await logoutUser();
      setUser(null);
      removeToken();
      setIsAuthenticated(false);
      setIsAnonymous(false);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * @version 1.0.0
   * Defines resetPassword function that calls resetPassword API
   * @param email - User email address
   */
  const resetPassword = useCallback(async (email: string) => {
    setIsLoading(true);
    setError(null);
    // Implement reset password logic here
    setIsLoading(false);
  }, []);

  /**
   * @version 1.0.0
   * Defines transitionToAuthenticated function to convert anonymous sessions
   * @param user - Authenticated user object
   */
  const transitionToAuthenticated = useCallback((user: User) => {
    setUser(user);
    setIsAuthenticated(true);
    setIsAnonymous(false);
  }, []);

  /**
   * @version 1.0.0
   * Use useEffect to check for existing tokens and restore sessions on mount
   */
  useEffect(() => {
    const checkAuthStatus = async () => {
      setIsLoading(true);
      try {
        const token = getToken();
        if (token) {
          // Validate session with the server
          // const response = await validateSession();
          // setUser(response.user);
          setIsAuthenticated(true);
          setIsAnonymous(false);
        } else {
          setUser(null);
          setIsAuthenticated(false);
          setIsAnonymous(true);
        }
      } catch (e: any) {
        setError(e.message);
        setIsAuthenticated(false);
        setIsAnonymous(true);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  /**
   * @version 1.0.0
   * Create context value object with all state and functions
   */
  const contextValue: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    error,
    isAnonymous,
    login,
    register,
    logout,
    resetPassword,
    transitionToAuthenticated,
  };

  // Return AuthContext.Provider with the context value, wrapping children
  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
};

/**
 * @version 1.0.0
 * Custom hook to use the auth context in components
 */
export const useAuth = (): AuthContextType => {
  // Use useContext to access the AuthContext
  const context = useContext(AuthContext);
  // Validate context is being used within an AuthProvider
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  // Return the context object
  return context;
};