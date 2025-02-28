# Chat API

## Introduction

The Chat API enables free-form conversations with the AI assistant to get document improvement suggestions and writing assistance. This interface allows users to interact with the AI using natural language, beyond the predefined templates, creating a flexible experience for document enhancement.

## Authentication

The Chat API supports both anonymous and authenticated usage. For detailed authentication information, see the [Authentication API documentation](./auth.md).

### Anonymous Usage

- **Session-based**: Anonymous users can access the Chat API using a session ID
- **No login required**: Immediate access without registration
- **Limitations**: Subject to more restrictive rate limits and no persistence across browser sessions

### Authenticated Usage

- **JWT Authentication**: Uses Bearer token authentication
- **Header format**: `Authorization: Bearer {access_token}`
- **Benefits**: Higher rate limits, chat history persistence, and access to account-specific features

## Rate Limits

| User Type | Rate Limit | Header Response |
|-----------|------------|-----------------|
| Anonymous | 10 requests/minute | `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` |
| Authenticated | 50 requests/minute | `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` |

When rate limits are exceeded, the API will return a `429 Too Many Requests` response with a `Retry-After` header.

## Endpoints

### POST /api/chat

Send a message to the AI assistant and receive a response.

#### Request

**URL**: `POST /api/chat`

**Authentication**: Optional

**Headers**:
- `Content-Type: application/json`
- `Authorization: Bearer {access_token}` (optional)

**Request Body**:

