// msw: ^1.0.0
import { rest, ResponseResolver, RequestHandler } from 'msw';
import { LoginResponse, Document, SuggestionResponse } from '../../types';
import { API_ROUTES } from '../../constants/api';

/**
 * Mock handler for user login authentication requests
 * @returns MSW request handler for the login endpoint
 */
export const authLoginHandler: () => RequestHandler = () => {
  // Create a REST POST handler for the API_ROUTES.AUTH.LOGIN endpoint
  return rest.post(API_ROUTES.AUTH.LOGIN, ((req, res, ctx) => {
    // Parse the request body for email and password
    const { email, password } = req.body as any;

    // Return a mocked successful response with user data and JWT token
    return res(
      ctx.status(200), // Include response status 200 for successful authentication
      ctx.json<LoginResponse>({
        user: {
          id: 'user-123',
          email: email,
          firstName: 'Test',
          lastName: 'User',
          profileImage: null,
          role: 'user',
          emailVerified: true,
          createdAt: new Date().toISOString(),
          lastLoginAt: new Date().toISOString(),
          preferences: null,
          isAnonymous: false,
        },
        token: 'mocked-jwt-token',
        refreshToken: 'mocked-refresh-token',
        expiresIn: 3600,
      })
    );
  }) as ResponseResolver);
};

/**
 * Mock handler for user registration requests
 * @returns MSW request handler for the register endpoint
 */
export const authRegisterHandler: () => RequestHandler = () => {
  // Create a REST POST handler for the API_ROUTES.AUTH.REGISTER endpoint
  return rest.post(API_ROUTES.AUTH.REGISTER, ((req, res, ctx) => {
    // Parse the request body for user registration data
    const { email, password, firstName, lastName } = req.body as any;

    // Return a mocked successful response with created user data
    return res(
      ctx.status(201), // Include response status 201 for successful user creation
      ctx.json({
        user: {
          id: 'new-user-456',
          email: email,
          firstName: firstName,
          lastName: lastName,
          profileImage: null,
          role: 'user',
          emailVerified: false,
          createdAt: new Date().toISOString(),
          lastLoginAt: null,
          preferences: null,
          isAnonymous: false,
        },
        token: 'mocked-jwt-token',
        refreshToken: 'mocked-refresh-token',
        expiresIn: 3600,
      })
    );
  }) as ResponseResolver);
};

/**
 * Mock handler for retrieving a list of user documents
 * @returns MSW request handler for the documents list endpoint
 */
export const documentsListHandler: () => RequestHandler = () => {
  // Create a REST GET handler for the API_ROUTES.DOCUMENTS.LIST endpoint
  return rest.get(API_ROUTES.DOCUMENTS.BASE, ((req, res, ctx) => {
    // Generate an array of mock document objects
    const documents: Document[] = [
      {
        id: 'doc-1',
        userId: 'user-123',
        sessionId: null,
        content: 'This is a mock document 1.',
        metadata: {
          title: 'Mock Document 1',
          tags: ['mock', 'test'],
          createdAt: new Date(),
          updatedAt: new Date(),
          lastAccessedAt: new Date(),
          isArchived: false,
          format: 'text',
        },
        state: 'saved',
        changes: [],
        stats: {
          wordCount: 5,
          characterCount: 30,
          paragraphCount: 1,
          readingTime: 1,
          suggestionCount: 0,
          acceptedSuggestions: 0,
          rejectedSuggestions: 0,
          pendingSuggestions: 0,
        },
        currentVersionId: null,
        isAnonymous: false,
      },
      {
        id: 'doc-2',
        userId: 'user-123',
        sessionId: null,
        content: 'This is a mock document 2.',
        metadata: {
          title: 'Mock Document 2',
          tags: ['mock', 'test'],
          createdAt: new Date(),
          updatedAt: new Date(),
          lastAccessedAt: new Date(),
          isArchived: false,
          format: 'text',
        },
        state: 'saved',
        changes: [],
         stats: {
          wordCount: 5,
          characterCount: 30,
          paragraphCount: 1,
          readingTime: 1,
          suggestionCount: 0,
          acceptedSuggestions: 0,
          rejectedSuggestions: 0,
          pendingSuggestions: 0,
        },
        currentVersionId: null,
        isAnonymous: false,
      },
    ];

    // Return the documents array with 200 status code
    return res(
      ctx.status(200),
      ctx.json({
        documents: documents,
        total: documents.length,
        page: 1,
        pageSize: 10,
        totalPages: 1,
      })
    ); // Include pagination metadata if requested
  }) as ResponseResolver);
};

