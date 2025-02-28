import React from 'react'; // React v18.2.0
import classNames from 'classnames'; // classnames v2.3.2
import { captureError } from '../../utils/error-handling';

/**
 * A customizable button component with various styles and states
 * 
 * @example
 * // Primary button
 * <Button>Click Me</Button>
 * 
 * // Secondary button with icon
 * <Button variant="secondary" leftIcon={<Icon name="edit" />}>Edit</Button>
 * 
 * // Loading state
 * <Button isLoading>Processing</Button>
 */
export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  isFullWidth = false,
  leftIcon,
  rightIcon,
  children,
  className,
  disabled,
  type = 'button',
  onClick,
  ...props
}) => {
  // Handle button click with error capturing
  const handleClick = (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    if (onClick && !isLoading && !disabled) {
      captureError(() => onClick(event));
    }
  };

  // Generate class names based on props
  const buttonClasses = classNames(
    // Base styles
    'inline-flex items-center justify-center rounded font-medium transition-colors focus:outline-none',
    
    // Variant styles
    {
      // Primary button (Primary Blue: #2C6ECB)
      'bg-[#2C6ECB] text-white hover:bg-[#2C6ECB]/90 active:bg-[#2C6ECB]/95 focus:ring-2 focus:ring-[#2C6ECB]/50': 
        variant === 'primary',
        
      // Secondary button
      'border border-[#2C6ECB] text-[#2C6ECB] bg-transparent hover:bg-[#2C6ECB]/10 active:bg-[#2C6ECB]/20 focus:ring-2 focus:ring-[#2C6ECB]/50': 
        variant === 'secondary',
        
      // Tertiary button (text only)
      'text-[#2C6ECB] bg-transparent hover:bg-[#2C6ECB]/10 active:bg-[#2C6ECB]/20 focus:ring-2 focus:ring-[#2C6ECB]/50': 
        variant === 'tertiary',
        
      // Danger button (Error Red: #DC3545)
      'bg-[#DC3545] text-white hover:bg-[#DC3545]/90 active:bg-[#DC3545]/95 focus:ring-2 focus:ring-[#DC3545]/50': 
        variant === 'danger'
    },
    
    // Size styles
    {
      'text-sm px-3 py-1 h-8': size === 'sm',
      'text-base px-4 py-2 h-10': size === 'md',
      'text-lg px-6 py-3 h-12': size === 'lg'
    },
    
    // Width styles
    {
      'w-full': isFullWidth
    },
    
    // State styles
    {
      'opacity-50 cursor-not-allowed': disabled || isLoading,
      'cursor-pointer': !disabled && !isLoading
    },
    
    // Custom class
    className
  );

  return (
    <button
      type={type}
      className={buttonClasses}
      disabled={disabled || isLoading}
      onClick={handleClick}
      aria-busy={isLoading}
      aria-disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <span className="mr-2 inline-block animate-spin">
          <svg 
            className="h-4 w-4" 
            xmlns="http://www.w3.org/2000/svg" 
            fill="none" 
            viewBox="0 0 24 24"
          >
            <circle 
              className="opacity-25" 
              cx="12" 
              cy="12" 
              r="10" 
              stroke="currentColor" 
              strokeWidth="4"
            />
            <path 
              className="opacity-75" 
              fill="currentColor" 
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </span>
      )}
      
      {leftIcon && !isLoading && (
        <span className="mr-2 inline-flex items-center">{leftIcon}</span>
      )}
      
      <span>{children}</span>
      
      {rightIcon && (
        <span className="ml-2 inline-flex items-center">{rightIcon}</span>
      )}
    </button>
  );
};

// Add displayName for better debugging
Button.displayName = 'Button';