# Backend Server for AI Writing Enhancement Platform

## Overview

This repository contains the backend server implementation for the AI writing enhancement platform. The system provides a robust API layer that powers document processing, AI-assisted text improvements, and track changes functionality for the web application. 

Built with Python and Flask, the backend follows a modular architecture design with clear service boundaries. It integrates with OpenAI's language models to deliver intelligent writing suggestions while maintaining document context and user sessions.

The system supports both anonymous and authenticated users, with seamless transition between these states. It implements Microsoft Word-like track changes for reviewing AI suggestions directly within documents.

## Features

- **Document Management**: Storage, retrieval, and versioning of user documents
- **AI Suggestion Engine**: Integration with OpenAI API for intelligent writing improvements
- **Track Changes System**: Implementation of diff-based track changes for reviewing suggestions
- **Template-based Improvements**: Pre-defined improvement prompts (make shorter, more professional, etc.)
- **Free-form AI Chat**: Contextual chat interface with document awareness
- **Anonymous Usage**: Session-based document editing without login requirement
- **User Authentication**: JWT-based authentication with account management
- **Document Storage**: Persistent storage for authenticated users with version history

## Technology Stack

### Core Technologies
- **Python 3.10+**: Primary backend language
- **Flask 2.3.0**: Web framework for API implementation
- **MongoDB 6.0**: Document-oriented database for flexible storage
- **Redis 7.0**: Session management and caching
- **JWT**: Token-based authentication

### Key Libraries
- **Langchain 0.0.267**: Orchestration for AI language model interactions
- **Flask-RESTful 0.3.10**: Structured API development
- **PyJWT 2.7.0**: JWT token handling for authentication
- **pymongo**: MongoDB driver for Python
- **redis-py**: Redis client for Python
- **diff-match-patch**: Text differencing for track changes
- **gunicorn 21.2.0**: WSGI HTTP server for production deployments

### External Services
- **OpenAI API**: Powers AI suggestion and chat functionality
- **AWS S3** (optional): Document backup storage

## Getting Started

### Prerequisites

- Python 3.10 or higher
- MongoDB 6.0 or higher
- Redis 7.0 or higher
- OpenAI API key

### Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

The application uses environment variables for configuration. Create a `.env` file in the root directory with the following variables:

```
# Application Settings
FLASK_APP=app
FLASK_ENV=development
DEBUG=True
PORT=5000
LOG_LEVEL=DEBUG

# Security
SECRET_KEY=your_secure_secret_key
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour in seconds
JWT_REFRESH_TOKEN_EXPIRES=604800  # 7 days in seconds

# Database Settings
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=ai_writing_enhancement
REDIS_URI=redis://localhost:6379/0

# OpenAI Settings
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
MAX_TOKENS=4096
TEMPERATURE=0.7

# Storage Settings (Optional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET=document-backup-bucket
```

For different environments (development, staging, production), you can create separate `.env` files or use the appropriate configuration management for your deployment environment.

### Running the Application

```bash
# Activate virtual environment if not already activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the application
flask run
```

For development with auto-reload:

```bash
flask run --debug
```

## Project Structure

```
src/backend/
├── app/
│   ├── __init__.py           # Application factory
│   ├── config.py             # Configuration settings
│   ├── api/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── documents.py      # Document management endpoints
│   │   ├── suggestions.py    # AI suggestion endpoints
│   │   └── chat.py           # AI chat endpoints
│   ├── models/               # Database models
│   │   ├── __init__.py
│   │   ├── user.py           # User model
│   │   ├── document.py       # Document model
│   │   └── ai_interaction.py # AI interaction history
│   ├── services/             # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py   # Authentication service
│   │   ├── document_service.py # Document operations
│   │   ├── ai_service.py     # AI integration
│   │   └── diff_service.py   # Track changes implementation
│   ├── utils/                # Utility functions
│   │   ├── __init__.py
│   │   ├── security.py       # Security helpers
│   │   ├── validators.py     # Input validation
│   │   └── helpers.py        # Misc helper functions
│   └── extensions/           # Flask extensions
│       ├── __init__.py
│       ├── database.py       # MongoDB connection
│       ├── redis.py          # Redis connection
│       └── jwt.py            # JWT configuration
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── conftest.py           # Test configuration
│   ├── test_auth.py          # Authentication tests
│   ├── test_documents.py     # Document API tests
│   └── test_suggestions.py   # AI suggestion tests
├── migrations/               # Database migrations
├── scripts/                  # Utility scripts
├── .env.example              # Example environment variables
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Docker Compose configuration
└── README.md                 # This documentation
```

## API Documentation

The backend exposes a RESTful API for frontend integration. All endpoints return JSON responses and accept JSON requests where applicable.

