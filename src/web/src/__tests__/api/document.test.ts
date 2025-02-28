import { rest } from 'msw';
import { server } from '../../mocks/server';
import {
  createDocument,
  getDocument,
  updateDocument,
  deleteDocument,
  getDocuments
} from '../../../api/document';
import { 
  Document, 
  DocumentCreateDTO, 
  DocumentUpdateDTO,
  DocumentListResponse
} from '../../../types/document';
import { API_ROUTES } from '../../../constants/api';

describe('Document API', () => {
  beforeAll(() => {
    server.listen();
  });

  afterEach(() => {
    server.resetHandlers();
  });

  afterAll(() => {
    server.close();
  });

  describe('createDocument', () => {
    it('should create a document successfully', async () => {
      const docData: DocumentCreateDTO = {
        title: 'Test Document',
        content: 'This is test content',
        tags: ['test', 'document']
      };

      const mockResponse: Document = {
        id: 'test-doc-id',
        userId: 'user-123',
        sessionId: null,
        content: docData.content,
        metadata: {
          title: docData.title,
          tags: docData.tags || [],
          createdAt: new Date(),
          updatedAt: new Date(),
          lastAccessedAt: new Date(),
          isArchived: false,
          format: 'text'
        },
        state: 'saved',
        changes: [],
        stats: {
          wordCount: 4,
          characterCount: 21,
          paragraphCount: 1,
          readingTime: 1,
          suggestionCount: 0,
          acceptedSuggestions: 0,
          rejectedSuggestions: 0,
          pendingSuggestions: 0
        },
        currentVersionId: null,
        isAnonymous: false
      };

      server.use(
        rest.post(API_ROUTES.DOCUMENTS.BASE, (req, res, ctx) => {
          return res(ctx.status(201), ctx.json(mockResponse));
        })
      );

      const result = await createDocument(docData);
      expect(result).toEqual(mockResponse);
      expect(result.metadata.title).toBe(docData.title);
      expect(result.content).toBe(docData.content);
    });

    it('should handle errors when creating a document', async () => {
      const docData: DocumentCreateDTO = {
        title: 'Test Document',
        content: 'This is test content'
      };

      server.use(
        rest.post(API_ROUTES.DOCUMENTS.BASE, (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ message: 'Server error' }));
        })
      );

      await expect(createDocument(docData)).rejects.toThrow();
    });
  });

  describe('getDocument', () => {
    it('should retrieve a document successfully', async () => {
      const docId = 'test-doc-id';

      const mockResponse: Document = {
        id: docId,
        userId: 'user-123',
        sessionId: null,
        content: 'Document content',
        metadata: {
          title: 'Test Document',
          tags: ['test'],
          createdAt: new Date(),
          updatedAt: new Date(),
          lastAccessedAt: new Date(),
          isArchived: false,
          format: 'text'
        },
        state: 'saved',
        changes: [],
        stats: {
          wordCount: 2,
          characterCount: 16,
          paragraphCount: 1,
          readingTime: 1,
          suggestionCount: 0,
          acceptedSuggestions: 0,
          rejectedSuggestions: 0,
          pendingSuggestions: 0
        },
        currentVersionId: null,
        isAnonymous: false
      };

      server.use(
        rest.get(API_ROUTES.DOCUMENTS.DOCUMENT(docId), (req, res, ctx) => {
          return res(ctx.status(200), ctx.json(mockResponse));
        })
      );

      const result = await getDocument(docId);
      expect(result).toEqual(mockResponse);
      expect(result.id).toBe(docId);
    });

    it('should handle errors when retrieving a document', async () => {
      const docId = 'nonexistent-id';

      server.use(
        rest.get(API_ROUTES.DOCUMENTS.DOCUMENT(docId), (req, res, ctx) => {
          return res(ctx.status(404), ctx.json({ message: 'Document not found' }));
        })
      );

      await expect(getDocument(docId)).rejects.toThrow();
    });
  });

  describe('updateDocument', () => {
    it('should update a document successfully', async () => {
      const docId = 'test-doc-id';
      const updateData: DocumentUpdateDTO = {
        content: 'Updated content',
        title: 'Updated Title'
      };

      const mockResponse: Document = {
        id: docId,
        userId: 'user-123',
        sessionId: null,
        content: updateData.content || '',
        metadata: {
          title: updateData.title || '',
          tags: [],
          createdAt: new Date(),
          updatedAt: new Date(),
          lastAccessedAt: new Date(),
          isArchived: false,
          format: 'text'
        },
        state: 'saved',
        changes: [],
        stats: {
          wordCount: 2,
          characterCount: 15,
          paragraphCount: 1,
          readingTime: 1,
          suggestionCount: 0,
          acceptedSuggestions: 0,
          rejectedSuggestions: 0,
          pendingSuggestions: 0
        },
        currentVersionId: null,
        isAnonymous: false
      };

      server.use(
        rest.put(API_ROUTES.DOCUMENTS.DOCUMENT(docId), (req, res, ctx) => {
          return res(ctx.status(200), ctx.json(mockResponse));
        })
      );

      const result = await updateDocument(docId, updateData);
      expect(result).toEqual(mockResponse);
      expect(result.content).toBe(updateData.content);
      expect(result.metadata.title).toBe(updateData.title);
    });

    it('should handle errors when updating a document', async () => {
      const docId = 'test-doc-id';
      const updateData: DocumentUpdateDTO = {
        content: 'Updated content'
      };

      server.use(
        rest.put(API_ROUTES.DOCUMENTS.DOCUMENT(docId), (req, res, ctx) => {
          return res(ctx.status(403), ctx.json({ message: 'Permission denied' }));
        })
      );

      await expect(updateDocument(docId, updateData)).rejects.toThrow();
    });
  });

  describe('deleteDocument', () => {
    it('should delete a document successfully', async () => {
      const docId = 'test-doc-id';

      server.use(
        rest.delete(API_ROUTES.DOCUMENTS.DOCUMENT(docId), (req, res, ctx) => {
          return res(ctx.status(204));
        })
      );

      await expect(deleteDocument(docId)).resolves.not.toThrow();
    });

    it('should handle errors when deleting a document', async () => {
      const docId = 'test-doc-id';

      server.use(
        rest.delete(API_ROUTES.DOCUMENTS.DOCUMENT(docId), (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ message: 'Server error' }));
        })
      );

      await expect(deleteDocument(docId)).rejects.toThrow();
    });
  });

  describe('getAllDocuments', () => {
    it('should retrieve all documents successfully', async () => {
      const mockDocuments = [
        {
          id: 'doc-1',
          userId: 'user-123',
          sessionId: null,
          content: 'Document 1 content',
          metadata: {
            title: 'Document 1',
            tags: ['test'],
            createdAt: new Date(),
            updatedAt: new Date(),
            lastAccessedAt: new Date(),
            isArchived: false,
            format: 'text'
          },
          state: 'saved',
          changes: [],
          stats: {
            wordCount: 3,
            characterCount: 19,
            paragraphCount: 1,
            readingTime: 1,
            suggestionCount: 0,
            acceptedSuggestions: 0,
            rejectedSuggestions: 0,
            pendingSuggestions: 0
          },
          currentVersionId: null,
          isAnonymous: false
        },
        {
          id: 'doc-2',
          userId: 'user-123',
          sessionId: null,
          content: 'Document 2 content',
          metadata: {
            title: 'Document 2',
            tags: ['test'],
            createdAt: new Date(),
            updatedAt: new Date(),
            lastAccessedAt: new Date(),
            isArchived: false,
            format: 'text'
          },
          state: 'saved',
          changes: [],
          stats: {
            wordCount: 3,
            characterCount: 19,
            paragraphCount: 1,
            readingTime: 1,
            suggestionCount: 0,
            acceptedSuggestions: 0,
            rejectedSuggestions: 0,
            pendingSuggestions: 0
          },
          currentVersionId: null,
          isAnonymous: false
        }
      ];

      const mockResponse: DocumentListResponse = {
        documents: mockDocuments,
        total: mockDocuments.length,
        page: 1,
        pageSize: 10,
        totalPages: 1
      };

      server.use(
        rest.get(API_ROUTES.DOCUMENTS.BASE, (req, res, ctx) => {
          return res(ctx.status(200), ctx.json(mockResponse));
        })
      );

      const result = await getDocuments();
      expect(result).toEqual(mockResponse);
      expect(result.documents.length).toBe(2);
      expect(result.documents[0].id).toBe('doc-1');
      expect(result.documents[1].id).toBe('doc-2');
    });

    it('should handle errors when retrieving all documents', async () => {
      server.use(
        rest.get(API_ROUTES.DOCUMENTS.BASE, (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ message: 'Server error' }));
        })
      );

      await expect(getDocuments()).rejects.toThrow();
    });
  });

  it('should handle anonymous user state', async () => {
    const docData: DocumentCreateDTO = {
      title: 'Anonymous Document',
      content: 'This is an anonymous document',
      sessionId: 'anonymous-session-123'
    };

    const mockResponse: Document = {
      id: 'anon-doc-id',
      userId: null,
      sessionId: 'anonymous-session-123',
      content: docData.content,
      metadata: {
        title: docData.title,
        tags: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        lastAccessedAt: new Date(),
        isArchived: false,
        format: 'text'
      },
      state: 'saved',
      changes: [],
      stats: {
        wordCount: 5,
        characterCount: 29,
        paragraphCount: 1,
        readingTime: 1,
        suggestionCount: 0,
        acceptedSuggestions: 0,
        rejectedSuggestions: 0,
        pendingSuggestions: 0
      },
      currentVersionId: null,
      isAnonymous: true
    };

    server.use(
      rest.post(API_ROUTES.DOCUMENTS.BASE, (req, res, ctx) => {
        return res(ctx.status(201), ctx.json(mockResponse));
      })
    );

    const result = await createDocument(docData);
    expect(result.isAnonymous).toBe(true);
    expect(result.sessionId).toBe('anonymous-session-123');
    expect(result.userId).toBeNull();
  });
});