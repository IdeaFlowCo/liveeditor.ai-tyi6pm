import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Document, DocumentMetadata, DocumentVersion, ChangeStatus } from '../types/document';
import { Suggestion, SuggestionStatus, ChangeType, SuggestionType } from '../types/suggestion';
import { 
  getDocument, 
  saveDocument as saveDocumentApi, 
  listDocuments, 
  createDocument as createDocumentApi 
} from '../api/document';
import { generateTextDiff } from '../lib/diffing';
import { applyTrackChanges } from '../lib/prosemirror-track-changes';
import { ProsemirrorNode } from 'prosemirror-model';

/**
 * Interface defining the document state shape
 */
export interface DocumentState {
  document: Document | null;
  documentList: DocumentMetadata[];
  documentVersions: DocumentVersion[];
  suggestions: Suggestion[];
  loading: boolean;
  error: string | null;
  dirty: boolean;
  hasChanges: boolean;
}

/**
 * Initial state for the document slice
 */
const initialState: DocumentState = {
  document: null,
  documentList: [],
  documentVersions: [],
  suggestions: [],
  loading: false,
  error: null,
  dirty: false,
  hasChanges: false
};

/**
 * Helper function to convert DocumentChange to Suggestion
 */
const documentChangeToSuggestion = (change: any, documentId: string): Suggestion => ({
  id: change.id,
  documentId,
  changeType: change.sourceType?.includes('deletion') 
    ? ChangeType.DELETION 
    : change.sourceType?.includes('addition') 
      ? ChangeType.ADDITION 
      : ChangeType.REPLACEMENT,
  status: change.status === ChangeStatus.PENDING 
    ? SuggestionStatus.PENDING 
    : change.status === ChangeStatus.ACCEPTED 
      ? SuggestionStatus.ACCEPTED 
      : SuggestionStatus.REJECTED,
  category: SuggestionType.CUSTOM,
  position: {
    from: change.position.from,
    to: change.position.to
  },
  originalText: change.originalText,
  suggestedText: change.suggestedText,
  explanation: change.explanation || '',
  createdAt: new Date(change.timestamp)
});

/**
 * Async thunk to create a new document
 */
export const createDocument = createAsyncThunk(
  'document/createDocument',
  async (metadata: DocumentMetadata, { rejectWithValue }) => {
    try {
      const response = await createDocumentApi(metadata);
      return response;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to create document');
    }
  }
);

/**
 * Async thunk to save a document to the server
 */
export const saveDocument = createAsyncThunk(
  'document/saveDocument',
  async (document: Document, { rejectWithValue }) => {
    try {
      const response = await saveDocumentApi(document);
      return response;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to save document');
    }
  }
);

/**
 * Async thunk to fetch a document from the server
 */
export const fetchDocument = createAsyncThunk(
  'document/fetchDocument',
  async (documentId: string, { rejectWithValue }) => {
    try {
      const response = await getDocument(documentId);
      return response;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch document');
    }
  }
);

/**
 * Async thunk to fetch a list of documents for the user
 */
export const fetchDocumentList = createAsyncThunk(
  'document/fetchDocumentList',
  async (_, { rejectWithValue }) => {
    try {
      const response = await listDocuments();
      return Array.isArray(response) ? response : (response.documents || []);
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch document list');
    }
  }
);

/**
 * Document slice containing reducers and actions
 */
