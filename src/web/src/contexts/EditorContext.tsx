import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  ReactNode,
} from 'react'; // react v18.2.0
import { EditorState, Transaction } from 'prosemirror-state'; // prosemirror-state v1.4.1
import { EditorView } from 'prosemirror-view'; // prosemirror-view v1.28.1
import { Schema } from 'prosemirror-model'; // prosemirror-model v1.18.1
import { v4 as uuidv4 } from 'uuid'; // uuid v8.3.2
import { Document, Suggestion, AiPromptTemplate } from '../types';
import { useDocument } from '../hooks/useDocument';
import { useAi } from '../hooks/useAi';
import { createEditorState as initializeEditorState } from '../components/editor/prosemirror/setup';
import { schema } from '../components/editor/prosemirror/schema';
import { trackChangesPlugin } from '../lib/prosemirror-track-changes';
import { applyTrackChanges } from '../lib/prosemirror-track-changes/track-changes';
import { diffToChanges } from '../lib/diffing';

/**
 * Type definition for the editor context value.
 * This context provides access to the ProseMirror editor state, view, document data,
 * AI suggestions, and methods for manipulating the editor.
 */
interface EditorContextType {
  editorState: EditorState;
  editorView: EditorView | null;
  document: Document | null;
  suggestions: Suggestion[];
  currentSuggestion: Suggestion | null;
  isLoading: boolean;
  isProcessingAi: boolean;
  error: string | null;
  setEditorView: (view: EditorView | null) => void;
  updateEditorState: (state: EditorState) => void;
  loadDocument: (documentId: string) => Promise<void>;
  saveDocument: () => Promise<void>;
  createDocument: (title: string, content: string) => Promise<void>;
  requestAiSuggestions: () => Promise<void>;
  acceptSuggestion: (suggestionId: string) => Promise<void>;
  rejectSuggestion: (suggestionId: string) => Promise<void>;
  acceptAllSuggestions: () => Promise<void>;
  rejectAllSuggestions: () => Promise<void>;
  getSelectedText: () => string;
  setCurrentSuggestion: (suggestion: Suggestion | null) => void;
  getDocumentContent: () => string;
  trackChanges: {
    enabled: boolean;
    toggle: () => void;
  };
}

/**
 * Create the editor context with a default value.
 * The actual context value will be provided by the EditorProvider.
 */
export const EditorContext = createContext<EditorContextType>({
  editorState: initializeEditorState(),
  editorView: null,
  document: null,
  suggestions: [],
  currentSuggestion: null,
  isLoading: false,
  isProcessingAi: false,
  error: null,
  setEditorView: () => {},
  updateEditorState: () => {},
  loadDocument: async () => {},
  saveDocument: async () => {},
  createDocument: async () => {},
  requestAiSuggestions: async () => {},
  acceptSuggestion: async () => {},
  rejectSuggestion: async () => {},
  acceptAllSuggestions: async () => {},
  rejectAllSuggestions: async () => {},
  getSelectedText: () => '',
  setCurrentSuggestion: () => {},
  getDocumentContent: () => '',
  trackChanges: {
    enabled: true,
    toggle: () => {},
  },
});

/**
 * EditorProvider component that provides the editor context to its children.
 * This component manages the ProseMirror editor state, view, document data,
 * AI suggestions, and methods for manipulating the editor.
 */
export const EditorProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [editorView, setEditorView] = useState<EditorView | null>(null);
  const [editorState, setEditorState] = useState<EditorState>(initializeEditorState());
  const [currentSuggestion, setCurrentSuggestion] = useState<Suggestion | null>(null);
  const [trackChangesEnabled, setTrackChangesEnabled] = useState(true);

  const {
    document,
    documentContent,
    status,
    isLoading,
    isError,
    saveDocumentChanges,
    updateDocumentContent,
  } = useDocument();

  const { generateSuggestion, isProcessing: isProcessingAi, clearSuggestions } = useAi();

  /**
   * Toggles track changes functionality
   */
  const toggleTrackChanges = useCallback(() => {
    setTrackChangesEnabled(prev => !prev);
  }, []);

  /**
   * Loads a document by its ID and updates the editor state with the document content.
   */
  const loadDocument = useCallback(
    async (documentId: string) => {
      // TODO: Implement load document logic
      console.log('Loading document:', documentId);
    },
    []
  );

  /**
   * Saves the current document content.
   */
  const saveDocument = useCallback(async () => {
    if (document) {
      await saveDocumentChanges();
    }
  }, [document, saveDocumentChanges]);

  /**
   * Creates a new document with the given title and content.
   */
  const createDocument = useCallback(async (title: string, content: string) => {
    // TODO: Implement create document logic
    console.log('Creating document:', title, content);
  }, []);

  /**
   * Requests AI suggestions for the current document content.
   */
  const requestAiSuggestions = useCallback(async () => {
    // TODO: Implement request AI suggestions logic
    console.log('Requesting AI suggestions');
    await generateSuggestion(null, null);
  }, [generateSuggestion]);

  /**
   * Accepts a suggestion and applies it to the document.
   */
  const acceptSuggestion = useCallback(async (suggestionId: string) => {
    // TODO: Implement accept suggestion logic
    console.log('Accepting suggestion:', suggestionId);
  }, []);

  /**
   * Rejects a suggestion and removes it from the document.
   */
  const rejectSuggestion = useCallback(async (suggestionId: string) => {
    // TODO: Implement reject suggestion logic
    console.log('Rejecting suggestion:', suggestionId);
  }, []);

  /**
   * Accepts all suggestions in the document.
   */
  const acceptAllSuggestions = useCallback(async () => {
    // TODO: Implement accept all suggestions logic
    console.log('Accepting all suggestions');
  }, []);

  /**
   * Rejects all suggestions in the document.
   */
  const rejectAllSuggestions = useCallback(async () => {
    // TODO: Implement reject all suggestions logic
    console.log('Rejecting all suggestions');
  }, []);

  /**
   * Gets the currently selected text in the editor.
   */
  const getSelectedText = useCallback(() => {
    return editorView?.state.doc.cut(editorView.state.selection.from, editorView.state.selection.to).textContent || '';
  }, [editorView]);

  /**
   * Gets the document content from the editor state.
   */
  const getDocumentContent = useCallback(() => {
    return editorState.doc.textContent;
  }, [editorState]);

  // Provide the context value
  const contextValue: EditorContextType = {
    editorState,
    editorView,
    document,
    suggestions: [], // TODO: Implement suggestions
    currentSuggestion,
    isLoading,
    isProcessingAi,
    error: isError ? 'Failed to load document' : null,
    setEditorView,
    updateEditorState: setEditorState,
    loadDocument,
    saveDocument,
    createDocument,
    requestAiSuggestions,
    acceptSuggestion,
    rejectSuggestion,
    acceptAllSuggestions,
    rejectAllSuggestions,
    getSelectedText,
    setCurrentSuggestion,
    getDocumentContent,
    trackChanges: {
      enabled: trackChangesEnabled,
      toggle: toggleTrackChanges,
    },
  };

  return (
    <EditorContext.Provider value={contextValue}>
      {children}
    </EditorContext.Provider>
  );
};

/**
 * Custom hook to access the EditorContext within components
 */
export function useEditorContext(): EditorContextType {
  // Retrieve the current context using useContext(EditorContext)
  const context = useContext(EditorContext);

  // Check if context exists, throw error if trying to use outside provider
  if (!context) {
    throw new Error('useEditorContext must be used within an EditorProvider');
  }

  // Return the context object for component consumption
  return context;
}