### Authentication Endpoints

#### `POST /api/auth/register`
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "firstName": "John",
  "lastName": "Doe"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe"
  },
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token"
}
```

#### `POST /api/auth/login`
Authenticate a user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe"
  },
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token"
}
```

#### `POST /api/auth/refresh`
Refresh authentication tokens.

**Request:**
```json
{
  "refresh_token": "jwt_refresh_token"
}
```

**Response:**
```json
{
  "access_token": "new_jwt_access_token",
  "refresh_token": "new_jwt_refresh_token"
}
```

### Document Endpoints

#### `GET /api/documents`
Get user's documents (requires authentication).

**Response:**
```json
{
  "documents": [
    {
      "id": "document_id",
      "title": "Document Title",
      "description": "Document description",
      "createdAt": "2023-09-01T12:00:00Z",
      "updatedAt": "2023-09-02T15:30:00Z",
      "tags": ["tag1", "tag2"]
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 20
}
```

#### `POST /api/documents`
Create a new document.

**Request:**
```json
{
  "title": "Document Title",
  "description": "Document description",
  "content": "Document content goes here...",
  "tags": ["tag1", "tag2"]
}
```

**Response:**
```json
{
  "message": "Document created successfully",
  "document": {
    "id": "document_id",
    "title": "Document Title",
    "description": "Document description",
    "createdAt": "2023-09-03T10:15:00Z",
    "updatedAt": "2023-09-03T10:15:00Z",
    "tags": ["tag1", "tag2"]
  }
}
```

#### `GET /api/documents/:id`
Get a specific document.

**Response:**
```json
{
  "id": "document_id",
  "title": "Document Title",
  "description": "Document description",
  "content": "Document content goes here...",
  "createdAt": "2023-09-01T12:00:00Z",
  "updatedAt": "2023-09-02T15:30:00Z",
  "tags": ["tag1", "tag2"],
  "versions": [
    {
      "id": "version_id",
      "versionNumber": 1,
      "createdAt": "2023-09-01T12:00:00Z"
    }
  ]
}
```

#### `PUT /api/documents/:id`
Update a document.

**Request:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "content": "Updated content...",
  "tags": ["tag1", "newtag"]
}
```

**Response:**
```json
{
  "message": "Document updated successfully",
  "document": {
    "id": "document_id",
    "title": "Updated Title",
    "description": "Updated description",
    "updatedAt": "2023-09-03T11:20:00Z",
    "tags": ["tag1", "newtag"]
  }
}
```

### AI Suggestion Endpoints

#### `POST /api/suggestions`
Generate AI suggestions for text improvement.

**Request:**
```json
{
  "documentId": "document_id", // Optional, if working with saved document
  "content": "Text to improve with AI suggestions",
  "promptTemplate": "make_professional", // Optional, use predefined template
  "customPrompt": "Make this more concise and formal", // Optional, custom instruction
  "selectedText": "portion to focus on" // Optional, if targeting specific section
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "id": "suggestion_id",
      "original": "Text to improve",
      "suggested": "Improved text suggestion",
      "explanation": "This suggestion improves formality and conciseness",
      "position": {
        "start": 0,
        "end": 16
      }
    }
  ],
  "metadata": {
    "promptType": "custom", // or "template"
    "modelUsed": "gpt-4",
    "processTime": 1.24 // seconds
  }
}
```

#### `POST /api/chat`
Interact with the AI assistant through chat.

**Request:**
```json
{
  "documentId": "document_id", // Optional
  "message": "Can you help me improve the second paragraph?",
  "conversationId": "conversation_id" // Optional, for continuing conversation
}
```

**Response:**
```json
{
  "response": "I'd be happy to help improve the second paragraph. Currently, it appears to be quite wordy and lacks clear structure. Would you like me to make it more concise, improve its organization, or focus on a particular aspect?",
  "conversationId": "conversation_id",
  "suggestions": [] // Optional, if AI provides specific text improvements
}
```

## AI Integration

### OpenAI Integration

The backend integrates with OpenAI's API using the Langchain library for enhanced context management. This integration powers both the structured suggestion capabilities and the free-form chat assistant.

### Key Components:

1. **AI Service**: Orchestrates communication with OpenAI, handling prompt creation, context management, and response parsing.

2. **Prompt Templates**: Pre-defined templates for common improvement requests (e.g., "make more concise", "improve grammar").

3. **Context Management**: Maintains document context during AI interactions to ensure relevant suggestions.

4. **Token Optimization**: Implements strategies to optimize token usage for cost efficiency:
   - Context windowing for large documents
   - Selective context inclusion
   - Response streaming for long outputs
   - Caching similar requests

### Prompt Structure

The system uses carefully engineered prompts to get high-quality suggestions from the AI model:

```
You are an expert writing assistant that helps improve text.
The user provides text and wants it to be {improvement_type}.

