import React, { useCallback } from 'react'; // React v18.2.0
import classNames from 'classnames'; // classnames v2.3.2

import PromptTemplates from './PromptTemplates';
import ChatInterface from './ChatInterface';
import SuggestionReview from './SuggestionReview';
import CustomPrompt from './CustomPrompt';
import AiProcessingIndicator from './AiProcessingIndicator';
import Button from '../common/Button';
import useAi from '../../hooks/useAi';
import useSidebar from '../../hooks/useSidebar';
import { AiSidebarMode } from '../../types/ai';
import { useMediaQuery, useIsMobile } from '../../hooks/useMediaQuery';

/**
 * @interface AiSidebarProps
 * @description Defines the props for the AiSidebar component.
 * @param {string} [className] - Optional CSS class name for styling.
 * @param {string} [documentContext] - Optional document context to provide to the AI.
 */
interface AiSidebarProps {
  className?: string;
  documentContext?: string;
}

/**
 * @function AiSidebar
 * @description Main sidebar component that manages different AI interaction modes and renders appropriate sub-components
 * @param {AiSidebarProps} props - The props for the AiSidebar component
 * @returns {JSX.Element} Rendered sidebar component with appropriate mode content
 */
const AiSidebar: React.FC<AiSidebarProps> = (props) => {
  // LD1: Destructure props for className and documentContext
  const { className, documentContext } = props;

  // IE3: Get sidebar state and control functions from useSidebar hook
  const { isOpen, mode, toggleSidebar, setMode } = useSidebar();

  // IE3: Get AI state from useAi hook (isProcessing, suggestions, currentChat)
  const { isProcessing, suggestions, currentChat } = useAi();

  // IE3: Check mobile viewport status with useIsMobile hook
  const isMobile = useIsMobile();

  // LD1: Implement tab selection logic to switch between modes
  const handleTemplatesClick = useCallback(() => {
    setMode(AiSidebarMode.TEMPLATES);
  }, [setMode]);

  const handleChatClick = useCallback(() => {
    setMode(AiSidebarMode.CHAT);
  }, [setMode]);

  const handleReviewClick = useCallback(() => {
    setMode(AiSidebarMode.REVIEW);
  }, [setMode]);

  // LD1: Implement close button functionality
  const handleCloseClick = useCallback(() => {
    toggleSidebar();
  }, [toggleSidebar]);

  // LD1: Render sidebar container with classes based on isOpen state
  const sidebarClasses = classNames(
    'ai-sidebar',
    'bg-gray-50',
    'border-l',
    'border-gray-200',
    'shadow-md',
    'h-full',
    'flex',
    'flex-col',
    'transition-transform',
    'duration-300',
    'ease-in-out',
    {
      'translate-x-0': isOpen,
      '-translate-x-full': !isOpen,
    },
    className
  );

  // LD1: Add responsive classes for mobile vs desktop layout
  const responsiveClasses = classNames({
    'w-96': !isMobile,
    'w-full': isMobile,
  });

  // LD1: Display suggestion count badge when suggestions are available
  const hasSuggestions = suggestions && suggestions.length > 0;
  const hasChat = currentChat && currentChat.messages.length > 0;

  // LD1: Render appropriate content component based on active mode
  return (
    <aside className={classNames(sidebarClasses, responsiveClasses)}>
      {/* LD1: Render sidebar header with mode tabs and close button */}
      <SidebarHeader
        activeMode={mode}
        onModeChange={setMode}
        onClose={handleCloseClick}
        hasSuggestions={hasSuggestions}
        hasChat={hasChat}
      />

      {/* LD1: Render appropriate content component based on active mode */}
      <SidebarContent mode={mode} documentContext={documentContext} />
    </aside>
  );
};

interface SidebarHeaderProps {
  activeMode: string;
  onModeChange: (mode: string) => void;
  onClose: () => void;
  hasSuggestions: boolean;
  hasChat: boolean;
}

/**
 * @function SidebarHeader
 * @description Component for the sidebar header with mode tabs and close button
 * @param {SidebarHeaderProps} props - The props for the SidebarHeader component
 * @returns {JSX.Element} Rendered sidebar header
 */
const SidebarHeader: React.FC<SidebarHeaderProps> = ({ activeMode, onModeChange, onClose, hasSuggestions, hasChat }) => {
  // LD1: Render header container with styling
  return (
    <div className="flex items-center justify-between p-4 border-b border-gray-200">
      {/* LD1: Render tab buttons for each mode (Templates, Chat, Review) */}
      <div className="flex space-x-4">
        <Button
          variant={activeMode === AiSidebarMode.TEMPLATES ? 'primary' : 'secondary'}
          size="sm"
          onClick={() => onModeChange(AiSidebarMode.TEMPLATES)}
        >
          Templates
        </Button>
        <Button
          variant={activeMode === AiSidebarMode.CHAT ? 'primary' : 'secondary'}
          size="sm"
          onClick={() => onModeChange(AiSidebarMode.CHAT)}
        >
          Chat {hasChat && <span className="ml-1 text-xs bg-green-500 text-white rounded-full px-2 py-0.5">!</span>}
        </Button>
        <Button
          variant={activeMode === AiSidebarMode.REVIEW ? 'primary' : 'secondary'}
          size="sm"
          onClick={() => onModeChange(AiSidebarMode.REVIEW)}
        >
          Review {hasSuggestions && <span className="ml-1 text-xs bg-blue-500 text-white rounded-full px-2 py-0.5">!</span>}
        </Button>
      </div>

      {/* LD1: Show close button with appropriate accessibility attributes */}
      <Button
        variant="tertiary"
        size="sm"
        onClick={onClose}
        aria-label="Close AI Sidebar"
      >
        X
      </Button>
    </div>
  );
};

interface SidebarContentProps {
  mode: string;
  documentContext?: string;
}

/**
 * @function SidebarContent
 * @description Component that renders the appropriate content based on active sidebar mode
 * @param {SidebarContentProps} props - The props for the SidebarContent component
 * @returns {JSX.Element} Rendered content for the active mode
 */
const SidebarContent: React.FC<SidebarContentProps> = ({ mode, documentContext }) => {
  // LD1: Use switch statement to determine which component to render based on mode
  switch (mode) {
    // LD1: For TEMPLATES mode, render PromptTemplates component
    case AiSidebarMode.TEMPLATES:
      return (
        <div className="p-4">
          <PromptTemplates showRecentTemplates showAllCategories documentContext={documentContext} />
        </div>
      );

    // LD1: For CHAT mode, render ChatInterface component
    case AiSidebarMode.CHAT:
      return (
        <div className="p-4">
          <ChatInterface documentContext={documentContext} />
        </div>
      );

    // LD1: For REVIEW mode, render SuggestionReview component
    case AiSidebarMode.REVIEW:
      return (
        <div className="p-4">
          <SuggestionReview documentContext={documentContext} />
        </div>
      );

    default:
      return <div className="p-4">Select an AI mode</div>;
  }
};

// IE3: Be generous about your exports so long as it doesn't create a security risk.
export default AiSidebar;