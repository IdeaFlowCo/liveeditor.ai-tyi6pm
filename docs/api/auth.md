# Authentication API

## Overview

The AI Writing Enhancement Platform uses JSON Web Tokens (JWT) for authentication. The authentication system supports both anonymous and authenticated usage paths while maintaining security for user data and documents.

### Authentication Strategy

- **JWT-based Authentication**: Secure, stateless authentication using JSON Web Tokens
- **Token Pair System**: Short-lived access tokens paired with longer-lived refresh tokens
- **Anonymous Sessions**: Support for immediate usage without registration
- **Seamless Transition**: Conversion from anonymous to registered accounts while preserving user data

### Token Handling

- **Access Token**: Short-lived (1 hour), used for API authorization
- **Refresh Token**: Longer-lived (7 days), used to obtain new access tokens
- **Token Storage**: HTTP-only, secure cookies (recommended) or secure local storage
- **CSRF Protection**: Implemented for cookie-based token storage

## Endpoints

### Login

Authenticates a user and returns access and refresh tokens.

**URL**: `POST /api/auth/login`

**Authentication Required**: No

#### Request Body

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Successful Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

#### Error Responses

- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Invalid credentials
- **429 Too Many Requests**: Rate limit exceeded

#### Example Request

```bash
curl -X POST https://api.aiwritingenhancement.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword123"}'
```

#### JavaScript Example

```javascript
async function login(email, password) {
  try {
    const response = await fetch('https://api.aiwritingenhancement.com/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    });
    
    if (!response.ok) {
      throw new Error('Login failed');
    }
    
    const data = await response.json();
    // Store tokens securely
    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}
```

### Register

Creates a new user account and returns access and refresh tokens.

**URL**: `POST /api/auth/register`

**Authentication Required**: No

#### Request Body

```json
{
  "email": "newuser@example.com",
  "password": "securepassword123",
  "first_name": "Jane",
  "last_name": "Smith"
}
```

#### Successful Response (201 Created)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user456",
    "email": "newuser@example.com",
    "first_name": "Jane",
    "last_name": "Smith"
  }
}
```

#### Error Responses

- **400 Bad Request**: Invalid input data or password requirements not met
- **409 Conflict**: Email already registered
- **429 Too Many Requests**: Rate limit exceeded

#### Example Request

```bash
curl -X POST https://api.aiwritingenhancement.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "password": "securepassword123", "first_name": "Jane", "last_name": "Smith"}'
```

#### JavaScript Example

```javascript
async function register(email, password, firstName, lastName) {
  try {
    const response = await fetch('https://api.aiwritingenhancement.com/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        email, 
        password, 
        first_name: firstName, 
        last_name: lastName 
      })
    });
    
    if (!response.ok) {
      throw new Error('Registration failed');
    }
    
    const data = await response.json();
    // Store tokens securely
    return data;
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
}
```

### Refresh Token

Gets a new access token using a valid refresh token.

**URL**: `POST /api/auth/refresh`

**Authentication Required**: No (Uses refresh token)

#### Request Body

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Successful Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

#### Error Responses

- **400 Bad Request**: Invalid input format
- **401 Unauthorized**: Invalid or expired refresh token
- **429 Too Many Requests**: Rate limit exceeded

#### Example Request

```bash
curl -X POST https://api.aiwritingenhancement.com/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}'
```

#### JavaScript Example

```javascript
async function refreshToken(refreshToken) {
  try {
    const response = await fetch('https://api.aiwritingenhancement.com/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    if (!response.ok) {
      throw new Error('Token refresh failed');
    }
    
    const data = await response.json();
    // Update stored access token
    return data;
  } catch (error) {
    console.error('Token refresh error:', error);
    throw error;
  }
}
```

### Logout

Invalidates the current access and refresh tokens.

**URL**: `POST /api/auth/logout`

**Authentication Required**: Yes

#### Request Headers

```
Authorization: Bearer {access_token}
```

#### Query Parameters

- `all_devices` (optional): Boolean. If true, invalidates all refresh tokens for the user.

#### Successful Response (200 OK)

```json
{
  "message": "Successfully logged out"
}
```

#### Error Responses

- **401 Unauthorized**: Invalid or missing access token
- **500 Server Error**: Logout operation failed

#### Example Request

```bash
curl -X POST https://api.aiwritingenhancement.com/api/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### JavaScript Example