/**
 * Mock handler for retrieving a single document by ID
 * @returns MSW request handler for the document get endpoint
 */
export const documentsGetHandler: () => RequestHandler = () => {
  // Create a REST GET handler for the API_ROUTES.DOCUMENTS.GET endpoint
  return rest.get(API_ROUTES.DOCUMENTS.DOCUMENT(':id'), ((req, res, ctx) => {
    // Extract document ID from the URL path parameters
    const { id } = req.params;

    // Return a mock document matching the requested ID
    if (id === 'doc-1') {
      return res(
        ctx.status(200),
        ctx.json<Document>({
          id: 'doc-1',
          userId: 'user-123',
          sessionId: null,
          content: 'This is a mock document 1.',
          metadata: {
            title: 'Mock Document 1',
            tags: ['mock', 'test'],
            createdAt: new Date(),
            updatedAt: new Date(),
            lastAccessedAt: new Date(),
            isArchived: false,
            format: 'text',
          },
          state: 'saved',
          changes: [],
           stats: {
          wordCount: 5,
          characterCount: 30,
          paragraphCount: 1,
          readingTime: 1,
          suggestionCount: 0,
          acceptedSuggestions: 0,
          rejectedSuggestions: 0,
          pendingSuggestions: 0,
        },
          currentVersionId: null,
          isAnonymous: false,
        })
      );
    } else {
      // Return 404 status code if document ID is not found
      return res(ctx.status(404));
    }
  }) as ResponseResolver);
};

/**
 * Mock handler for creating a new document
 * @returns MSW request handler for the document creation endpoint
 */
export const documentsCreateHandler: () => RequestHandler = () => {
  // Create a REST POST handler for the API_ROUTES.DOCUMENTS.CREATE endpoint
  return rest.post(API_ROUTES.DOCUMENTS.BASE, ((req, res, ctx) => {
    // Parse the request body for document data
    const { title, content } = req.body as any;

    // Generate a new document with unique ID
    const newDocument: Document = {
      id: 'new-doc-789',
      userId: 'user-123',
      sessionId: null,
      content: content,
      metadata: {
        title: title,
        tags: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        lastAccessedAt: new Date(),
        isArchived: false,
        format: 'text',
      },
      state: 'saved',
      changes: [],
       stats: {
          wordCount: 5,
          characterCount: 30,
          paragraphCount: 1,
          readingTime: 1,
          suggestionCount: 0,
          acceptedSuggestions: 0,
          rejectedSuggestions: 0,
          pendingSuggestions: 0,
        },
      currentVersionId: null,
      isAnonymous: false,
    };

    // Return the created document with 201 status code
    return res(ctx.status(201), ctx.json(newDocument));
  }) as ResponseResolver);
};

/**
 * Mock handler for updating an existing document
 * @returns MSW request handler for the document update endpoint
 */
export const documentsSaveHandler: () => RequestHandler = () => {
  // Create a REST PUT handler for the API_ROUTES.DOCUMENTS.UPDATE endpoint
  return rest.put(API_ROUTES.DOCUMENTS.DOCUMENT(':id'), ((req, res, ctx) => {
    // Extract document ID from the URL path parameters
    const { id } = req.params;

    // Parse the request body for updated document data
    const { content, title } = req.body as any;

    // Return the updated document with 200 status code
    return res(
      ctx.status(200),
      ctx.json<Document>({
        id: id as string,
        userId: 'user-123',
        sessionId: null,
        content: content,
        metadata: {
          title: title,
          tags: [],
          createdAt: new Date(),
          updatedAt: new Date(),
          lastAccessedAt: new Date(),
          isArchived: false,
          format: 'text',
        },
        state: 'saved',
        changes: [],
         stats: {
          wordCount: 5,
          characterCount: 30,
          paragraphCount: 1,
          readingTime: 1,
          suggestionCount: 0,
          acceptedSuggestions: 0,
          rejectedSuggestions: 0,
          pendingSuggestions: 0,
        },
        currentVersionId: null,
        isAnonymous: false,
      })
    );
  }) as ResponseResolver);
};

