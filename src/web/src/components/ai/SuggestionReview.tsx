import React, { useState, useEffect, useCallback, useMemo } from 'react'; // React v18.2.0
import classNames from 'classnames'; // classnames v2.3.2
import useAi from '../../hooks/useAi';
import useTrackChanges from '../../hooks/useTrackChanges';
import Button from '../common/Button';
import Card from '../common/Card';
import Alert from '../common/Alert';
import {
  Suggestion,
  SuggestionStatus,
} from '../../types/suggestion';
import { SuggestionType, SuggestionResponse } from '../../types/ai';
import { useMediaQuery, useIsMobile } from '../../hooks/useMediaQuery';

/**
 * Props interface for the SuggestionReview component
 */
interface SuggestionReviewProps {
  className?: string;
  onClose?: () => void;
}

/**
 * Component for reviewing and managing AI-generated suggestions in the sidebar
 */
export const SuggestionReview: React.FC<SuggestionReviewProps> = ({ className, onClose }) => {
  // LD1: Extract props: className, onClose
  // LD2: Get suggestions and suggestion functions from useAi hook
  const { suggestions, acceptSuggestion, rejectSuggestion, acceptAllSuggestions, rejectAllSuggestions, clearSuggestions: clearSuggestionsAction } = useAi();
  // LD2: Get track changes state and functions from useTrackChanges hook
  const { activeChangeIndex, totalChanges, currentSuggestion, acceptedChangesCount, rejectedChangesCount, pendingChangesCount, isReviewComplete, goToNextChange, goToPreviousChange, scrollToChange } = useTrackChanges();
  // LD2: Check if mobile view using useIsMobile hook
  const isMobile = useIsMobile();

  // LD2: Initialize state for the expanded suggestion item
  const [expandedSuggestionId, setExpandedSuggestionId] = useState<string | null>(null);

  // LD2: Calculate suggestion statistics (total, accepted, rejected, pending)

  // LD2: Use effect to scroll the editor to the active change when it changes
  useEffect(() => {
    if (!isMobile) {
      scrollToChange();
    }
  }, [scrollToChange, isMobile]);

  // LD2: Handle accept/reject actions with appropriate callbacks
  const handleAccept = useCallback(() => {
    if (currentSuggestion) {
      acceptSuggestion(currentSuggestion.id);
      goToNextChange();
    }
  }, [acceptSuggestion, currentSuggestion, goToNextChange]);

  const handleReject = useCallback(() => {
    if (currentSuggestion) {
      rejectSuggestion(currentSuggestion.id);
      goToNextChange();
    }
  }, [rejectSuggestion, currentSuggestion, goToNextChange]);

  // LD2: Implement accept all and reject all functionality
  const handleAcceptAll = useCallback(() => {
    acceptAllSuggestions();
  }, [acceptAllSuggestions]);

  const handleRejectAll = useCallback(() => {
    rejectAllSuggestions();
  }, [rejectAllSuggestions]);

  // LD2: Create handler for selecting and expanding suggestion details
  const handleSuggestionClick = useCallback((suggestionId: string) => {
    if (expandedSuggestionId === suggestionId) {
      setExpandedSuggestionId(null); // Collapse if already expanded
    } else {
      setExpandedSuggestionId(suggestionId); // Expand the clicked suggestion
    }
  }, [expandedSuggestionId]);

  // LD2: Format suggestions list with status indicators
  // LD2: Render empty state when no suggestions are available
  // LD2: Render statistics bar showing counts of accepted/rejected/pending
  // LD2: Render bulk action buttons (Accept All/Reject All)
  // LD2: Render navigation controls (Previous/Next)
  // LD2: Render suggestion details for the current or expanded suggestion
  // LD2: Apply responsive layout adjustments for mobile view
  return (
    <div className={classNames('suggestion-review', className)}>
      {suggestions && suggestions.length > 0 ? (
        <>
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-lg font-semibold">Suggestions</h3>
            <span className="text-sm text-gray-500">{pendingChangesCount} pending</span>
          </div>
          <div className="space-y-2">
            {suggestions.map((suggestion) => (
              <SuggestionItem
                key={suggestion.id}
                suggestion={suggestion}
                isActive={currentSuggestion?.id === suggestion.id}
                isExpanded={expandedSuggestionId === suggestion.id}
                onClick={handleSuggestionClick}
              />
            ))}
          </div>
          <div className="mt-4">
            <p className="text-sm text-gray-600">
              Accepted: {acceptedChangesCount}, Rejected: {rejectedChangesCount}, Total: {totalChanges}
            </p>
            <div className="flex justify-between mt-2">
              <Button variant="secondary" size="sm" onClick={handleAcceptAll} disabled={isReviewComplete}>
                Accept All
              </Button>
              <Button variant="secondary" size="sm" onClick={handleRejectAll} disabled={isReviewComplete}>
                Reject All
              </Button>
            </div>
            <div className="flex justify-between mt-2">
              <Button variant="tertiary" size="sm" onClick={goToPreviousChange} disabled={activeChangeIndex === 0}>
                Previous
              </Button>
              <Button variant="tertiary" size="sm" onClick={goToNextChange} disabled={activeChangeIndex === totalChanges - 1}>
                Next
              </Button>
            </div>
          </div>
          {currentSuggestion && (
            <SuggestionDetails suggestion={currentSuggestion} onAccept={handleAccept} onReject={handleReject} />
          )}
        </>
      ) : (
        <EmptyState />
      )}
    </div>
  );
};