```json
{
  "message": "Can you make this paragraph more concise?",
  "session_id": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
  "document_id": "5f7b5d8a9f4b3a2c1d0e9f8a",
  "context": "This is the paragraph I want to improve. It's currently quite verbose and could be more direct in making its point about the benefits of the product."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | The user's message to the AI assistant |
| `session_id` | string | No | Chat session identifier (required for anonymous users) |
| `document_id` | string | No | ID of the document being discussed (if applicable) |
| `context` | string | No | Additional document context or selected text |

#### Response

**Status Code**: 200 OK

**Response Body**:

```json
{
  "message": {
    "id": "msg_5f7b5d8a9f4b3a2c1d0e9f8c",
    "sessionId": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
    "content": "Here's a more concise version: 'This product offers significant benefits in a straightforward way.'",
    "role": "assistant",
    "timestamp": "2023-07-15T10:30:45Z",
    "metadata": {
      "documentId": "5f7b5d8a9f4b3a2c1d0e9f8a",
      "hasAppliedSuggestion": false
    }
  },
  "suggestions": [
    {
      "id": "sugg_1",
      "originalText": "This is the paragraph I want to improve. It's currently quite verbose and could be more direct in making its point about the benefits of the product.",
      "suggestedText": "This product offers significant benefits in a straightforward way.",
      "explanation": "Removed unnecessary words and simplified the message while preserving meaning.",
      "category": "conciseness",
      "startIndex": 0,
      "endIndex": 126
    }
  ],
  "sessionId": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
  "canApplyToDocument": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | object | The AI assistant's response message |
| `suggestions` | array | Optional array of specific text improvement suggestions |
| `sessionId` | string | Identifier for the chat session |
| `canApplyToDocument` | boolean | Indicates if suggestions can be directly applied to the document |

#### Error Responses

- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Invalid or missing authentication credentials
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server-side error

### GET /api/chat/history

Retrieve conversation history for a specific chat session.

#### Request

**URL**: `GET /api/chat/history?session_id=chat_5f7b5d8a9f4b3a2c1d0e9f8c&document_id=5f7b5d8a9f4b3a2c1d0e9f8a`

**Authentication**: Optional

**Headers**:
- `Authorization: Bearer {access_token}` (optional)

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | Chat session identifier |
| `document_id` | string | No | Document ID to filter conversation by document |
| `limit` | integer | No | Maximum number of messages to return (default: 50) |
| `before` | string | No | Return messages before this timestamp or message ID |

#### Response

**Status Code**: 200 OK

**Response Body**:

```json
{
  "sessionId": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
  "documentId": "5f7b5d8a9f4b3a2c1d0e9f8a",
  "messages": [
    {
      "id": "msg_1",
      "sessionId": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
      "content": "Can you make this paragraph more concise?",
      "role": "user",
      "timestamp": "2023-07-15T10:29:45Z",
      "metadata": {
        "documentId": "5f7b5d8a9f4b3a2c1d0e9f8a"
      }
    },
    {
      "id": "msg_2",
      "sessionId": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
      "content": "Here's a more concise version: 'This product offers significant benefits in a straightforward way.'",
      "role": "assistant",
      "timestamp": "2023-07-15T10:30:45Z",
      "metadata": {
        "documentId": "5f7b5d8a9f4b3a2c1d0e9f8a",
        "hasAppliedSuggestion": false
      }
    }
  ],
  "hasMore": false,
  "totalMessages": 2
}
```

| Field | Type | Description |
|-------|------|-------------|
| `sessionId` | string | Chat session identifier |
| `documentId` | string | Document ID if specified |
| `messages` | array | Array of chat messages in chronological order |
| `hasMore` | boolean | Indicates if more messages exist beyond the current result set |
| `totalMessages` | integer | Total count of messages in the conversation |

#### Error Responses

- **400 Bad Request**: Invalid parameters
- **401 Unauthorized**: Invalid or missing authentication credentials
- **404 Not Found**: Session not found

### POST /api/chat/stream

Stream an AI response for real-time display, providing a more interactive experience.

#### Request

**URL**: `POST /api/chat/stream`

**Authentication**: Optional

**Headers**:
- `Content-Type: application/json`
- `Authorization: Bearer {access_token}` (optional)
- `Accept: text/event-stream`

**Request Body**:

```json
{
  "message": "Can you make this paragraph more concise?",
  "session_id": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
  "document_id": "5f7b5d8a9f4b3a2c1d0e9f8a",
  "context": "This is the paragraph I want to improve. It's currently quite verbose and could be more direct in making its point about the benefits of the product."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | The user's message to the AI assistant |
| `session_id` | string | No | Chat session identifier (required for anonymous users) |
| `document_id` | string | No | ID of the document being discussed (if applicable) |
| `context` | string | No | Additional document context or selected text |

#### Response

**Status Code**: 200 OK

**Content-Type**: `text/event-stream`

**Response Stream**:

```
event: message
data: {"type":"text","content":"Here's"}

event: message
data: {"type":"text","content":" a more concise version:"}

event: message
data: {"type":"text","content":" 'This product offers significant benefits in a straightforward way.'"}

event: suggestion
data: {"id":"sugg_1","originalText":"This is the paragraph I want to improve. It's currently quite verbose and could be more direct in making its point about the benefits of the product.","suggestedText":"This product offers significant benefits in a straightforward way.","explanation":"Removed unnecessary words and simplified the message while preserving meaning.","category":"conciseness","startIndex":0,"endIndex":126}

event: done
data: {"sessionId":"chat_5f7b5d8a9f4b3a2c1d0e9f8c","messageId":"msg_3","timestamp":"2023-07-15T10:35:45Z"}
```

Each event in the stream contains a JSON payload with different types of content:
- `message` events contain text chunks of the AI response
- `suggestion` events contain document improvement suggestions
- `done` event signals the end of the response with metadata

#### Error Responses

- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Invalid or missing authentication credentials
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server-side error

## Schemas

### ChatRequestSchema

```json
{
  "type": "object",
  "required": ["message"],
  "properties": {
    "message": {
      "type": "string",
      "minLength": 1,
      "maxLength": 4000,
      "description": "The user's message to the AI assistant"
    },
    "session_id": {
      "type": "string",
      "description": "Chat session identifier (required for anonymous users)"
    },
    "document_id": {
      "type": "string",
      "description": "ID of the document being discussed (if applicable)"
    },
    "context": {
      "type": "string",
      "maxLength": 25000,
      "description": "Additional document context or selected text"
    }
  }
}
```

### ChatResponseSchema

```json
{
  "type": "object",
  "required": ["message", "sessionId"],
  "properties": {
    "message": {
      "type": "object",
      "required": ["id", "sessionId", "content", "role", "timestamp"],
      "properties": {
        "id": {
          "type": "string",
          "description": "Unique message identifier"
        },
        "sessionId": {
          "type": "string",
          "description": "Chat session identifier"
        },
        "content": {
          "type": "string",
          "description": "Message content"
        },
        "role": {
          "type": "string",
          "enum": ["user", "assistant"],
          "description": "Role of the message sender"
        },
        "timestamp": {
          "type": "string",
          "format": "date-time",
          "description": "Message timestamp in ISO 8601 format"
        },
        "metadata": {
          "type": "object",
          "description": "Additional message metadata"
        }
      }
    },
    "suggestions": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/ChatSuggestionSchema"
      },
      "description": "Optional array of specific text improvement suggestions"
    },
    "sessionId": {
      "type": "string",
      "description": "Identifier for the chat session"
    },
    "canApplyToDocument": {
      "type": "boolean",
      "description": "Indicates if suggestions can be directly applied to the document"
    }
  }
}
```

### ChatHistorySchema

```json
{
  "type": "object",
  "required": ["sessionId", "messages"],
  "properties": {
    "sessionId": {
      "type": "string",
      "description": "Chat session identifier"
    },
    "documentId": {
      "type": "string",
      "description": "Document ID if specified"
    },
    "messages": {
      "type": "array",
      "items": {
        "$ref": "#/components/schemas/ChatMessage"
      },
      "description": "Array of chat messages in chronological order"
    },
    "hasMore": {
      "type": "boolean",
      "description": "Indicates if more messages exist beyond the current result set"
    },
    "totalMessages": {
      "type": "integer",
      "description": "Total count of messages in the conversation"
    }
  }
}
```

### ChatSuggestionSchema

```json
{
  "type": "object",
  "required": ["id", "originalText", "suggestedText"],
  "properties": {
    "id": {
      "type": "string",
      "description": "Unique suggestion identifier"
    },
    "originalText": {
      "type": "string",
      "description": "The original text before improvement"
    },
    "suggestedText": {
      "type": "string",
      "description": "The suggested improved text"
    },
    "explanation": {
      "type": "string",
      "description": "Explanation of the changes made"
    },
    "category": {
      "type": "string",
      "description": "Category of the improvement (e.g., clarity, conciseness)"
    },
    "startIndex": {
      "type": "integer",
      "description": "Start index of the text in the document"
    },
    "endIndex": {
      "type": "integer",
      "description": "End index of the text in the document"
    }
  }
}
```

## Error Handling

All error responses follow a standard format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {} // Optional additional error details
  }
}
```

