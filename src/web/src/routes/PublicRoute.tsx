import React from 'react';
import { Navigate, Outlet } from 'react-router-dom'; // react-router-dom v6.15.0
import { useAuth } from '../hooks/useAuth';
import { ROUTES } from '../constants/routes';

/**
 * Props interface for the PublicRoute component
 */
interface PublicRouteProps {
  /**
   * When true, redirects authenticated users to the dashboard
   * When false, allows authenticated users to access the route
   */
  restrictAuthenticated?: boolean;
}

/**
 * Component that manages public routes accessibility. When restrictAuthenticated is true,
 * it redirects authenticated users to the dashboard.
 * 
 * This supports the Anonymous Usage (F-007) requirement by allowing routes to be
 * accessible without authentication while still providing a way to restrict certain
 * public routes from authenticated users when needed.
 * 
 * @param props - Component properties
 * @returns Either the Outlet component to render child routes or a Navigate component for redirection
 */
const PublicRoute: React.FC<PublicRouteProps> = ({ restrictAuthenticated = false }) => {
  // Get current authentication state
  const { isAuthenticated } = useAuth();

  // If restrictAuthenticated is true and user is authenticated, redirect to dashboard
  if (restrictAuthenticated && isAuthenticated) {
    return <Navigate to={ROUTES.DASHBOARD} replace />;
  }

  // Otherwise, render the child routes
  return <Outlet />;
};

export default PublicRoute;