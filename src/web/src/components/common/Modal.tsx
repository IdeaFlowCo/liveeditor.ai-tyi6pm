import React, { useState, useEffect, useRef, useCallback } from 'react'; // React 18.2.0
import classNames from 'classnames'; // classnames 2.3.2
import { FiX } from 'react-icons/fi'; // react-icons/fi 4.10.0
import { createPortal } from 'react-dom'; // react-dom 18.2.0
import { Button } from './Button';
import { useClickOutside } from '../../hooks/useClickOutside';
import { useTheme } from '../../contexts/ThemeContext';
import { captureError } from '../../utils/error-handling';

// Constants
const ESCAPE_KEY = 'Escape';
const ANIMATION_DURATION = 300;

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnEscape?: boolean;
  closeOnOutsideClick?: boolean;
  showCloseButton?: boolean;
  className?: string;
  contentClassName?: string;
  overlayClassName?: string;
  headerClassName?: string;
  bodyClassName?: string;
  footerClassName?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  preventScroll?: boolean;
  initialFocus?: React.RefObject<HTMLElement>;
  ariaDescribedBy?: string;
  ariaLabelledBy?: string;
  testId?: string;
}

/**
 * Custom hook to prevent body scrolling when modal is open
 */
const useBodyScrollLock = (preventScroll: boolean): void => {
  useEffect(() => {
    if (!preventScroll) return;

    // Store original body style
    const originalStyle = window.getComputedStyle(document.body).overflow;
    
    // Prevent scrolling
    document.body.style.overflow = 'hidden';
    
    // Restore original style on cleanup
    return () => {
      document.body.style.overflow = originalStyle;
    };
  }, [preventScroll]);
};

/**
 * Custom hook to trap focus within the modal for accessibility
 */
const useFocusTrap = (
  modalRef: React.RefObject<HTMLElement>,
  isOpen: boolean,
  initialFocusRef?: React.RefObject<HTMLElement>
): void => {
  // Store element that had focus before modal opened
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isOpen || !modalRef.current) return;

    // Store the previously focused element
    previousFocusRef.current = document.activeElement as HTMLElement;

    // Focus the specified element or first focusable element
    const focusInitialElement = () => {
      if (initialFocusRef && initialFocusRef.current) {
        initialFocusRef.current.focus();
      } else if (modalRef.current) {
        // Find all focusable elements
        const focusableElements = modalRef.current.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        // Focus the first one if it exists
        if (focusableElements.length > 0) {
          (focusableElements[0] as HTMLElement).focus();
        } else {
          // If no focusable elements, focus the modal itself
          modalRef.current.focus();
        }
      }
    };

    // Focus after a short delay to ensure the modal is rendered
    setTimeout(focusInitialElement, 50);

    // Handle tab key to trap focus within modal
    const handleTabKey = (e: KeyboardEvent) => {
      if (!modalRef.current || e.key !== 'Tab') return;

      const focusableElements = Array.from(
        modalRef.current.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
      );

      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[
        focusableElements.length - 1
      ] as HTMLElement;

      // If shift+tab on first element, move to last element
      if (e.shiftKey && document.activeElement === firstElement) {
        lastElement.focus();
        e.preventDefault();
      } 
      // If tab on last element, move to first element
      else if (!e.shiftKey && document.activeElement === lastElement) {
        firstElement.focus();
        e.preventDefault();
      }
    };

    // Add event listener for tab key
    document.addEventListener('keydown', handleTabKey);

    // Clean up event listener and restore focus
    return () => {
      document.removeEventListener('keydown', handleTabKey);
      
      // Return focus to previous element when modal closes
      if (isOpen && previousFocusRef.current) {
        setTimeout(() => {
          if (previousFocusRef.current) {
            previousFocusRef.current.focus();
          }
        }, ANIMATION_DURATION);
      }
    };
  }, [isOpen, modalRef, initialFocusRef]);
};

/**
 * A customizable modal dialog component that displays content in an overlay
 */
