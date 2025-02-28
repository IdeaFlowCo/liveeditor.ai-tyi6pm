import { configureStore } from '@reduxjs/toolkit'; // @reduxjs/toolkit ^1.9.5
import { jest } from '@jest/globals'; // jest ^29.5.0
import axios from 'axios'; // axios ^1.4.0
import {
  documentReducer,
  createDocument,
  saveDocument,
  fetchDocument,
  fetchDocumentList,
  setDocument,
  updateContent,
  addSuggestion,
  acceptSuggestion,
  rejectSuggestion,
  acceptAllSuggestions,
  rejectAllSuggestions,
  resetDocument,
  setDirty,
  addVersion,
  selectDocument,
  selectDocumentContent,
  selectDocumentList,
  selectSuggestions,
  selectDocumentLoading,
} from '../../../store/slices/documentSlice';
import {
  Document,
  DocumentMetadata,
  DocumentState,
  DocumentVersion,
  DocumentChange,
  ChangeStatus,
} from '../../../types/document';
import { Suggestion } from '../../../types/suggestion';
import {
  getDocument,
  saveDocument as saveDocumentApi,
  createDocument as createDocumentApi,
  listDocuments,
} from '../../../api/document';
import { createTestStore } from '../../utils/test-utils';

// Mock the API functions
jest.mock('../../../api/document', () => ({
  getDocument: jest.fn(),
  saveDocument: jest.fn(),
  createDocument: jest.fn(),
  listDocuments: jest.fn(),
}));

// Helper function to create a mock successful document retrieval response
const mockGetDocumentSuccess = (documentId: string): Promise<Document> => {
  const mockDocument: Document = {
    id: documentId,
    userId: 'test-user',
    sessionId: null,
    content: 'Test document content',
    metadata: {
      title: 'Test Document',
      tags: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      lastAccessedAt: new Date(),
      isArchived: false,
      format: 'text',
    },
    state: DocumentState.SAVED,
    changes: [],
    currentVersionId: null,
    isAnonymous: false,
  };
  return Promise.resolve(mockDocument);
};

// Helper function to create a mock failed document retrieval response
const mockGetDocumentFailure = (documentId: string): Promise<never> => {
  return Promise.reject(new Error(`Failed to fetch document with ID ${documentId}`));
};

// Helper function to create a mock successful document save response
const mockSaveDocumentSuccess = (document: Document): Promise<Document> => {
  const savedDocument: Document = {
    ...document,
    metadata: {
      ...document.metadata,
      updatedAt: new Date(),
    },
  };
  return Promise.resolve(savedDocument);
};

// Helper function to create a mock successful document creation response
const mockCreateDocumentSuccess = (metadata: DocumentMetadata): Promise<Document> => {
  const newDocument: Document = {
    id: 'new-document-id',
    userId: 'test-user',
    sessionId: null,
    content: '',
    metadata: {
      ...metadata,
      createdAt: new Date(),
      updatedAt: new Date(),
      lastAccessedAt: new Date(),
      isArchived: false,
      format: 'text',
    },
    state: DocumentState.DRAFT,
    changes: [],
    currentVersionId: null,
    isAnonymous: false,
  };
  return Promise.resolve(newDocument);
};

// Helper function to create a mock successful document list response
const mockListDocumentsSuccess = (): Promise<Document[]> => {
  const documents: Document[] = [
    {
      id: 'doc-1',
      userId: 'test-user',
      sessionId: null,
      content: 'Test document 1 content',
      metadata: {
        title: 'Test Document 1',
        tags: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        lastAccessedAt: new Date(),
        isArchived: false,
        format: 'text',
      },
      state: DocumentState.SAVED,
      changes: [],
      currentVersionId: null,
      isAnonymous: false,
    },
    {
      id: 'doc-2',
      userId: 'test-user',
      sessionId: null,
      content: 'Test document 2 content',
      metadata: {
        title: 'Test Document 2',
        tags: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        lastAccessedAt: new Date(),
        isArchived: false,
        format: 'text',
      },
      state: DocumentState.SAVED,
      changes: [],
      currentVersionId: null,
      isAnonymous: false,
    },
  ];
  return Promise.resolve(documents);
};

// Helper function to create a mock suggestion object
const createMockSuggestion = (overrides: Partial<Suggestion> = {}): Suggestion => ({
  id: 'suggestion-1',
  documentId: 'doc-1',
  changeType: 'addition',
  status: 'pending',
  category: 'grammar',
  position: { from: 0, to: 5 },
  originalText: 'hello',
  suggestedText: 'hi',
  explanation: 'Test explanation',
  createdAt: new Date(),
  ...overrides,
});

