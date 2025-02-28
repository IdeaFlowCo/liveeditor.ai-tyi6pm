import React, { useState, useEffect, useRef, useCallback } from 'react'; // React v18.2.0
import classNames from 'classnames'; // classnames v2.3.2

import ChatMessage from './ChatMessage';
import CustomPrompt from './CustomPrompt';
import AiProcessingIndicator from './AiProcessingIndicator';
import Button from '../common/Button';
import useAi from '../../hooks/useAi';
import { ChatRole, ProcessingStatus } from '../../types/ai';

/**
 * @interface ChatInterfaceProps
 * @description Defines the props for the ChatInterface component.
 * @param {string} [className] - Optional CSS class name for styling.
 * @param {string} [documentContext] - Optional document context to provide to the AI.
 * @param {boolean} [showHeader] - Optional boolean to show the header.
 */
interface ChatInterfaceProps {
  className?: string;
  documentContext?: string;
  showHeader?: boolean;
}

/**
 * @function ChatInterface
 * @description A component that renders a chat interface for interacting with the AI assistant
 * @param {ChatInterfaceProps} props - The props for the ChatInterface component
 * @returns {JSX.Element} Rendered chat interface component
 */
const ChatInterface: React.FC<ChatInterfaceProps> = ({ className, documentContext, showHeader }) => {
  // LD1: Destructure props including className, documentContext, and showHeader
  // IE3: Get AI state and functions from useAi hook (currentChat, sendMessage, etc.)
  const { currentChat, sendMessage, startNewChat, clearChatHistory, isProcessing, processingStatus, applyGeneratedContent } = useAi();

  // LD1: Create a ref for the chat messages container for auto-scrolling
  const chatMessagesRef = useRef<HTMLDivElement>(null);

  // LD1: Implement useEffect to scroll to the bottom of chat messages when new messages arrive
  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [currentChat?.messages]);

  // LD1: Create handleSendMessage function to send user input to AI
  const handleSendMessage = useCallback((message: string) => {
    sendMessage(message);
  }, [sendMessage]);

  // LD1: Create handleActionClick function to handle suggestion implementation
  const handleActionClick = useCallback(() => {
    applyGeneratedContent();
  }, [applyGeneratedContent]);

  // LD1: Create handleStartNewChat function to reset the conversation
  const handleStartNewChat = useCallback(() => {
    startNewChat();
  }, [startNewChat]);

  // LD1: Create handleClearHistory function to clear chat messages
  const handleClearHistory = useCallback(() => {
    clearChatHistory();
  }, [clearChatHistory]);

  // LD1: Create message list renderer to display all messages with appropriate styling
  const renderMessageList = () => {
    if (!currentChat || currentChat.messages.length === 0) {
      return (
        <div className="text-center text-gray-500 italic my-4">
          No messages yet. Start a conversation!
        </div>
      );
    }

    return currentChat.messages.map((message) => (
      <ChatMessage
        key={message.id}
        message={message}
        isLoading={isProcessing && processingStatus === ProcessingStatus.PROCESSING}
      />
    ));
  };

  // LD1: Render the chat interface with header (optional), message list, and input area
  return (
    <div className={classNames('flex flex-col h-full', className)}>
      {showHeader && (
        <div className="p-4 border-b">
          <h3 className="text-lg font-semibold">AI Assistant Chat</h3>
        </div>
      )}

      <div ref={chatMessagesRef} className="flex-grow overflow-y-auto p-4">
        {renderMessageList()}
        <AiProcessingIndicator />
      </div>

      <div className="p-4 border-t">
        <CustomPrompt onSubmit={handleSendMessage} />
      </div>
    </div>
  );
};

// IE3: Export ChatInterface component
export default ChatInterface;