```javascript
async function logout(accessToken, logoutFromAllDevices = false) {
  try {
    const url = new URL('https://api.aiwritingenhancement.com/api/auth/logout');
    
    if (logoutFromAllDevices) {
      url.searchParams.append('all_devices', 'true');
    }
    
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Logout failed');
    }
    
    // Clear stored tokens
    return await response.json();
  } catch (error) {
    console.error('Logout error:', error);
    throw error;
  }
}
```

### Create Anonymous Session

Creates an anonymous session for immediate usage without registration.

**URL**: `POST /api/auth/anonymous`

**Authentication Required**: No

#### Request Body

Empty or can be omitted.

#### Successful Response (201 Created)

```json
{
  "session_id": "anon_session_12345",
  "expires_at": "2023-07-15T15:30:45Z"
}
```

#### Error Responses

- **429 Too Many Requests**: Rate limit exceeded
- **500 Server Error**: Session creation failed

#### Example Request

```bash
curl -X POST https://api.aiwritingenhancement.com/api/auth/anonymous
```

#### JavaScript Example

```javascript
async function createAnonymousSession() {
  try {
    const response = await fetch('https://api.aiwritingenhancement.com/api/auth/anonymous', {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error('Failed to create anonymous session');
    }
    
    const data = await response.json();
    // Store session ID securely
    return data;
  } catch (error) {
    console.error('Anonymous session error:', error);
    throw error;
  }
}
```

### Convert Anonymous to Registered

Converts an anonymous session to a registered user account while preserving user data.

**URL**: `POST /api/auth/convert`

**Authentication Required**: No (Uses anonymous session ID)

#### Request Body

```json
{
  "session_id": "anon_session_12345",
  "email": "newuser@example.com",
  "password": "securepassword123",
  "first_name": "Jane",
  "last_name": "Smith"
}
```

#### Successful Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user789",
    "email": "newuser@example.com",
    "first_name": "Jane",
    "last_name": "Smith"
  },
  "converted_data": {
    "documents": 2,
    "preferences": true
  }
}
```

#### Error Responses

- **400 Bad Request**: Invalid input data or password requirements not met
- **404 Not Found**: Invalid or expired anonymous session
- **409 Conflict**: Email already registered
- **429 Too Many Requests**: Rate limit exceeded

#### Example Request

```bash
curl -X POST https://api.aiwritingenhancement.com/api/auth/convert \
  -H "Content-Type: application/json" \
  -d '{"session_id": "anon_session_12345", "email": "newuser@example.com", "password": "securepassword123", "first_name": "Jane", "last_name": "Smith"}'
```

#### JavaScript Example

```javascript
async function convertAnonymousToRegistered(sessionId, email, password, firstName, lastName) {
  try {
    const response = await fetch('https://api.aiwritingenhancement.com/api/auth/convert', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionId,
        email,
        password,
        first_name: firstName,
        last_name: lastName
      })
    });
    
    if (!response.ok) {
      throw new Error('Conversion failed');
    }
    
    const data = await response.json();
    // Store tokens and clear anonymous session
    return data;
  } catch (error) {
    console.error('Conversion error:', error);
    throw error;
  }
}
```

### Request Password Reset

Initiates the password reset process by sending a reset token to the user's email.

**URL**: `POST /api/auth/password-reset/request`

**Authentication Required**: No

#### Request Body

```json
{
  "email": "user@example.com"
}
```

#### Successful Response (200 OK)

```json
{
  "message": "If an account with this email exists, a password reset link has been sent"
}
```

> Note: The response is intentionally vague to prevent email enumeration.

#### Error Responses

- **400 Bad Request**: Invalid email format
- **429 Too Many Requests**: Rate limit exceeded

#### Example Request

```bash
curl -X POST https://api.aiwritingenhancement.com/api/auth/password-reset/request \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

