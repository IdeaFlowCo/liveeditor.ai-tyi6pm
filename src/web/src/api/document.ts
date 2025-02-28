/**
 * API module providing functions for document operations.
 * 
 * This module acts as the interface between frontend React components and the backend
 * document service, supporting both anonymous and authenticated users with features for
 * document retrieval, creation, updates, and management.
 *
 * @version 1.0.0
 */

import { get, post, put, delete as del } from '../utils/api';
import { API_ROUTES } from '../constants/api';
import { 
  Document, 
  DocumentCreateDTO, 
  DocumentUpdateDTO, 
  DocumentListResponse,
  DocumentFormat 
} from '../types/document';
import { handleApiError } from '../utils/error-handling';

/**
 * Retrieves a list of documents for the authenticated user or from the anonymous session
 * 
 * @param params - Optional query parameters for filtering, pagination, and sorting
 * @returns Promise resolving to a list of documents with pagination metadata
 */
export const getDocuments = async (params?: object): Promise<DocumentListResponse> => {
  try {
    const response = await get<DocumentListResponse>(API_ROUTES.DOCUMENTS.BASE, params);
    return response;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Retrieves a specific document by its ID
 * 
 * @param id - Unique identifier of the document to retrieve
 * @returns Promise resolving to the document data
 */
export const getDocument = async (id: string): Promise<Document> => {
  try {
    const response = await get<Document>(API_ROUTES.DOCUMENTS.DOCUMENT(id));
    return response;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Creates a new document with the provided content and metadata
 * 
 * @param documentData - Data for the new document
 * @returns Promise resolving to the newly created document
 */
export const createDocument = async (documentData: DocumentCreateDTO): Promise<Document> => {
  try {
    const response = await post<Document>(API_ROUTES.DOCUMENTS.BASE, documentData);
    return response;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Updates an existing document with new content or metadata
 * 
 * @param id - Unique identifier of the document to update
 * @param documentData - Updated data for the document
 * @returns Promise resolving to the updated document
 */
export const updateDocument = async (id: string, documentData: DocumentUpdateDTO): Promise<Document> => {
  try {
    const response = await put<Document>(API_ROUTES.DOCUMENTS.DOCUMENT(id), documentData);
    return response;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Deletes a document by its ID
 * 
 * @param id - Unique identifier of the document to delete
 * @returns Promise resolving when the document is successfully deleted
 */
export const deleteDocument = async (id: string): Promise<void> => {
  try {
    await del(API_ROUTES.DOCUMENTS.DOCUMENT(id));
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Exports a document to a specified format (e.g., PDF, DOCX)
 * 
 * @param id - Unique identifier of the document to export
 * @param format - Target format for the export
 * @returns Promise resolving to a Blob containing the exported document
 */
export const exportDocument = async (id: string, format: DocumentFormat): Promise<Blob> => {
  try {
    const url = `${API_ROUTES.DOCUMENTS.DOCUMENT(id)}/export`;
    const response = await get<Blob>(url, { format }, { responseType: 'blob' });
    return response;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Uploads a document file to create a new document
 * 
 * @param file - The file to upload
 * @param metadata - Optional metadata for the document
 * @returns Promise resolving to the created document from the uploaded file
 */
export const uploadDocument = async (file: File, metadata?: object): Promise<Document> => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }
    
    const url = `${API_ROUTES.DOCUMENTS.BASE}/upload`;
    const response = await post<Document>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    return response;
  } catch (error) {
    throw handleApiError(error);
  }
};