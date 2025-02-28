import React from 'react'; // React 18.2.0
import classNames from 'classnames'; // v2.3.2
import { captureError } from '../../utils/error-handling';
import { useTheme } from '../../contexts/ThemeContext';

/**
 * Props interface for the Card component
 */
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Visual style variant of the card */
  variant?: 'default' | 'outlined' | 'elevated' | 'flat';
  /** Size variant controlling padding and potentially other size-related styles */
  size?: 'sm' | 'md' | 'lg';
  /** Whether the card is in a selected state */
  isSelected?: boolean;
  /** Whether the card responds to hover and focus interactions */
  isInteractive?: boolean;
  /** Whether the card should take up the full width of its container */
  isFullWidth?: boolean;
  /** Whether to remove default padding from the card */
  noPadding?: boolean;
  /** Render the card as a different element type */
  as?: React.ElementType;
}

/**
 * A reusable Card component that provides a container with consistent styling
 * for displaying content throughout the application.
 * 
 * @example
 * <Card variant="elevated" isInteractive onClick={handleClick}>
 *   <h3>Card Title</h3>
 *   <p>Card content goes here</p>
 * </Card>
 */
const Card: React.FC<CardProps> = (props) => {
  const {
    variant = 'default',
    size = 'md',
    isSelected = false,
    isInteractive = false,
    isFullWidth = false,
    noPadding = false,
    as: Component = 'div',
    className,
    children,
    onClick,
    onKeyDown,
    ...rest
  } = props;

  // Access theme context for theme-aware styling
  const { isDarkMode } = useTheme();

  // Handle keyboard interactions for interactive cards
  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (isInteractive && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();
      onClick?.(event as unknown as React.MouseEvent<HTMLDivElement>);
    }
    
    onKeyDown?.(event);
  };

  // Combine class names based on props
  const cardClasses = classNames(
    'card',
    `card--${variant}`,
    `card--${size}`,
    {
      'card--selected': isSelected,
      'card--interactive': isInteractive,
      'card--full-width': isFullWidth,
      'card--no-padding': noPadding,
      'card--dark': isDarkMode,
    },
    className
  );

  // For interactive cards, add appropriate accessibility attributes
  const interactiveProps = isInteractive ? {
    role: 'button',
    tabIndex: 0,
    'aria-pressed': isSelected,
    onKeyDown: handleKeyDown,
  } : {};

  // Use error boundary for error handling
  try {
    return (
      <Component
        className={cardClasses}
        onClick={isInteractive ? onClick : undefined}
        {...interactiveProps}
        {...rest}
      >
        {children}
      </Component>
    );
  } catch (error) {
    // Use the captureError utility for consistent error handling
    captureError(error as Error, {
      context: { component: 'Card', props },
      showNotification: true
    });
    
    // Render a fallback div on error
    return <div className="card card--error">Error rendering card</div>;
  }
};

export default Card;