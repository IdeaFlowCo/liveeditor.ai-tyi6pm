import { useState, useEffect, useCallback, useMemo } from 'react'; // react ^18.2.0
import { useSelector, useDispatch } from '../store';
import {
  acceptSuggestion,
  rejectSuggestion,
  acceptAllSuggestions,
  rejectAllSuggestions,
  selectDocumentChanges,
  selectDocument,
} from '../store/slices/documentSlice';
import { useEditorContext } from '../contexts/EditorContext';
import { Suggestion, SuggestionStatus } from '../types/suggestion';
import { getSuggestionAt, getAllSuggestions } from '../lib/prosemirror-track-changes/track-changes';

/**
 * A custom React hook that provides functionality for managing and navigating track changes in the document editor.
 *
 * @returns {object} An object containing track changes state and functions
 */
export const useTrackChanges = () => {
  // LD1: Initialize state for tracking active change index
  const [activeChangeIndex, setActiveChangeIndex] = useState<number>(0);

  // LD1: Get the current document and suggestions from Redux store
  const document = useSelector(selectDocument);
  const suggestions = useSelector(selectDocumentChanges);

  // LD1: Get the editor state and methods from EditorContext
  const { editorState, editorView, trackChanges } = useEditorContext();

  // LD1: Calculate total changes and filter pending suggestions
  const totalChanges = useMemo(() => {
    return suggestions?.length || 0;
  }, [suggestions]);

  const pendingChangesCount = useMemo(() => {
    return suggestions?.filter(suggestion => suggestion.status === SuggestionStatus.PENDING).length || 0;
  }, [suggestions]);

  const acceptedChangesCount = useMemo(() => {
    return suggestions?.filter(suggestion => suggestion.status === SuggestionStatus.ACCEPTED).length || 0;
  }, [suggestions]);

  const rejectedChangesCount = useMemo(() => {
    return suggestions?.filter(suggestion => suggestion.status === SuggestionStatus.REJECTED).length || 0;
  }, [suggestions]);

  const isReviewComplete = useMemo(() => {
    return pendingChangesCount === 0;
  }, [pendingChangesCount]);

  // LD1: Get the current suggestion based on the activeChangeIndex
  const currentSuggestion = useMemo<Suggestion | null>(() => {
    if (!suggestions || suggestions.length === 0 || activeChangeIndex < 0 || activeChangeIndex >= suggestions.length) {
      return null;
    }
    return suggestions[activeChangeIndex];
  }, [activeChangeIndex, suggestions]);

  // LD1: Redux dispatch function
  const dispatch = useDispatch();

  // LD1: Define function to handle accepting the current change
  const acceptCurrentChange = useCallback(() => {
    if (currentSuggestion && document) {
      dispatch(acceptSuggestion(currentSuggestion.id));
    }
  }, [currentSuggestion, dispatch, document]);

  // LD1: Define function to handle rejecting the current change
  const rejectCurrentChange = useCallback(() => {
    if (currentSuggestion && document) {
      dispatch(rejectSuggestion(currentSuggestion.id));
    }
  }, [currentSuggestion, dispatch, document]);

  // LD1: Define function to navigate to the next change
  const goToNextChange = useCallback(() => {
    if (totalChanges === 0) return;
    setActiveChangeIndex((prevIndex) => (prevIndex + 1) % totalChanges);
  }, [totalChanges]);

  // LD1: Define function to navigate to the previous change
  const goToPreviousChange = useCallback(() => {
    if (totalChanges === 0) return;
    setActiveChangeIndex((prevIndex) => (prevIndex - 1 + totalChanges) % totalChanges);
  }, [totalChanges]);

  // LD1: Define function to accept all changes at once
  const acceptAllChanges = useCallback(() => {
    if (document) {
      dispatch(acceptAllSuggestions());
    }
  }, [dispatch, document]);

  // LD1: Define function to reject all changes at once
  const rejectAllChanges = useCallback(() => {
    if (document) {
      dispatch(rejectAllSuggestions());
    }
  }, [dispatch, document]);

  // LD1: Define function to scroll to the current change position in the editor
  const scrollToChange = useCallback(() => {
    if (!editorView || !currentSuggestion) return;

    // Get the position of the current suggestion
    const { from, to } = currentSuggestion.position;

    // Ensure the editor is focused
    editorView.focus();

    // Scroll the editor to the position of the suggestion
    editorView.dispatch(editorView.state.tr.scrollIntoView());
  }, [currentSuggestion, editorView]);

  // LD1: Update editor view to highlight active change when activeChangeIndex changes
  useEffect(() => {
    scrollToChange();
  }, [activeChangeIndex, scrollToChange]);

  // LD1: Return state and functions object
  return {
    activeChangeIndex,
    totalChanges,
    currentSuggestion,
    acceptCurrentChange,
    rejectCurrentChange,
    goToNextChange,
    goToPreviousChange,
    acceptAllChanges,
    rejectAllChanges,
    acceptedChangesCount,
    rejectedChangesCount,
    pendingChangesCount,
    isReviewComplete,
    scrollToChange
  };
};