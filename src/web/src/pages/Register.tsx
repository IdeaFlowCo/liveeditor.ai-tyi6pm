import React, { useState, useEffect } from 'react'; // React 18.2.0
import { useNavigate, useLocation, Link } from 'react-router-dom'; // react-router-dom
import AuthLayout from '../components/layout/AuthLayout';
import RegisterForm from '../components/auth/RegisterForm';
import OAuth from '../components/auth/OAuth';
import { useAuth } from '../hooks/useAuth';
import { ROUTES } from '../constants/routes';

/**
 * The main component function for the user registration page that handles form state, submission, and navigation.
 * @returns Rendered React component
 */
const Register: React.FC = () => {
  // Initialize navigate function using useNavigate hook from react-router-dom
  const navigate = useNavigate();

  // Initialize location using useLocation hook to access query parameters
  const location = useLocation();

  // Get authentication state and functions from useAuth hook
  const { isAuthenticated, setRedirectUrl } = useAuth();

  // Parse isAnonymousConversion and redirectTo from URL query parameters if present
  const isAnonymousConversion = new URLSearchParams(location.search).get('isAnonymousConversion') === 'true';
  const redirectTo = new URLSearchParams(location.search).get('redirectTo');

  // Use useEffect to redirect to dashboard or editor if user is already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      // If redirectTo is present, navigate to it, otherwise navigate to the dashboard
      if (redirectTo) {
        navigate(redirectTo);
      } else {
        navigate(ROUTES.DASHBOARD);
      }
    }
  }, [isAuthenticated, navigate, redirectTo]);

  // Use useEffect to save redirectTo parameter to auth context for post-registration redirect
  useEffect(() => {
    if (redirectTo) {
      setRedirectUrl(redirectTo);
    }
  }, [redirectTo, setRedirectUrl]);

  /**
   * Handles successful registration by redirecting user to appropriate page
   */
  const handleRegisterSuccess = () => {
    // Get redirect URL from auth context
    const redirectURL = new URLSearchParams(location.search).get('redirectTo');

    // If redirect URL exists, navigate to it and clear from context
    if (redirectURL) {
      navigate(redirectURL);
    } else {
      // Otherwise, navigate to dashboard as default destination
      navigate(ROUTES.DASHBOARD);
    }
  };

  return (
    <AuthLayout title="Create Account">
      <RegisterForm
        onSuccess={handleRegisterSuccess}
        isAnonymousConversion={isAnonymousConversion}
        showLoginLink
      />
      <div className="mt-6 text-center text-gray-600">
        OR
      </div>
      <OAuth className="mt-6" />
      <div className="mt-4 text-center">
        Already have an account? <Link to={ROUTES.LOGIN} className="text-[#2C6ECB]">Login</Link>
      </div>
    </AuthLayout>
  );
};

export default Register;