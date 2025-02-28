# AI Suggestions API

## Overview

The AI Suggestions API provides endpoints for generating and managing intelligent writing improvements. This API powers the core AI capabilities of the writing enhancement platform, allowing users to receive contextual suggestions to improve their documents.

## Base URL

```
https://api.enhancewriting.com/api
```

## Authentication

Most endpoints support both authenticated and anonymous usage:

- **Authenticated requests**: Include a JWT bearer token in the Authorization header
- **Anonymous requests**: No authentication required, but subject to stricter rate limits

```
Authorization: Bearer <jwt_token>
```

## Rate Limiting

| User Type | Rate Limit |
|------------|------------|
| Anonymous | 10 requests per minute |
| Authenticated | 50 requests per minute |

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 49
X-RateLimit-Reset: 1620000000
```

When rate limits are exceeded, the API returns a 429 Too Many Requests response.

## Endpoints

### Generate Text Suggestions

`POST /suggestions/text`

Generates contextual suggestions for improving text content.

#### Request Parameters

| Parameter | Type | Required | Description |
|------------|------|----------|------------|
| document_text | string | Yes | The full text content to analyze |
| selection_range | object | No | Range to focus suggestions on (if omitted, entire document is analyzed) |
| prompt_type | string | Yes | Type of improvement to suggest (e.g., "shorten", "professional", "grammar") |
| template_id | string | No | ID of a specific improvement template to use |

**Selection Range Object:**

```json
{
  "start": 0,
  "end": 100
}
```

#### Example Request

```json
{
  "document_text": "The company needs to prioritize customer satisfaction and make sure to address all complaints promptly. The big advantage of this approach is that it allows for greater flexibility.",
  "selection_range": {
    "start": 0,
    "end": 100
  },
  "prompt_type": "professional"
}
```

#### Example Response

```json
{
  "request_id": "req_1234567890",
  "suggestions": [
    {
      "id": "sug_001",
      "original_text": "needs to",
      "suggested_text": "should",
      "position": {
        "start": 12,
        "end": 20
      },
      "explanation": "\"Should\" sounds more professional and concise in this business context."
    },
    {
      "id": "sug_002",
      "original_text": "make sure to",
      "suggested_text": "ensure",
      "position": {
        "start": 59,
        "end": 70
      },
      "explanation": "\"Ensure\" is more concise and formal than \"make sure to\"."
    },
    {
      "id": "sug_003",
      "original_text": "big",
      "suggested_text": "significant",
      "position": {
        "start": 106,
        "end": 109
      },
      "explanation": "\"Significant\" has a more professional tone than \"big\"."
    }
  ],
  "metadata": {
    "processing_time_ms": 1250,
    "suggestion_count": 3,
    "prompt_type": "professional"
  }
}
```

### Generate Style Suggestions

`POST /suggestions/style`

Generates suggestions focused on writing style improvements.

#### Request Parameters

| Parameter | Type | Required | Description |
|------------|------|----------|------------|
| document_text | string | Yes | The full text content to analyze |
| style_parameters | object | Yes | Style parameters to adjust |

**Style Parameters Object:**

```json
{
  "tone": "formal",
  "formality": 0.8,
  "length": "shorter",
  "audience": "executive"
}
```

**Available Tone Options:** "formal", "casual", "persuasive", "informative", "enthusiastic"  
**Formality Range:** 0.0 (very casual) to 1.0 (extremely formal)  
**Length Options:** "shorter", "same", "longer"  
**Audience Options:** "general", "technical", "executive", "academic", "customer"

#### Example Request

```json
{
  "document_text": "Our team thinks this new product is really cool and customers will definitely love it. It's got tons of features that make it super easy to use.",
  "style_parameters": {
    "tone": "formal",
    "formality": 0.8,
    "length": "same",
    "audience": "executive"
  }
}
```

#### Example Response

```json
{
  "request_id": "req_2345678901",
  "suggestions": [
    {
      "id": "sug_101",
      "original_text": "Our team thinks",
      "suggested_text": "Our analysis indicates",
      "position": {
        "start": 0,
        "end": 14
      },
      "explanation": "More formal and data-driven language for executive audience"
    },
    {
      "id": "sug_102",
      "original_text": "really cool",
      "suggested_text": "highly innovative",
      "position": {
        "start": 35,
        "end": 45
      },
      "explanation": "More formal business terminology for executive communication"
    },
    {
      "id": "sug_103",
      "original_text": "will definitely love",
      "suggested_text": "are anticipated to value",
      "position": {
        "start": 58,
        "end": 77
      },
      "explanation": "More measured, formal language appropriate for executive summaries"
    },
    {
      "id": "sug_104",
      "original_text": "It's got tons of features that make it super easy",
      "suggested_text": "It includes numerous features designed to enhance usability",
      "position": {
        "start": 83,
        "end": 131
      },
      "explanation": "More precise, professional language that avoids casual phrases"
    }
  ],
  "metadata": {
    "processing_time_ms": 1320,
    "suggestion_count": 4,
    "style_parameters": {
      "tone": "formal",
      "formality": 0.8,
      "length": "same",
      "audience": "executive"
    }
  }
}
```

### Generate Grammar Suggestions

`POST /suggestions/grammar`

Focuses specifically on grammar, spelling, and punctuation improvements.

#### Request Parameters

| Parameter | Type | Required | Description |
|------------|------|----------|------------|
| document_text | string | Yes | The full text content to analyze |
| language | string | No | Language code (default: "en-US") |

**Supported Language Codes:** "en-US", "en-GB", "en-CA", "en-AU"

#### Example Request

```json
{
  "document_text": "The company have been growing fast, they're revenue doubled last year and there expecting even more growth this year.",
  "language": "en-US"
}
```

#### Example Response

```json
{
  "request_id": "req_3456789012",
  "suggestions": [
    {
      "id": "sug_201",
      "original_text": "company have been",
      "suggested_text": "company has been",
      "position": {
        "start": 4,
        "end": 20
      },
      "explanation": "Subject-verb agreement correction: 'company' is singular and requires 'has'"
    },
    {
      "id": "sug_202",
      "original_text": "they're",
      "suggested_text": "their",
      "position": {
        "start": 39,
        "end": 45
      },
      "explanation": "Homophone correction: 'they're' (they are) should be the possessive 'their'"
    },
    {
      "id": "sug_203",
      "original_text": "there",
      "suggested_text": "they're",
      "position": {
        "start": 69,
        "end": 74
      },
      "explanation": "Homophone correction: 'there' (location) should be 'they're' (they are)"
    }
  ],
  "metadata": {
    "processing_time_ms": 980,
    "suggestion_count": 3,
    "language": "en-US"
  }
}
```

### Get Suggestion Templates

`GET /suggestions/templates`

Retrieves available suggestion templates for different improvement types.

#### Query Parameters

| Parameter | Type | Required | Description |
|------------|------|----------|------------|
| category | string | No | Filter templates by category |

#### Example Response

```json
{
  "templates": [
    {
      "id": "tmpl_001",
      "name": "Make it shorter",
      "description": "Condense text while preserving key information",
      "category": "length",
      "prompt_type": "shorten"
    },
    {
      "id": "tmpl_002",
      "name": "More professional",
      "description": "Enhance formality and professional tone",
      "category": "tone",
      "prompt_type": "professional"
    },
    {
      "id": "tmpl_003",
      "name": "Improve grammar",
      "description": "Fix grammatical issues and spelling errors",
      "category": "correctness",
      "prompt_type": "grammar"
    },
    {
      "id": "tmpl_004",
      "name": "Simplify language",
      "description": "Make text easier to understand",
      "category": "clarity",
      "prompt_type": "simplify"
    },
    {
      "id": "tmpl_005",
      "name": "Add examples",
      "description": "Enhance explanation with relevant examples",
      "category": "content",
      "prompt_type": "examples"
    }
  ],
  "categories": [
    {
      "id": "length",
      "name": "Length Adjustments"
    },
    {
      "id": "tone",
      "name": "Tone Adjustments"
    },
    {
      "id": "correctness",
      "name": "Correctness"
    },
    {
      "id": "clarity",
      "name": "Clarity"
    },
    {
      "id": "content",
      "name": "Content Enrichment"
    }
  ]
}
```

### Apply Suggestion

`POST /suggestions/{suggestion_id}/apply`

Marks a suggestion as accepted and applies it to the document.

#### URL Parameters

| Parameter | Type | Required | Description |
|------------|------|----------|------------|
| suggestion_id | string | Yes | ID of the suggestion to apply |

#### Request Body

| Parameter | Type | Required | Description |
|------------|------|----------|------------|
| document_id | string | No | Document ID (required only for authenticated users with saved documents) |

#### Example Request

```json
{
  "document_id": "doc_12345"
}
```

#### Example Response

```json
{
  "success": true,
  "suggestion_id": "sug_001",
  "document_id": "doc_12345",
  "status": "applied"
}
```

### Reject Suggestion

`POST /suggestions/{suggestion_id}/reject`

Marks a suggestion as rejected.

#### URL Parameters

| Parameter | Type | Required | Description |
|------------|------|----------|------------|
| suggestion_id | string | Yes | ID of the suggestion to reject |

#### Request Body

| Parameter | Type | Required | Description |
|------------|------|----------|------------|
| document_id | string | No | Document ID (required only for authenticated users with saved documents) |
| feedback | string | No | Optional feedback about why the suggestion was rejected |

#### Example Request

```json
{
  "document_id": "doc_12345",
  "feedback": "The suggested word changed the intended meaning"
}
```

#### Example Response

```json
{
  "success": true,
  "suggestion_id": "sug_001",
  "document_id": "doc_12345",
  "status": "rejected"
}
```

### Provide Suggestion Feedback

`POST /suggestions/{suggestion_id}/feedback`

Submits feedback about a suggestion's quality.

#### URL Parameters

| Parameter | Type | Required | Description |
|------------|------|----------|------------|
| suggestion_id | string | Yes | ID of the suggestion to provide feedback for |

#### Request Body

| Parameter | Type | Required | Description |
|------------|------|----------|------------|
| rating | integer | Yes | Rating from 1-5 (1=poor, 5=excellent) |
| comments | string | No | Detailed feedback comments |

#### Example Request

```json
{
  "rating": 4,
  "comments": "Great suggestion, but slightly changed the tone I wanted"
}
```

#### Example Response

```json
{
  "success": true,
  "suggestion_id": "sug_001",
  "feedback_id": "fb_67890"
}
```

## Error Responses

### Common Error Codes

| Status Code | Error Code | Description |
|------------|------------|------------|
| 400 | INVALID_REQUEST | The request was malformed or contained invalid parameters |
| 401 | UNAUTHORIZED | Authentication required or token is invalid |
| 403 | FORBIDDEN | The authenticated user doesn't have permission |
| 404 | NOT_FOUND | The requested resource was not found |
| 429 | RATE_LIMIT_EXCEEDED | Request rate limit has been exceeded |
| 500 | SERVER_ERROR | An unexpected server error occurred |

### Error Response Format

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Anonymous user rate limit exceeded",
    "details": {
      "limit": 10,
      "reset_at": 1620000000,
      "retry_after": 45
    }
  }
}
```

