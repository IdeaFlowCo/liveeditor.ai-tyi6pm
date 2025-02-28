import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
} from 'react'; // React v18.2.0
import { EditorState, Transaction } from 'prosemirror-state'; // v1.4.1
import { EditorView } from 'prosemirror-view'; // v1.28.1

import EditorToolbar from './EditorToolbar';
import EditorContent from './EditorContent';
import TrackChanges from './TrackChanges';
import AiSidebar from '../ai/AiSidebar';
import DocumentSavePrompt from '../document/DocumentSavePrompt';
import Button from '../common/Button';
import Spinner from '../common/Spinner';
import Alert from '../common/Alert';
import useDocument from '../../hooks/useDocument';
import useAi from '../../hooks/useAi';
import useTrackChanges from '../../hooks/useTrackChanges';
import useAuth from '../../hooks/useAuth';
import useDebounce from '../../hooks/useDebounce';
import { setupEditor, schema } from './prosemirror/setup';
import { trackChangesPlugin } from './prosemirror/plugins/track-changes';
import { Document } from '../../types/document';
import {
  setDocument,
  saveDocument,
  clearDocument,
} from '../../store/slices/documentSlice';
import {
  setSuggestions,
  clearSuggestions,
} from '../../store/slices/aiSlice';
import {
  AUTOSAVE_INTERVAL,
  MAX_DOCUMENT_SIZE,
} from '../../constants/editor';

/**
 * Interface defining the props for the Editor component
 */
interface EditorProps {
  documentId?: string;
  readOnly?: boolean;
  initialContent?: string;
  autoSave?: boolean;
}

/**
 * Main component for the document editor with integrated AI writing enhancement capabilities,
 * including track changes functionality and AI suggestion interface
 * @param props - EditorProps
 * @returns Rendered editor component
 */
const Editor: React.FC<EditorProps> = (props) => {
  // LD1: Destructure props to get documentId, readOnly, initialContent, and autoSave
  const { documentId, readOnly, initialContent, autoSave } = props;

  // LD1: Access document state and operations using the useDocument hook
  const {
    document,
    documentContent,
    documentTitle,
    documentStats,
    documentList,
    status,
    isLoading,
    isError,
    isSaving,
    isAutosaving,
    createNewDocument,
    loadDocument: loadDocumentHook,
    saveDocumentChanges,
    updateDocumentContent,
    updateDocumentTitle,
    deleteCurrentDocument,
    uploadDocumentFile,
    exportDocumentTo,
  } = useDocument(documentId);

  // LD1: Access AI state and operations using the useAi hook
  const {
    processingStatus,
    isProcessing,
    error: aiError,
    suggestions,
    selectedTemplate,
    templates,
    currentChat,
    chatInput,
    setChatInput,
    selectedText,
    setSelectedText,
    generateSuggestion,
    handleTemplateSelect,
    acceptSuggestion,
    rejectSuggestion,
    acceptAllSuggestions,
    rejectAllSuggestions,
    clearSuggestions: clearSuggestionsHook,
    sendMessage,
    startNewChat,
    clearChatHistory,
    applyGeneratedContent,
  } = useAi();

  // LD1: Access track changes state and operations using the useTrackChanges hook
  const {
    activeChangeIndex,
    totalChanges,
    currentSuggestion,
    acceptCurrentChange,
    rejectCurrentChange,
    goToNextChange,
    goToPreviousChange,
    acceptAllChanges: acceptAllChangesHook,
    rejectAllChanges: rejectAllChangesHook,
    acceptedChangesCount,
    rejectedChangesCount,
    pendingChangesCount,
    isReviewComplete,
    scrollToChange,
  } = useTrackChanges();

  // LD1: Access authentication state and operations using the useAuth hook
  const { user, isAuthenticated, isAnonymous, login, register, logout } =
    useAuth();

  // LD1: Define state variables for track changes visibility, review mode, and show explanations
  const [isAiSidebarVisible, setIsAiSidebarVisible] = useState(true);
  const [isReviewMode, setIsReviewMode] = useState(false);
  const [showExplanations, setShowExplanations] = useState(true);
  const [showSavePrompt, setShowSavePrompt] = useState(false);

  // LD1: Create a ref for the editor component
  const editorRef = useRef(null);

  // LD1: Implement function to handle document loading
  const loadDocument = useCallback(async () => {
    if (documentId) {
      try {
        await loadDocumentHook(documentId);
      } catch (error) {
        console.error('Failed to load document:', error);
      }
    }
  }, [documentId, loadDocumentHook]);

  // LD1: Implement function to handle document saving
  const handleSaveDocument = useCallback(async () => {
    try {
      await saveDocumentChanges();
    } catch (error) {
      console.error('Failed to save document:', error);
    }
  }, [saveDocumentChanges]);

  // LD1: Implement function to handle AI suggestion generation
  const handleSuggestionGenerate = useCallback(async () => {
    try {
      await generateSuggestion(null, null);
    } catch (error) {
      console.error('Failed to generate suggestions:', error);
    }
  }, [generateSuggestion]);

  // LD1: Implement function to handle track changes visibility toggle
  const handleAiSidebarVisibilityToggle = () => {
    setIsAiSidebarVisible((prev) => !prev);
  };

  // LD1: Implement function to handle track changes review mode toggle
  const handleTrackChangesReviewModeToggle = () => {
    setIsReviewMode((prev) => !prev);
  };

  // LD1: Implement function to handle show explanations toggle
  const handleShowExplanationsToggle = () => {
    setShowExplanations((prev) => !prev);
  };

  // O1: Render the component
  return (
    <div className="flex h-screen">
      {/* O1: Render the EditorContent component */}
      <div className="flex-grow flex-col">
        <EditorToolbar />
        <EditorContent
          initialContent={initialContent}
          readOnly={readOnly}
          onContentChange={updateDocumentContent}
        />
      </div>

      {/* O1: Render the AiSidebar component */}
      {isAiSidebarVisible && <AiSidebar />}
    </div>
  );
};

export default Editor;