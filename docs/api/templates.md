# Templates API

This document outlines the API endpoints for managing and using templates in the AI writing enhancement platform. Templates provide predefined improvement prompts that help users enhance their writing through AI-powered suggestions.

## Overview

Templates are predefined prompts that guide the AI in generating specific types of writing improvements. They can be system-defined (built into the platform) or user-created. Examples include "Make it shorter," "More professional tone," and "Improve grammar."

Each template consists of:
- A name and description
- The prompt text that instructs the AI
- A category that organizes templates by purpose
- Metadata about creation and usage

Templates are accessible via the sidebar interface and provide a streamlined way to request common writing improvements without requiring users to craft custom prompts.

## Base URL

All API endpoints are relative to:

```
https://api.example.com/api
```

## Authentication

Most template endpoints require authentication with a valid JWT token. Include the token in the Authorization header:

```
Authorization: Bearer YOUR_JWT_TOKEN
```

Anonymous users can access system templates but cannot create or modify templates.

## Endpoints

### List Templates

Retrieves a paginated list of templates available to the user.

**URL:** `GET /templates`

**Authentication:** Optional (affects results)

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| category | string | Filter templates by category |
| systemOnly | boolean | If true, returns only system templates |
| userOnly | boolean | If true, returns only user-created templates |
| page | integer | Page number for pagination (default: 1) |
| perPage | integer | Items per page (default: 20, max: 100) |

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/templates?category=professional&page=1&perPage=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Successful Response:**

```json
{
  "templates": [
    {
      "id": "template123",
      "name": "Professional Email",
      "description": "Transforms casual text into a professional email format",
      "promptText": "Rewrite the following text as a professional email maintaining the same information but with a formal tone: {{text}}",
      "category": "professional",
      "isSystem": true,
      "createdAt": "2023-01-15T14:22:10Z",
      "createdBy": null
    },
    {
      "id": "template456",
      "name": "Business Proposal",
      "description": "Formats text as a business proposal with appropriate structure",
      "promptText": "Reformat the following content as a professional business proposal, adding appropriate structure and maintaining a formal tone: {{text}}",
      "category": "professional",
      "isSystem": true,
      "createdAt": "2023-01-18T09:15:32Z",
      "createdBy": null
    }
    // More templates...
  ],
  "total": 45,
  "page": 1,
  "perPage": 10,
  "pages": 5
}
```

**Status Codes:**

| Status | Description |
|--------|-------------|
| 200 | Templates retrieved successfully |
| 400 | Invalid query parameters |
| 401 | Authentication required for user-specific results |
| 500 | Server error |

### Get Template

Retrieves a specific template by ID.

**URL:** `GET /templates/{id}`

**Authentication:** Optional (required for user-created templates)

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Template ID |

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/templates/template123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Successful Response:**

```json
{
  "id": "template123",
  "name": "Professional Email",
  "description": "Transforms casual text into a professional email format",
  "promptText": "Rewrite the following text as a professional email maintaining the same information but with a formal tone: {{text}}",
  "category": "professional",
  "isSystem": true,
  "createdAt": "2023-01-15T14:22:10Z",
  "createdBy": null
}
```

**Status Codes:**

| Status | Description |
|--------|-------------|
| 200 | Template retrieved successfully |
| 404 | Template not found |
| 401 | Authentication required for user-created templates |
| 500 | Server error |

### Create Template

Creates a new custom template.

**URL:** `POST /templates`

**Authentication:** Required

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Template name (max 100 chars) |
| description | string | No | Template description (max 500 chars) |
| promptText | string | Yes | AI instruction with placeholders (max 1000 chars) |
| category | string | Yes | Template category |

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/templates" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Technical Simplification",
    "description": "Simplifies technical content for a general audience",
    "promptText": "Rewrite the following technical content to make it accessible to a non-technical audience while maintaining accuracy: {{text}}",
    "category": "clarity"
  }'
```

**Successful Response:**

```json
{
  "id": "template789",
  "name": "Technical Simplification",
  "description": "Simplifies technical content for a general audience",
  "promptText": "Rewrite the following technical content to make it accessible to a non-technical audience while maintaining accuracy: {{text}}",
  "category": "clarity",
  "isSystem": false,
  "createdAt": "2023-05-12T10:43:22Z",
  "createdBy": "user123"
}
```

**Status Codes:**

| Status | Description |
|--------|-------------|
| 201 | Template created successfully |
| 400 | Invalid request body |
| 401 | Authentication required |
| 422 | Validation error |
| 500 | Server error |

### Update Template

Updates an existing template.

**URL:** `PUT /templates/{id}`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Template ID |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | No | Template name (max 100 chars) |
| description | string | No | Template description (max 500 chars) |
| promptText | string | No | AI instruction with placeholders (max 1000 chars) |
| category | string | No | Template category |

**Example Request:**

```bash
curl -X PUT "https://api.example.com/api/templates/template789" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Simplifies technical content for a general audience without losing important details",
    "promptText": "Rewrite the following technical content to make it accessible to a non-technical audience. Maintain accuracy and explain technical terms when necessary: {{text}}"
  }'