export const documentSlice = createSlice({
  name: 'document',
  initialState,
  reducers: {
    // Set the current document
    setDocument: (state, action: PayloadAction<Document | null>) => {
      state.document = action.payload;
      state.dirty = false;
      
      if (action.payload) {
        // Convert document changes to suggestions
        state.suggestions = action.payload.changes.map(change => 
          documentChangeToSuggestion(change, action.payload.id)
        );
        
        state.hasChanges = action.payload.changes.some(
          change => change.status === ChangeStatus.PENDING
        );
      } else {
        state.suggestions = [];
        state.hasChanges = false;
      }
    },
    
    // Update the document content
    updateContent: (state, action: PayloadAction<string>) => {
      if (state.document) {
        state.document.content = action.payload;
        state.dirty = true;
      }
    },
    
    // Add a suggestion to the document
    addSuggestion: (state, action: PayloadAction<Suggestion>) => {
      // Add to suggestions array
      state.suggestions.push(action.payload);
      
      // Also add to document changes if document exists
      if (state.document) {
        state.document.changes.push({
          id: action.payload.id,
          position: {
            from: action.payload.position.from,
            to: action.payload.position.to
          },
          originalText: action.payload.originalText,
          suggestedText: action.payload.suggestedText,
          explanation: action.payload.explanation,
          status: ChangeStatus.PENDING,
          timestamp: action.payload.createdAt,
          sourceType: action.payload.category.toString(),
          metadata: {}
        });
      }
      
      state.hasChanges = true;
      state.dirty = true;
    },
    
    // Accept a suggestion
    acceptSuggestion: (state, action: PayloadAction<string>) => {
      const suggestionIndex = state.suggestions.findIndex(s => s.id === action.payload);
      
      if (suggestionIndex >= 0 && state.document) {
        const suggestion = state.suggestions[suggestionIndex];
        
        // Update suggestion status
        state.suggestions[suggestionIndex].status = SuggestionStatus.ACCEPTED;
        
        // Update corresponding document change if it exists
        const changeIndex = state.document.changes.findIndex(c => c.id === action.payload);
        if (changeIndex >= 0) {
          state.document.changes[changeIndex].status = ChangeStatus.ACCEPTED;
        }
        
        // Apply the change to the document content
        const diffResult = generateTextDiff(suggestion.originalText, suggestion.suggestedText);
        
        if (state.document.content.includes(suggestion.originalText)) {
          state.document.content = state.document.content.replace(
            suggestion.originalText,
            suggestion.suggestedText
          );
        }
        
        // Mark document as dirty
        state.dirty = true;
        
        // Recalculate hasChanges flag
        state.hasChanges = state.suggestions.some(s => s.status === SuggestionStatus.PENDING);
      }
    },
    
    // Reject a suggestion
    rejectSuggestion: (state, action: PayloadAction<string>) => {
      const suggestionIndex = state.suggestions.findIndex(s => s.id === action.payload);
      
      if (suggestionIndex >= 0 && state.document) {
        // Update suggestion status
        state.suggestions[suggestionIndex].status = SuggestionStatus.REJECTED;
        
        // Update corresponding document change if it exists
        const changeIndex = state.document.changes.findIndex(c => c.id === action.payload);
        if (changeIndex >= 0) {
          state.document.changes[changeIndex].status = ChangeStatus.REJECTED;
        }
        
        // Recalculate hasChanges flag
        state.hasChanges = state.suggestions.some(s => s.status === SuggestionStatus.PENDING);
      }
    },
    
    // Accept all suggestions
    acceptAllSuggestions: (state) => {
      if (state.document) {
        let content = state.document.content;
        const pendingSuggestions = state.suggestions.filter(s => s.status === SuggestionStatus.PENDING);
        
        // Update all pending suggestions to accepted
        state.suggestions = state.suggestions.map(suggestion => ({
          ...suggestion,
          status: suggestion.status === SuggestionStatus.PENDING 
            ? SuggestionStatus.ACCEPTED 
            : suggestion.status
        }));
        
        // Update all pending document changes to accepted
        if (state.document) {
          state.document.changes = state.document.changes.map(change => ({
            ...change,
            status: change.status === ChangeStatus.PENDING 
              ? ChangeStatus.ACCEPTED 
              : change.status
          }));
        }
        
        // Apply all accepted suggestions to the document content
        pendingSuggestions.forEach(suggestion => {
          if (content.includes(suggestion.originalText)) {
            content = content.replace(suggestion.originalText, suggestion.suggestedText);
          }
        });
        
        state.document.content = content;
        state.dirty = true;
        state.hasChanges = false;
      }
    },
    
    // Reject all suggestions
    rejectAllSuggestions: (state) => {
      // Update all pending suggestions to rejected
      state.suggestions = state.suggestions.map(suggestion => ({
        ...suggestion,
        status: suggestion.status === SuggestionStatus.PENDING 
          ? SuggestionStatus.REJECTED 
          : suggestion.status
      }));
      
      // Update all pending document changes to rejected
      if (state.document) {
        state.document.changes = state.document.changes.map(change => ({
          ...change,
          status: change.status === ChangeStatus.PENDING 
            ? ChangeStatus.REJECTED 
            : change.status
        }));
      }
      
      state.hasChanges = false;
    },
    
    // Reset the document state
    resetDocument: (state) => {
      state.document = null;
      state.documentVersions = [];
      state.suggestions = [];
      state.dirty = false;
      state.hasChanges = false;
    },
    
    // Set the dirty flag
    setDirty: (state, action: PayloadAction<boolean>) => {
      state.dirty = action.payload;
    },
    
    // Add a new document version
    addVersion: (state, action: PayloadAction<DocumentVersion>) => {
      state.documentVersions.push(action.payload);
      
      // Update the current version ID if this is a version for the current document
      if (state.document && action.payload.documentId === state.document.id) {
        state.document.currentVersionId = action.payload.id;
      }
    }
  },
  extraReducers: (builder) => {
    // Handle async thunk states
    builder
      // Create document
      .addCase(createDocument.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createDocument.fulfilled, (state, action) => {
        state.loading = false;
        state.document = action.payload;
        
        // Convert document changes to suggestions
        state.suggestions = action.payload.changes.map(change => 
          documentChangeToSuggestion(change, action.payload.id)
        );
        
        state.dirty = false;
        state.hasChanges = action.payload.changes.some(
          change => change.status === ChangeStatus.PENDING
        );
        
        // Add to document list if not already there
        const exists = state.documentList.some(doc => doc.title === action.payload.metadata.title);
        if (!exists) {
          state.documentList.push(action.payload.metadata);
        }
      })
      .addCase(createDocument.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to create document';
      })
      
      // Save document
      .addCase(saveDocument.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(saveDocument.fulfilled, (state, action) => {
        state.loading = false;
        state.document = action.payload;
        
        // Convert document changes to suggestions
        state.suggestions = action.payload.changes.map(change => 
          documentChangeToSuggestion(change, action.payload.id)
        );
        
        state.dirty = false;
        state.hasChanges = action.payload.changes.some(
          change => change.status === ChangeStatus.PENDING
        );
        
        // Update document in the document list
        const index = state.documentList.findIndex(doc => doc.title === action.payload.metadata.title);
        if (index >= 0) {
          state.documentList[index] = action.payload.metadata;
        } else {
          state.documentList.push(action.payload.metadata);
        }
      })
      .addCase(saveDocument.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to save document';
      })
      
      // Fetch document
      .addCase(fetchDocument.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDocument.fulfilled, (state, action) => {
        state.loading = false;
        state.document = action.payload;
        
        // Convert document changes to suggestions
        state.suggestions = action.payload.changes.map(change => 
          documentChangeToSuggestion(change, action.payload.id)
        );
        
        state.dirty = false;
        state.hasChanges = action.payload.changes.some(
          change => change.status === ChangeStatus.PENDING
        );
      })
      .addCase(fetchDocument.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch document';
      })
      
      // Fetch document list
      .addCase(fetchDocumentList.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDocumentList.fulfilled, (state, action) => {
        state.loading = false;
        state.documentList = action.payload;
      })
      .addCase(fetchDocumentList.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch document list';
      });
  }
});

/**
 * Type for defining the expected Redux root state structure needed by selectors
 */
export interface AppRootState {
  document: DocumentState;
}

/**
 * Selector to get the current document from the Redux state
 */
export const selectDocument = (state: AppRootState) => state.document.document;

/**
 * Selector to get just the document content from the Redux state
 */
export const selectDocumentContent = (state: AppRootState) => 
  state.document.document?.content || null;

/**
 * Selector to get the list of document metadata from the Redux state
 */
export const selectDocumentList = (state: AppRootState) => state.document.documentList;

/**
 * Selector to get the current document suggestions from the Redux state
 */
export const selectSuggestions = (state: AppRootState) => state.document.suggestions;

/**
 * Selector to check if a document is currently loading
 */
export const selectDocumentLoading = (state: AppRootState) => state.document.loading;

// Export individual actions for direct usage
export const {
  setDocument,
  updateContent,
  addSuggestion,
  acceptSuggestion,
  rejectSuggestion,
  acceptAllSuggestions,
  rejectAllSuggestions,
  resetDocument,
  setDirty,
  addVersion
} = documentSlice.actions;

// Export the full actions object
export const actions = documentSlice.actions;

// Export reducer as default
export default documentSlice.reducer;