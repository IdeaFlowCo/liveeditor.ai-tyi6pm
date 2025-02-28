import React from 'react'; // ^18.2.0
import { classNames } from '../utils/formatting';

/**
 * Props for the Spinner component
 */
interface SpinnerProps {
  /** Size of the spinner: 'sm' (small), 'md' (medium), or 'lg' (large) */
  size?: 'sm' | 'md' | 'lg';
  /** Color theme of the spinner */
  color?: 'primary' | 'secondary' | 'white';
  /** Whether to center the spinner in its container */
  center?: boolean;
  /** Additional CSS classes to apply */
  className?: string;
  /** Test ID for testing purposes */
  testId?: string;
}

/**
 * A circular loading indicator component with customizable size and color.
 * Used to indicate asynchronous operations throughout the application.
 */
const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  color = 'primary',
  center = false,
  className = '',
  testId = 'spinner',
}) => {
  // Size classes
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-3',
    lg: 'h-12 w-12 border-4',
  };

  // Color classes
  const colorClasses = {
    primary: 'border-primary border-t-transparent',
    secondary: 'border-secondary border-t-transparent',
    white: 'border-white border-t-transparent',
  };

  // Center positioning classes if center prop is true
  const centerClasses = center ? 'absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2' : '';

  return (
    <div
      className={classNames(
        'inline-block animate-spin rounded-full', 
        sizeClasses[size],
        colorClasses[color],
        centerClasses,
        className
      )}
      role="status"
      aria-live="polite"
      data-testid={testId}
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
};

export default Spinner;