Original text:
{document_text}

Please provide specific improvements to make this text {improvement_type}.
Format your response as JSON with the following structure:
{
  "suggestions": [
    {
      "original": "original text segment",
      "suggested": "improved text segment",
      "explanation": "brief explanation of the improvement"
    }
  ]
}
```

### Error Handling

The AI integration includes robust error handling for:
- API rate limiting
- Token limit exceeded
- Service unavailability
- Malformed responses

The system implements exponential backoff for retries and fallback strategies for service degradation.

## Track Changes Implementation

The track changes functionality is powered by the `diff_service.py` module, which uses the diff-match-patch library to generate and manage text differences.

### Diff Generation Process

1. The original document text is stored
2. AI suggestions are received
3. The diff service compares original with suggested text
4. Differences are identified and classified (additions, deletions, modifications)
5. A structured diff format is generated that the frontend can render as track changes

### Diff Format

The system uses a specialized JSON format to represent text differences:

```json
{
  "diffs": [
    {
      "type": "unchanged",
      "text": "This is unchanged text. "
    },
    {
      "type": "deletion",
      "text": "This will be removed. "
    },
    {
      "type": "addition",
      "text": "This is new text. "
    },
    {
      "type": "unchanged",
      "text": "More unchanged text."
    }
  ],
  "metadata": {
    "changeCount": 2,
    "timestamp": "2023-09-03T14:25:00Z"
  }
}
```

### Change Management

The diff service also handles:
- Applying accepted changes to documents
- Rejecting changes while preserving document integrity
- Maintaining change history for tracking purposes
- Merging multiple suggestion sets into a coherent view

This implementation enables a familiar Microsoft Word-like track changes experience directly in the browser.

## Database Schema

The application uses MongoDB as its primary database with the following collections:

### Users Collection

```json
{
  "_id": ObjectId("user_id"),
  "email": "user@example.com",
  "passwordHash": "hashed_password",
  "firstName": "John",
  "lastName": "Doe",
  "createdAt": ISODate("2023-09-01T12:00:00Z"),
  "lastLogin": ISODate("2023-09-03T10:15:00Z"),
  "accountStatus": "active"
}
```

### Documents Collection

```json
{
  "_id": ObjectId("document_id"),
  "userId": ObjectId("user_id"), // null for anonymous documents
  "sessionId": "session_id", // for anonymous users
  "title": "Document Title",
  "description": "Document description",
  "createdAt": ISODate("2023-09-01T12:00:00Z"),
  "updatedAt": ISODate("2023-09-02T15:30:00Z"),
  "lastAccessedAt": ISODate("2023-09-03T09:45:00Z"),
  "isArchived": false,
  "tags": ["tag1", "tag2"],
  "currentVersionId": ObjectId("version_id")
}
```

### Document Versions Collection

```json
{
  "_id": ObjectId("version_id"),
  "documentId": ObjectId("document_id"),
  "versionNumber": 1,
  "content": "Document content text...",
  "createdAt": ISODate("2023-09-01T12:00:00Z"),
  "createdBy": ObjectId("user_id"), // or null for anonymous
  "changeDescription": "Initial version",
  "previousVersionId": null
}
```

### User Preferences Collection

```json
{
  "_id": ObjectId("preference_id"),
  "userId": ObjectId("user_id"),
  "theme": "light",
  "fontSize": 16,
  "defaultPromptCategories": ["professional", "concise"],
  "notificationSettings": {
    "email": true,
    "inApp": true
  },
  "privacySettings": {
    "shareAnalytics": false
  }
}
```

### AI Prompt Templates Collection

```json
{
  "_id": ObjectId("template_id"),
  "name": "Make Professional",
  "description": "Improves text to sound more professional and formal",
  "promptText": "Transform the following text to use professional language and formal tone...",
  "category": "tone",
  "isSystem": true,
  "createdAt": ISODate("2023-09-01T00:00:00Z"),
  "createdBy": null // system template
}
```

### AI Interactions Collection

```json
{
  "_id": ObjectId("interaction_id"),
  "userId": ObjectId("user_id"), // null for anonymous
  "sessionId": "session_id", // for anonymous users
  "documentId": ObjectId("document_id"),
  "promptTemplateId": ObjectId("template_id"), // null for custom prompts
  "customPrompt": "Make this paragraph more engaging", // null for template prompts
  "aiResponse": "AI response content...",
  "timestamp": ISODate("2023-09-03T14:25:00Z"),
  "acceptedSuggestions": 3,
  "rejectedSuggestions": 1
}
```

## Authentication

### JWT-based Authentication

The system uses JSON Web Tokens (JWT) for stateless authentication with separate access and refresh tokens:

- **Access Token**: Short-lived (1 hour) token for API access
- **Refresh Token**: Longer-lived (7 days) token for obtaining new access tokens

### Anonymous Sessions

The system also supports anonymous usage through secure session IDs:

1. A unique session ID is generated for each new anonymous user
2. This ID is stored in an HTTP-only secure cookie
3. Documents created during anonymous sessions are linked to the session ID
4. When a user registers, anonymous documents can be transferred to their account

### Security Measures

- Passwords are hashed using bcrypt with appropriate work factors
- JWT tokens use RS256 or HS256 algorithm with secure keys
- Token validation includes expiration and signature verification
- Rate limiting is applied to authentication endpoints
- Refresh token rotation is implemented for enhanced security

## Development Guidelines

### Coding Standards

- Follow PEP 8 Python style guide
- Use type hints for function parameters and return values
- Write docstrings for all modules, classes, and functions
- Keep functions small and focused on a single responsibility
- Use meaningful variable and function names

### Code Structure

- Place API endpoints in the `api` directory
- Implement business logic in the `services` directory
- Define database models in the `models` directory
- Place helper functions in the `utils` directory

### Error Handling

- Use appropriate HTTP status codes
- Return descriptive error messages
- Log errors with proper severity levels
- Handle exceptions gracefully

### API Design

- Follow RESTful principles
- Version the API as needed
- Use consistent naming conventions
- Document all endpoints

## Testing

The backend uses pytest for unit and integration testing.

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=. --cov-report=term-missing
```

