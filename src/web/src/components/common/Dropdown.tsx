import React, { useState, useRef, useCallback, useEffect } from 'react';
import classNames from 'classnames'; // classnames 2.3.2
import { useClickOutside } from '../../hooks/useClickOutside';
import { captureError } from '../../utils/error-handling';

interface DropdownOption<T = any> {
  label: string;
  value: T;
  icon?: React.ReactNode;
  disabled?: boolean;
}

interface DropdownTriggerProps<T = any> {
  selectedOption?: DropdownOption<T>;
  isOpen: boolean;
  toggleDropdown: () => void;
  disabled?: boolean;
}

interface DropdownProps<T = any> {
  options: DropdownOption<T>[];
  value?: T;
  onChange?: (value: T) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  menuClassName?: string;
  buttonClassName?: string;
  renderTrigger?: (props: DropdownTriggerProps<T>) => React.ReactNode;
  renderItem?: (option: DropdownOption<T>, isSelected: boolean) => React.ReactNode;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  width?: string | number;
  maxHeight?: string | number;
  isFullWidth?: boolean;
  closeOnSelect?: boolean;
}

function Dropdown<T = any>(props: DropdownProps<T>): JSX.Element {
  try {
    const {
      options,
      value,
      onChange,
      placeholder = 'Select an option',
      disabled = false,
      className = '',
      menuClassName = '',
      buttonClassName = '',
      renderTrigger,
      renderItem,
      placement = 'bottom',
      width,
      maxHeight = '300px',
      isFullWidth = false,
      closeOnSelect = true,
    } = props;

    // State for dropdown open/closed status
    const [isOpen, setIsOpen] = useState(false);
    
    // Refs for dropdown components
    const dropdownRef = useRef<HTMLDivElement>(null);
    const menuRef = useRef<HTMLDivElement>(null);
    const triggerRef = useRef<HTMLButtonElement>(null);
    
    // Find the selected option based on value prop
    const selectedOption = options.find(option => option.value === value);

    // Close dropdown when clicking outside
    useClickOutside(() => {
      if (isOpen) {
        setIsOpen(false);
      }
    }, dropdownRef);

    // Toggle dropdown open/closed
    const toggleDropdown = useCallback(() => {
      if (!disabled) {
        setIsOpen(prevIsOpen => !prevIsOpen);
      }
    }, [disabled]);

    // Handle selecting an option
    const handleSelectOption = useCallback((option: DropdownOption<T>) => {
      if (option.disabled) return;
      
      try {
        onChange?.(option.value);
        
        if (closeOnSelect) {
          setIsOpen(false);
          // Return focus to trigger button after closing
          triggerRef.current?.focus();
        }
      } catch (error) {
        captureError(error);
      }
    }, [onChange, closeOnSelect]);

    // Focus the first non-disabled option
    const focusFirstOption = useCallback(() => {
      setTimeout(() => {
        const options = menuRef.current?.querySelectorAll('[data-dropdown-option]:not([aria-disabled="true"])');
        if (options && options.length > 0) {
          (options[0] as HTMLElement).focus();
        }
      }, 0);
    }, []);

    // Handle keyboard navigation
    const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
      try {
        // If dropdown is closed and Down Arrow is pressed, open it
        if (!isOpen && (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ')) {
          event.preventDefault();
          setIsOpen(true);
          return;
        }

        // Only handle keyboard navigation when dropdown is open
        if (!isOpen) return;

        switch (event.key) {
          case 'Escape':
            event.preventDefault();
            setIsOpen(false);
            triggerRef.current?.focus();
            break;
          case 'ArrowDown':
            event.preventDefault();
            // Focus next option
            const currentElement = document.activeElement;
            const allOptions = Array.from(menuRef.current?.querySelectorAll('[data-dropdown-option]:not([aria-disabled="true"])') || []);
            const currentIndex = allOptions.indexOf(currentElement as Element);
            
            if (currentIndex === -1 || currentIndex === allOptions.length - 1) {
              // Focus first option if at end or no option is focused
              if (allOptions.length > 0) {
                (allOptions[0] as HTMLElement).focus();
              }
            } else {
              // Focus next option
              (allOptions[currentIndex + 1] as HTMLElement).focus();
            }
            break;
          case 'ArrowUp':
            event.preventDefault();
            // Focus previous option
            const activeElement = document.activeElement;
            const optionElements = Array.from(menuRef.current?.querySelectorAll('[data-dropdown-option]:not([aria-disabled="true"])') || []);
            const activeIndex = optionElements.indexOf(activeElement as Element);
            
            if (activeIndex <= 0) {
              // Focus last option if at start or no option is focused
              if (optionElements.length > 0) {
                (optionElements[optionElements.length - 1] as HTMLElement).focus();
              }
            } else {
              // Focus previous option
              (optionElements[activeIndex - 1] as HTMLElement).focus();
            }
            break;
          case 'Enter':
          case ' ':
            event.preventDefault();
            // Select focused option
            const focusedOption = document.activeElement;
            if (focusedOption && focusedOption.hasAttribute('data-dropdown-option')) {
              const index = parseInt(focusedOption.getAttribute('data-index') || '0', 10);
              if (!options[index]?.disabled) {
                handleSelectOption(options[index]);
              }
            }
            break;
          case 'Tab':
            // Close dropdown when tabbing out
            setIsOpen(false);
            break;
          case 'Home':
            event.preventDefault();
            // Focus first option
            const firstOption = menuRef.current?.querySelector('[data-dropdown-option]:not([aria-disabled="true"])');
            if (firstOption instanceof HTMLElement) {
              firstOption.focus();
            }
            break;
          case 'End':
            event.preventDefault();
            // Focus last option
            const optionsList = menuRef.current?.querySelectorAll('[data-dropdown-option]:not([aria-disabled="true"])');
            if (optionsList && optionsList.length > 0) {
              (optionsList[optionsList.length - 1] as HTMLElement).focus();
            }
            break;
          default:
            break;
        }
      } catch (error) {
        captureError(error);
      }
    }, [isOpen, options, handleSelectOption, focusFirstOption]);

    // Focus the first option when dropdown opens
    useEffect(() => {
      if (isOpen) {
        focusFirstOption();
      }
    }, [isOpen, focusFirstOption]);

    // Dropdown container style
    const containerStyle: React.CSSProperties = {
      position: 'relative',
      width: isFullWidth ? '100%' : width,
    };

    // Dropdown menu style
    const menuStyle: React.CSSProperties = {
      position: 'absolute',
      zIndex: 100,
      maxHeight,
      overflow: 'auto',
      minWidth: '100%',
      width: isFullWidth ? '100%' : 'auto',
      boxSizing: 'border-box',
    };

    // Position the dropdown menu based on placement
    switch (placement) {
      case 'top':
        menuStyle.bottom = '100%';
        menuStyle.marginBottom = '4px';
        break;
      case 'bottom':
      default:
        menuStyle.top = '100%';
        menuStyle.marginTop = '4px';
        break;
      case 'left':
        menuStyle.right = '100%';
        menuStyle.top = 0;
        menuStyle.marginRight = '4px';
        break;
      case 'right':
        menuStyle.left = '100%';
        menuStyle.top = 0;
        menuStyle.marginLeft = '4px';
        break;
    }

    return (
      <div 
        ref={dropdownRef}
        className={classNames('dropdown', className)}
        style={containerStyle}
        onKeyDown={handleKeyDown}
      >
        {/* Custom trigger or default button */}
        {renderTrigger ? (
          renderTrigger({
            selectedOption,
            isOpen,
            toggleDropdown,
            disabled,
          })
        ) : (
          <button
            ref={triggerRef}
            type="button"
            className={classNames('dropdown-toggle', buttonClassName, {
              'dropdown-toggle-disabled': disabled
            })}
            onClick={toggleDropdown}
            disabled={disabled}
            aria-haspopup="listbox"
            aria-expanded={isOpen}
            aria-label={selectedOption ? `Selected: ${selectedOption.label}` : placeholder}
          >
            <span className="dropdown-toggle-text">
              {selectedOption ? selectedOption.label : placeholder}
            </span>
            <span className="dropdown-arrow" aria-hidden="true">
              ▼
            </span>
          </button>
        )}

        {/* Dropdown menu */}
        {isOpen && (
          <div 
            ref={menuRef}
            className={classNames('dropdown-menu', menuClassName)} 
            style={menuStyle}
            role="listbox"
            aria-orientation="vertical"
            aria-activedescendant={selectedOption ? `option-${options.findIndex(o => o.value === selectedOption.value)}` : undefined}
            tabIndex={-1}
          >
            {options.length === 0 ? (
              <div className="dropdown-no-options">No options available</div>
            ) : (
              options.map((option, index) => {
                const isSelected = selectedOption?.value === option.value;
                
                return (
                  <div
                    key={index}
                    id={`option-${index}`}
                    className={classNames('dropdown-item', {
                      'dropdown-item-selected': isSelected,
                      'dropdown-item-disabled': option.disabled
                    })}
                    onClick={() => !option.disabled && handleSelectOption(option)}
                    onKeyDown={(e) => {
                      if ((e.key === 'Enter' || e.key === ' ') && !option.disabled) {
                        e.preventDefault();
                        handleSelectOption(option);
                      }
                    }}
                    tabIndex={option.disabled ? -1 : 0}
                    role="option"
                    aria-selected={isSelected}
                    aria-disabled={option.disabled}
                    data-dropdown-option
                    data-index={index}
                  >
                    {renderItem ? renderItem(option, isSelected) : (
                      <>
                        {option.icon && (
                          <span className="dropdown-item-icon" aria-hidden="true">{option.icon}</span>
                        )}
                        <span className="dropdown-item-label">{option.label}</span>
                      </>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>
    );
  } catch (error) {
    captureError(error);
    // Fallback rendering in case of error
    return (
      <div className="dropdown dropdown-error">
        <button type="button" className="dropdown-toggle dropdown-toggle-error" disabled>
          Error loading dropdown
        </button>
      </div>
    );
  }
}

export default Dropdown;