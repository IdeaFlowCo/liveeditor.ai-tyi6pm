import React, { useState, useEffect } from 'react'; // React 18.2.0
import { useNavigate, useSearchParams } from 'react-router-dom'; // react-router-dom ^6.0.0
import AuthLayout from '../components/layout/AuthLayout';
import ResetPasswordForm from '../components/auth/ResetPasswordForm';
import Alert from '../components/common/Alert';
import { resetPassword, ResetPasswordRequest } from '../api/auth';
import { useAuth } from '../hooks/useAuth';
import { ROUTES } from '../constants/routes';

/**
 * Page component for resetting user password with a token
 *
 * @returns {JSX.Element} The rendered reset password page
 */
const ResetPassword: React.FC = () => {
  // LD1: Initialize state variables for loading, success, and error messages
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // LD1: Get searchParams using useSearchParams hook to extract token from URL
  const [searchParams] = useSearchParams();

  // LD1: Get navigate function using useNavigate hook for redirection
  const navigate = useNavigate();

  // LD1: Get auth state and functions from useAuth hook
  const { clearAuthError } = useAuth();

  // LD1: Extract token from URL query parameters
  const token = searchParams.get('token');

  // LD1: Check if token exists in URL on component mount
  useEffect(() => {
    if (!token) {
      // LD1: If token is missing, display an error message
      setErrorMessage('Invalid or missing token.');
    }
    // Clear any existing auth errors
    clearAuthError();
  }, [token, clearAuthError]);

  // LD1: Define handleResetPassword function to process form submission
  const handleResetPassword = async (password: string, confirmPassword: string) => {
    // LD1: Check if password and confirmPassword match
    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    // LD1: Set loading state to true during API request
    setLoading(true);
    setErrorMessage(null);

    try {
      if (token) {
        // LD1: Call resetPassword API function with token and new password
        const resetRequest: ResetPasswordRequest = {
          token,
          password,
          confirmPassword,
        };
        await resetPassword(resetRequest);

        // LD1: Handle successful password reset with success message
        setSuccess(true);
      } else {
        setErrorMessage('Invalid or missing token.');
      }
    } catch (error: any) {
      // LD1: Handle API errors by setting appropriate error message
      setErrorMessage(error.message || 'Failed to reset password. Please try again.');
    } finally {
      // LD1: Finally set loading back to false
      setLoading(false);
    }
  };

  return (
    // LD1: Render AuthLayout with 'Reset Password' title
    <AuthLayout title="Reset Password">
      {/* LD1: Display error alert if token is missing or invalid */}
      {errorMessage && (
        <Alert variant="error" message={errorMessage} dismissible onDismiss={() => setErrorMessage(null)} />
      )}

      {/* LD1: Display success alert if password reset was successful with link to login */}
      {success && (
        <Alert
          variant="success"
          message="Password reset successfully! You can now log in with your new password."
          dismissible
          onDismiss={() => setSuccess(false)}
        >
          <Link to={ROUTES.LOGIN} className="text-[#2C6ECB] hover:underline">
            Back to Login
          </Link>
        </Alert>
      )}

      {/* LD1: Render ResetPasswordForm with token and handleResetPassword callback when token is valid and reset not yet successful */}
      {token && !success && (
        <ResetPasswordForm token={token} onSubmit={handleResetPassword} loading={loading} />
      )}
    </AuthLayout>
  );
};

// IE3: Be generous about your exports so long as it doesn't create a security risk.
export default ResetPassword;