// Helper function to create a mock document object
const createMockDocument = (overrides: Partial<Document> = {}): Document => ({
  id: 'doc-1',
  userId: 'test-user',
  sessionId: null,
  content: 'Test document content',
  metadata: {
    title: 'Test Document',
    tags: [],
    createdAt: new Date(),
    updatedAt: new Date(),
    lastAccessedAt: new Date(),
    isArchived: false,
    format: 'text',
  },
  state: DocumentState.SAVED,
  changes: [],
  currentVersionId: null,
  isAnonymous: false,
  ...overrides,
});

describe('documentSlice', () => {
  let store: any;

  beforeEach(() => {
    store = createTestStore({ document: { ...documentReducer(undefined, {} as any) } });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should handle initial state', () => {
    expect(documentReducer(undefined, {} as any)).toEqual({
      document: null,
      documentList: [],
      documentVersions: [],
      suggestions: [],
      loading: false,
      error: null,
      dirty: false,
      hasChanges: false,
    });
  });

  test('should set document and clear dirty flag', () => {
    const mockDocument = createMockDocument();
    store.dispatch(setDocument(mockDocument));
    expect(store.getState().document.document).toEqual(mockDocument);
    expect(store.getState().document.dirty).toBe(false);
  });

  test('should update content and set dirty flag', () => {
    store.dispatch(updateContent('New content'));
    expect(store.getState().document.document.content).toBe('New content');
    expect(store.getState().document.dirty).toBe(true);
  });

  test('should add a suggestion and set hasChanges flag', () => {
    const mockSuggestion = createMockSuggestion();
    store.dispatch(setDocument(createMockDocument()));
    store.dispatch(addSuggestion(mockSuggestion));
    expect(store.getState().document.suggestions).toContainEqual(mockSuggestion);
    expect(store.getState().document.hasChanges).toBe(true);
  });

  test('should accept a suggestion and update content', () => {
    const mockSuggestion = createMockSuggestion({ originalText: 'hello', suggestedText: 'hi' });
    store.dispatch(setDocument(createMockDocument({ content: 'hello world' })));
    store.dispatch(addSuggestion(mockSuggestion));
    store.dispatch(acceptSuggestion(mockSuggestion.id));
    expect(store.getState().document.document.content).toBe('hi world');
    expect(store.getState().document.suggestions[0].status).toBe('accepted');
    expect(store.getState().document.hasChanges).toBe(false);
  });

  test('should reject a suggestion', () => {
    const mockSuggestion = createMockSuggestion();
    store.dispatch(setDocument(createMockDocument()));
    store.dispatch(addSuggestion(mockSuggestion));
    store.dispatch(rejectSuggestion(mockSuggestion.id));
    expect(store.getState().document.suggestions[0].status).toBe('rejected');
    expect(store.getState().document.hasChanges).toBe(false);
  });

  test('should accept all suggestions', () => {
    const mockSuggestion1 = createMockSuggestion({ id: '1', originalText: 'hello', suggestedText: 'hi', status: 'pending' });
    const mockSuggestion2 = createMockSuggestion({ id: '2', originalText: 'world', suggestedText: 'there', status: 'pending' });
    store.dispatch(setDocument(createMockDocument({ content: 'hello world' })));
    store.dispatch(addSuggestion(mockSuggestion1));
    store.dispatch(addSuggestion(mockSuggestion2));
    store.dispatch(acceptAllSuggestions());
    expect(store.getState().document.document.content).toBe('hi there');
    expect(store.getState().document.suggestions[0].status).toBe('accepted');
    expect(store.getState().document.suggestions[1].status).toBe('accepted');
    expect(store.getState().document.hasChanges).toBe(false);
  });

  test('should reject all suggestions', () => {
    const mockSuggestion1 = createMockSuggestion({ id: '1', originalText: 'hello', suggestedText: 'hi', status: 'pending' });
    const mockSuggestion2 = createMockSuggestion({ id: '2', originalText: 'world', suggestedText: 'there', status: 'pending' });
    store.dispatch(setDocument(createMockDocument()));
    store.dispatch(addSuggestion(mockSuggestion1));
    store.dispatch(addSuggestion(mockSuggestion2));
    store.dispatch(rejectAllSuggestions());
    expect(store.getState().document.suggestions[0].status).toBe('rejected');
    expect(store.getState().document.suggestions[1].status).toBe('rejected');
    expect(store.getState().document.hasChanges).toBe(false);
  });

  test('should reset the document state', () => {
    store.dispatch(setDocument(createMockDocument()));
    store.dispatch(updateContent('New content'));
    store.dispatch(resetDocument());
    expect(store.getState().document.document).toBeNull();
    expect(store.getState().document.documentVersions).toEqual([]);
    expect(store.getState().document.suggestions).toEqual([]);
    expect(store.getState().document.dirty).toBe(false);
    expect(store.getState().document.hasChanges).toBe(false);
  });

  test('should set the dirty flag', () => {
    store.dispatch(setDirty(true));
    expect(store.getState().document.dirty).toBe(true);
    store.dispatch(setDirty(false));
    expect(store.getState().document.dirty).toBe(false);
  });

  test('should add a new document version', () => {
    const mockVersion: DocumentVersion = {
      id: 'version-1',
      documentId: 'doc-1',
      versionNumber: 1,
      content: 'Version 1 content',
      createdAt: new Date(),
      createdBy: 'test-user',
      changeDescription: 'Initial version',
      previousVersionId: null,
    };
    store.dispatch(setDocument(createMockDocument({ id: 'doc-1' })));
    store.dispatch(addVersion(mockVersion));
    expect(store.getState().document.documentVersions).toContainEqual(mockVersion);
    expect(store.getState().document.document.currentVersionId).toBe('version-1');
  });

  describe('async thunks', () => {
    test('should fetch a document successfully', async () => {
      (getDocument as jest.Mock).mockImplementation(() => mockGetDocumentSuccess('doc-1'));
      await store.dispatch(fetchDocument('doc-1'));
      expect(store.getState().document.document.id).toBe('doc-1');
      expect(store.getState().document.loading).toBe(false);
      expect(store.getState().document.error).toBeNull();
    });

    test('should handle fetch document failure', async () => {
      (getDocument as jest.Mock).mockImplementation(() => mockGetDocumentFailure('doc-1'));
      await store.dispatch(fetchDocument('doc-1'));
      expect(store.getState().document.document).toBeNull();
      expect(store.getState().document.loading).toBe(false);
      expect(store.getState().document.error).toBe('Failed to fetch document with ID doc-1');
    });

    test('should save a document successfully', async () => {
      const mockDocument = createMockDocument();
      (saveDocumentApi as jest.Mock).mockImplementation(() => mockSaveDocumentSuccess(mockDocument));
      await store.dispatch(saveDocument(mockDocument));
      expect(store.getState().document.document.id).toBe('doc-1');
      expect(store.getState().document.loading).toBe(false);
      expect(store.getState().document.error).toBeNull();
    });

    test('should create a document successfully', async () => {
      const mockMetadata: DocumentMetadata = {
        title: 'New Document',
        tags: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        lastAccessedAt: new Date(),
        isArchived: false,
        format: 'text',
      };
      (createDocumentApi as jest.Mock).mockImplementation(() => mockCreateDocumentSuccess(mockMetadata));
      await store.dispatch(createDocument(mockMetadata));
      expect(store.getState().document.document.id).toBe('new-document-id');
      expect(store.getState().document.loading).toBe(false);
      expect(store.getState().document.error).toBeNull();
    });

    test('should fetch document list successfully', async () => {
      (listDocuments as jest.Mock).mockImplementation(() => mockListDocumentsSuccess());
      await store.dispatch(fetchDocumentList());
      expect(store.getState().document.documentList.length).toBe(2);
      expect(store.getState().document.loading).toBe(false);
      expect(store.getState().document.error).toBeNull();
    });
  });

  describe('selectors', () => {
    test('selectDocument should return the document', () => {
      const mockDocument = createMockDocument();
      store.dispatch(setDocument(mockDocument));
      expect(selectDocument(store.getState())).toEqual(mockDocument);
    });

    test('selectDocumentContent should return the document content', () => {
      const mockDocument = createMockDocument({ content: 'Test content' });
      store.dispatch(setDocument(mockDocument));
      expect(selectDocumentContent(store.getState())).toBe('Test content');
    });

    test('selectDocumentList should return the document list', () => {
      const mockDocumentList = [createMockDocument()];
      (listDocuments as jest.Mock).mockImplementation(() => mockListDocumentsSuccess());
      store.dispatch(fetchDocumentList());
      expect(selectDocumentList(store.getState())).toEqual(store.getState().document.documentList);
    });

    test('selectSuggestions should return the suggestions', () => {
      const mockSuggestion = createMockSuggestion();
      store.dispatch(setDocument(createMockDocument()));
      store.dispatch(addSuggestion(mockSuggestion));
      expect(selectSuggestions(store.getState())).toEqual([mockSuggestion]);
    });

    test('selectDocumentLoading should return the loading state', () => {
      expect(selectDocumentLoading(store.getState())).toBe(false);
      store.dispatch(fetchDocument('doc-1').pending);
      expect(selectDocumentLoading(store.getState())).toBe(true);
    });
  });
});