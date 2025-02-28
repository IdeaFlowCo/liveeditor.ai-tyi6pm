# AI Writing Enhancement Interface

[![Build Status](https://img.shields.io/github/workflow/status/example/ai-writing-enhancement/main)](https://github.com/example/ai-writing-enhancement/actions)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://semver.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An AI-powered writing enhancement platform that helps users improve their content through intelligent suggestions and edits with an intuitive Microsoft Word-like review interface.

## Introduction

The AI Writing Enhancement Interface streamlines the writing process by providing AI-assisted improvements with a familiar review interface. It addresses the common challenge writers face in efficiently revising content by offering contextual suggestions directly inline with the document, reducing editing time while improving content quality.

Designed for content creators, students, professionals, casual writers, editors, and educational institutions, this platform makes advanced AI writing assistance accessible and intuitive.

## Features

✨ **Rich Document Editor** - Paste, upload, or directly type content with support for standard text formatting

🤖 **AI-Powered Suggestions** - Receive intelligent, contextual improvement suggestions for your writing

📝 **Track Changes Interface** - Review, accept, or reject suggestions with a familiar Microsoft Word-like experience

🧰 **Improvement Templates** - Use predefined prompts like "Make it shorter" or "More professional tone" without writing complex instructions

💬 **AI Assistant Chat** - Engage in free-form conversation with the AI about your document for customized help

🔒 **No Login Required** - Start using immediately without creating an account

👤 **Optional User Accounts** - Create an account to save and retrieve documents across sessions

📱 **Responsive Design** - Access from desktop or mobile devices with an optimized experience

## Technology Stack

### Frontend
- [React 18](https://reactjs.org/) - UI framework
- [TypeScript 4.9+](https://www.typescriptlang.org/) - Type safety
- [ProseMirror](https://prosemirror.net/) - Rich text editor with track changes capabilities
- [TailwindCSS](https://tailwindcss.com/) - Styling
- [Redux Toolkit](https://redux-toolkit.js.org/) - State management

### Backend
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Python 3.10+](https://www.python.org/) - Server-side language
- [Langchain](https://github.com/hwchase17/langchain) - AI orchestration
- [MongoDB](https://www.mongodb.com/) - Document storage
- [Redis](https://redis.io/) - Caching and session management

### External Services
- [OpenAI API](https://openai.com/) - AI language model integration
- [AWS Services](https://aws.amazon.com/) - Hosting and infrastructure

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Python 3.10+
- MongoDB 6.0
- Redis 7.0
- OpenAI API key

### Frontend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/example/ai-writing-enhancement.git
   cd ai-writing-enhancement
   ```

2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

3. Create a `.env` file in the `frontend` directory:
   ```
   REACT_APP_API_URL=http://localhost:5000/api
   ```

4. Start the development server:
   ```bash
   npm start
   ```

### Backend Setup

1. Set up a Python virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the `backend` directory:
   ```
   FLASK_APP=app.py
   FLASK_ENV=development
   MONGODB_URI=mongodb://localhost:27017/ai_writing
   REDIS_URL=redis://localhost:6379/0
   OPENAI_API_KEY=your_openai_api_key
   JWT_SECRET_KEY=your_jwt_secret
   ```

4. Start the Flask server:
   ```bash
   flask run
   ```

## Usage

### Document Improvement Workflow

1. **Input Document**: Paste text, upload a file, or type directly in the editor
2. **Request Suggestions**: Select text (optional) and choose an improvement template from the sidebar, or use the AI chat
3. **Review Suggestions**: View AI-suggested changes inline with track changes formatting
4. **Accept or Reject**: Review each suggestion and accept or reject as needed
5. **Save Document**: Optionally create an account to save your improved document

### Anonymous vs. Authenticated Usage

- **Anonymous**: Start using immediately, with documents stored in your browser session
- **Authenticated**: Create an account to save documents and access them across devices and sessions

## Development

### Testing

Run frontend tests:
```bash
cd frontend
npm test
```

Run backend tests:
```bash
cd backend
pytest
```

### Code Style

This project uses:
- ESLint and Prettier for JavaScript/TypeScript
- Black and isort for Python

Format frontend code:
```bash
cd frontend
npm run format
```

Format backend code:
```bash
cd backend
black .
isort .
```

### Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for more details.

## Deployment

### Docker Deployment

A Docker Compose setup is available for easy deployment:

```bash
docker-compose up -d
```

### AWS Deployment

The application can be deployed to AWS using:
- Amazon ECS for containerized services
- MongoDB Atlas for database
- Amazon ElastiCache for Redis
- Amazon S3 and CloudFront for static assets

Detailed deployment instructions are available in the [deployment documentation](docs/deployment.md).

## Project Structure

```
ai-writing-enhancement/
├── frontend/                  # React frontend application
│   ├── public/                # Static assets
│   ├── src/                   # Source code
│   │   ├── components/        # React components
│   │   ├── services/          # API services
│   │   ├── store/             # Redux store
│   │   └── utils/             # Utility functions
│   └── package.json           # Frontend dependencies
├── backend/                   # Flask backend API
│   ├── app.py                 # Application entry point
│   ├── config.py              # Configuration management
│   ├── routes/                # API routes
│   ├── services/              # Business logic
│   ├── models/                # Data models
│   └── requirements.txt       # Backend dependencies
├── docker-compose.yml         # Docker services configuration
├── docs/                      # Documentation
├── tests/                     # End-to-end tests
├── LICENSE                    # License information
└── README.md                  # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [OpenAI](https://openai.com/) for the AI capabilities
- [ProseMirror](https://prosemirror.net/) for the rich text editor
- [Langchain](https://github.com/hwchase17/langchain) for AI orchestration
- All the developers of the open-source libraries used in this project