import React, { useState } from 'react'; // v18.2.0
import classNames from 'classnames'; // v2.3.0

/**
 * Props interface for the Toggle component
 */
export interface ToggleProps {
  /** Controlled state of the toggle (checked or not) */
  checked?: boolean;
  /** Callback function triggered when toggle state changes */
  onChange?: (checked: boolean) => void;
  /** Whether the toggle is disabled */
  disabled?: boolean;
  /** HTML id attribute */
  id?: string;
  /** HTML name attribute (useful for forms) */
  name?: string;
  /** Text label displayed next to the toggle */
  label?: string;
  /** Additional CSS class for the label container */
  labelClassName?: string;
  /** Additional CSS class for the toggle container */
  className?: string;
  /** Size variant of the toggle */
  size?: 'sm' | 'md' | 'lg';
  /** Accessible label for screen readers */
  ariaLabel?: string;
}

/**
 * Toggle component that provides a visual on/off control
 * with support for accessibility and customization.
 * Similar to a checkbox but with a slider-style visual representation.
 */
export const Toggle: React.FC<ToggleProps> = ({
  checked: controlledChecked,
  onChange,
  disabled = false,
  id,
  name,
  label,
  labelClassName = '',
  className = '',
  size = 'md',
  ariaLabel,
}) => {
  // Internal state for uncontrolled usage
  const [internalChecked, setInternalChecked] = useState(false);
  
  // Determine if component is controlled or uncontrolled
  const isControlled = controlledChecked !== undefined;
  const checked = isControlled ? controlledChecked : internalChecked;
  
  // Handle toggle state changes
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newChecked = e.target.checked;
    
    if (!isControlled) {
      setInternalChecked(newChecked);
    }
    
    if (onChange) {
      onChange(newChecked);
    }
  };
  
  // Generate unique ID if not provided
  const toggleId = id || `toggle-${Math.random().toString(36).substring(2, 9)}`;
  
  // Compute CSS classes for the toggle wrapper
  const toggleWrapperClasses = classNames(
    'toggle',
    {
      'toggle--checked': checked,
      'toggle--disabled': disabled,
      'toggle--sm': size === 'sm',
      'toggle--md': size === 'md',
      'toggle--lg': size === 'lg'
    },
    className
  );
  
  // Compute CSS classes for the label container
  const labelContainerClasses = classNames(
    'toggle-label-container',
    { 'toggle-label-container--disabled': disabled },
    labelClassName
  );
  
  return (
    <label 
      className={labelContainerClasses} 
      htmlFor={toggleId}
    >
      <div className={toggleWrapperClasses}>
        <input
          type="checkbox"
          id={toggleId}
          name={name}
          checked={checked}
          onChange={handleChange}
          disabled={disabled}
          className="toggle__input"
          aria-label={ariaLabel || label || 'Toggle'}
          aria-checked={checked}
        />
        <div className="toggle__track">
          <span className="toggle__knob" />
        </div>
      </div>
      {label && <span className="toggle-label">{label}</span>}
    </label>
  );
};

export default Toggle;