/**
 * Mock handler for generating AI suggestions for document improvement
 * @returns MSW request handler for the suggestions endpoint
 */
export const suggestionsHandler: () => RequestHandler = () => {
  // Create a REST POST handler for the API_ROUTES.SUGGESTIONS.GENERATE endpoint
  return rest.post(API_ROUTES.SUGGESTIONS.BASE, ((req, res, ctx) => {
    // Parse the request body for document content and improvement type
    const { content, promptType } = req.body as any;

    // Generate mock AI suggestions in track changes format
    const suggestions = [
      {
        id: 'suggestion-1',
        originalText: 'needs to',
        suggestedText: 'should',
        explanation: 'More professional tone',
        position: {
          start: 14,
          end: 23,
        },
      },
      {
        id: 'suggestion-2',
        originalText: 'make sure to',
        suggestedText: 'ensure',
        explanation: 'More concise wording',
        position: {
          start: 40,
          end: 52,
        },
      },
    ];

    // Return suggestions with 200 status code
    return res(
      ctx.status(200),
      ctx.json<SuggestionResponse>({
        suggestions: suggestions,
        suggestionGroupId: 'group-1',
        promptUsed: promptType,
        processingTime: 150,
      })
    );
  }) as ResponseResolver);
};

/**
 * Mock handler for AI chat interactions
 * @returns MSW request handler for the chat endpoint
 */
export const chatHandler: () => RequestHandler = () => {
  // Create a REST POST handler for the API_ROUTES.CHAT.SEND endpoint
  return rest.post(API_ROUTES.CHAT.MESSAGE, ((req, res, ctx) => {
    // Parse the request body for user message and context
    const { message } = req.body as any;

    // Generate a mock AI response message
    const aiResponse = `Mock AI response to: ${message}`;

    // Return the response with 200 status code
    return res(
      ctx.status(200),
      ctx.json({
        response: aiResponse,
      })
    );
  }) as ResponseResolver);
};

/**
 * Mock handler for retrieving AI improvement templates
 * @returns MSW request handler for the templates endpoint
 */
export const templatesHandler: () => RequestHandler = () => {
  // Create a REST GET handler for the API_ROUTES.TEMPLATES.LIST endpoint
  return rest.get(API_ROUTES.TEMPLATES.BASE, ((req, res, ctx) => {
    // Generate an array of mock improvement templates
    const templates = [
      {
        id: 'template-1',
        name: 'Make it shorter',
        description: 'Condense the text to be more concise.',
        promptText: 'Make this shorter.',
        category: 'general',
        isSystem: true,
        icon: 'shorten',
        templateType: 'shorter',
      },
      {
        id: 'template-2',
        name: 'More professional',
        description: 'Adjust the tone to be more professional.',
        promptText: 'Make this more professional.',
        category: 'general',
        isSystem: true,
        icon: 'professional',
        templateType: 'professional',
      },
    ];

    // Return the templates array with 200 status code
    return res(
      ctx.status(200),
      ctx.json(templates)
    );
  }) as ResponseResolver);
};

/**
 * Array of MSW request handlers to mock API endpoints for testing
 */
export const handlers: RequestHandler[] = [
  authLoginHandler(),
  authRegisterHandler(),
  documentsListHandler(),
  documentsGetHandler(),
  documentsCreateHandler(),
  documentsSaveHandler(),
  suggestionsHandler(),
  chatHandler(),
  templatesHandler(),
];