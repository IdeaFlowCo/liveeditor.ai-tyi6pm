import { useState, useEffect, useCallback, useRef } from 'react';
import { useDispatch, useSelector } from '../store';
import { RootState } from '../store';
import {
  createDocument, fetchDocument, saveDocument, fetchDocumentList, deleteDocument,
  setDocumentContent, setDocumentTitle,
  selectDocument, selectDocumentContent, selectDocumentTitle, selectDocumentStatus, selectDocumentStats, selectDocumentList
} from '../store/slices/documentSlice';
import { Document, DocumentCreateDTO, DocumentUpdateDTO, DocumentState, AsyncStatus } from '../types/document';
import { useAuth } from './useAuth';
import useDebounce from './useDebounce';
import { saveCurrentDocument, getCurrentDocument } from '../utils/storage';
import { exportDocument, uploadDocument } from '../api/document';

/**
 * Custom React hook that provides document management functionality to components,
 * abstracting interactions with Redux state and API calls for document operations.
 * Supports both anonymous and authenticated users with features for creating,
 * editing, saving, and retrieving documents.
 * 
 * @param documentId - Optional ID of the document to load and manage
 * @returns Document state and management functions
 */
function useDocument(documentId?: string) {
  // Redux state management
  const dispatch = useDispatch();
  const { isAuthenticated, isAnonymous, user } = useAuth();
  
  // Local state
  const [isAutosaving, setIsAutosaving] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [exportProgress, setExportProgress] = useState(0);
  
  // Progress interval references for cleanup
  const uploadIntervalRef = useRef<number | null>(null);
  const exportIntervalRef = useRef<number | null>(null);
  
  // Redux selectors for document state
  const document = useSelector((state: RootState) => selectDocument(state));
  const content = useSelector((state: RootState) => selectDocumentContent(state));
  const title = useSelector((state: RootState) => selectDocumentTitle(state));
  const status = useSelector((state: RootState) => selectDocumentStatus(state));
  const stats = useSelector((state: RootState) => selectDocumentStats(state));
  const documentList = useSelector((state: RootState) => selectDocumentList(state));
  
  // Derived state
  const isLoading = status === AsyncStatus.LOADING;
  const isError = status === AsyncStatus.ERROR;
  const isSaving = status === AsyncStatus.LOADING && document?.id === documentId;
  
  // Helper to clean up progress intervals
  const clearProgressIntervals = () => {
    if (uploadIntervalRef.current) {
      clearInterval(uploadIntervalRef.current);
      uploadIntervalRef.current = null;
    }
    if (exportIntervalRef.current) {
      clearInterval(exportIntervalRef.current);
      exportIntervalRef.current = null;
    }
  };
  
  /**
   * Creates a new document with the provided title and content
   */
  const createNewDocument = useCallback(async (title: string, content: string = '') => {
    try {
      const documentData: DocumentCreateDTO = {
        title,
        content,
        tags: [],
        sessionId: isAnonymous && user ? (user as AnonymousUser).sessionId : undefined
      };
      
      const result = await dispatch(createDocument(documentData)).unwrap();
      return result;
    } catch (error) {
      console.error('Error creating document:', error);
      throw error;
    }
  }, [dispatch, isAnonymous, user]);
  
  /**
   * Loads a document by its ID
   */
  const loadDocument = useCallback(async (id: string) => {
    try {
      const result = await dispatch(fetchDocument(id)).unwrap();
      return result;
    } catch (error) {
      console.error('Error loading document:', error);
      throw error;
    }
  }, [dispatch]);
  
  /**
   * Saves the current document changes
   */
  const saveDocumentChanges = useCallback(async () => {
    if (!document) return null;
    
    try {
      setIsAutosaving(true);
      const documentData: DocumentUpdateDTO = {
        content: content,
        title: title
      };
      
      const result = await dispatch(saveDocument({ 
        id: document.id, 
        ...documentData 
      })).unwrap();
      
      return result;
    } catch (error) {
      console.error('Error saving document:', error);
      throw error;
    } finally {
      setIsAutosaving(false);
    }
  }, [dispatch, document, content, title]);
  
  /**
   * Updates the document content in Redux
   */
  const updateDocumentContent = useCallback((newContent: string) => {
    dispatch(setDocumentContent(newContent));
  }, [dispatch]);
  
  /**
   * Updates the document title in Redux
   */
  const updateDocumentTitle = useCallback((newTitle: string) => {
    dispatch(setDocumentTitle(newTitle));
  }, [dispatch]);
  
  /**
   * Deletes the current document
   */
  const deleteCurrentDocument = useCallback(async () => {
    if (!document) return;
    
    try {
      await dispatch(deleteDocument(document.id)).unwrap();
      return true;
    } catch (error) {
      console.error('Error deleting document:', error);
      throw error;
    }
  }, [dispatch, document]);
  
  /**
   * Uploads a document file
   */
  const uploadDocumentFile = useCallback(async (file: File) => {
    clearProgressIntervals();
    
    try {
      // Simulate upload progress since the API doesn't provide it
      setUploadProgress(10);
      uploadIntervalRef.current = window.setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            if (uploadIntervalRef.current) {
              clearInterval(uploadIntervalRef.current);
              uploadIntervalRef.current = null;
            }
            return prev;
          }
          return prev + 10;
        });
      }, 300);
      
      // Upload the file with metadata
      const result = await uploadDocument(file, {
        title: file.name
      });
      
      // Clean up interval and complete progress
      if (uploadIntervalRef.current) {
        clearInterval(uploadIntervalRef.current);
        uploadIntervalRef.current = null;
      }
      
      setUploadProgress(100);
      setTimeout(() => setUploadProgress(0), 1000);
      
      return result;
    } catch (error) {
      if (uploadIntervalRef.current) {
        clearInterval(uploadIntervalRef.current);
        uploadIntervalRef.current = null;
      }
      setUploadProgress(0);
      console.error('Error uploading document:', error);
      throw error;
    }
  }, []);
  
  /**
   * Exports the document to a specified format
   */
  const exportDocumentTo = useCallback(async (format: string) => {
    if (!document) return null;
    
    clearProgressIntervals();
    
    try {
      // Simulate export progress since the API doesn't provide it
      setExportProgress(10);
      exportIntervalRef.current = window.setInterval(() => {
        setExportProgress(prev => {
          if (prev >= 90) {
            if (exportIntervalRef.current) {
              clearInterval(exportIntervalRef.current);
              exportIntervalRef.current = null;
            }
            return prev;
          }
          return prev + 10;
        });
      }, 200);
      
      // Export the document
      const blob = await exportDocument(document.id, format);
      
      // Clean up interval and complete progress
      if (exportIntervalRef.current) {
        clearInterval(exportIntervalRef.current);
        exportIntervalRef.current = null;
      }
      
      setExportProgress(100);
      
      // Create and trigger download
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${document.title || 'document'}.${format.toLowerCase()}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setTimeout(() => setExportProgress(0), 1000);
      
      return true;
    } catch (error) {
      if (exportIntervalRef.current) {
        clearInterval(exportIntervalRef.current);
        exportIntervalRef.current = null;
      }
      setExportProgress(0);
      console.error('Error exporting document:', error);
      throw error;
    }
  }, [document]);
  
  // Debounce content changes to avoid excessive saves
  const debouncedContent = useDebounce(content, 1000);
  
  // Load document when ID changes
  useEffect(() => {
    if (documentId) {
      loadDocument(documentId).catch(error => {
        console.error('Failed to load document:', error);
      });
    }
  }, [documentId, loadDocument]);
  
  // Set up autosave for content changes
  useEffect(() => {
    if (!document || !debouncedContent) return;
    
    // Only save if content has changed from the original
    if (debouncedContent !== document.content) {
      const saveChanges = async () => {
        try {
          await saveDocumentChanges();
        } catch (error) {
          console.error('Autosave failed:', error);
        }
      };
      
      // Only autosave for authenticated users or anonymous users with existing documents
      if (isAuthenticated || (isAnonymous && document.id)) {
        saveChanges();
      }
    }
  }, [debouncedContent, document, isAuthenticated, isAnonymous, saveDocumentChanges]);
  
  // Load document list for authenticated users
  useEffect(() => {
    if (isAuthenticated) {
      const fetchDocuments = async () => {
        try {
          await dispatch(fetchDocumentList());
        } catch (error) {
          console.error('Failed to fetch document list:', error);
        }
      };
      
      fetchDocuments();
    }
  }, [isAuthenticated, dispatch]);
  
  // Handle local storage for anonymous users
  useEffect(() => {
    if (isAnonymous && document) {
      // Save current document to browser storage for anonymous users
      saveCurrentDocument(document, false);
    }
    
    // For authenticated users without a current document, check local storage
    if (isAuthenticated && !document && !documentId) {
      const localDocument = getCurrentDocument();
      if (localDocument) {
        updateDocumentContent(localDocument.content);
        updateDocumentTitle(localDocument.title || 'Untitled Document');
      }
    }
  }, [isAnonymous, isAuthenticated, document, documentId, updateDocumentContent, updateDocumentTitle]);
  
  // Clean up on unmount
  useEffect(() => {
    return () => {
      clearProgressIntervals();
    };
  }, []);
  
  return {
    // Document state
    document,
    documentContent: content,
    documentTitle: title,
    documentStats: stats,
    documentList,
    status,
    isLoading,
    isError,
    isSaving,
    isAutosaving,
    uploadProgress,
    exportProgress,
    
    // Document methods
    createNewDocument,
    loadDocument,
    saveDocumentChanges,
    updateDocumentContent,
    updateDocumentTitle,
    deleteCurrentDocument,
    uploadDocumentFile,
    exportDocumentTo
  };
}

export default useDocument;