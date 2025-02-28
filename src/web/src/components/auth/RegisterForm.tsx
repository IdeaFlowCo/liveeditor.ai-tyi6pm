import React, { useState, useEffect } from 'react'; // React v18.2.0
import { useForm, Controller } from 'react-hook-form'; // react-hook-form v7.43.0
import { Button } from '../common/Button';
import Input from '../common/Input';
import Alert from '../common/Alert';
import { useAuth } from '../../hooks/useAuth';
import { RegisterCredentials } from '../../types/auth';
import {
  validateEmail,
  validatePassword,
  validatePasswordMatch,
  validateRequired,
} from '../../utils/validation';

/**
 * Props for the RegisterForm component
 */
interface RegisterFormProps {
  /** Callback function to execute on successful registration */
  onSuccess?: () => void;
  /** Flag indicating if this is a conversion from anonymous to registered user */
  isAnonymousConversion?: boolean;
  /** Flag indicating whether to show the login link */
  showLoginLink?: boolean;
}

/**
 * Registration form component with validation and submission handling
 *
 * @param props - RegisterForm properties
 * @returns Rendered registration form component
 */
export const RegisterForm: React.FC<RegisterFormProps> = (props) => {
  // Destructure props
  const { onSuccess, isAnonymousConversion, showLoginLink } = props;

  // Get authentication functions and state from useAuth hook
  const { register: registerFn, convertToRegistered, error, isLoading, isAnonymous, clearError } = useAuth();

  // Initialize react-hook-form with default values and validation
  const {
    control,
    handleSubmit,
    formState: { errors },
    watch,
    register,
  } = useForm<RegisterCredentials>({
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
      firstName: '',
      lastName: '',
      agreeToTerms: false,
    },
  });

  // Watch password field for password match validation
  const password = watch('password');

  // Set up form submission handler to process registration data
  const onSubmit = async (data: RegisterCredentials) => {
    try {
      // Call appropriate registration function based on isAnonymousConversion
      if (isAnonymousConversion && isAnonymous) {
        await convertToRegistered({
          sessionId: (typeof(user) !== null && user && 'sessionId' in user) ? user.sessionId : '',
          email: data.email,
          password: data.password,
          firstName: data.firstName,
          lastName: data.lastName,
          agreeToTerms: data.agreeToTerms,
        });
      } else {
        await registerFn(data);
      }

      // Trigger onSuccess callback when registration completes successfully
      if (onSuccess) {
        onSuccess();
      }
    } catch (registrationError: any) {
      console.error('Registration failed:', registrationError);
    }
  };

  // Clear API errors when form fields change
  useEffect(() => {
    if (errors && Object.keys(errors).length > 0) {
      clearError();
    }
  }, [errors, clearError]);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="w-full">
      {/* Display API errors in Alert component */}
      {error && <Alert message={error} variant="error" dismissible onDismiss={clearError} />}

      {/* First Name Input */}
      <Input
        label="First Name"
        id="firstName"
        error={errors.firstName?.message}
        {...register("firstName", {
          required: "First Name is required",
        })}
      />

      {/* Last Name Input */}
      <Input
        label="Last Name"
        id="lastName"
        error={errors.lastName?.message}
        {...register("lastName", {
          required: "Last Name is required",
        })}
      />

      {/* Email Input */}
      <Input
        label="Email"
        id="email"
        type="email"
        error={errors.email?.message}
        {...register("email", {
          required: "Email is required",
          validate: validateEmail,
        })}
      />

      {/* Password Input */}
      <Input
        label="Password"
        id="password"
        type="password"
        error={errors.password?.message}
        helperText="Must be at least 10 characters long and contain one uppercase letter, one lowercase letter, one number, and one special character."
        {...register("password", {
          required: "Password is required",
          validate: validatePassword,
        })}
      />

      {/* Confirm Password Input */}
      <Input
        label="Confirm Password"
        id="confirmPassword"
        type="password"
        error={errors.confirmPassword?.message}
        {...register("confirmPassword", {
          required: "Confirm Password is required",
          validate: (value) =>
            validatePasswordMatch(password, value) || "Passwords must match",
        })}
      />

      {/* Terms and Conditions Checkbox */}
      <div className="mb-4">
        <label className="inline-flex items-center">
          <input
            type="checkbox"
            className="rounded border-gray-300 text-[#2C6ECB] shadow-sm focus:border-[#2C6ECB] focus:ring-[#2C6ECB]"
            {...register("agreeToTerms", {
              required: "You must agree to the terms and conditions",
            })}
          />
          <span className="ml-2 text-sm text-gray-700">
            I agree to the <a href="#" className="text-[#2C6ECB]">terms and conditions</a>
          </span>
        </label>
        {errors.agreeToTerms && (
          <p className="mt-1 text-sm text-red-500" role="alert">
            {errors.agreeToTerms.message}
          </p>
        )}
      </div>

      {/* Submit Button */}
      <Button type="submit" isLoading={isLoading} isFullWidth>
        {isAnonymousConversion ? 'Create Account' : 'Register'}
      </Button>

      {/* Conditionally show login link */}
      {showLoginLink && (
        <div className="mt-4 text-center">
          Already have an account? <a href="#" className="text-[#2C6ECB]">Login</a>
        </div>
      )}
    </form>
  );
};