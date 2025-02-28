import React, { createContext, useContext, useState, useMemo, ReactNode } from 'react';
import classNames from 'classnames'; // classnames 2.3.1
import useMediaQuery from '../../../hooks/useMediaQuery';

// Define the context value interface
interface TabsContextValue {
  activeIndex: number;
  setActiveIndex: (index: number) => void;
}

// Create the context with default values
const TabsContext = createContext<TabsContextValue>({
  activeIndex: 0,
  setActiveIndex: () => {},
});

/**
 * Type guard to check if an element is a Tab component
 * @param element The element to check
 * @returns True if the element is a Tab component
 */
function isTabElement(element: React.ReactElement): boolean {
  return element.type && (element.type as any).displayName === 'Tab';
}

/**
 * Individual tab component for use within the Tabs container
 */
const Tab: React.FC<TabProps> = ({ label, icon, disabled = false, className, children }) => {
  // This component is primarily a data container for the Tabs component
  // The parent Tabs component extracts props and renders appropriately
  return null;
};

// Set displayName for the type guard
Tab.displayName = 'Tab';

/**
 * Hook for accessing tabs context in child components
 * @returns The current tabs context value with active index and setter
 */
function useTabsContext(): TabsContextValue {
  return useContext(TabsContext);
}

/**
 * Container component that manages multiple Tab children
 */
const Tabs: React.FC<TabsProps> = ({
  children,
  activeIndex: controlledIndex,
  defaultIndex = 0,
  onChange,
  className,
  variant = 'default',
}) => {
  // State for uncontrolled component
  const [internalIndex, setInternalIndex] = useState(defaultIndex);
  
  // Use controlled or uncontrolled index
  const activeIndex = controlledIndex !== undefined ? controlledIndex : internalIndex;
  
  // Filter children to get only Tab components
  const tabElements = React.Children.toArray(children)
    .filter((child): child is React.ReactElement => 
      React.isValidElement(child) && isTabElement(child)
    );
  
  // Handle tab selection
  const handleTabChange = (index: number) => {
    if (onChange) {
      onChange(index);
    }
    if (controlledIndex === undefined) {
      setInternalIndex(index);
    }
  };
  
  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent, index: number) => {
    let newIndex = index;
    const tabCount = tabElements.length;
    
    if (tabCount === 0) return;
    
    switch (event.key) {
      case 'ArrowRight': {
        // Find next enabled tab
        for (let i = 1; i <= tabCount; i++) {
          const nextIndex = (index + i) % tabCount;
          if (!tabElements[nextIndex].props.disabled) {
            newIndex = nextIndex;
            break;
          }
        }
        break;
      }
      case 'ArrowLeft': {
        // Find previous enabled tab
        for (let i = 1; i <= tabCount; i++) {
          const prevIndex = (index - i + tabCount) % tabCount;
          if (!tabElements[prevIndex].props.disabled) {
            newIndex = prevIndex;
            break;
          }
        }
        break;
      }
      case 'Home': {
        // Find first non-disabled tab
        for (let i = 0; i < tabCount; i++) {
          if (!tabElements[i].props.disabled) {
            newIndex = i;
            break;
          }
        }
        break;
      }
      case 'End': {
        // Find last non-disabled tab
        for (let i = tabCount - 1; i >= 0; i--) {
          if (!tabElements[i].props.disabled) {
            newIndex = i;
            break;
          }
        }
        break;
      }
      default:
        return;
    }
    
    if (newIndex !== index) {
      event.preventDefault();
      handleTabChange(newIndex);
      // Focus the newly selected tab button
      document.getElementById(`tab-${newIndex}`)?.focus();
    }
  };
  
  // Create memoized context value
  const contextValue = useMemo(
    () => ({ activeIndex, setActiveIndex: handleTabChange }),
    [activeIndex, handleTabChange]
  );
  
  // Check if on mobile for responsive behavior
  const isMobile = useMediaQuery('(max-width: 768px)');
  
  return (
    <TabsContext.Provider value={contextValue}>
      <div className={classNames('tabs', className)}>
        {/* Tab list with proper ARIA roles */}
        <div 
          role="tablist" 
          className={classNames(
            'tabs-list',
            `tabs-${variant}`,
            { 'tabs-mobile': isMobile }
          )}
          aria-orientation="horizontal"
        >
          {tabElements.map((tab, index) => {
            const { label, icon, disabled = false, className: tabClassName } = tab.props;
            const isActive = index === activeIndex;
            
            return (
              <button
                id={`tab-${index}`}
                key={`tab-${index}`}
                role="tab"
                aria-selected={isActive}
                aria-controls={`panel-${index}`}
                aria-disabled={disabled}
                tabIndex={isActive ? 0 : -1}
                className={classNames(
                  'tab-button',
                  { 'active': isActive },
                  { 'disabled': disabled },
                  tabClassName
                )}
                onClick={() => !disabled && handleTabChange(index)}
                onKeyDown={(e) => handleKeyDown(e, index)}
                disabled={disabled}
              >
                {icon && <span className="tab-icon">{icon}</span>}
                <span className="tab-label">{label}</span>
              </button>
            );
          })}
        </div>
        
        {/* Tab panels/content */}
        {tabElements.map((tab, index) => (
          <div
            id={`panel-${index}`}
            key={`panel-${index}`}
            role="tabpanel"
            aria-labelledby={`tab-${index}`}
            hidden={index !== activeIndex}
            className="tab-panel"
            tabIndex={0}
          >
            {tab.props.children}
          </div>
        ))}
      </div>
    </TabsContext.Provider>
  );
};

// Define Tab component props
interface TabProps {
  label: string;
  icon?: ReactNode;
  disabled?: boolean;
  className?: string;
  children: ReactNode;
}

// Define Tabs container props
interface TabsProps {
  children: ReactNode;
  activeIndex?: number;
  defaultIndex?: number;
  onChange?: (index: number) => void;
  className?: string;
  variant?: 'default' | 'underlined' | 'pills';
}

// Attach Tab component to Tabs for convenient import
Tabs.Tab = Tab;

// Export components
export { Tab, Tabs, useTabsContext };