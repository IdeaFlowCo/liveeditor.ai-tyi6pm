import React, { useEffect } from 'react'; // React 18.2.0
import { useNavigate, useLocation } from 'react-router-dom'; // react-router-dom 6.15.0

import AuthLayout from '../components/layout/AuthLayout';
import LoginForm from '../components/auth/LoginForm';
import { useAuth } from '../hooks/useAuth';
import { ROUTES } from '../constants/routes';

/**
 * Main page component for user login functionality
 *
 * @returns {JSX.Element} Rendered Login page component
 */
const Login: React.FC = () => {
  // Initialize navigate function using useNavigate hook from react-router-dom
  const navigate = useNavigate();

  // Initialize location using useLocation hook from react-router-dom to access query parameters
  const location = useLocation();

  // Get authentication state and functions from useAuth hook
  const { isAuthenticated, getRedirectUrl, setRedirectUrl } = useAuth();

  // Parse redirectTo from URL query parameters if present
  const redirectTo = new URLSearchParams(location.search).get('redirectTo');

  // Use useEffect from React to redirect user to dashboard or saved redirect URL if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      // Get redirect URL from auth context
      const storedRedirectUrl = getRedirectUrl();

      if (storedRedirectUrl) {
        // If redirect URL exists, navigate to it and clear from context
        navigate(storedRedirectUrl, { replace: true });
      } else {
        // Otherwise, navigate to dashboard as default destination
        navigate(ROUTES.DASHBOARD, { replace: true });
      }
    }
  }, [isAuthenticated, navigate, getRedirectUrl]);

  // Use useEffect from React to save redirectTo parameter to auth context for post-login redirect
  useEffect(() => {
    if (redirectTo) {
      setRedirectUrl(redirectTo);
    }
  }, [redirectTo, setRedirectUrl]);

  /**
   * Handles successful login by redirecting user to appropriate page
   *
   * @returns {void} No return value
   */
  const handleLoginSuccess = (): void => {
    // Get redirect URL from auth context
    const storedRedirectUrl = getRedirectUrl();

    if (storedRedirectUrl) {
      // If redirect URL exists, navigate to it and clear from context
      navigate(storedRedirectUrl, { replace: true });
    } else {
      // Otherwise, navigate to dashboard as default destination
      navigate(ROUTES.DASHBOARD, { replace: true });
    }
  };

  // Render AuthLayout with appropriate title
  // Render LoginForm component with success handler and redirect URL
  return (
    <AuthLayout title="Sign in">
      <LoginForm onSuccess={handleLoginSuccess} redirectTo={redirectTo || ROUTES.DASHBOARD} />
    </AuthLayout>
  );
};

export default Login;