#### JavaScript Example

```javascript
async function requestPasswordReset(email) {
  try {
    const response = await fetch('https://api.aiwritingenhancement.com/api/auth/password-reset/request', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email })
    });
    
    if (!response.ok) {
      throw new Error('Password reset request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Password reset request error:', error);
    throw error;
  }
}
```

### Reset Password

Resets a user's password using a valid reset token.

**URL**: `POST /api/auth/password-reset/confirm`

**Authentication Required**: No (Uses reset token)

#### Request Body

```json
{
  "token": "reset_token_abc123",
  "new_password": "newsecurepassword456"
}
```

#### Successful Response (200 OK)

```json
{
  "message": "Password has been reset successfully",
  "can_login": true
}
```

#### Error Responses

- **400 Bad Request**: Invalid password format or token missing
- **401 Unauthorized**: Invalid or expired token
- **429 Too Many Requests**: Rate limit exceeded

#### Example Request

```bash
curl -X POST https://api.aiwritingenhancement.com/api/auth/password-reset/confirm \
  -H "Content-Type: application/json" \
  -d '{"token": "reset_token_abc123", "new_password": "newsecurepassword456"}'
```

#### JavaScript Example

```javascript
async function resetPassword(token, newPassword) {
  try {
    const response = await fetch('https://api.aiwritingenhancement.com/api/auth/password-reset/confirm', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        token, 
        new_password: newPassword 
      })
    });
    
    if (!response.ok) {
      throw new Error('Password reset failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Password reset error:', error);
    throw error;
  }
}
```

### Verify Email

Verifies a user's email address using a verification token.

**URL**: `POST /api/auth/verify-email`

**Authentication Required**: No (Uses verification token)

#### Request Body

```json
{
  "token": "verify_email_token_xyz789"
}
```

#### Successful Response (200 OK)

```json
{
  "message": "Email address has been verified successfully"
}
```

#### Error Responses

- **400 Bad Request**: Token missing
- **401 Unauthorized**: Invalid or expired token
- **429 Too Many Requests**: Rate limit exceeded

#### Example Request

```bash
curl -X POST https://api.aiwritingenhancement.com/api/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "verify_email_token_xyz789"}'
```

#### JavaScript Example

```javascript
async function verifyEmail(token) {
  try {
    const response = await fetch('https://api.aiwritingenhancement.com/api/auth/verify-email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ token })
    });
    
    if (!response.ok) {
      throw new Error('Email verification failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Email verification error:', error);
    throw error;
  }
}
```

### Validate Session

Validates the current session and returns user information.

**URL**: `GET /api/auth/session`

**Authentication Required**: Yes

#### Request Headers

```
Authorization: Bearer {access_token}
```

#### Successful Response (200 OK)

```json
{
  "user": {
    "id": "user123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "email_verified": true
  },
  "session_valid": true
}
```

#### Error Responses

- **401 Unauthorized**: Invalid or expired access token

#### Example Request

