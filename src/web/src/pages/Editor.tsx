import React, { useState, useEffect, useCallback, useRef } from 'react'; // React v18.2.0
import { useParams, useNavigate } from 'react-router-dom'; // react-router-dom v6.14.2
import { useDispatch, useSelector } from 'react-redux'; // react-redux v8.1.1

import MainLayout from '../components/layout/MainLayout';
import EditorComponent from '../components/editor/Editor';
import AiSidebar from '../components/ai/AiSidebar';
import Button from '../components/common/Button';
import Spinner from '../components/common/Spinner';
import Alert from '../components/common/Alert';
import DocumentSavePrompt from '../components/document/DocumentSavePrompt';
import useDocument from '../hooks/useDocument';
import useAi from '../hooks/useAi';
import useAuth from '../hooks/useAuth';
import { Document } from '../types/document';

/**
 * @function EditorPage
 * @description Main page component that renders the document editor with AI enhancement interface
 * @returns {JSX.Element} Rendered page component
 */
const EditorPage: React.FC = () => {
  // LD1: Get document ID from URL parameters using useParams
  const { documentId } = useParams<{ documentId: string }>();

  // LD1: Initialize state for editor loading, saving, and error states
  const [isEditorLoading, setIsEditorLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // LD1: Initialize state for save prompt visibility
  const [showSavePrompt, setShowSavePrompt] = useState(false);

  // IE3: Get authentication state from useAuth hook
  const { isAuthenticated, isAnonymous, user } = useAuth();

  // IE3: Get document functionality from useDocument hook
  const {
    document,
    documentContent,
    isLoading,
    isError,
    loadDocument,
    saveDocumentChanges,
    updateDocumentContent,
  } = useDocument(documentId);

  // IE3: Get AI functionality from useAi hook
  const {
    isProcessing,
    processingStatus,
    error: aiError,
    suggestions,
    generateSuggestion,
    acceptSuggestion,
    rejectSuggestion,
  } = useAi();

  // LD1: Use useEffect to load document when component mounts or ID changes
  useEffect(() => {
    const load = async () => {
      setIsEditorLoading(true);
      setErrorMessage(null);
      try {
        if (documentId) {
          await loadDocument(documentId);
        }
      } catch (error: any) {
        setErrorMessage(error.message || 'Failed to load document');
      } finally {
        setIsEditorLoading(false);
      }
    };

    load();
  }, [documentId, loadDocument]);

  // LD1: Implement handleDocumentChange function to update document content
  const handleDocumentChange = useCallback((content: string) => {
    updateDocumentContent(content);
  }, [updateDocumentContent]);

  // LD1: Implement handleSaveDocument function to save the current document
  const handleSaveDocument = useCallback(async (showPromptForAnonymous: boolean = false) => {
    setIsSaving(true);
    setErrorMessage(null);

    try {
      if (isAuthenticated) {
        await saveDocumentChanges();
      } else if (isAnonymous) {
        if (showPromptForAnonymous) {
          setShowSavePrompt(true);
        } else {
          // Save to local storage
          await saveDocumentChanges();
        }
      }
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to save document');
    } finally {
      setIsSaving(false);
    }
  }, [isAuthenticated, isAnonymous, saveDocumentChanges]);

  // LD1: Implement handleAcceptSuggestion function for accepting AI suggestions
  const handleAcceptSuggestion = useCallback(async (suggestionId: string) => {
    try {
      await acceptSuggestion(suggestionId);
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to accept suggestion');
    }
  }, [acceptSuggestion]);

  // LD1: Implement handleRejectSuggestion function for rejecting AI suggestions
  const handleRejectSuggestion = useCallback(async (suggestionId: string) => {
    try {
      await rejectSuggestion(suggestionId);
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to reject suggestion');
    }
  }, [rejectSuggestion]);

  // LD1: Implement handleGenerateSuggestions function to request AI improvements
  const handleGenerateSuggestions = useCallback(async () => {
    try {
      await generateSuggestion(null, null);
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to generate suggestions');
    }
  }, [generateSuggestion]);

  // LD1: Implement handleSavePromptClose function to manage save prompt visibility
  const handleSavePromptClose = useCallback(() => {
    setShowSavePrompt(false);
  }, []);

  // O1: Render MainLayout with appropriate props
  return (
    <MainLayout>
      {/* O1: Show loading spinner while document is loading */}
      {isLoading || isEditorLoading ? (
        <div className="flex justify-center items-center h-full">
          <Spinner size="lg" />
        </div>
      ) : null}

      {/* O1: Show error message if document loading failed */}
      {isError || errorMessage ? (
        <Alert variant="error" message={errorMessage || 'Failed to load document'} />
      ) : null}

      {/* O1: Render Editor component with document content and callbacks */}
      {documentContent && (
        <EditorComponent
          initialContent={documentContent}
          readOnly={false}
          onContentChange={handleDocumentChange}
        />
      )}

      {/* O1: Render AiSidebar component for AI functionality */}
      <AiSidebar />

      {/* O1: Conditionally render DocumentSavePrompt for anonymous users */}
      {isAnonymous && showSavePrompt && (
        <DocumentSavePrompt
          isOpen={showSavePrompt}
          onClose={handleSavePromptClose}
          document={document}
          onSaveSuccess={() => {}}
        />
      )}
    </MainLayout>
  );
};

export default EditorPage;