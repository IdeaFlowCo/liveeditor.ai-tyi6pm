import React, { useState, useCallback } from 'react'; // React v17.0.0
import classNames from 'classnames'; // classnames v2.3.2
import { Button } from '../common/Button';
import { useTrackChanges } from '../../hooks/useTrackChanges';
import { Tooltip } from '../common/Tooltip';
import Badge from '../common/Badge';
import Modal from '../common/Modal';
import { Suggestion } from '../../types/suggestion';

/**
 * Props interface for the TrackChangesToolbar component
 */
interface TrackChangesToolbarProps {
  currentSuggestion: Suggestion | null;
  totalSuggestions: number;
  currentIndex: number;
  acceptedCount: number;
  rejectedCount: number;
  className?: string;
}

/**
 * A toolbar component for managing track changes in the document editor
 * Provides controls for accepting or rejecting changes individually or in bulk, and navigating between suggestions.
 */
export const TrackChangesToolbar: React.FC<TrackChangesToolbarProps> = ({
  currentSuggestion,
  totalSuggestions,
  currentIndex,
  acceptedCount,
  rejectedCount,
  className,
}) => {
  // LD1: Destructure props to access currentSuggestion, totalSuggestions, currentIndex, etc.

  // LD1: Get track changes functionality from useTrackChanges hook
  const {
    acceptCurrentChange,
    rejectCurrentChange,
    goToNextChange,
    goToPreviousChange,
    acceptAllChanges,
    rejectAllChanges,
    isReviewComplete,
    scrollToChange
  } = useTrackChanges();

  // LD1: Initialize state for confirmation dialogs using useState
  const [showAcceptAllConfirmation, setShowAcceptAllConfirmation] = useState(false);
  const [showRejectAllConfirmation, setShowRejectAllConfirmation] = useState(false);

  // LD1: Define handler for accepting current suggestion
  const handleAccept = useCallback(() => {
    if (currentSuggestion) {
      acceptCurrentChange();
    }
  }, [acceptCurrentChange, currentSuggestion]);

  // LD1: Define handler for rejecting current suggestion
  const handleReject = useCallback(() => {
    if (currentSuggestion) {
      rejectCurrentChange();
    }
  }, [rejectCurrentChange, currentSuggestion]);

  // LD1: Define handler for accepting all suggestions with confirmation
  const handleAcceptAll = useCallback(() => {
    setShowAcceptAllConfirmation(true);
  }, []);

  // LD1: Define handler for rejecting all suggestions with confirmation
  const handleRejectAll = useCallback(() => {
    setShowRejectAllConfirmation(true);
  }, []);

  // LD1: Define handlers for navigating to next and previous suggestions
  const handleNext = useCallback(() => {
    goToNextChange();
  }, [goToNextChange]);

  const handlePrevious = useCallback(() => {
    goToPreviousChange();
  }, [goToPreviousChange]);

  // LD1: Render toolbar container with appropriate classes
  return (
    <div className={classNames('track-changes-toolbar', className)}>
      {/* LD1: Render bulk action buttons (Accept All, Reject All) with tooltips */}
      <Tooltip content="Accept All Suggestions">
        <Button
          variant="success"
          size="sm"
          disabled={isReviewComplete}
          onClick={handleAcceptAll}
        >
          Accept All
        </Button>
      </Tooltip>
      <Tooltip content="Reject All Suggestions">
        <Button
          variant="danger"
          size="sm"
          disabled={isReviewComplete}
          onClick={handleRejectAll}
        >
          Reject All
        </Button>
      </Tooltip>

      {/* LD1: Render navigation controls with current/total suggestion count */}
      <span>
        {currentIndex + 1} / {totalSuggestions}
      </span>
      <Tooltip content="Go to Previous Suggestion">
        <Button
          variant="secondary"
          size="sm"
          disabled={totalSuggestions === 0}
          onClick={handlePrevious}
        >
          Previous
        </Button>
      </Tooltip>
      <Tooltip content="Go to Next Suggestion">
        <Button
          variant="secondary"
          size="sm"
          disabled={totalSuggestions === 0}
          onClick={handleNext}
        >
          Next
        </Button>
      </Tooltip>

      {/* LD1: Render individual suggestion action buttons (Accept, Reject) */}
      <Tooltip content="Accept Suggestion">
        <Button
          variant="success"
          size="sm"
          disabled={!currentSuggestion}
          onClick={handleAccept}
        >
          Accept
        </Button>
      </Tooltip>
      <Tooltip content="Reject Suggestion">
        <Button
          variant="danger"
          size="sm"
          disabled={!currentSuggestion}
          onClick={handleReject}
        >
          Reject
        </Button>
      </Tooltip>

      {/* LD1: Render confirmation dialogs for bulk actions when necessary */}
      <Modal
        isOpen={showAcceptAllConfirmation}
        onClose={() => setShowAcceptAllConfirmation(false)}
        title="Accept All Suggestions"
      >
        <p>Are you sure you want to accept all suggestions?</p>
        <Button onClick={acceptAllChanges}>Yes, Accept All</Button>
        <Button onClick={() => setShowAcceptAllConfirmation(false)}>Cancel</Button>
      </Modal>

      <Modal
        isOpen={showRejectAllConfirmation}
        onClose={() => setShowRejectAllConfirmation(false)}
        title="Reject All Suggestions"
      >
        <p>Are you sure you want to reject all suggestions?</p>
        <Button onClick={rejectAllChanges}>Yes, Reject All</Button>
        <Button onClick={() => setShowRejectAllConfirmation(false)}>Cancel</Button>
      </Modal>
    </div>
  );
};