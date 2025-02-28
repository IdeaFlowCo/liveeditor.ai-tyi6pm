import React, { useState, useCallback } from 'react'; // React v18.0.0
import classNames from 'classnames'; // classnames ^2.3.2
import useAi from '../../hooks/useAi';
import Button from '../common/Button';
import Input from '../common/Input';
import useDebounce from '../../hooks/useDebounce';

/**
 * @interface CustomPromptProps
 * @description Defines the props for the CustomPrompt component.
 * @param {string} [className] - Optional CSS class name for styling.
 * @param {string} [placeholder] - Optional placeholder text for the input field.
 * @param {(prompt: string) => void} [onSubmit] - Optional callback function to handle form submission.
 * @param {boolean} [autoFocus] - Optional boolean to autofocus the input field.
 */
interface CustomPromptProps {
  className?: string;
  placeholder?: string;
  onSubmit?: (prompt: string) => void;
  autoFocus?: boolean;
}

/**
 * @function CustomPrompt
 * @description A component that renders a text input field for custom AI prompts with a send button
 * @param {CustomPromptProps} props - The props for the CustomPrompt component
 * @returns {JSX.Element} The rendered CustomPrompt component
 */
const CustomPrompt: React.FC<CustomPromptProps> = ({ className, placeholder, onSubmit, autoFocus }) => {
  // Initialize state for the prompt input text using useState
  const [prompt, setPrompt] = useState<string>('');

  // Get AI functionality (isProcessing, sendMessage) from useAi hook
  const { isProcessing, sendMessage } = useAi();

  // Set up debounced value for the prompt input to prevent excessive updates
  const debouncedPrompt = useDebounce(prompt, 300);

  /**
   * @function handleChange
   * @description Callback function to update the input state when user types
   * @param {React.ChangeEvent<HTMLInputElement>} event - The change event from the input field
   * @returns {void}
   */
  const handleChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setPrompt(event.target.value);
  }, []);

  /**
   * @function handleSubmit
   * @description Callback function that validates input, sends the prompt, and clears the input field
   * @param {React.FormEvent} event - The form submission event
   * @returns {void}
   */
  const handleSubmit = useCallback((event: React.FormEvent) => {
    event.preventDefault();
    if (debouncedPrompt.trim() && !isProcessing) {
      sendMessage(debouncedPrompt.trim());
      setPrompt('');
    }
  }, [debouncedPrompt, isProcessing, sendMessage]);

  /**
   * @function handleKeyDown
   * @description Callback function to submit on Enter key press
   * @param {React.KeyboardEvent} event - The keyboard event
   * @returns {void}
   */
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSubmit(event);
    }
  }, [handleSubmit]);

  // Render a form container with input field and send button
  return (
    <form
      className={classNames('flex items-center', className)}
      onSubmit={handleSubmit}
    >
      {/* Apply proper styling using Tailwind CSS and conditional classNames */}
      <Input
        type="text"
        placeholder={placeholder || 'Enter custom prompt'}
        value={prompt}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        className="flex-grow rounded-l-md border-r-0"
        aria-label="Custom AI Prompt"
        disabled={isProcessing}
        autoFocus={autoFocus}
      />
      {/* Add input accessibility attributes including aria-label */}
      <Button
        type="submit"
        variant="primary"
        size="md"
        // Disable the send button when input is empty or AI is processing
        disabled={!debouncedPrompt.trim() || isProcessing}
        // Provide visual feedback during processing state
        className="rounded-r-md"
      >
        Send
      </Button>
    </form>
  );
};

export default CustomPrompt;