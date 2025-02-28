import React from 'react'; // React v18.2.0
import classNames from 'classnames'; // classnames v2.3.2

import { Button } from '../common/Button';
import { ChatMessage as ChatMessageType, ChatRole } from '../../types/ai';

/**
 * Props for the ChatMessage component
 */
interface ChatMessageProps {
  /** The message object to display */
  message: ChatMessageType;
  /** Whether the message is currently loading/generating */
  isLoading?: boolean;
  /** Callback function when an action button is clicked */
  onActionClick?: (actionType: string, content?: string) => void;
}

/**
 * Component that renders an individual message in the AI chat interface
 * 
 * Displays user queries or AI responses with appropriate styling and
 * optional action buttons for implementing suggestions.
 */
export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  isLoading = false,
  onActionClick
}) => {
  // Determine message type from role
  const isUser = message.role === ChatRole.USER;
  const isAssistant = message.role === ChatRole.ASSISTANT;
  const isSystem = message.role === ChatRole.SYSTEM;
  
  // Apply appropriate styling based on message source
  const containerClasses = classNames(
    'p-4 rounded-lg mb-3 shadow-sm',
    {
      'bg-[#F5F7FA] text-gray-800 self-start rounded-tl-none border border-gray-200 max-w-[85%]': isAssistant,
      'bg-[#2C6ECB] text-white self-end rounded-tr-none max-w-[75%]': isUser,
      'bg-[#FFC107] text-gray-800 self-start italic border border-yellow-300 w-full': isSystem
    }
  );

  /**
   * Format message content for display with line breaks preserved
   */
  const formatContent = (content: string) => {
    if (!content || !content.trim()) {
      return <p className="text-gray-400 italic">Empty message</p>;
    }
    
    // Split content by lines and preserve line breaks
    const lines = content.split('\n');
    
    return lines.map((line, index) => (
      <React.Fragment key={index}>
        {line}
        {index < lines.length - 1 && <br />}
      </React.Fragment>
    ));
  };

  /**
   * Extract actionable suggestions from message metadata
   */
  const getActions = () => {
    if (!isAssistant || !message.metadata) return [];
    
    const actions = [];
    
    // Check for direct suggestion in metadata
    if (message.metadata.suggestedText || message.metadata.suggestion) {
      actions.push({
        type: 'apply',
        label: 'Apply suggestion',
        content: message.metadata.suggestedText || message.metadata.suggestion
      });
    }
    
    // Check for actions array in metadata
    if (message.metadata.actions && Array.isArray(message.metadata.actions)) {
      message.metadata.actions.forEach(action => {
        actions.push({
          type: action.type || 'apply',
          label: action.label || 'Apply',
          content: action.content || action.text || message.content
        });
      });
    }
    
    return actions;
  };

  const actions = getActions();

  return (
    <div 
      className={classNames(
        'flex w-full mb-4', 
        { 
          'justify-end': isUser,
          'justify-start': !isUser
        }
      )}
    >
      <div 
        className={classNames(
          containerClasses,
          { 'opacity-75': isLoading }
        )}
        data-testid={`chat-message-${message.role}`}
      >
        {/* Message content with preserved formatting */}
        <div className="whitespace-pre-wrap break-words">
          {formatContent(message.content)}
        </div>
        
        {/* Loading indicator for messages being processed */}
        {isLoading && (
          <div 
            className="mt-3 flex items-center" 
            role="status"
            aria-label="Loading response"
          >
            <div className="h-2 w-2 bg-current rounded-full mr-1 animate-bounce"></div>
            <div className="h-2 w-2 bg-current rounded-full mx-1 animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            <div className="h-2 w-2 bg-current rounded-full ml-1 animate-bounce" style={{ animationDelay: '0.4s' }}></div>
            <span className="sr-only">Loading</span>
          </div>
        )}
        
        {/* Action buttons for AI suggestions */}
        {actions.length > 0 && onActionClick && (
          <div className="mt-3 flex flex-wrap gap-2 justify-end">
            {actions.map((action, index) => (
              <Button 
                key={`${action.type}-${index}`}
                size="sm" 
                variant={action.type === 'apply' ? 'primary' : 'secondary'}
                onClick={() => onActionClick(action.type, action.content)}
                disabled={isLoading}
                aria-label={`${action.label} suggestion`}
              >
                {action.label}
              </Button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Add displayName for better debugging
ChatMessage.displayName = 'ChatMessage';

export default ChatMessage;