### Common Error Codes

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | `invalid_request` | The request contains invalid parameters or malformed data |
| 400 | `message_too_long` | The message exceeds the maximum allowed length |
| 400 | `context_too_large` | The provided context exceeds the maximum allowed size |
| 401 | `authentication_required` | Authentication is required for this operation |
| 401 | `invalid_token` | The provided authentication token is invalid or expired |
| 403 | `forbidden` | The authenticated user doesn't have permission to access this resource |
| 404 | `session_not_found` | The specified chat session was not found |
| 429 | `rate_limit_exceeded` | Too many requests, try again later |
| 500 | `internal_error` | An unexpected error occurred on the server |
| 503 | `service_unavailable` | The AI service is temporarily unavailable |

### Rate Limiting Headers

When a request is rate-limited, the response will include the following headers:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1635528000
Retry-After: 60
```

## Examples

### Sending a simple chat message

#### Request

```bash
curl -X POST https://api.aiwritingenhancement.com/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "message": "Can you suggest ways to improve the clarity of this text?",
    "session_id": "chat_5f7b5d8a9f4b3a2c1d0e9f8c"
  }'
```

#### Response

```json
{
  "message": {
    "id": "msg_5f7b5d8a9f4b3a2c1d0e9f8d",
    "sessionId": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
    "content": "I'd be happy to help improve the clarity of your text. Could you please provide the text you'd like me to review?",
    "role": "assistant",
    "timestamp": "2023-07-15T11:30:45Z",
    "metadata": {}
  },
  "suggestions": [],
  "sessionId": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
  "canApplyToDocument": false
}
```

### Sending a document-specific message

#### Request

```bash
curl -X POST https://api.aiwritingenhancement.com/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "message": "Make this introduction more engaging",
    "session_id": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
    "document_id": "5f7b5d8a9f4b3a2c1d0e9f8a",
    "context": "Welcome to our annual report. This document contains information about our financial performance in the last fiscal year."
  }'