## Common Usage Flows

### Basic Suggestion Flow

1. Send document text to `/suggestions/text` with desired prompt type
2. Receive suggestions with tracked changes format
3. Display suggestions to user with accept/reject controls
4. For each suggestion, call `/suggestions/{suggestion_id}/apply` or `/suggestions/{suggestion_id}/reject`
5. Optionally, provide feedback via `/suggestions/{suggestion_id}/feedback`

### Template-Based Suggestion Flow

1. Retrieve available templates via `/suggestions/templates`
2. User selects a template from the interface
3. Send document text to `/suggestions/text` with the selected template's `prompt_type`
4. Process suggestions as with the basic flow

### Anonymous Rate-Limited Flow

For anonymous users managing rate limits:

1. Check rate limit headers in each response
2. If approaching limits, inform user about creating an account
3. If 429 response received, wait for the duration specified in `retry_after`
4. Consider implementing exponential backoff for retry attempts

## Best Practices

### Performance Optimization

- Limit text size to under 25,000 words per request
- Use selection ranges to focus on specific sections when possible
- Batch suggestion applications/rejections when processing multiple changes

### Suggestion Quality

- Provide appropriate context by sending the full document text
- Use the most specific prompt type for your needs
- Submit feedback to help improve the system

### Rate Limit Management