```bash
curl -X GET https://api.aiwritingenhancement.com/api/auth/session \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### JavaScript Example

```javascript
async function validateSession(accessToken) {
  try {
    const response = await fetch('https://api.aiwritingenhancement.com/api/auth/session', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Session validation failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Session validation error:', error);
    throw error;
  }
}
```

## Request and Response Schemas

### Login Request Schema

```json
{
  "type": "object",
  "required": ["email", "password"],
  "properties": {
    "email": {
      "type": "string",
      "format": "email",
      "description": "User's email address"
    },
    "password": {
      "type": "string",
      "minLength": 8,
      "description": "User's password"
    }
  }
}
```

### Registration Request Schema

```json
{
  "type": "object",
  "required": ["email", "password", "first_name", "last_name"],
  "properties": {
    "email": {
      "type": "string",
      "format": "email",
      "description": "User's email address"
    },
    "password": {
      "type": "string",
      "minLength": 10,
      "description": "User's password - must be at least 10 characters and include a combination of letters, numbers, and special characters"
    },
    "first_name": {
      "type": "string",
      "description": "User's first name"
    },
    "last_name": {
      "type": "string",
      "description": "User's last name"
    }
  }
}
```

### Token Response Schema

```json
{
  "type": "object",
  "required": ["access_token", "token_type", "expires_in"],
  "properties": {
    "access_token": {
      "type": "string",
      "description": "JWT access token for API authorization"
    },
    "refresh_token": {
      "type": "string",
      "description": "JWT refresh token to obtain new access tokens"
    },
    "token_type": {
      "type": "string",
      "enum": ["Bearer"],
      "description": "Token type, always 'Bearer'"
    },
    "expires_in": {
      "type": "integer",
      "description": "Access token validity period in seconds"
    },
    "user": {
      "type": "object",
      "description": "User information",
      "properties": {
        "id": {
          "type": "string",
          "description": "Unique user identifier"
        },
        "email": {
          "type": "string",
          "format": "email",
          "description": "User's email address"
        },
        "first_name": {
          "type": "string",
          "description": "User's first name"
        },
        "last_name": {
          "type": "string",
          "description": "User's last name"
        },
        "email_verified": {
          "type": "boolean",
          "description": "Indicates if the user's email has been verified"
        }
      }
    }
  }
}
```

### Anonymous Session Schema

```json
{
  "type": "object",
  "required": ["session_id", "expires_at"],
  "properties": {
    "session_id": {
      "type": "string",
      "description": "Unique identifier for the anonymous session"
    },
    "expires_at": {
      "type": "string",
      "format": "date-time",
      "description": "Expiration timestamp for the session (ISO 8601 format)"
    }
  }
}
```

## Error Responses

### Common Authentication Errors

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

#### 400 Bad Request

Returned when the request contains invalid data:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "The request data is invalid",
    "details": {
      "email": ["Email is not a valid email address"]
    }
  }
}
```

#### 401 Unauthorized

Returned for authentication failures:

```json
{
  "error": {
    "code": "authentication_failed",
    "message": "Invalid credentials"
  }
}
```

```json
{
  "error": {
    "code": "invalid_token",
    "message": "Access token is invalid or expired"
  }
}
```

#### 403 Forbidden

Returned when a user is authenticated but not authorized:

```json
{
  "error": {
    "code": "access_denied",
    "message": "You don't have permission to perform this action"
  }
}
```

#### 404 Not Found

Returned when a requested resource is not found:

```json
{
  "error": {
    "code": "resource_not_found",
    "message": "The requested resource was not found"
  }
}
```

#### 409 Conflict

Returned when there's a conflict with the current state:

```json
{
  "error": {
    "code": "email_already_exists",
    "message": "A user with this email address already exists"
  }
}
```

#### 429 Too Many Requests

Returned when rate limits are exceeded:

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Too many requests, please try again later",
    "details": {
      "retry_after": 30 // Seconds until retry is allowed
    }
  }
}
```

#### 500 Internal Server Error

Returned for server-side errors:

```json
{
  "error": {
    "code": "server_error",
    "message": "An unexpected error occurred"
  }
}
```

## Authentication Flows

### Standard Login Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth Service
    participant User Database
    
    Client->>API: POST /api/auth/login
    API->>Auth Service: Validate credentials
    Auth Service->>User Database: Check user
    User Database-->>Auth Service: User found
    Auth Service->>Auth Service: Verify password
    Auth Service->>Auth Service: Generate tokens
    Auth Service-->>API: Tokens + user info
    API-->>Client: 200 OK with tokens
    
    Note over Client,API: Later API requests
    Client->>API: Request with access token
    API->>Auth Service: Validate token
    Auth Service-->>API: Token valid
    API-->>Client: Request response
    
    Note over Client,API: When access token expires
    Client->>API: POST /api/auth/refresh
    API->>Auth Service: Validate refresh token
    Auth Service->>Auth Service: Generate new tokens
    Auth Service-->>API: New access token
    API-->>Client: 200 OK with new token
```