interface SuggestionItemProps {
  suggestion: Suggestion;
  isActive: boolean;
  isExpanded: boolean;
  onClick: (suggestionId: string) => void;
}

/**
 * Renders an individual suggestion item in the list
 */
const SuggestionItem: React.FC<SuggestionItemProps> = ({ suggestion, isActive, isExpanded, onClick }) => {
  // LD2: Destructure parameters to get suggestion data and state
  // LD2: Format original and suggested text for display
  // LD2: Apply appropriate status styling based on suggestion.status
  // LD2: Render a clickable card with suggestion preview
  // LD2: Show truncated text preview with ellipsis if too long
  // LD2: Include status indicator (pending/accepted/rejected)
  // LD2: Highlight active suggestion with different styling
  // LD2: Add expand/collapse functionality on click
  return (
    <Card
      isInteractive
      onClick={() => onClick(suggestion.id)}
      className={classNames(
        'suggestion-item',
        {
          'suggestion-item--active': isActive,
          'suggestion-item--expanded': isExpanded,
        }
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex-grow">
          <p className="font-medium">{suggestion.originalText.substring(0, 50)}{suggestion.originalText.length > 50 ? '...' : ''}</p>
          <p className="text-sm text-gray-500">{suggestion.suggestedText.substring(0, 50)}{suggestion.suggestedText.length > 50 ? '...' : ''}</p>
        </div>
        <StatusBadge status={suggestion.status} />
      </div>
    </Card>
  );
};

interface SuggestionDetailsProps {
  suggestion: Suggestion;
  onAccept: () => void;
  onReject: () => void;
}

/**
 * Displays detailed information about the selected suggestion
 */
const SuggestionDetails: React.FC<SuggestionDetailsProps> = ({ suggestion, onAccept, onReject }) => {
  // LD2: Destructure parameters to get suggestion and action handlers
  // LD2: Format the original and suggested text for display
  // LD2: Create a visual diff highlighting the changes
  // LD2: Display the AI's explanation for the suggested change
  // LD2: Render accept and reject buttons
  // LD2: Show suggestion status if already decided
  // LD2: Implement keyboard shortcuts for accept/reject
  return (
    <div className="suggestion-details">
      <h4 className="font-semibold">Suggestion Details</h4>
      <p>Original: {suggestion.originalText}</p>
      <p>Suggested: {suggestion.suggestedText}</p>
      <p>Explanation: {suggestion.explanation}</p>
      <div className="flex justify-end mt-2">
        <Button variant="primary" size="sm" onClick={onAccept}>
          Accept
        </Button>
        <Button variant="secondary" size="sm" onClick={onReject}>
          Reject
        </Button>
      </div>
    </div>
  );
};

/**
 * Component shown when no suggestions are available
 */
const EmptyState: React.FC = () => {
  // LD2: Render a message indicating no suggestions
  // LD2: Show guidance on how to generate suggestions
  // LD2: Include a visual indicator or illustration
  // LD2: Provide link or button to go to templates section
  return (
    <Alert message="No suggestions available. Try generating some!" />
  );
};

interface StatusBadgeProps {
  status: SuggestionStatus;
}

/**
 * Displays the status of a suggestion using a colored badge
 */
const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  // LD2: Map status value to display text (Pending/Accepted/Rejected)
  // LD2: Apply appropriate color based on status
  // LD2: Render badge with status text
  // LD2: Include subtle status icon if appropriate
  let badgeText = '';
  let badgeColor = '';

  switch (status) {
    case SuggestionStatus.PENDING:
      badgeText = 'Pending';
      badgeColor = 'bg-yellow-100 text-yellow-800';
      break;
    case SuggestionStatus.ACCEPTED:
      badgeText = 'Accepted';
      badgeColor = 'bg-green-100 text-green-800';
      break;
    case SuggestionStatus.REJECTED:
      badgeText = 'Rejected';
      badgeColor = 'bg-red-100 text-red-800';
      break;
    default:
      badgeText = 'Unknown';
      badgeColor = 'bg-gray-100 text-gray-800';
      break;
  }

  return (
    <span className={classNames('px-2 py-1 rounded-full text-xs font-medium', badgeColor)}>
      {badgeText}
    </span>
  );
};