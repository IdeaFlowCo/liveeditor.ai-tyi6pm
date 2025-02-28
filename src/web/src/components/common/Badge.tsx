import React from 'react';
import classNames from 'classnames'; // classnames 2.3.2
import { captureError } from '../../utils/error-handling';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
  count?: number;
  max?: number;
  dot?: boolean;
  outline?: boolean;
}

/**
 * A customizable badge component that displays short text, numbers, or status indicators
 */
const Badge: React.FC<BadgeProps> = ({
  variant = 'primary',
  size = 'md',
  count,
  max = 99,
  dot = false,
  outline = false,
  children,
  className,
  ...props
}) => {
  try {
    // Determine content to display
    let content = children;
    
    if (count !== undefined) {
      content = count > max ? `${max}+` : count.toString();
    } else if (dot) {
      // Dot badge has no text content
      content = null;
    }

    // Generate class names based on variant, size, and type
    const badgeClasses = classNames(
      'inline-flex items-center justify-center font-medium rounded-full',
      {
        // Variant classes
        'bg-blue-600 text-white': variant === 'primary' && !outline,
        'bg-teal-600 text-white': variant === 'secondary' && !outline,
        'bg-green-600 text-white': variant === 'success' && !outline,
        'bg-yellow-500 text-black': variant === 'warning' && !outline,
        'bg-red-600 text-white': variant === 'error' && !outline,
        'bg-blue-400 text-white': variant === 'info' && !outline,
        
        // Outline variant classes
        'bg-transparent border': outline,
        'text-blue-600 border-blue-600': variant === 'primary' && outline,
        'text-teal-600 border-teal-600': variant === 'secondary' && outline,
        'text-green-600 border-green-600': variant === 'success' && outline,
        'text-yellow-600 border-yellow-600': variant === 'warning' && outline,
        'text-red-600 border-red-600': variant === 'error' && outline,
        'text-blue-400 border-blue-400': variant === 'info' && outline,
        
        // Size classes for dots
        'w-2 h-2': dot && size === 'sm',
        'w-3 h-3': dot && size === 'md',
        'w-4 h-4': dot && size === 'lg',
        
        // Size classes for badges with content
        'text-xs px-1.5 py-0.5 min-w-[1.5rem]': !dot && size === 'sm',
        'text-sm px-2 py-0.5 min-w-[2rem]': !dot && size === 'md',
        'text-sm px-2.5 py-1 min-w-[2.5rem]': !dot && size === 'lg',
      },
      className
    );

    // Create final props with our defaults and consumer overrides
    const finalProps = {
      className: badgeClasses,
      role: 'status',
      ...dot && !props['aria-label'] && { 'aria-label': `${variant} status` },
      ...props
    };

    return (
      <span {...finalProps}>
        {content}
      </span>
    );
  } catch (error) {
    // Use the captureError utility to handle any rendering errors
    captureError(error as Error, {
      context: { component: 'Badge', props: { variant, size, count, max, dot, outline } }
    });
    
    // Return a simplified version as fallback
    return <span className="px-2 py-0.5 bg-gray-200 text-gray-700 rounded-full text-xs text-center">{children || count}</span>;
  }
};

export default Badge;