```

#### Response

```json
{
  "message": {
    "id": "msg_5f7b5d8a9f4b3a2c1d0e9f8e",
    "sessionId": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
    "content": "Here's a more engaging introduction for your annual report:",
    "role": "assistant",
    "timestamp": "2023-07-15T11:35:45Z",
    "metadata": {
      "documentId": "5f7b5d8a9f4b3a2c1d0e9f8a",
      "hasAppliedSuggestion": false
    }
  },
  "suggestions": [
    {
      "id": "sugg_2",
      "originalText": "Welcome to our annual report. This document contains information about our financial performance in the last fiscal year.",
      "suggestedText": "Dive into our remarkable journey through the past fiscal year! Our annual report unveils the financial milestones, challenges overcome, and the strategic decisions that shaped our success story.",
      "explanation": "Added enthusiasm, emotion, and specific elements to hook the reader's interest from the start.",
      "category": "engagement",
      "startIndex": 0,
      "endIndex": 114
    }
  ],
  "sessionId": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
  "canApplyToDocument": true
}
```

### Retrieving conversation history

#### Request

```bash
curl -X GET "https://api.aiwritingenhancement.com/api/chat/history?session_id=chat_5f7b5d8a9f4b3a2c1d0e9f8c" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Response

```json
{
  "sessionId": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
  "messages": [
    {
      "id": "msg_1",
      "sessionId": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
      "content": "Can you suggest ways to improve the clarity of this text?",
      "role": "user",
      "timestamp": "2023-07-15T11:30:15Z",
      "metadata": {}
    },
    {
      "id": "msg_2",
      "sessionId": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
      "content": "I'd be happy to help improve the clarity of your text. Could you please provide the text you'd like me to review?",
      "role": "assistant",
      "timestamp": "2023-07-15T11:30:45Z",
      "metadata": {}
    },
    {
      "id": "msg_3",
      "sessionId": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
      "content": "Make this introduction more engaging",
      "role": "user",
      "timestamp": "2023-07-15T11:35:15Z",
      "metadata": {
        "documentId": "5f7b5d8a9f4b3a2c1d0e9f8a"
      }
    },
    {
      "id": "msg_4",
      "sessionId": "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
      "content": "Here's a more engaging introduction for your annual report:",
      "role": "assistant",
      "timestamp": "2023-07-15T11:35:45Z",
      "metadata": {
        "documentId": "5f7b5d8a9f4b3a2c1d0e9f8a",
        "hasAppliedSuggestion": false
      }
    }
  ],
  "hasMore": false,
  "totalMessages": 4
}
```

### Using streaming for real-time responses

#### JavaScript Example

```javascript
async function streamChatResponse() {
  const response = await fetch('https://api.aiwritingenhancement.com/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
      'Accept': 'text/event-stream'
    },
    body: JSON.stringify({
      message: "Summarize this paragraph in three bullet points",
      session_id: "chat_5f7b5d8a9f4b3a2c1d0e9f8c",
      context: "The AI writing enhancement interface provides users with powerful tools to improve their documents. It features a Microsoft Word-like track changes system for reviewing suggestions, predefined improvement templates, and a free-form AI chat assistant. Users can access the system immediately without registration, or create an account to save their documents."
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  // Function to process text chunks from the stream
  function processChunk(chunk) {
    buffer += chunk;
    
    // Find complete events in the buffer
    const eventRegex = /event: (\w+)\ndata: (.+?)(?=event:|$)/gs;
    let match;
    let newBuffer = buffer;
    
    while ((match = eventRegex.exec(buffer)) !== null) {
      const eventType = match[1];
      const eventData = JSON.parse(match[2].trim());
      
      // Handle different event types
      switch (eventType) {
        case 'message':
          // Append text chunk to the UI
          console.log('Text chunk:', eventData.content);
          break;
        case 'suggestion':
          // Process document suggestion
          console.log('Suggestion:', eventData);
          break;
        case 'done':
          // End of response
          console.log('Stream completed:', eventData);
          break;
      }
      
      // Remove processed event from buffer
      newBuffer = newBuffer.replace(match[0], '');
    }
    
    buffer = newBuffer;
  }

  // Read and process the stream
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    processChunk(decoder.decode(value, { stream: true }));
  }
  
  // Process any remaining buffer
  if (buffer.trim()) {
    processChunk(decoder.decode(), { stream: false });
  }
}
```