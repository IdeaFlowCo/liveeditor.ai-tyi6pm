import React, { useRef } from 'react'; // React 18.2.0
import { useSelector, useDispatch } from 'react-redux'; // react-redux 8.1.1
import classNames from 'classnames'; // classnames 2.3.2

import Button from '../common/Button';
import useMediaQuery from '../../hooks/useMediaQuery';
import { useIsMobile } from '../../hooks/useMediaQuery';
import useClickOutside from '../../hooks/useClickOutside';
import { setSidebarOpen, selectSidebarOpen } from '../../store/slices/uiSlice';

interface SidebarProps {
  children: React.ReactNode;
  className?: string;
  position?: 'left' | 'right';
  showToggle?: boolean;
}

/**
 * A responsive sidebar component that can be collapsed to maximize space for main content
 * and adapts to different screen sizes.
 */
const Sidebar: React.FC<SidebarProps> = ({
  children,
  className,
  position = 'right',
  showToggle = true
}) => {
  // Get sidebar open state from Redux
  const isOpen = useSelector(selectSidebarOpen);
  const dispatch = useDispatch();
  
  // Create a ref for the sidebar for click outside detection
  const sidebarRef = useRef<HTMLDivElement>(null);
  
  // Check if we're on mobile
  const isMobile = useIsMobile();
  
  // Set up click outside detection to close sidebar on mobile
  useClickOutside(() => {
    if (isMobile && isOpen) {
      dispatch(setSidebarOpen(false));
    }
  }, sidebarRef);
  
  // Toggle sidebar open/closed
  const handleToggle = () => {
    dispatch(setSidebarOpen(!isOpen));
  };
  
  // Compute CSS classes based on state and props
  const sidebarClasses = classNames(
    // Base styles for all states
    'fixed bg-white transition-all duration-300 ease-in-out shadow-lg z-40',
    
    // Position styles for desktop
    {
      'right-0 border-l border-gray-200': position === 'right' && !isMobile,
      'left-0 border-r border-gray-200': position === 'left' && !isMobile,
      
      // Width based on open state for desktop
      'w-80': isOpen && !isMobile,
      'w-0 overflow-hidden': !isOpen && !isMobile,
      
      // Mobile specific styles
      'bottom-0 left-0 right-0 w-full border-t border-gray-200': isMobile,
      'h-64': isMobile && isOpen,
      'h-0 overflow-hidden': isMobile && !isOpen,
      'h-full': !isMobile,
    },
    
    // Additional classes passed from parent
    className
  );
  
  return (
    <div className={sidebarClasses} ref={sidebarRef} aria-hidden={!isOpen}>
      {/* Toggle button - only shown on desktop when specified */}
      {showToggle && !isMobile && (
        <Button
          variant="secondary"
          size="sm"
          className={`absolute top-4 ${position === 'right' ? 'left-0 -ml-10' : 'right-0 -mr-10'}`}
          onClick={handleToggle}
          aria-label={isOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          {isOpen ? '›' : '‹'}
        </Button>
      )}
      
      {/* Content container with padding and scrolling */}
      <div className="p-4 h-full overflow-y-auto">
        {children}
      </div>
    </div>
  );
};

export default Sidebar;