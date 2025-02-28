import React, { useState, FormEvent, useEffect } from 'react';
import { FiMail } from 'react-icons/fi';
import { Button } from '../common/Button';
import Input from '../common/Input';
import { Alert } from '../common/Alert';
import { Spinner } from '../common/Spinner';
import { forgotPassword } from '../../api/auth';
import { validateEmail } from '../../utils/validation';
import { ForgotPasswordRequest } from '../../types/auth';

interface ForgotPasswordFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
  className?: string;
}

export const ForgotPasswordForm: React.FC<ForgotPasswordFormProps> = ({
  onSuccess,
  onCancel,
  className = '',
}) => {
  // State for form input, validation, and submission status
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Reset error when email changes
  useEffect(() => {
    if (emailError && email) {
      setEmailError(undefined);
    }
  }, [email, emailError]);

  // Validate form inputs
  const validateForm = (): boolean => {
    if (!email.trim()) {
      setEmailError('Email is required');
      return false;
    }
    
    if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address');
      return false;
    }
    
    return true;
  };

  // Handle form submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    // Reset status
    setErrorMessage(null);
    setSuccessMessage(null);
    
    // Validate form
    if (!validateForm()) {
      return;
    }
    
    // Set loading state
    setIsLoading(true);
    
    try {
      // Prepare request data
      const requestData: ForgotPasswordRequest = {
        email: email.trim(),
      };
      
      // Send password reset request
      const response = await forgotPassword(requestData);
      
      // Handle successful response
      setSuccessMessage(
        response.message || 
        'Password reset link has been sent to your email. Please check your inbox.'
      );
      setEmail('');
      
      // Call onSuccess callback if provided
      if (onSuccess) {
        onSuccess();
      }
    } catch (error: any) {
      // Handle error
      setErrorMessage(
        error.message || 
        'An error occurred while processing your request. Please try again.'
      );
    } finally {
      // Reset loading state
      setIsLoading(false);
    }
  };

  return (
    <div className={`w-full ${className}`}>
      {successMessage && (
        <Alert 
          variant="success"
          message={successMessage}
          dismissible={true}
          className="mb-4"
        />
      )}
      
      {errorMessage && (
        <Alert 
          variant="error"
          message={errorMessage}
          dismissible={true}
          className="mb-4"
        />
      )}
      
      <form onSubmit={handleSubmit}>
        <Input
          label="Email Address"
          type="email"
          id="forgot-password-email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={emailError}
          fullWidth={true}
          startAdornment={<FiMail className="text-gray-500" />}
          placeholder="Enter your email address"
          disabled={isLoading}
        />
        
        <div className="flex justify-between mt-6">
          {onCancel && (
            <Button 
              variant="secondary" 
              onClick={onCancel}
              disabled={isLoading}
              type="button"
            >
              Cancel
            </Button>
          )}
          
          <Button 
            type="submit"
            disabled={isLoading}
            className={onCancel ? 'ml-4' : 'w-full'}
          >
            {isLoading ? (
              <>
                <Spinner size="sm" color="white" className="mr-2" />
                Sending...
              </>
            ) : (
              'Send Reset Link'
            )}
          </Button>
        </div>
      </form>
    </div>
  );
};

// Set display name for better debugging
ForgotPasswordForm.displayName = 'ForgotPasswordForm';