```

**Successful Response:**

```json
{
  "id": "template789",
  "name": "Technical Simplification",
  "description": "Simplifies technical content for a general audience without losing important details",
  "promptText": "Rewrite the following technical content to make it accessible to a non-technical audience. Maintain accuracy and explain technical terms when necessary: {{text}}",
  "category": "clarity",
  "isSystem": false,
  "createdAt": "2023-05-12T10:43:22Z",
  "updatedAt": "2023-05-15T09:12:45Z",
  "createdBy": "user123"
}
```

**Status Codes:**

| Status | Description |
|--------|-------------|
| 200 | Template updated successfully |
| 400 | Invalid request body |
| 401 | Authentication required |
| 403 | Forbidden (cannot update system templates or templates created by other users) |
| 404 | Template not found |
| 422 | Validation error |
| 500 | Server error |

### Delete Template

Deletes a user-created template.

**URL:** `DELETE /templates/{id}`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Template ID |

**Example Request:**

```bash
curl -X DELETE "https://api.example.com/api/templates/template789" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Successful Response:**

```json
{
  "success": true,
  "message": "Template deleted successfully"
}
```

**Status Codes:**

| Status | Description |
|--------|-------------|
| 200 | Template deleted successfully |
| 401 | Authentication required |
| 403 | Forbidden (cannot delete system templates or templates created by other users) |
| 404 | Template not found |
| 500 | Server error |

### Get Template Categories

Retrieves the list of available template categories.

**URL:** `GET /templates/categories`

