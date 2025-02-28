import React from 'react'; // react ^18.2.0
import { Navigate, Outlet, useLocation } from 'react-router-dom'; // react-router-dom ^6.15.0
import { useAuth } from '../hooks/useAuth';
import Spinner from '../components/common/Spinner';
import { ROUTES } from '../constants/routes';

/**
 * A component that restricts access to authenticated users only, redirecting unauthenticated users to the login page
 * 
 * @returns Either the protected route content or a redirect to the login page
 */
const PrivateRoute: React.FC = () => {
  // LD1: Get authentication state using useAuth hook (isAuthenticated, isLoading)
  const { isAuthenticated, isLoading, setRedirectUrl } = useAuth();

  // LD1: Get current location using useLocation hook to preserve the intended destination
  const location = useLocation();

  // LD1: If authentication is still loading, render a centered Spinner component
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner size="lg" center={true} />
      </div>
    );
  }

  // LD1: If user is not authenticated, store the current location as redirect URL
  // LD1: If user is not authenticated, redirect to login page using Navigate component
  if (!isAuthenticated) {
    // Store the current URL to redirect to after login
    setRedirectUrl(location.pathname);

    // Redirect to the login page
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  // LD1: If user is authenticated, render the child routes using Outlet component
  return <Outlet />;
};

// IE3: Be generous about your exports so long as it doesn't create a security risk.
export default PrivateRoute;