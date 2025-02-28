import React, { useId, forwardRef } from 'react'; // ^18.2.0
import classNames from 'classnames'; // ^2.3.2

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  id?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
  startAdornment?: React.ReactNode;
  endAdornment?: React.ReactNode;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      id,
      error,
      helperText,
      fullWidth = false,
      className,
      startAdornment,
      endAdornment,
      ...rest
    },
    ref
  ) => {
    // Generate unique ID if not provided
    const uniqueId = useId();
    const inputId = id || `input-${uniqueId}`;
    const errorId = error ? `error-${inputId}` : undefined;
    const helperId = helperText && !error ? `helper-${inputId}` : undefined;
    const describedBy = errorId || helperId;

    // CSS classes for the input
    const inputClasses = classNames(
      // Base styles
      'h-10', // 40px height
      'px-3 py-2', // 8px 12px padding
      'border rounded', // border and radius
      'focus:outline-none focus:ring-0', // remove default focus
      'placeholder-[#999999]', // Placeholder color for tertiary text
      'transition-colors duration-200', // smooth transition
      // Conditional styles
      {
        'w-full': fullWidth,
        'border-[#CCCCCC]': !error, // Default border color
        'border-red-500': !!error, // Error border color
        'focus:border-[#2C6ECB] focus:border-2': !error, // Focus state (2px blue border)
        'focus:border-red-500 focus:border-2': !!error, // Error focus state
        'opacity-50 bg-gray-100 cursor-not-allowed': rest.disabled, // Disabled state
        'pl-10': !!startAdornment, // Add padding for start adornment
        'pr-10': !!endAdornment, // Add padding for end adornment
      },
      className
    );

    // CSS classes for the label
    const labelClasses = classNames(
      'block',
      'text-sm font-medium',
      'mb-1',
      {
        'text-gray-700': !error && !rest.disabled,
        'text-red-500': !!error,
        'text-gray-500': rest.disabled,
      }
    );

    // CSS classes for the wrapper
    const wrapperClasses = classNames(
      'relative',
      {
        'w-full': fullWidth,
      }
    );

    return (
      <div className={classNames('mb-4', { 'w-full': fullWidth })}>
        <label htmlFor={inputId} className={labelClasses}>
          {label}
        </label>
        <div className={wrapperClasses}>
          {startAdornment && (
            <div className="absolute left-3 top-1/2 transform -translate-y-1/2 flex items-center pointer-events-none">
              {startAdornment}
            </div>
          )}
          <input
            id={inputId}
            className={inputClasses}
            aria-invalid={!!error}
            aria-describedby={describedBy}
            ref={ref}
            {...rest}
          />
          {endAdornment && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center pointer-events-none">
              {endAdornment}
            </div>
          )}
        </div>
        {error && (
          <p id={errorId} className="mt-1 text-sm text-red-500" role="alert">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id={helperId} className="mt-1 text-sm text-gray-500">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

// Display name for debugging
Input.displayName = 'Input';

export default Input;