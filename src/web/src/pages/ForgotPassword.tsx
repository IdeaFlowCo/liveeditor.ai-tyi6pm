import React, { useState, useEffect, FormEvent } from 'react'; // React v18.2.0
import { Helmet } from 'react-helmet'; // react-helmet v6.1.0
import { Link } from 'react-router-dom'; // react-router-dom v6.0.0
import AuthLayout from '../components/layout/AuthLayout';
import { ForgotPasswordForm } from '../components/auth/ForgotPasswordForm';
import { useAuth } from '../hooks/useAuth';
import { forgotPassword } from '../api/auth';
import { ROUTES } from '../constants/routes';
import { handleError } from '../utils/error-handling';

/**
 * Functional component that renders the forgot password page with a form to request password reset
 * @returns Rendered forgot password page
 */
const ForgotPassword: React.FC = () => {
  // Initialize loading state using useState
  const [loading, setLoading] = useState(false);
  // Initialize error and success message states using useState
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  /**
   * Create handleSubmit function that takes an email string parameter
   * @param email 
   */
  const handleSubmit = async (email: string) => {
    // Set loading state to true when form is submitted
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Call forgotPassword API function with the email
      await forgotPassword({ email });

      // Handle successful response by setting success message and clearing error
      setSuccess('A password reset link has been sent to your email address.');
    } catch (err: any) {
      // Handle error response using handleError utility and set error message
      handleError(err);
      setError(err.message || 'An error occurred. Please try again.');
    } finally {
      // Set loading state to false after API call completes
      setLoading(false);
    }
  };

  return (
    <>
      {/* Use Helmet to set the page title and meta description */}
      <Helmet>
        <title>Forgot Password | AI Writing Enhancement</title>
        <meta name="description" content="Request a password reset link to regain access to your AI Writing Enhancement account." />
      </Helmet>

      {/* Wrap ForgotPasswordForm with AuthLayout for consistent styling */}
      <AuthLayout title="Forgot Password">
        {/* Pass loading, error, success, and handleSubmit to the ForgotPasswordForm */}
        <ForgotPasswordForm
          onSuccess={() => setSuccess('A password reset link has been sent to your email address.')}
          onCancel={() => {}}
          className="mt-8"
        />

        {/* Provide navigation back to login page with Link component */}
        <div className="mt-4 text-center">
          <Link to={ROUTES.LOGIN} className="text-[#2C6ECB] hover:underline">
            Back to Login
          </Link>
        </div>
      </AuthLayout>
    </>
  );
};

export default ForgotPassword;