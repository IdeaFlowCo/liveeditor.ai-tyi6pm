import React, { useState, useEffect, useRef, ReactNode } from 'react'; // React ^18.0.0
import classnames from 'classnames'; // classnames ^2.3.2
import useMediaQuery from '../../../hooks/useMediaQuery';

// Define types for tooltip positions and triggers
type TooltipPosition = 'top' | 'right' | 'bottom' | 'left';
type TooltipTrigger = 'hover' | 'click' | 'focus';

/**
 * Props interface for the Tooltip component
 */
interface TooltipProps {
  /** Content to display in the tooltip */
  content: ReactNode;
  /** Element that triggers the tooltip */
  children: ReactNode;
  /** Preferred position of the tooltip relative to the trigger */
  position?: string;
  /** Control tooltip visibility externally */
  visible?: boolean;
  /** Additional class name for the tooltip container */
  className?: string;
  /** Additional class name for the tooltip content */
  contentClassName?: string;
  /** Event that triggers the tooltip display */
  trigger?: string;
  /** Delay before showing the tooltip (in ms) */
  delay?: number;
  /** Whether to show an arrow pointing to the trigger */
  arrow?: boolean;
  /** Accessibility label for the tooltip */
  ariaLabel?: string;
}

// Interface for position calculations
interface Position {
  top: number;
  left: number;
}

/**
 * Calculates optimal tooltip position based on trigger element position and viewport constraints
 * @param triggerRect DOMRect of the trigger element
 * @param tooltipRect DOMRect of the tooltip element
 * @param preferredPosition Preferred tooltip position
 * @returns Position coordinates for the tooltip
 */
const calculatePosition = (
  triggerRect: DOMRect,
  tooltipRect: DOMRect,
  preferredPosition: string
): Position => {
  // Get viewport dimensions
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  
  // Calculate available space in each direction from trigger
  const spaceTop = triggerRect.top;
  const spaceRight = viewportWidth - (triggerRect.left + triggerRect.width);
  const spaceBottom = viewportHeight - (triggerRect.top + triggerRect.height);
  const spaceLeft = triggerRect.left;
  
  // Initialize position
  let top = 0;
  let left = 0;
  
  // Determine best position based on preferred position and available space
  let position = preferredPosition as TooltipPosition;
  
  // Check if preferred position has enough space, otherwise find alternative
  if (position === 'top' && spaceTop < tooltipRect.height) {
    position = spaceBottom >= tooltipRect.height ? 'bottom' : (spaceRight >= tooltipRect.width ? 'right' : 'left');
  } else if (position === 'right' && spaceRight < tooltipRect.width) {
    position = spaceLeft >= tooltipRect.width ? 'left' : (spaceTop >= tooltipRect.height ? 'top' : 'bottom');
  } else if (position === 'bottom' && spaceBottom < tooltipRect.height) {
    position = spaceTop >= tooltipRect.height ? 'top' : (spaceRight >= tooltipRect.width ? 'right' : 'left');
  } else if (position === 'left' && spaceLeft < tooltipRect.width) {
    position = spaceRight >= tooltipRect.width ? 'right' : (spaceTop >= tooltipRect.height ? 'top' : 'bottom');
  }
  
  // Calculate position based on final position decision
  switch (position) {
    case 'top':
      top = triggerRect.top - tooltipRect.height - 8; // 8px offset
      left = triggerRect.left + (triggerRect.width / 2) - (tooltipRect.width / 2);
      break;
    case 'right':
      top = triggerRect.top + (triggerRect.height / 2) - (tooltipRect.height / 2);
      left = triggerRect.left + triggerRect.width + 8; // 8px offset
      break;
    case 'bottom':
      top = triggerRect.top + triggerRect.height + 8; // 8px offset
      left = triggerRect.left + (triggerRect.width / 2) - (tooltipRect.width / 2);
      break;
    case 'left':
      top = triggerRect.top + (triggerRect.height / 2) - (tooltipRect.height / 2);
      left = triggerRect.left - tooltipRect.width - 8; // 8px offset
      break;
  }
  
  // Ensure tooltip stays within viewport boundaries
  // Adjust horizontal position if needed
  if (left < 0) {
    left = 0;
  } else if (left + tooltipRect.width > viewportWidth) {
    left = viewportWidth - tooltipRect.width;
  }
  
  // Adjust vertical position if needed
  if (top < 0) {
    top = 0;
  } else if (top + tooltipRect.height > viewportHeight) {
    top = viewportHeight - tooltipRect.height;
  }
  
  return { top, left };
};

/**
 * A React component that renders a tooltip with contextual information
 * Provides helpful information when users hover over or focus on elements
 */
