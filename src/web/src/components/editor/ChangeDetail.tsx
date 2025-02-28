import React, { FC, useCallback, useMemo } from 'react'; // React v18.2.0
import classnames from 'classnames'; // classnames v2.3.2

import { Button } from '../common/Button';
import Card from '../common/Card';
import useTrackChanges from '../../hooks/useTrackChanges';
import { SuggestionChange } from '../../types/suggestion';

/**
 * Interface defining the props for the ChangeDetail component
 */
interface ChangeDetailProps {
  /** The suggestion change object containing details about the change */
  change: SuggestionChange;
  /** Optional callback function to execute when the accept button is clicked */
  onAccept?: (changeId: string) => void;
  /** Optional callback function to execute when the reject button is clicked */
  onReject?: (changeId: string) => void;
  /** Optional callback function to execute when navigation is triggered */
  onNavigate?: (direction: 'next' | 'previous') => void;
  /** Optional CSS class name to apply to the component */
  className?: string;
  /** Optional flag indicating if this is the currently selected change */
  isCurrentChange?: boolean;
    /** Optional flag indicating whether to show the AI explanation */
  showExplanation?: boolean;
}

/**
 * A React component that displays detailed information about a specific AI suggestion
 * in the track changes interface, including the original text, suggested replacement,
 * explanation, and accept/reject controls.
 *
 * @param {ChangeDetailProps} props - The props object containing the change details and callbacks
 * @returns {JSX.Element} A React component for displaying change details
 */
const ChangeDetail: FC<ChangeDetailProps> = ({
  change,
  onAccept,
  onReject,
  onNavigate,
  className,
  isCurrentChange,
  showExplanation = true
}) => {
  // IE1: Use the useTrackChanges hook to manage track changes functionality
  const { acceptCurrentChange, rejectCurrentChange, goToNextChange, goToPreviousChange } = useTrackChanges();

  // LD1: Define a memoized class name for the component
  const changeDetailClasses = useMemo(() => {
    return classnames(
      'change-detail',
      {
        'change-detail--current': isCurrentChange,
      },
      className
    );
  }, [className, isCurrentChange]);

  // LD1: Define a function to handle accepting the current change
  const handleAccept = useCallback(() => {
    // Call the acceptChange method from useTrackChanges hook
    acceptCurrentChange();

    // Execute the onAccept callback if provided in props
    onAccept?.(change.id);
  }, [acceptCurrentChange, change.id, onAccept]);

  // LD1: Define a function to handle rejecting the current change
  const handleReject = useCallback(() => {
    // Call the rejectChange method from useTrackChanges hook
    rejectCurrentChange();

    // Execute the onReject callback if provided in props
    onReject?.(change.id);
  }, [change.id, onReject, rejectCurrentChange]);

  // LD1: Define a function to handle navigation to the next change
  const handleNext = useCallback(() => {
    // Call the goToNextChange method from useTrackChanges hook
    goToNextChange();

    // Execute the onNavigate callback if provided in props
    onNavigate?.('next');
  }, [goToNextChange, onNavigate]);

  // LD1: Define a function to handle navigation to the previous change
  const handlePrevious = useCallback(() => {
    // Call the goToPreviousChange method from useTrackChanges hook
    goToPreviousChange();

    // Execute the onNavigate callback if provided in props
    onNavigate?.('previous');
  }, [goToPreviousChange, onNavigate]);

  // O1: Render the component
  return (
    <Card className={changeDetailClasses}>
      {/* O1: Display the original text with deleted content styling */}
      <div className="mb-4">
        <h4 className="font-semibold">Original Text</h4>
        <p className="text-red-500 line-through">{change.originalText}</p>
      </div>

      {/* O1: Display the suggested text with added content styling */}
      <div className="mb-4">
        <h4 className="font-semibold">Suggested Change</h4>
        <p className="text-green-500 underline">{change.suggestedText}</p>
      </div>

      {/* O1: Conditionally render the explanation section */}
      {showExplanation && change.explanation && (
        <div className="mb-4">
          <h4 className="font-semibold">Explanation</h4>
          <p className="text-gray-700">{change.explanation}</p>
        </div>
      )}

      {/* O1: Render the action buttons */}
      <div className="flex justify-between">
        <Button variant="secondary" size="sm" onClick={handleReject}>
          Reject
        </Button>
        <Button variant="primary" size="sm" onClick={handleAccept}>
          Accept
        </Button>
      </div>

      {/* O1: Render the navigation controls */}
      <div className="flex justify-between mt-4">
        <Button variant="tertiary" size="sm" onClick={handlePrevious}>
          &lt; Previous
        </Button>
        <Button variant="tertiary" size="sm" onClick={handleNext}>
          Next &gt;
        </Button>
      </div>
    </Card>
  );
};

export default ChangeDetail;