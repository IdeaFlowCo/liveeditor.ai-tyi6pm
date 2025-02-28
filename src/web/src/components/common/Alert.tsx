import React, { useState, useEffect, useRef } from 'react'; // React v18.2.0
import classNames from 'classnames'; // classnames v2.3.2
import { FiAlertCircle, FiCheckCircle, FiInfo, FiX } from 'react-icons/fi'; // react-icons/fi v4.10.0
import { Button } from './Button';
import { useTheme } from '../../contexts/ThemeContext';
import { captureError, NotificationType } from '../../utils/error-handling';

// Default auto-dismiss timeout (5 seconds)
const AUTO_DISMISS_DEFAULT_TIMEOUT = 5000;

interface AlertProps {
  /** The visual style variant of the alert */
  variant?: 'success' | 'error' | 'warning' | 'info';
  /** Optional title displayed above the message */
  title?: string;
  /** The main message content of the alert */
  message: string;
  /** Whether the alert can be dismissed */
  dismissible?: boolean;
  /** Callback function when alert is dismissed */
  onDismiss?: () => void;
  /** Whether the alert should auto-dismiss after a timeout */
  autoDismiss?: boolean;
  /** Timeout in ms before auto-dismissal (default: 5000ms) */
  autoDismissTimeout?: number;
  /** Custom icon to override the default */
  icon?: React.ReactNode;
  /** Custom className for the alert container */
  className?: string;
  /** Custom className for the text content */
  textClassName?: string;
  /** Custom className for the icon */
  iconClassName?: string;
  /** Data test identifier for testing */
  testId?: string;
}

/**
 * A customizable alert component that displays messages with different visual styles based on severity
 */
export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  message,
  dismissible = false,
  onDismiss,
  autoDismiss = false,
  autoDismissTimeout = AUTO_DISMISS_DEFAULT_TIMEOUT,
  icon,
  className,
  textClassName,
  iconClassName,
  testId,
}) => {
  const [visible, setVisible] = useState(true);
  const alertRef = useRef<HTMLDivElement>(null);
  const { isDarkMode } = useTheme();

  // Use provided icon or get default based on variant
  const alertIcon = icon || getIconForVariant(variant);

  // Handle auto-dismiss
  useEffect(() => {
    let dismissTimer: NodeJS.Timeout;

    if (autoDismiss && visible) {
      dismissTimer = setTimeout(() => {
        handleDismiss();
      }, autoDismissTimeout);
    }

    return () => {
      if (dismissTimer) {
        clearTimeout(dismissTimer);
      }
    };
  }, [autoDismiss, autoDismissTimeout, visible]);

  // Handle dismiss with animation
  const handleDismiss = () => {
    setVisible(false);
    
    // Add exit animation and call onDismiss after animation completes
    if (alertRef.current) {
      alertRef.current.classList.add('opacity-0', 'translate-y-[-10px]');
      
      setTimeout(() => {
        if (onDismiss) {
          captureError(onDismiss);
        }
      }, 300); // Match the transition duration
    } else if (onDismiss) {
      captureError(onDismiss);
    }
  };

  // If alert has been dismissed and animation completed, don't render
  if (!visible) {
    return null;
  }

  // Get classes based on variant and theme
  const { containerClasses, textClasses, iconClasses } = getVariantClasses(variant, isDarkMode);

  // Determine appropriate ARIA role
  const alertRole = variant === 'error' || variant === 'warning' ? 'alert' : 'status';

  return (
    <div
      ref={alertRef}
      className={classNames(
        // Base styles
        'flex items-start p-4 rounded-md shadow-sm transition-all duration-300 transform',
        // Animation entrance classes
        'opacity-100 translate-y-0',
        // Apply variant-specific styles
        containerClasses,
        // Custom class
        className
      )}
      role={alertRole}
      aria-live={variant === 'error' ? 'assertive' : 'polite'}
      data-testid={testId || `alert-${variant}`}
    >
      {/* Icon */}
      <div className={classNames('flex-shrink-0 mr-3 mt-0.5', iconClasses, iconClassName)}>
        {alertIcon}
      </div>

      {/* Content */}
      <div className={classNames('flex-grow', textClasses, textClassName)}>
        {title && <h4 className="font-semibold mb-1">{title}</h4>}
        <p className="text-sm">{message}</p>
      </div>

      {/* Dismiss button */}
      {dismissible && (
        <div className="flex-shrink-0 ml-3">
          <Button
            variant="tertiary"
            size="sm"
            onClick={handleDismiss}
            aria-label="Dismiss alert"
            className={classNames('p-1 opacity-70 hover:opacity-100', textClasses)}
          >
            <FiX className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
};

/**
 * Helper function that returns the appropriate icon component based on alert variant
 */
const getIconForVariant = (variant: AlertProps['variant']): React.ReactNode => {
  switch (variant) {
    case 'success':
      return <FiCheckCircle className="h-5 w-5" />;
    case 'error':
      return <FiAlertCircle className="h-5 w-5" />;
    case 'warning':
      return <FiAlertCircle className="h-5 w-5" />;
    case 'info':
    default:
      return <FiInfo className="h-5 w-5" />;
  }
};

/**
 * Helper function that returns the appropriate CSS classes based on alert variant and theme
 */
const getVariantClasses = (variant: AlertProps['variant'], isDarkMode: boolean) => {
  // Base classes that apply to all variants
  const baseContainerClasses = 'border-l-4';
  const baseTextClasses = '';
  const baseIconClasses = '';
  
  // Variant-specific classes for light mode
  const lightModeClasses = {
    success: {
      container: 'bg-green-50 border-green-500',
      text: 'text-green-800',
      icon: 'text-green-500',
    },
    error: {
      container: 'bg-red-50 border-red-500',
      text: 'text-red-800',
      icon: 'text-red-500',
    },
    warning: {
      container: 'bg-yellow-50 border-yellow-500',
      text: 'text-yellow-800',
      icon: 'text-yellow-500',
    },
    info: {
      container: 'bg-blue-50 border-blue-500',
      text: 'text-blue-800',
      icon: 'text-blue-500',
    },
  };
  
  // Variant-specific classes for dark mode
  const darkModeClasses = {
    success: {
      container: 'bg-green-900/20 border-green-500',
      text: 'text-green-300',
      icon: 'text-green-400',
    },
    error: {
      container: 'bg-red-900/20 border-red-500',
      text: 'text-red-300',
      icon: 'text-red-400',
    },
    warning: {
      container: 'bg-yellow-900/20 border-yellow-500',
      text: 'text-yellow-300',
      icon: 'text-yellow-400',
    },
    info: {
      container: 'bg-blue-900/20 border-blue-500',
      text: 'text-blue-300',
      icon: 'text-blue-400',
    },
  };

  return {
    containerClasses: `${baseContainerClasses} ${isDarkMode ? darkModeClasses[variant || 'info'].container : lightModeClasses[variant || 'info'].container}`,
    textClasses: `${baseTextClasses} ${isDarkMode ? darkModeClasses[variant || 'info'].text : lightModeClasses[variant || 'info'].text}`,
    iconClasses: `${baseIconClasses} ${isDarkMode ? darkModeClasses[variant || 'info'].icon : lightModeClasses[variant || 'info'].icon}`,
  };
};