const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  position = 'top',
  visible: controlledVisible,
  className = '',
  contentClassName = '',
  trigger = 'hover',
  delay = 200,
  arrow = true,
  ariaLabel,
}) => {
  // State for managing tooltip visibility and positioning
  const [isVisible, setIsVisible] = useState(!!controlledVisible);
  const [tooltipPosition, setTooltipPosition] = useState<Position>({ top: 0, left: 0 });
  const [actualPosition, setActualPosition] = useState<TooltipPosition>(position as TooltipPosition);
  const [isPositioned, setIsPositioned] = useState(false);
  
  // Refs for DOM elements
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<number | null>(null);
  
  // Check if on mobile using the custom media query hook
  const isMobile = useMediaQuery('(max-width: 768px)');
  
  // Use controlled visibility if provided, otherwise use internal state
  const visible = controlledVisible !== undefined ? controlledVisible : isVisible;
  
  // Position the tooltip based on trigger element and viewport
  const positionTooltip = () => {
    if (visible && triggerRef.current && tooltipRef.current) {
      const triggerRect = triggerRef.current.getBoundingClientRect();
      const tooltipRect = tooltipRef.current.getBoundingClientRect();
      
      // On mobile, prefer top/bottom positions for better user experience
      const mobileAdjustedPosition = isMobile 
        ? (position === 'left' || position === 'right' ? 'bottom' : position)
        : position;
      
      // Calculate optimal position
      const newPosition = calculatePosition(triggerRect, tooltipRect, mobileAdjustedPosition);
      setTooltipPosition(newPosition);
      
      // Determine actual position for arrow positioning
      let newActualPosition = mobileAdjustedPosition as TooltipPosition;
      if (newPosition.top <= triggerRect.top - tooltipRect.height / 2) {
        newActualPosition = 'top';
      } else if (newPosition.left >= triggerRect.left + triggerRect.width) {
        newActualPosition = 'right';
      } else if (newPosition.top >= triggerRect.top + triggerRect.height - tooltipRect.height / 2) {
        newActualPosition = 'bottom';
      } else if (newPosition.left <= triggerRect.left - tooltipRect.width / 2) {
        newActualPosition = 'left';
      }
      
      setActualPosition(newActualPosition);
      setIsPositioned(true);
    }
  };
  
  // Effect to position the tooltip when it becomes visible
  useEffect(() => {
    if (visible) {
      // Initial positioning might need a small delay to ensure tooltip is rendered
      setTimeout(() => {
        positionTooltip();
      }, 10);
    } else {
      setIsPositioned(false);
    }
  }, [visible, position, isMobile]);
  
  // Effect to reposition on resize or scroll
  useEffect(() => {
    const handleReposition = () => {
      if (visible) {
        positionTooltip();
      }
    };
    
    window.addEventListener('resize', handleReposition);
    window.addEventListener('scroll', handleReposition, true); // true for capturing phase
    
    return () => {
      window.removeEventListener('resize', handleReposition);
      window.removeEventListener('scroll', handleReposition, true);
    };
  }, [visible, position, isMobile]);
  
  // Effect to handle keyboard events (Escape to close) for accessibility
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && visible) {
        setIsVisible(false);
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [visible]);
  
  // Effect to clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current !== null) {
        window.clearTimeout(timeoutRef.current);
      }
    };
  }, []);
  
  // Show tooltip with delay
  const showTooltip = () => {
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
    }
    
    timeoutRef.current = window.setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };
  
  // Hide tooltip immediately
  const hideTooltip = () => {
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    
    setIsVisible(false);
  };
  
  // Toggle tooltip visibility (for click trigger)
  const toggleTooltip = () => {
    setIsVisible(prev => !prev);
  };
  
  // Event handlers based on trigger type
  const triggerProps = trigger === 'hover' 
    ? {
        onMouseEnter: showTooltip,
        onMouseLeave: hideTooltip,
        onFocus: showTooltip,
        onBlur: hideTooltip,
      }
    : trigger === 'click'
    ? {
        onClick: toggleTooltip,
      }
    : {
        onFocus: showTooltip,
        onBlur: hideTooltip,
      };
  
  // Additional accessibility attributes
  const accessibilityProps = {
    'aria-describedby': visible ? 'tooltip' : undefined,
  };
  
  return (
    <div 
      className="tooltip-container" 
      ref={triggerRef}
      {...triggerProps}
    >
      {/* Trigger element */}
      <div {...accessibilityProps}>
        {children}
      </div>
      
      {/* Tooltip */}
      {visible && (
        <div
          id="tooltip"
          role="tooltip"
          ref={tooltipRef}
          className={classnames(
            'tooltip',
            `tooltip-${actualPosition}`,
            className,
            { 'tooltip-with-arrow': arrow }
          )}
          style={{
            position: 'fixed',
            top: `${tooltipPosition.top}px`,
            left: `${tooltipPosition.left}px`,
            zIndex: 1000,
            opacity: isPositioned ? 1 : 0,
            transition: 'opacity 150ms ease-in-out',
          }}
          aria-hidden={!visible}
          aria-label={ariaLabel}
        >
          <div className={classnames('tooltip-content', contentClassName)}>
            {content}
          </div>
          {arrow && (
            <div 
              className={classnames(
                'tooltip-arrow',
                `tooltip-arrow-${actualPosition}`
              )}
              aria-hidden="true"
            />
          )}
        </div>
      )}
    </div>
  );
};

export default Tooltip;