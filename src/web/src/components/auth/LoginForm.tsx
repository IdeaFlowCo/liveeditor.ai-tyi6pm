import React, { useState, useEffect, FormEvent } from 'react'; // React v18.2.0
import classNames from 'classnames'; // classnames v2.3.2
import { Link, useNavigate, useLocation } from 'react-router-dom'; // react-router-dom v6.15.0

import { useAuth } from '../../hooks/useAuth';
import Button from '../common/Button';
import Input from '../common/Input';
import Alert from '../common/Alert';
import OAuth from './OAuth';
import { LoginCredentials } from '../../types/auth';
import { validateEmail, validateRequired } from '../../utils/validation';
import { ROUTES } from '../../constants/routes';

// Define the LoginFormProps interface
interface LoginFormProps {
  onSuccess?: () => void;
  redirectTo?: string;
  showRegisterLink?: boolean;
  showTitle?: boolean;
  className?: string;
}

/**
 * Component that renders a login form with email/password fields and OAuth options
 *
 * @param {LoginFormProps} props - The component props
 * @returns {JSX.Element} Rendered login form component
 */
export const LoginForm: React.FC<LoginFormProps> = (props) => {
  // Destructure props with defaults
  const { showRegisterLink = true, showTitle = true, className } = props;

  // Get authentication hooks and utilities
  const { login, isLoading, error, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Initialize form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);

  // Initialize validation state
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');

  // Implement handleSubmit function to process form submission
  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();

    // Validate form
    const isValid = validateForm();
    if (!isValid) {
      return;
    }

    try {
      // Call the login function from the useAuth hook
      await login({ email, password, rememberMe });

      // Handle successful login
      if (props.onSuccess) {
        props.onSuccess();
      }

      // Redirect user if redirectTo prop is provided
      if (props.redirectTo) {
        navigate(props.redirectTo);
      } else {
        // Redirect to the previous page or the dashboard
        const redirectPath = location.state?.from || ROUTES.DASHBOARD;
        navigate(redirectPath, { replace: true });
      }
    } catch (loginError: any) {
      // Handle login errors
      console.error('Login failed:', loginError);
      // The useAuth hook handles setting the error state
    }
  };

  // Implement validateForm function to check all form fields
  const validateForm = (): boolean => {
    let isValid = true;

    // Validate email
    if (!validateRequired(email)) {
      setEmailError('Email is required');
      isValid = false;
    } else if (!validateEmail(email)) {
      setEmailError('Invalid email format');
      isValid = false;
    } else {
      setEmailError('');
    }

    // Validate password
    if (!validateRequired(password)) {
      setPasswordError('Password is required');
      isValid = false;
    } else {
      setPasswordError('');
    }

    return isValid;
  };

  // Implement handleChange function to update form state on input changes
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = event.target;

    switch (name) {
      case 'email':
        setEmail(value);
        break;
      case 'password':
        setPassword(value);
        break;
      case 'rememberMe':
        setRememberMe(type === 'checkbox' ? checked : false);
        break;
      default:
        break;
    }
  };

  // useEffect to clear authentication errors when form values change
  useEffect(() => {
    if (error) {
      clearError();
    }
  }, [email, password, clearError, error]);

  // CSS classes for the login form
  const formClasses = classNames(
    'max-w-md w-full space-y-8',
    className
  );

  return (
    <form className={formClasses} onSubmit={handleSubmit}>
      {/* Render form title if showTitle is true */}
      {showTitle && (
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Or{' '}
            {showRegisterLink && (
              <Link to={ROUTES.REGISTER} className="font-medium text-blue-600 hover:text-blue-500">
                register here
              </Link>
            )}
          </p>
        </div>
      )}

      {/* Render error Alert component if there are authentication errors */}
      {error && <Alert variant="error" message={error} />}

      <div className="space-y-4">
        {/* Render email input field with validation feedback */}
        <Input
          label="Email address"
          type="email"
          name="email"
          autoComplete="email"
          required
          fullWidth
          placeholder="Email address"
          value={email}
          onChange={handleChange}
          error={emailError}
        />

        {/* Render password input field with validation feedback */}
        <Input
          label="Password"
          type="password"
          name="password"
          autoComplete="current-password"
          required
          fullWidth
          placeholder="Password"
          value={password}
          onChange={handleChange}
          error={passwordError}
        />
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Input
            id="remember-me"
            name="rememberMe"
            type="checkbox"
            checked={rememberMe}
            onChange={handleChange}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            label=""
          />
          <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
            Remember me
          </label>
        </div>

        <div className="text-sm">
          <Link to={ROUTES.FORGOT_PASSWORD} className="font-medium text-blue-600 hover:text-blue-500">
            Forgot password?
          </Link>
        </div>
      </div>

      <div>
        {/* Render login button with loading state */}
        <Button type="submit" isFullWidth isLoading={isLoading}>
          Sign in
        </Button>
      </div>

      {/* Render OAuth component for social login options */}
      <div>
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="bg-white px-2 text-gray-500">
              Or continue with
            </span>
          </div>
        </div>

        <OAuth className="mt-3" onSuccess={props.onSuccess} onError={() => {}} isProcessing={isLoading} />
      </div>
    </form>
  );
};