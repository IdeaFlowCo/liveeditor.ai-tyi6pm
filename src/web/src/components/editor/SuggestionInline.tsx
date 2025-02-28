import React, { useCallback } from 'react'; // React v18.0.0
import classnames from 'classnames'; // classnames v2.3.2
import { Suggestion } from '../../../types/suggestion';
import { useTrackChanges } from '../../../hooks/useTrackChanges';
import { Button } from '../../common/Button';
import { Tooltip } from '../../common/Tooltip';
import { formatDiff } from '../../../lib/diffing/text-diff';
import { useEditorContext } from '../../../contexts/EditorContext';

/**
 * Interface defining the props for the SuggestionInline component
 */
interface SuggestionInlineProps {
  /** The suggestion object to display */
  suggestion: Suggestion;
  /** Index of the suggestion in the list */
  index: number;
  /** Whether the suggestion is currently active */
  isActive: boolean;
  /** Callback function to accept the suggestion */
  onAccept: (suggestionId: string) => void;
  /** Callback function to reject the suggestion */
  onReject: (suggestionId: string) => void;
}

/**
 * Determines the CSS classes to apply based on suggestion type (addition, deletion, modification)
 * @param suggestion 
 * @returns CSS class string
 */
const getSuggestionClasses = (suggestion: Suggestion): string => {
  // LD1: Determine the suggestion type (addition, deletion, or modification)
  let classes = 'suggestion-inline';

  // LD1: Return the appropriate CSS classes for styling
  switch (suggestion.changeType) {
    case 'addition':
      classes = classnames(classes, 'suggestion-addition');
      break;
    case 'deletion':
      classes = classnames(classes, 'suggestion-deletion');
      break;
    default:
      classes = classnames(classes, 'suggestion-modification');
      break;
  }

  return classes;
};

/**
 * A React functional component that displays an inline suggestion with visual differentiation
 * between original and suggested text, along with controls to accept or reject the change.
 * @param props 
 * @returns Rendered suggestion component
 */
export const SuggestionInline: React.FC<SuggestionInlineProps> = (props) => {
  // LD1: Extract suggestion, index, isActive, onAccept, and onReject from props
  const { suggestion, index, isActive, onAccept, onReject } = props;

  // LD1: Use useTrackChanges hook to get track changes functionality
  const { scrollToChange } = useTrackChanges();

  // LD1: Determine CSS classes based on suggestion type
  const suggestionClasses = getSuggestionClasses(suggestion);

  // LD1: Create handleAccept and handleReject callbacks for button actions
  const handleAccept = useCallback(() => {
    onAccept(suggestion.id);
  }, [onAccept, suggestion.id]);

  const handleReject = useCallback(() => {
    onReject(suggestion.id);
  }, [onReject, suggestion.id]);

  // LD1: Render container div with appropriate styling
  return (
    <div className={suggestionClasses}>
      {/* LD1: Show original text with strikethrough for deletions */}
      {suggestion.changeType === 'deletion' && (
        <del aria-label={`Original text: ${suggestion.originalText}`}>
          {suggestion.originalText}
        </del>
      )}

      {/* LD1: Show suggested text with highlighting for additions */}
      {suggestion.changeType === 'addition' && (
        <ins aria-label={`Suggested text: ${suggestion.suggestedText}`}>
          {suggestion.suggestedText}
        </ins>
      )}

      {/* LD1: Render accept and reject buttons when suggestion is active */}
      {isActive && (
        <div className="suggestion-controls">
          <Button size="sm" onClick={handleAccept}>
            Accept
          </Button>
          <Button size="sm" variant="secondary" onClick={handleReject}>
            Reject
          </Button>
        </div>
      )}

      {/* LD1: Apply appropriate accessibility attributes for screen readers */}
      <span aria-live="polite" aria-atomic="true">
        {suggestion.explanation}
      </span>
    </div>
  );
};