### Test Coverage Requirements

- Minimum overall coverage: 80%
- API endpoints: 90% coverage
- Core services: 85% coverage
- Authentication: 95% coverage

### Test Types

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **API Tests**: Test API endpoints with requests
4. **Security Tests**: Verify authentication and authorization

## Deployment

### Docker Deployment

The backend can be deployed using Docker:

```bash
# Build Docker image
docker build -t ai-writing-backend .

# Run Docker container
docker run -p 5000:5000 --env-file .env ai-writing-backend
```

### Docker Compose

For local development with services:

```bash
# Start all services
docker-compose up

# Rebuild and start
docker-compose up --build
```

### Production Deployment

For production, consider:

1. Using Gunicorn as the WSGI server
2. Deploying behind Nginx for SSL termination
3. Setting up proper monitoring and logging
4. Using environment-specific configuration
5. Implementing health checks

## Performance Considerations

### Caching Strategy

The application uses Redis for caching:

1. **Document Cache**: Frequently accessed documents
2. **AI Response Cache**: Similar AI requests to reduce API calls
3. **User Session Cache**: Active user sessions
4. **Template Cache**: AI prompt templates

### Performance Optimization

- Database indexes on frequently queried fields
- Efficient MongoDB query patterns
- Asynchronous processing for non-blocking operations
- Pagination for large data sets
- Response compression

### Scaling Considerations

- Horizontal scaling for API servers
- Vertical scaling for database as needed
- Connection pooling for database connections
- Rate limiting for external API calls
- Load balancing for distributed deployment

## Security

### API Security

- Input validation for all requests
- Output encoding to prevent injection
- Rate limiting to prevent abuse
- CORS configuration for frontend access

### Data Protection

- Encryption of sensitive data at rest
- TLS for all communications
- Secure handling of API keys and secrets
- Regular security updates

### Authentication Security

- Secure password storage with bcrypt
- Short-lived JWT tokens
- Refresh token rotation
- Session invalidation capabilities

## Troubleshooting

### Logging

The application uses structured logging with different severity levels:

```python
# Example logging
logger.debug("Detailed debug information")
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
```

Logs can be configured to output to console, file, or external services.

### Common Issues

1. **Connection Issues**:
   - Check MongoDB and Redis connection strings
   - Verify network connectivity
   - Check for firewall restrictions

2. **Authentication Problems**:
   - Verify JWT secret keys
   - Check token expiration settings
   - Confirm proper token handling in requests

3. **AI Integration Issues**:
   - Validate OpenAI API key
   - Check API rate limits
   - Verify prompt structure

4. **Performance Problems**:
   - Check database indexes
   - Review caching implementation
   - Monitor resource utilization

## Contributing

We welcome contributions to the backend codebase. Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to ensure they pass
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Pull Request Process

1. Ensure all tests pass
2. Update documentation as needed
3. Add your changes to the CHANGELOG.md
4. Get approval from at least one maintainer

## License

This project is licensed under the MIT License - see the LICENSE file for details.