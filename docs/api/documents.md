# Document API Documentation

This document provides a comprehensive reference for the document management API endpoints in the AI writing enhancement platform. These endpoints enable document creation, retrieval, updating, versioning, and management for both anonymous and authenticated users.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [List Documents](#list-documents)
  - [Create Document](#create-document)
  - [Get Document](#get-document)
  - [Update Document](#update-document)
  - [Delete Document](#delete-document)
  - [Document Versions](#document-versions)
  - [Restore Document Version](#restore-document-version)
  - [Compare Document Versions](#compare-document-versions)
  - [Export Document](#export-document)
  - [Import Document](#import-document)
  - [Transfer Anonymous Document](#transfer-anonymous-document)
- [Schemas](#schemas)
  - [Document Schema](#document-schema)
  - [Document Version Schema](#document-version-schema)
  - [Document Change Schema](#document-change-schema)
  - [Request Schemas](#request-schemas)
  - [Response Schemas](#response-schemas)
- [Common Flows](#common-flows)
  - [Anonymous Document Flow](#anonymous-document-flow)
  - [Document Versioning Flow](#document-versioning-flow)
  - [Track Changes Flow](#track-changes-flow)
- [Error Handling](#error-handling)

## Overview

The Document API provides the foundation for the AI writing enhancement platform, enabling users to create, edit, and manage documents with or without authentication. The API supports:

- Anonymous document creation and editing with session-based storage
- Authenticated user document management with cloud storage
- Document versioning and history tracking
- Track changes functionality for AI suggestions
- Multiple format import/export

## Authentication

Endpoints have varying authentication requirements:

- **Anonymous Access**: Some endpoints can be accessed without authentication, using session-based identification
- **Authenticated Access**: Most endpoints require a valid JWT token in the Authorization header
- **Owner-only Operations**: Some operations require the authenticated user to be the document owner

**Authentication Header Format:**
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### List Documents

Returns a paginated list of documents owned by the authenticated user.

**Endpoint:** `GET /api/documents`

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number |
| limit | integer | 20 | Items per page (max 100) |
| sort | string | "updatedAt" | Field to sort by (options: "title", "createdAt", "updatedAt") |
| order | string | "desc" | Sort order (options: "asc", "desc") |
| search | string | null | Search term for document title/content |
| tags | string | null | Comma-separated list of tags to filter by |

**Success Response:**

`200 OK`
```json
{
  "documents": [
    {
      "id": "60d21b4667d0d8992e610c85",
      "title": "Project Proposal",
      "createdAt": "2023-03-15T18:23:45Z",
      "updatedAt": "2023-03-17T09:12:30Z",
      "tags": ["business", "proposal"],
      "wordCount": 1250,
      "currentVersionId": "60d21b4667d0d8992e610c87"
    },
    // Additional documents...
  ],
  "pagination": {
    "totalDocuments": 28,
    "totalPages": 2,
    "currentPage": 1,
    "limit": 20
  }
}
```

**Error Responses:**

`401 Unauthorized` - Missing or invalid authentication token
`403 Forbidden` - Insufficient permissions to access the resource
`500 Internal Server Error` - Server-side error

**Example Request:**

```bash
curl -X GET "https://api.aiwriting.app/api/documents?page=1&limit=20&sort=updatedAt&order=desc" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**JavaScript Example:**

```javascript
async function getDocuments() {
  const response = await fetch('https://api.aiwriting.app/api/documents?page=1&limit=20', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error ${response.status}`);
  }
  
  const data = await response.json();
  console.log(data.documents);
}
```

### Create Document

Creates a new document. Supports both anonymous and authenticated creation.

**Endpoint:** `POST /api/documents`

**Authentication:** Optional

**Request Body:**

```json
{
  "title": "My New Document",
  "content": "The content of the document goes here...",
  "tags": ["draft", "personal"],
  "sessionId": "anonymous-session-id" // Required only for anonymous users
}
```

**Success Response:**

`201 Created`
```json
{
  "document": {
    "id": "60d21b4667d0d8992e610c85",
    "title": "My New Document",
    "content": "The content of the document goes here...",
    "createdAt": "2023-03-15T18:23:45Z",
    "updatedAt": "2023-03-15T18:23:45Z",
    "tags": ["draft", "personal"],
    "userId": "auth0|123456789" // null for anonymous documents
  }
}
```

**Error Responses:**

`400 Bad Request` - Invalid document format or missing required fields
`401 Unauthorized` - Invalid authentication token (if provided)
`500 Internal Server Error` - Server-side error

**Example Request:**

```bash
# For authenticated user
curl -X POST "https://api.aiwriting.app/api/documents" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"title":"My New Document","content":"The content of the document goes here...","tags":["draft","personal"]}'

# For anonymous user
curl -X POST "https://api.aiwriting.app/api/documents" \
  -H "Content-Type: application/json" \
  -d '{"title":"My New Document","content":"The content of the document goes here...","tags":["draft","personal"],"sessionId":"anonymous-session-id"}'
```

**JavaScript Example:**

```javascript
async function createDocument(title, content, tags, isAnonymous = false) {
  const requestBody = {
    title,
    content,
    tags
  };
  
  if (isAnonymous) {
    requestBody.sessionId = localStorage.getItem('sessionId');
  }
  
  const headers = {
    'Content-Type': 'application/json'
  };
  
  if (!isAnonymous) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await fetch('https://api.aiwriting.app/api/documents', {
    method: 'POST',
    headers,
    body: JSON.stringify(requestBody)
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error ${response.status}`);
  }
  
  return await response.json();
}
```

### Get Document

Retrieves a specific document by ID.

**Endpoint:** `GET /api/documents/{id}`

**Authentication:** Required for user documents, optional for anonymous documents (requires matching sessionId)

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Document ID |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| version | string | null | Optional version ID to retrieve specific document version |
| sessionId | string | null | Required for anonymous documents |

**Success Response:**

`200 OK`
```json
{
  "document": {
    "id": "60d21b4667d0d8992e610c85",
    "title": "Project Proposal",
    "content": "The full content of the document...",
    "createdAt": "2023-03-15T18:23:45Z",
    "updatedAt": "2023-03-17T09:12:30Z",
    "tags": ["business", "proposal"],
    "userId": "auth0|123456789", // null for anonymous documents
    "versionNumber": 3,
    "versionId": "60d21b4667d0d8992e610c87"
  }
}
```

**Error Responses:**

`401 Unauthorized` - Missing or invalid authentication token
`403 Forbidden` - Insufficient permissions to access the document
`404 Not Found` - Document not found
`500 Internal Server Error` - Server-side error

**Example Request:**

```bash
# For authenticated user document
curl -X GET "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# For anonymous document
curl -X GET "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85?sessionId=anonymous-session-id"
```

**JavaScript Example:**

```javascript
async function getDocument(documentId, versionId = null) {
  let url = `https://api.aiwriting.app/api/documents/${documentId}`;
  
  if (versionId) {
    url += `?version=${versionId}`;
  }
  
  // Add sessionId for anonymous documents
  const sessionId = localStorage.getItem('sessionId');
  if (sessionId && !versionId) {
    url += `?sessionId=${sessionId}`;
  } else if (sessionId && versionId) {
    url += `&sessionId=${sessionId}`;
  }
  
  const headers = {};
  const token = localStorage.getItem('token');
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    method: 'GET',
    headers
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error ${response.status}`);
  }
  
  return await response.json();
}
```

### Update Document

Updates an existing document. Creates a new version when content is modified.

**Endpoint:** `PUT /api/documents/{id}`

**Authentication:** Required for user documents, optional for anonymous documents (requires matching sessionId)

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Document ID |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| sessionId | string | null | Required for anonymous documents |

**Request Body:**

```json
{
  "title": "Updated Document Title",
  "content": "Updated content of the document...",
  "tags": ["edited", "proposal"],
  "changes": [
    {
      "id": "change-123",
      "status": "accepted" // or "rejected"
    }
    // Additional changes...
  ]
}
```

**Success Response:**

`200 OK`
```json
{
  "document": {
    "id": "60d21b4667d0d8992e610c85",
    "title": "Updated Document Title",
    "content": "Updated content of the document...",
    "createdAt": "2023-03-15T18:23:45Z",
    "updatedAt": "2023-03-17T10:45:22Z",
    "tags": ["edited", "proposal"],
    "userId": "auth0|123456789", // null for anonymous documents
    "versionNumber": 4,
    "versionId": "60d21b4667d0d8992e610c90"
  }
}
```

**Error Responses:**

`400 Bad Request` - Invalid document format
`401 Unauthorized` - Missing or invalid authentication token
`403 Forbidden` - Insufficient permissions to update the document
`404 Not Found` - Document not found
`500 Internal Server Error` - Server-side error

**Example Request:**

```bash
# For authenticated user document
curl -X PUT "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated Document Title","content":"Updated content of the document...","tags":["edited","proposal"]}'

# For anonymous document
curl -X PUT "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85?sessionId=anonymous-session-id" \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated Document Title","content":"Updated content of the document...","tags":["edited","proposal"]}'
```

**JavaScript Example:**

```javascript
async function updateDocument(documentId, updates) {
  let url = `https://api.aiwriting.app/api/documents/${documentId}`;
  
  // Add sessionId for anonymous documents
  const sessionId = localStorage.getItem('sessionId');
  if (sessionId) {
    url += `?sessionId=${sessionId}`;
  }
  
  const headers = {
    'Content-Type': 'application/json'
  };
  
  const token = localStorage.getItem('token');
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    method: 'PUT',
    headers,
    body: JSON.stringify(updates)
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error ${response.status}`);
  }
  
  return await response.json();
}
```

### Delete Document

Deletes a document. By default, this performs a soft delete.

**Endpoint:** `DELETE /api/documents/{id}`

**Authentication:** Required for user documents, optional for anonymous documents (requires matching sessionId)

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Document ID |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| permanent | boolean | false | Whether to permanently delete the document |
| sessionId | string | null | Required for anonymous documents |

**Success Response:**

`204 No Content`

**Error Responses:**

`401 Unauthorized` - Missing or invalid authentication token
`403 Forbidden` - Insufficient permissions to delete the document
`404 Not Found` - Document not found
`500 Internal Server Error` - Server-side error

**Example Request:**

```bash
# For authenticated user document (soft delete)
curl -X DELETE "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# For authenticated user document (permanent delete)
curl -X DELETE "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85?permanent=true" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# For anonymous document
curl -X DELETE "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85?sessionId=anonymous-session-id"
```

**JavaScript Example:**

```javascript
async function deleteDocument(documentId, permanent = false) {
  let url = `https://api.aiwriting.app/api/documents/${documentId}`;
  
  if (permanent) {
    url += '?permanent=true';
  }
  
  // Add sessionId for anonymous documents
  const sessionId = localStorage.getItem('sessionId');
  if (sessionId && !permanent) {
    url += `?sessionId=${sessionId}`;
  } else if (sessionId && permanent) {
    url += `&sessionId=${sessionId}`;
  }
  
  const headers = {};
  const token = localStorage.getItem('token');
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    method: 'DELETE',
    headers
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error ${response.status}`);
  }
  
  return true;
}
```

### Document Versions

Retrieves version history for a document.

**Endpoint:** `GET /api/documents/{id}/versions`

**Authentication:** Required for user documents, optional for anonymous documents (requires matching sessionId)

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Document ID |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number |
| limit | integer | 20 | Items per page |
| sessionId | string | null | Required for anonymous documents |

**Success Response:**

`200 OK`
```json
{
  "versions": [
    {
      "id": "60d21b4667d0d8992e610c90",
      "versionNumber": 4,
      "createdAt": "2023-03-17T10:45:22Z",
      "changeDescription": "Content update"
    },
    {
      "id": "60d21b4667d0d8992e610c87",
      "versionNumber": 3,
      "createdAt": "2023-03-17T09:12:30Z",
      "changeDescription": "AI suggestions applied"
    },
    // Additional versions...
  ],
  "pagination": {
    "totalVersions": 4,
    "totalPages": 1,
    "currentPage": 1,
    "limit": 20
  }
}
```

**Error Responses:**

`401 Unauthorized` - Missing or invalid authentication token
`403 Forbidden` - Insufficient permissions to access the document
`404 Not Found` - Document not found
`500 Internal Server Error` - Server-side error

**Example Request:**

```bash
# For authenticated user document
curl -X GET "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85/versions" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# For anonymous document
curl -X GET "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85/versions?sessionId=anonymous-session-id"
```

**JavaScript Example:**

```javascript
async function getDocumentVersions(documentId, page = 1, limit = 20) {
  let url = `https://api.aiwriting.app/api/documents/${documentId}/versions?page=${page}&limit=${limit}`;
  
  // Add sessionId for anonymous documents
  const sessionId = localStorage.getItem('sessionId');
  if (sessionId) {
    url += `&sessionId=${sessionId}`;
  }
  
  const headers = {};
  const token = localStorage.getItem('token');
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    method: 'GET',
    headers
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error ${response.status}`);
  }
  
  return await response.json();
}
```

### Restore Document Version

Restores a document to a previous version.

**Endpoint:** `POST /api/documents/{id}/versions/{versionId}/restore`

**Authentication:** Required for user documents, optional for anonymous documents (requires matching sessionId)

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Document ID |
| versionId | string | Version ID to restore |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| sessionId | string | null | Required for anonymous documents |

**Success Response:**

`200 OK`
```json
{
  "document": {
    "id": "60d21b4667d0d8992e610c85",
    "title": "Project Proposal",
    "content": "Content from the restored version...",
    "createdAt": "2023-03-15T18:23:45Z",
    "updatedAt": "2023-03-18T14:22:18Z",
    "tags": ["business", "proposal"],
    "userId": "auth0|123456789", // null for anonymous documents
    "versionNumber": 5,
    "versionId": "60d21b4667d0d8992e610c95",
    "restoredFromVersion": 3
  }
}
```

**Error Responses:**

`401 Unauthorized` - Missing or invalid authentication token
`403 Forbidden` - Insufficient permissions to modify the document
`404 Not Found` - Document or version not found
`500 Internal Server Error` - Server-side error

**Example Request:**

```bash
# For authenticated user document
curl -X POST "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85/versions/60d21b4667d0d8992e610c87/restore" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# For anonymous document
curl -X POST "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85/versions/60d21b4667d0d8992e610c87/restore?sessionId=anonymous-session-id"
```

**JavaScript Example:**

```javascript
async function restoreDocumentVersion(documentId, versionId) {
  let url = `https://api.aiwriting.app/api/documents/${documentId}/versions/${versionId}/restore`;
  
  // Add sessionId for anonymous documents
  const sessionId = localStorage.getItem('sessionId');
  if (sessionId) {
    url += `?sessionId=${sessionId}`;
  }
  
  const headers = {};
  const token = localStorage.getItem('token');
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    method: 'POST',
    headers
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error ${response.status}`);
  }
  
  return await response.json();
}
```

### Compare Document Versions

Compares two document versions and returns the differences.

**Endpoint:** `GET /api/documents/{id}/compare`

**Authentication:** Required for user documents, optional for anonymous documents (requires matching sessionId)

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Document ID |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| fromVersion | string | previousVersion | Version ID to compare from |
| toVersion | string | currentVersion | Version ID to compare to |
| format | string | "html" | Response format (options: "html", "json") |
| sessionId | string | null | Required for anonymous documents |

**Success Response:**

`200 OK`
```json
{
  "comparison": {
    "fromVersion": {
      "id": "60d21b4667d0d8992e610c87",
      "versionNumber": 3,
      "createdAt": "2023-03-17T09:12:30Z"
    },
    "toVersion": {
      "id": "60d21b4667d0d8992e610c90",
      "versionNumber": 4,
      "createdAt": "2023-03-17T10:45:22Z"
    },
    "differences": [
      {
        "type": "deletion",
        "position": {
          "start": 145,
          "end": 162
        },
        "content": "needs to be improved"
      },
      {
        "type": "addition",
        "position": {
          "start": 145,
          "end": 157
        },
        "content": "can be enhanced"
      }
      // Additional differences...
    ],
    "htmlDiff": "<p>The document content with <del class=\"deletion\">needs to be improved</del><ins class=\"addition\">can be enhanced</ins> for better clarity.</p>"
  }
}
```

**Error Responses:**

`400 Bad Request` - Invalid version IDs or format
`401 Unauthorized` - Missing or invalid authentication token
`403 Forbidden` - Insufficient permissions to access the document
`404 Not Found` - Document or versions not found
`500 Internal Server Error` - Server-side error

**Example Request:**

```bash
# For authenticated user document
curl -X GET "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85/compare?fromVersion=60d21b4667d0d8992e610c87&toVersion=60d21b4667d0d8992e610c90" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# For anonymous document
curl -X GET "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85/compare?fromVersion=60d21b4667d0d8992e610c87&toVersion=60d21b4667d0d8992e610c90&sessionId=anonymous-session-id"
```

**JavaScript Example:**

```javascript
async function compareDocumentVersions(documentId, fromVersionId, toVersionId, format = 'html') {
  let url = `https://api.aiwriting.app/api/documents/${documentId}/compare?fromVersion=${fromVersionId}&toVersion=${toVersionId}&format=${format}`;
  
  // Add sessionId for anonymous documents
  const sessionId = localStorage.getItem('sessionId');
  if (sessionId) {
    url += `&sessionId=${sessionId}`;
  }
  
  const headers = {};
  const token = localStorage.getItem('token');
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    method: 'GET',
    headers
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error ${response.status}`);
  }
  
  return await response.json();
}
```

### Export Document

Exports a document in the specified format.

**Endpoint:** `GET /api/documents/{id}/export`

**Authentication:** Required for user documents, optional for anonymous documents (requires matching sessionId)

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Document ID |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| format | string | "txt" | Export format (options: "txt", "html", "docx", "pdf", "md") |
| versionId | string | null | Optional version ID to export |
| includeChanges | boolean | false | Whether to include track changes in the export |
| sessionId | string | null | Required for anonymous documents |

**Success Response:**

`200 OK`

Response is a binary file with the appropriate content type for the requested format.

**Error Responses:**

`400 Bad Request` - Invalid format or parameters
`401 Unauthorized` - Missing or invalid authentication token
`403 Forbidden` - Insufficient permissions to access the document
`404 Not Found` - Document not found
`500 Internal Server Error` - Server-side error

**Example Request:**

```bash
# For authenticated user document
curl -X GET "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85/export?format=docx" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  --output document.docx

# For anonymous document
curl -X GET "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85/export?format=docx&sessionId=anonymous-session-id" \
  --output document.docx
```

**JavaScript Example:**

```javascript
async function exportDocument(documentId, format = 'docx', versionId = null, includeChanges = false) {
  let url = `https://api.aiwriting.app/api/documents/${documentId}/export?format=${format}`;
  
  if (versionId) {
    url += `&versionId=${versionId}`;
  }
  
  if (includeChanges) {
    url += '&includeChanges=true';
  }
  
  // Add sessionId for anonymous documents
  const sessionId = localStorage.getItem('sessionId');
  if (sessionId) {
    url += `&sessionId=${sessionId}`;
  }
  
  const headers = {};
  const token = localStorage.getItem('token');
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    method: 'GET',
    headers
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error ${response.status}`);
  }
  
  // Return blob for download
  return await response.blob();
}
```

### Import Document

Imports a document from an uploaded file.

**Endpoint:** `POST /api/documents/import`

**Authentication:** Optional (anonymous users can import documents with a sessionId)

**Content-Type:** `multipart/form-data`

**Form Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | The document file to import |
| title | string | No | Custom title for the document (defaults to filename) |
| tags | string | No | Comma-separated list of tags |
| sessionId | string | Yes (for anonymous) | Session ID for anonymous users |

**Success Response:**

`201 Created`
```json
{
  "document": {
    "id": "60d21b4667d0d8992e610c85",
    "title": "Imported Document",
    "content": "Imported content of the document...",
    "createdAt": "2023-03-18T16:45:22Z",
    "updatedAt": "2023-03-18T16:45:22Z",
    "tags": ["imported"],
    "userId": "auth0|123456789", // null for anonymous documents
    "versionNumber": 1,
    "versionId": "60d21b4667d0d8992e610c86"
  }
}
```

**Error Responses:**

`400 Bad Request` - Invalid file format or too large
`401 Unauthorized` - Invalid authentication token (if provided)
`413 Payload Too Large` - File exceeds size limit
`415 Unsupported Media Type` - Unsupported file format
`500 Internal Server Error` - Server-side error

**Example Request:**

```bash
# For authenticated user
curl -X POST "https://api.aiwriting.app/api/documents/import" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "file=@/path/to/document.docx" \
  -F "title=Imported Document" \
  -F "tags=imported,work"

# For anonymous user
curl -X POST "https://api.aiwriting.app/api/documents/import" \
  -F "file=@/path/to/document.docx" \
  -F "title=Imported Document" \
  -F "tags=imported,work" \
  -F "sessionId=anonymous-session-id"
```

**JavaScript Example:**

```javascript
async function importDocument(file, title = null, tags = []) {
  const formData = new FormData();
  formData.append('file', file);
  
  if (title) {
    formData.append('title', title);
  }
  
  if (tags.length > 0) {
    formData.append('tags', tags.join(','));
  }
  
  // Add sessionId for anonymous users
  const sessionId = localStorage.getItem('sessionId');
  if (sessionId) {
    formData.append('sessionId', sessionId);
  }
  
  const headers = {};
  const token = localStorage.getItem('token');
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  const response = await fetch('https://api.aiwriting.app/api/documents/import', {
    method: 'POST',
    headers,
    body: formData
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error ${response.status}`);
  }
  
  return await response.json();
}
```

### Transfer Anonymous Document

Transfers an anonymous document to an authenticated user account.

**Endpoint:** `POST /api/documents/{id}/transfer`

**Authentication:** Required (target user account)

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Document ID |

**Request Body:**

```json
{
  "sessionId": "anonymous-session-id"
}
```

**Success Response:**

`200 OK`
```json
{
  "document": {
    "id": "60d21b4667d0d8992e610c85",
    "title": "Transferred Document",
    "content": "Document content...",
    "createdAt": "2023-03-15T18:23:45Z",
    "updatedAt": "2023-03-18T17:12:30Z",
    "tags": ["transferred"],
    "userId": "auth0|123456789",
    "versionNumber": 1,
    "versionId": "60d21b4667d0d8992e610c86"
  }
}
```

**Error Responses:**

`400 Bad Request` - Invalid sessionId or document ID
`401 Unauthorized` - Missing or invalid authentication token
`403 Forbidden` - Session does not match the document
`404 Not Found` - Document not found or already transferred
`500 Internal Server Error` - Server-side error

**Example Request:**

```bash
curl -X POST "https://api.aiwriting.app/api/documents/60d21b4667d0d8992e610c85/transfer" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"anonymous-session-id"}'
```

**JavaScript Example:**

```javascript
async function transferAnonymousDocument(documentId, sessionId) {
  const response = await fetch(`https://api.aiwriting.app/api/documents/${documentId}/transfer`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ sessionId })
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error ${response.status}`);
  }
  
  return await response.json();
}
```

## Schemas

### Document Schema

```json
{
  "id": "string",
  "title": "string",
  "content": "string",
  "userId": "string | null",
  "sessionId": "string | null",
  "createdAt": "string (ISO date)",
  "updatedAt": "string (ISO date)",
  "tags": "string[]",
  "isArchived": "boolean",
  "versionNumber": "integer",
  "currentVersionId": "string",
  "wordCount": "integer",
  "changes": [
    {
      "id": "string",
      "position": {
        "start": "integer",
        "end": "integer"
      },
      "originalText": "string",
      "suggestedText": "string",
      "status": "string (pending | accepted | rejected)",
      "createdAt": "string (ISO date)",
      "explanation": "string"
    }
  ]
}
```

**Field Descriptions:**

- `id`: Unique identifier for the document
- `title`: Document title
- `content`: Full text content of the document
- `userId`: ID of the owning user (null for anonymous documents)
- `sessionId`: Session identifier for anonymous documents (null for user documents)
- `createdAt`: Creation timestamp
- `updatedAt`: Last update timestamp
- `tags`: Array of tag strings for categorization
- `isArchived`: Whether the document is archived (soft-deleted)
- `versionNumber`: Current version number (increments with content changes)
- `currentVersionId`: ID of the current version
- `wordCount`: Number of words in the document
- `changes`: Array of tracked changes from AI suggestions

**Example:**

```json
{
  "id": "60d21b4667d0d8992e610c85",
  "title": "Project Proposal",
  "content": "This project aims to revolutionize the industry by implementing...",
  "userId": "auth0|123456789",
  "sessionId": null,
  "createdAt": "2023-03-15T18:23:45Z",
  "updatedAt": "2023-03-17T09:12:30Z",
  "tags": ["business", "proposal"],
  "isArchived": false,
  "versionNumber": 3,
  "currentVersionId": "60d21b4667d0d8992e610c87",
  "wordCount": 1250,
  "changes": [
    {
      "id": "change-123",
      "position": {
        "start": 145,
        "end": 162
      },
      "originalText": "needs to be improved",
      "suggestedText": "can be enhanced",
      "status": "pending",
      "createdAt": "2023-03-17T09:10:15Z",
      "explanation": "More professional phrasing"
    }
  ]
}
```

### Document Version Schema

```json
{
  "id": "string",
  "documentId": "string",
  "versionNumber": "integer",
  "content": "string",
  "createdAt": "string (ISO date)",
  "createdBy": "string | null",
  "changeDescription": "string",
  "previousVersionId": "string | null"
}
```

**Field Descriptions:**

- `id`: Unique identifier for the version
- `documentId`: ID of the parent document
- `versionNumber`: Sequential version number
- `content`: Full text content of this version
- `createdAt`: Creation timestamp
- `createdBy`: User ID who created this version (null for anonymous or system)
- `changeDescription`: Description of changes made in this version
- `previousVersionId`: ID of the previous version (null for first version)

**Example:**

```json
{
  "id": "60d21b4667d0d8992e610c87",
  "documentId": "60d21b4667d0d8992e610c85",
  "versionNumber": 3,
  "content": "This project aims to revolutionize the industry by implementing...",
  "createdAt": "2023-03-17T09:12:30Z",
  "createdBy": "auth0|123456789",
  "changeDescription": "AI suggestions applied",
  "previousVersionId": "60d21b4667d0d8992e610c86"
}
```

### Document Change Schema

Used for track changes functionality.

```json
{
  "id": "string",
  "documentId": "string",
  "position": {
    "start": "integer",
    "end": "integer"
  },
  "originalText": "string",
  "suggestedText": "string",
  "status": "string (pending | accepted | rejected)",
  "createdAt": "string (ISO date)",
  "updatedAt": "string (ISO date)",
  "source": "string (ai | user)",
  "explanation": "string"
}
```

**Field Descriptions:**

- `id`: Unique identifier for the change
- `documentId`: ID of the document this change applies to
- `position`: Start and end position in the document
- `originalText`: Original text being changed
- `suggestedText`: Suggested replacement text
- `status`: Current status of the change (pending, accepted, rejected)
- `createdAt`: When the change was suggested
- `updatedAt`: When the change status was last updated
- `source`: Origin of the suggestion (ai or user)
- `explanation`: Explanation of why the change was suggested

**Example:**

```json
{
  "id": "change-123",
  "documentId": "60d21b4667d0d8992e610c85",
  "position": {
    "start": 145,
    "end": 162
  },
  "originalText": "needs to be improved",
  "suggestedText": "can be enhanced",
  "status": "pending",
  "createdAt": "2023-03-17T09:10:15Z",
  "updatedAt": "2023-03-17T09:10:15Z",
  "source": "ai",
  "explanation": "More professional phrasing"
}
```

### Request Schemas

#### Document Create Request Schema

```json
{
  "title": "string",
  "content": "string",
  "tags": "string[] (optional)",
  "sessionId": "string (required for anonymous)"
}
```

**Validation Rules:**
- `title`: Required, 1-100 characters
- `content`: Required, max 100,000 characters
- `tags`: Optional, max 10 tags, each 1-30 characters
- `sessionId`: Required for anonymous users, valid session ID

**Example:**

```json
{
  "title": "My New Document",
  "content": "The content of the document goes here...",
  "tags": ["draft", "personal"],
  "sessionId": "anonymous-session-id"
}
```

#### Document Update Request Schema

```json
{
  "title": "string (optional)",
  "content": "string (optional)",
  "tags": "string[] (optional)",
  "changes": [
    {
      "id": "string",
      "status": "string (accepted | rejected)"
    }
  ] (optional)
}
```

**Validation Rules:**
- At least one field must be provided
- `title`: 1-100 characters if provided
- `content`: Max 100,000 characters if provided
- `tags`: Max 10 tags, each 1-30 characters
- `changes`: Valid change IDs with valid status values

**Example:**

```json
{
  "title": "Updated Document Title",
  "content": "Updated content of the document...",
  "tags": ["edited", "proposal"],
  "changes": [
    {
      "id": "change-123",
      "status": "accepted"
    },
    {
      "id": "change-124",
      "status": "rejected"
    }
  ]
}
```

### Response Schemas

#### Document List Response Schema

```json
{
  "documents": [
    {
      "id": "string",
      "title": "string",
      "createdAt": "string (ISO date)",
      "updatedAt": "string (ISO date)",
      "tags": "string[]",
      "wordCount": "integer",
      "currentVersionId": "string"
    }
  ],
  "pagination": {
    "totalDocuments": "integer",
    "totalPages": "integer",
    "currentPage": "integer",
    "limit": "integer"
  }
}
```

**Example:**

```json
{
  "documents": [
    {
      "id": "60d21b4667d0d8992e610c85",
      "title": "Project Proposal",
      "createdAt": "2023-03-15T18:23:45Z",
      "updatedAt": "2023-03-17T09:12:30Z",
      "tags": ["business", "proposal"],
      "wordCount": 1250,
      "currentVersionId": "60d21b4667d0d8992e610c87"
    },
    {
      "id": "60d21b4667d0d8992e610c95",
      "title": "Meeting Notes",
      "createdAt": "2023-03-14T10:15:30Z",
      "updatedAt": "2023-03-14T10:15:30Z",
      "tags": ["notes", "meeting"],
      "wordCount": 450,
      "currentVersionId": "60d21b4667d0d8992e610c96"
    }
  ],
  "pagination": {
    "totalDocuments": 28,
    "totalPages": 2,
    "currentPage": 1,
    "limit": 20
  }
}
```

## Common Flows

### Anonymous Document Flow

Anonymous users can create and edit documents without authentication. These documents are stored in the session and can later be transferred to a user account.

```
1. Anonymous user visits the application
2. User creates a document (POST /api/documents with sessionId)
3. Document is stored with the sessionId as the owner identifier
4. User can edit the document (PUT /api/documents/{id}?sessionId=...)
5. User can apply AI suggestions (track changes)
6. If user creates an account:
   a. User authenticates
   b. User transfers document (POST /api/documents/{id}/transfer)
   c. Document is now associated with the user account
7. If user doesn't create an account:
   a. Document remains accessible via sessionId
   b. Document is automatically purged after the session expires (typically 7 days)
```

**Limitations:**
- Anonymous documents are tied to the browser session
- Session expiration will result in document loss if not transferred
- Some advanced features may be rate-limited for anonymous users

### Document Versioning Flow

The API automatically creates new versions of documents when content is modified, enabling version history and comparison.

```
1. Document is created (version 1)
2. User edits document content (PUT /api/documents/{id})
3. System creates a new version (version 2)
4. User applies AI suggestions
5. System creates another version (version 3)
6. User can:
   a. View version history (GET /api/documents/{id}/versions)
   b. Compare versions (GET /api/documents/{id}/compare?fromVersion=...&toVersion=...)
   c. Restore a previous version (POST /api/documents/{id}/versions/{versionId}/restore)
   d. Export a specific version (GET /api/documents/{id}/export?versionId=...)
```

**Version Creation Rules:**
- New versions are created when document content changes
- Metadata-only changes (title, tags) don't create new versions
- Accepting/rejecting track changes creates a new version
- Restoring a previous version creates a new version

### Track Changes Flow

The track changes functionality allows users to review, accept, or reject AI-suggested improvements.

```
1. User requests AI suggestions for document
2. AI generates suggestions and returns them as tracked changes
3. Changes are displayed in the document with track changes formatting
4. User reviews changes:
   a. Accept individual changes (PUT /api/documents/{id} with changes[].status="accepted")
   b. Reject individual changes (PUT /api/documents/{id} with changes[].status="rejected")
   c. Accept all changes (PUT /api/documents/{id} with all changes[].status="accepted")
   d. Reject all changes (PUT /api/documents/{id} with all changes[].status="rejected")
5. Accepted changes are incorporated into the document content
6. Rejected changes are discarded
7. A new document version is created with the applied changes
```

**Change Status Transitions:**
- `pending` → `accepted`: Change is incorporated into the document
- `pending` → `rejected`: Change is discarded
- Once a change is accepted or rejected, its status is final

## Error Handling

### Common Error Responses

#### 400 Bad Request

Returned when the request is malformed or contains invalid data.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data",
    "details": [
      {
        "field": "title",
        "message": "Title is required"
      },
      {
        "field": "content",
        "message": "Content exceeds maximum length of 100,000 characters"
      }
    ]
  }
}
```

#### 401 Unauthorized

Returned when authentication is required but not provided or invalid.

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication is required to access this resource"
  }
}
```

#### 403 Forbidden

Returned when the authenticated user doesn't have permission to access the resource.

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You don't have permission to access this document"
  }
}
```

#### 404 Not Found

Returned when the requested resource doesn't exist.

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Document with ID '60d21b4667d0d8992e610c85' not found"
  }
}
```

#### 429 Too Many Requests

Returned when the client has sent too many requests in a given time period.

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests, please try again later",
    "retryAfter": 60
  }
}
```

#### 500 Internal Server Error

Returned when an unexpected error occurs on the server.

```json
{
  "error": {
    "code": "SERVER_ERROR",
    "message": "An unexpected error occurred",
    "requestId": "req_123456789"
  }
}
```

### Handling Specific Document Errors

#### Document Size Limits

```json
{
  "error": {
    "code": "DOCUMENT_TOO_LARGE",
    "message": "Document exceeds the maximum size limit of 100,000 characters"
  }
}
```

#### Version Not Found

```json
{
  "error": {
    "code": "VERSION_NOT_FOUND",
    "message": "Version with ID '60d21b4667d0d8992e610c87' not found for document"
  }
}
```

#### Invalid Session for Document

```json
{
  "error": {
    "code": "INVALID_SESSION",
    "message": "The provided session ID does not match the document's session"
  }
}
```

#### Document Already Transferred

```json
{
  "error": {
    "code": "DOCUMENT_ALREADY_TRANSFERRED",
    "message": "This anonymous document has already been transferred to a user account"
  }
}
```

### Best Practices for Error Handling

1. Always check HTTP status codes to determine the type of error
2. For 400-level errors, examine the response body for details on how to fix the request
3. Implement exponential backoff for retrying after 429 errors
4. Log the `requestId` from 500 errors to help with troubleshooting
5. Provide meaningful error messages to users based on the error code
6. For version conflicts, fetch the latest document state before retrying operations