**Authentication:** Not required

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/templates/categories"
```

**Successful Response:**

```json
{
  "categories": [
    {
      "id": "grammar",
      "name": "Grammar",
      "description": "Improvements focused on grammar and spelling"
    },
    {
      "id": "style",
      "name": "Style",
      "description": "Enhancements to writing style and tone"
    },
    {
      "id": "conciseness",
      "name": "Conciseness",
      "description": "Shorting and simplifying content"
    },
    {
      "id": "clarity",
      "name": "Clarity",
      "description": "Making content clearer and easier to understand"
    },
    {
      "id": "professional",
      "name": "Professional",
      "description": "Business and professional writing improvements"
    },
    {
      "id": "academic",
      "name": "Academic",
      "description": "Academic and research-oriented improvements"
    },
    {
      "id": "creative",
      "name": "Creative",
      "description": "Creative writing enhancements"
    },
    {
      "id": "custom",
      "name": "Custom",
      "description": "User-defined improvement categories"
    }
  ]
}
```

**Status Codes:**

| Status | Description |
|--------|-------------|
| 200 | Categories retrieved successfully |
| 500 | Server error |

### Get Template Usage Metrics

Retrieves usage metrics for a specific template.

**URL:** `GET /templates/{id}/metrics`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Template ID |

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/templates/template123/metrics" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Successful Response:**

```json
{
  "usageCount": 1458,
  "acceptanceRate": 0.87,
  "rejectionRate": 0.13,
  "lastUsed": "2023-05-18T14:23:10Z",
  "timeframeStats": [
    {
      "period": "last30Days",
      "usageCount": 342,
      "acceptanceRate": 0.89
    },
    {
      "period": "last7Days",
      "usageCount": 87,
      "acceptanceRate": 0.92
    }
  ]
}
```

**Status Codes:**

| Status | Description |
|--------|-------------|
| 200 | Metrics retrieved successfully |
| 401 | Authentication required |
| 403 | Forbidden (insufficient permissions) |
| 404 | Template not found |
| 500 | Server error |

### Search Templates

Searches for templates matching specific criteria.

**URL:** `GET /templates/search`

**Authentication:** Optional (affects results)

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| query | string | Search term to match against name, description, and prompt text |
| category | string | Filter by category |
| includeSystem | boolean | Include system templates (default: true) |
| page | integer | Page number for pagination (default: 1) |
| perPage | integer | Items per page (default: 20, max: 100) |

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/templates/search?query=professional&category=style&page=1&perPage=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Successful Response:**

```json
{
  "templates": [
    {
      "id": "template234",
      "name": "Professional Tone",
      "description": "Adjusts the tone to be more professional and business-appropriate",
      "promptText": "Rewrite the following text to have a more professional tone suitable for business communication: {{text}}",
      "category": "style",
      "isSystem": true,
      "createdAt": "2023-01-18T09:15:32Z",
      "createdBy": null
    },
    // More templates...
  ],
  "total": 8,
  "page": 1,
  "perPage": 10,
  "pages": 1
}
```

**Status Codes:**

| Status | Description |
|--------|-------------|
| 200 | Search completed successfully |
| 400 | Invalid query parameters |
| 500 | Server error |

## Schemas

### Template Schema

The core template object used throughout the API.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| id | string | Unique template identifier |
| name | string | Display name of the template |
| description | string | Detailed description of what the template does |
| promptText | string | The actual instruction sent to the AI with placeholders |
| category | string | Category identifier (must match one from the categories endpoint) |
| isSystem | boolean | Indicates if this is a system-provided template |
| createdAt | string | ISO timestamp of creation time |
| updatedAt | string | ISO timestamp of last update time (if applicable) |
| createdBy | string | User ID of creator (null for system templates) |

**Example:**

```json
{
  "id": "template123",
  "name": "Professional Email",
  "description": "Transforms casual text into a professional email format",
  "promptText": "Rewrite the following text as a professional email maintaining the same information but with a formal tone: {{text}}",
  "category": "professional",
  "isSystem": true,
  "createdAt": "2023-01-15T14:22:10Z",
  "updatedAt": null,
  "createdBy": null
}
```

### Template Creation Request Schema

Schema for the request body when creating a new template.

**Properties:**

| Property | Type | Required | Validation |
|----------|------|----------|------------|
| name | string | Yes | 3-100 characters |
| description | string | No | 0-500 characters |
| promptText | string | Yes | 10-1000 characters, must include at least one placeholder |
| category | string | Yes | Must be one of the valid categories |

**Placeholders:**

Prompts should include placeholders for dynamic content using the double-curly braces syntax:

- `{{text}}`: The text to be improved
- `{{selection}}`: The selected portion of text (if applicable)
- `{{context}}`: Additional context from the document

**Example:**

```json
{
  "name": "Technical Simplification",
  "description": "Simplifies technical content for a general audience",
  "promptText": "Rewrite the following technical content to make it accessible to a non-technical audience while maintaining accuracy: {{text}}",
  "category": "clarity"
}
```

### Template Update Request Schema

Schema for the request body when updating an existing template.

**Properties:**

| Property | Type | Required | Validation |
|----------|------|----------|------------|
| name | string | No | 3-100 characters |
| description | string | No | 0-500 characters |
| promptText | string | No | 10-1000 characters, must include at least one placeholder |
| category | string | No | Must be one of the valid categories |

**Note:** System templates cannot be updated by regular users, and users can only update their own templates.

**Example:**

```json
{
  "description": "Simplifies technical content for a general audience without losing important details",
  "promptText": "Rewrite the following technical content to make it accessible to a non-technical audience. Maintain accuracy and explain technical terms when necessary: {{text}}"
}
```

### Template List Response Schema

Schema for the response when listing templates.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| templates | array | Array of template objects |
| total | integer | Total number of templates matching the query |
| page | integer | Current page number |
| perPage | integer | Number of items per page |
| pages | integer | Total number of pages |

**Example:**

```json
{
  "templates": [
    {
      "id": "template123",
      "name": "Professional Email",
      "description": "Transforms casual text into a professional email format",
      "promptText": "Rewrite the following text as a professional email maintaining the same information but with a formal tone: {{text}}",
      "category": "professional",
      "isSystem": true,
      "createdAt": "2023-01-15T14:22:10Z",
      "createdBy": null
    },
    // More templates...
  ],
  "total": 45,
  "page": 1,
  "perPage": 10,
  "pages": 5
}
```

### Template Metrics Schema

Schema for the response when retrieving template usage metrics.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| usageCount | integer | Total number of times the template has been used |
| acceptanceRate | number | Percentage (0-1) of suggestions that were accepted |
| rejectionRate | number | Percentage (0-1) of suggestions that were rejected |
| lastUsed | string | ISO timestamp of the last usage |
| timeframeStats | array | Array of usage statistics for different time periods |

**Timeframe Stats Properties:**

| Property | Type | Description |
|----------|------|-------------|
| period | string | Time period identifier (e.g., "last7Days", "last30Days") |
| usageCount | integer | Number of uses in this time period |
| acceptanceRate | number | Acceptance rate during this time period |

**Example:**

```json
{
  "usageCount": 1458,
  "acceptanceRate": 0.87,
  "rejectionRate": 0.13,
  "lastUsed": "2023-05-18T14:23:10Z",
  "timeframeStats": [
    {
      "period": "last30Days",
      "usageCount": 342,
      "acceptanceRate": 0.89
    },
    {
      "period": "last7Days",
      "usageCount": 87,
      "acceptanceRate": 0.92
    }
  ]
}
```

## Error Responses

All API errors follow a standard format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {} // Optional additional error details
  }
}
```