- Implement proper handling of 429 responses
- Consider upgrading to authenticated access for higher limits
- Space out requests when processing large documents

## JavaScript Example

```javascript
async function getTextSuggestions(documentText, promptType = 'professional') {
  try {
    const response = await fetch('https://api.enhancewriting.com/api/suggestions/text', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Include authorization header if authenticated
        // 'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        document_text: documentText,
        prompt_type: promptType
      })
    });
    
    // Check for rate limiting
    const rateLimit = {
      limit: response.headers.get('X-RateLimit-Limit'),
      remaining: response.headers.get('X-RateLimit-Remaining'),
      reset: response.headers.get('X-RateLimit-Reset')
    };
    
    if (response.status === 429) {
      const retryAfter = response.headers.get('Retry-After');
      console.log(`Rate limited. Retry after ${retryAfter} seconds`);
      return { rateLimited: true, retryAfter };
    }
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error.message);
    }
    
    const suggestions = await response.json();
    return { suggestions, rateLimit };
  } catch (error) {
    console.error('Error getting suggestions:', error);
    throw error;
  }
}

// Usage example
async function improveProfessionalTone() {
  const documentText = "Our team thinks this new product is really cool and customers will definitely love it.";
  
  try {
    const { suggestions, rateLimit } = await getTextSuggestions(documentText, 'professional');
    
    console.log(`Received ${suggestions.suggestions.length} suggestions`);
    console.log(`Rate limit: ${rateLimit.remaining}/${rateLimit.limit}`);
    
    // Display suggestions to user...
    
    // When user accepts a suggestion
    if (suggestions.suggestions.length > 0) {
      const firstSuggestion = suggestions.suggestions[0];
      await applySuggestion(firstSuggestion.id);
    }
  } catch (error) {
    console.error('Failed to improve text:', error);
  }
}

async function applySuggestion(suggestionId) {
  try {
    const response = await fetch(`https://api.enhancewriting.com/api/suggestions/${suggestionId}/apply`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({})
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error.message);
    }
    
    const result = await response.json();
    console.log(`Suggestion ${suggestionId} applied successfully`);
    return result;
  } catch (error) {
    console.error('Error applying suggestion:', error);
    throw error;
  }
}
```

## CURL Examples

### Generate Text Suggestions

```bash
curl -X POST "https://api.enhancewriting.com/api/suggestions/text" \
  -H "Content-Type: application/json" \
  -d '{
    "document_text": "The company needs to prioritize customer satisfaction and make sure to address all complaints promptly.",
    "prompt_type": "professional"
  }'
```

### Apply Suggestion

```bash
curl -X POST "https://api.enhancewriting.com/api/suggestions/sug_001/apply" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Get Templates

```bash
curl -X GET "https://api.enhancewriting.com/api/suggestions/templates" \
  -H "Content-Type: application/json"
```