export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  size = 'md',
  closeOnEscape = true,
  closeOnOutsideClick = true,
  showCloseButton = true,
  className,
  contentClassName,
  overlayClassName,
  headerClassName,
  bodyClassName,
  footerClassName,
  children,
  footer,
  preventScroll = true,
  initialFocus,
  ariaDescribedBy,
  ariaLabelledBy,
  testId,
}) => {
  // Theme context for styling
  const { isDarkMode } = useTheme();
  
  // Refs
  const modalRef = useRef<HTMLDivElement>(null);
  
  // State for animation
  const [isAnimating, setIsAnimating] = useState(false);
  const [direction, setDirection] = useState<'in' | 'out'>('in');
  
  // Handle body scroll locking
  useBodyScrollLock(isOpen && preventScroll);
  
  // Handle focus trapping
  useFocusTrap(modalRef, isOpen, initialFocus);
  
  // Handle click outside
  useClickOutside(() => {
    if (closeOnOutsideClick && isOpen) {
      handleClose();
    }
  }, modalRef);
  
  // Handle escape key press
  useEffect(() => {
    if (!closeOnEscape) return;
    
    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === ESCAPE_KEY && isOpen) {
        handleClose();
      }
    };
    
    document.addEventListener('keydown', handleEscapeKey);
    
    return () => {
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [closeOnEscape, isOpen]);
  
  // Handle animation state on open/close
  useEffect(() => {
    if (isOpen) {
      setIsAnimating(true);
      setDirection('in');
    } else if (isAnimating) {
      setDirection('out');
      const timer = setTimeout(() => {
        setIsAnimating(false);
      }, ANIMATION_DURATION);
      
      return () => clearTimeout(timer);
    }
  }, [isOpen, isAnimating]);
  
  // Safe close handler with error capturing
  const handleClose = useCallback(() => {
    setDirection('out');
    const timer = setTimeout(() => {
      captureError(onClose);
    }, ANIMATION_DURATION * 0.8); // Slightly before animation completes
    
    return () => clearTimeout(timer);
  }, [onClose]);
  
  // Don't render anything if not open and not animating
  if (!isOpen && !isAnimating) {
    return null;
  }
  
  // CSS animation styles
  const animationStyles = {
    '--animation-duration': `${ANIMATION_DURATION}ms`,
  } as React.CSSProperties;
  
  // Modal overlay classes
  const overlayClasses = classNames(
    'fixed inset-0 flex items-center justify-center z-50 transition-opacity',
    {
      'bg-black bg-opacity-50 dark:bg-opacity-70': true,
      'opacity-0': direction === 'out',
      'opacity-100': direction === 'in',
    },
    overlayClassName
  );
  
  // Modal content classes based on size
  const modalClasses = classNames(
    'bg-white dark:bg-gray-800 rounded-lg shadow-xl overflow-hidden relative flex flex-col max-h-[90vh] transition-transform',
    {
      'w-full max-w-sm': size === 'sm',
      'w-full max-w-md': size === 'md',
      'w-full max-w-lg': size === 'lg',
      'w-full max-w-xl': size === 'xl',
      'w-[95vw] h-[90vh]': size === 'full',
      'scale-95 opacity-0': direction === 'out',
      'scale-100 opacity-100': direction === 'in',
      'dark:text-white text-gray-900': true,
    },
    className
  );
  
  // Create portal for the modal
  return createPortal(
    <div 
      className={overlayClasses}
      aria-modal="true"
      role="dialog"
      aria-labelledby={ariaLabelledBy || (title ? 'modal-title' : undefined)}
      aria-describedby={ariaDescribedBy}
      data-testid={testId}
      style={animationStyles}
    >
      <div 
        ref={modalRef}
        className={modalClasses}
        tabIndex={-1} // Make modal focusable but not in tab order
        style={animationStyles}
      >
        {/* Modal Header */}
        {(title || showCloseButton) && (
          <div 
            className={classNames(
              'flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700',
              headerClassName
            )}
          >
            {title && (
              <h2 
                id={ariaLabelledBy || 'modal-title'} 
                className="text-xl font-semibold"
              >
                {title}
              </h2>
            )}
            {showCloseButton && (
              <Button
                variant="tertiary"
                size="sm"
                aria-label="Close"
                onClick={handleClose}
                className={classNames(
                  "ml-auto",
                  !title && "mr-2 mt-2"
                )}
              >
                <FiX size={20} />
              </Button>
            )}
          </div>
        )}
        
        {/* Modal Body */}
        <div 
          className={classNames(
            'flex-1 p-4 overflow-auto',
            bodyClassName
          )}
        >
          {children}
        </div>
        
        {/* Modal Footer */}
        {footer && (
          <div 
            className={classNames(
              'p-4 border-t border-gray-200 dark:border-gray-700',
              footerClassName
            )}
          >
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body // Render at the body level to avoid stacking context issues
  );
};

// Add displayName for better debugging
Modal.displayName = 'Modal';