#### Token Storage Best Practices

1. **HTTP-only Cookies**: For web applications, store tokens in HTTP-only, secure cookies to prevent XSS attacks
2. **Secure Storage**: For mobile or desktop apps, use secure, encrypted storage mechanisms
3. **Access Token**: Short-lived, used for API authorization
4. **Refresh Token**: Longer-lived, stored securely, used only to obtain new access tokens

#### Session Management

1. **Token Expiration**: Access tokens expire after 1 hour, refresh tokens after 7 days
2. **Token Renewal**: Proactively refresh access tokens before expiration
3. **Logout Handling**: Clear tokens on logout, invalidate refresh token on server
4. **Multiple Devices**: Support concurrent sessions across devices with individual refresh tokens

### Anonymous to Registered Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth Service
    participant Session Store
    participant User Database
    
    Client->>API: POST /api/auth/anonymous
    API->>Auth Service: Create anonymous session
    Auth Service->>Session Store: Store session
    Session Store-->>Auth Service: Session created
    Auth Service-->>API: Session info
    API-->>Client: 201 Created with session ID
    
    Note over Client,API: Client uses app anonymously
    Client->>API: Requests with session ID
    API->>Session Store: Validate session
    Session Store-->>API: Session valid
    API-->>Client: Resource access
    
    Note over Client,API: User decides to register
    Client->>API: POST /api/auth/convert
    API->>Auth Service: Convert anonymous to registered
    Auth Service->>User Database: Create user
    Auth Service->>Session Store: Get anonymous data
    Auth Service->>User Database: Associate data with user
    Auth Service->>Auth Service: Generate tokens
    Auth Service-->>API: User & token info
    API-->>Client: 200 OK with tokens and user info
```

#### Data Preservation During Conversion

1. **Document Preservation**: Any documents created during the anonymous session are transferred to the new user account
2. **Preference Preservation**: User preferences and settings are maintained
3. **History Preservation**: Document history and versions are maintained
4. **Session Invalidation**: The anonymous session is invalidated after successful conversion

### Password Reset Flow

```mermaid
sequenceDiagram
    participant User
    participant Client
    participant API
    participant Auth Service
    participant Email Service
    participant Token Store
    
    User->>Client: Request password reset
    Client->>API: POST /api/auth/password-reset/request
    API->>Auth Service: Initiate password reset
    Auth Service->>Token Store: Generate reset token
    Auth Service->>Email Service: Send reset email
    Email Service-->>User: Password reset email
    Auth Service-->>API: Request processed
    API-->>Client: 200 OK with message
    
    User->>Client: Click reset link & enter new password
    Client->>API: POST /api/auth/password-reset/confirm
    API->>Auth Service: Verify token & update password
    Auth Service->>Token Store: Validate token
    Token Store-->>Auth Service: Token valid
    Auth Service->>User Database: Update password
    Auth Service-->>API: Password updated
    API-->>Client: 200 OK with success message
```

#### Security Considerations

1. **Token Expiration**: Reset tokens expire after 1 hour
2. **Single Use**: Reset tokens are invalidated after use
3. **Rate Limiting**: Password reset requests are rate-limited to prevent abuse
4. **Secure Delivery**: Reset links are delivered via email only
5. **Ambiguous Responses**: API responses do not reveal whether an email exists in the system