### Common Error Codes

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | INVALID_REQUEST | The request was malformed or contained invalid parameters |
| 401 | AUTHENTICATION_REQUIRED | Authentication is required for this endpoint |
| 403 | PERMISSION_DENIED | The authenticated user doesn't have permission for this action |
| 404 | RESOURCE_NOT_FOUND | The requested resource was not found |
| 422 | VALIDATION_ERROR | The request body failed validation |
| 500 | SERVER_ERROR | An unexpected server error occurred |

### Validation Error Example

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "name": "Name is required and must be between 3 and 100 characters",
      "promptText": "Prompt text must include at least one placeholder"
    }
  }
}
```

### Not Found Error Example

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Template with ID 'template999' was not found"
  }
}
```

### Permission Denied Error Example

```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "You do not have permission to modify this template"
  }
}
```

## Usage Tutorials

### Creating Effective Custom Templates

Templates can significantly improve the AI's ability to provide specific types of writing enhancements. Follow these guidelines to create effective custom templates:

#### Template Structure Best Practices

1. **Be specific and clear** in your instructions
2. **Use placeholders** to indicate where text should be inserted
3. **Provide context** about the desired outcome
4. **Specify the tone** you want the AI to use
5. **Include examples** for complex transformations

#### Example Template Creation

Creating a template for simplifying legal language:

```json
{
  "name": "Legal Simplification",
  "description": "Converts legal jargon into plain, understandable language",
  "promptText": "Rewrite the following legal text in plain, easy-to-understand language while preserving all important details and meanings. Explain legal terms when necessary: {{text}}",
  "category": "clarity"
}
```

#### Using Variables in Templates

Templates support several variables that are replaced with actual content:

- `{{text}}` - The full document or selected text to improve
- `{{selection}}` - Only the selected portion of text
- `{{context}}` - Additional surrounding context from the document

For example, a template for improving paragraph transitions:

```
Improve the transitions between paragraphs in the following text to create better flow. Focus on connecting ideas between paragraphs while maintaining the original meaning: {{text}}
```

### Frontend Integration

Integrate with the Templates API from your frontend application using these examples:

#### Fetching Templates

```javascript
// Using fetch API
async function getTemplates(category = null) {
  let url = 'https://api.example.com/api/templates';
  if (category) {
    url += `?category=${encodeURIComponent(category)}`;
  }
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`
    }
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error.message);
  }
  
  return response.json();
}
```

#### Using a Template for Text Improvement

```javascript
async function improveText(templateId, text) {
  // First, fetch the template
  const response = await fetch(`https://api.example.com/api/templates/${templateId}`, {
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`
    }
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error.message);
  }
  
  const template = await response.json();
  
  // Then use the template with the AI suggestion endpoint
  const suggestionResponse = await fetch('https://api.example.com/api/suggestions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      text: text,
      templateId: templateId,
      // The suggestion endpoint handles replacing the placeholders
    })
  });
  
  if (!suggestionResponse.ok) {
    const error = await suggestionResponse.json();
    throw new Error(error.error.message);
  }
  
  return suggestionResponse.json();
}
```

#### React Component Example

```jsx
import React, { useState, useEffect } from 'react';

function TemplateSelector({ onSelectTemplate, category }) {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    async function fetchTemplates() {
      try {
        setLoading(true);
        const response = await fetch(
          `https://api.example.com/api/templates?category=${category}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
          }
        );
        
        if (!response.ok) {
          throw new Error('Failed to fetch templates');
        }
        
        const data = await response.json();
        setTemplates(data.templates);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    
    fetchTemplates();
  }, [category]);
  
  if (loading) return <div>Loading templates...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div className="template-selector">
      <h3>Select a template</h3>
      <div className="template-list">
        {templates.map(template => (
          <button 
            key={template.id}
            className="template-button"
            onClick={() => onSelectTemplate(template)}
          >
            {template.name}
            <span className="template-description">{template.description}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default TemplateSelector;
```