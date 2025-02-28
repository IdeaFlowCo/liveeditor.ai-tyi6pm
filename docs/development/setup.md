# Development Environment Setup Guide

## Introduction

This documentation provides comprehensive setup instructions for developers working on the AI Writing Enhancement Platform. This guide will help you set up a local development environment that closely mirrors the production environment, ensuring consistency across development and deployment.

The platform consists of a React frontend for document editing, a Python Flask backend for API services and AI integration, MongoDB for document storage, and connections to external services like OpenAI for AI capabilities.

## Prerequisites

Before setting up the development environment, ensure you have the following software installed:

| Software | Minimum Version | Notes |
|----------|-----------------|-------|
| Docker | 20.10.0+ | Required for containerized development |
| Docker Compose | 2.0.0+ | For orchestrating multi-container setup |
| Git | 2.20.0+ | For source control |
| Node.js | 16.14.0+ | For frontend development (if not using Docker) |
| npm | 8.0.0+ | For package management (if not using Docker) |
| Python | 3.10+ | For backend development (if not using Docker) |
| pip | 21.0.0+ | For Python package management (if not using Docker) |
| MongoDB | 6.0+ | For local database (if not using Docker) |

### Hardware Recommendations

- **CPU**: 4+ cores recommended
- **Memory**: 8GB+ RAM (16GB+ recommended for running all services)
- **Storage**: 20GB+ free disk space
- **Network**: Stable internet connection for API access and dependencies

## Getting Started

### Cloning the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-writing-enhancement.git

# Navigate to the project directory
cd ai-writing-enhancement
```

### Project Structure Overview

The repository has the following structure:

```
ai-writing-enhancement/
├── docs/                     # Documentation
├── frontend/                 # React frontend application
│   ├── public/               # Static files
│   ├── src/                  # Source code
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── redux/            # Redux store configuration
│   │   ├── services/         # API services
│   │   └── utils/            # Utility functions
│   ├── package.json          # Frontend dependencies
│   └── .env.example          # Example environment variables
├── backend/                  # Python Flask backend
│   ├── api/                  # API endpoints
│   ├── ai/                   # AI service integration
│   ├── models/               # Data models
│   ├── tests/                # Backend tests
│   ├── requirements.txt      # Backend dependencies
│   └── .env.example          # Example environment variables
├── docker/                   # Docker configuration
│   ├── frontend/             # Frontend Docker configuration
│   ├── backend/              # Backend Docker configuration
│   └── mongodb/              # MongoDB Docker configuration
├── docker-compose.yml        # Docker Compose configuration
├── .env.example              # Root example environment variables
└── README.md                 # Project overview
```

## Docker Compose Setup

The recommended way to set up the development environment is using Docker Compose, which will set up all required services with proper networking.

### Setting Up with Docker Compose

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your settings (especially API keys)
# Use your favorite editor to modify the .env file
# For example:
# nano .env
# or
# code .env

# Start all services
docker-compose up

# Alternatively, run in detached mode
docker-compose up -d

# To view logs when running in detached mode
docker-compose logs -f

# To view logs for a specific service
docker-compose logs -f backend
```

### Environment File Configuration

Here's an example of what your `.env` file should contain:

```
# Application Settings
APP_ENV=development
DEBUG=true

# Port Configuration
BACKEND_PORT=5000
FRONTEND_PORT=3000

# Database Configuration
MONGODB_URI=mongodb://mongodb:27017/ai_writing
MONGODB_USER=admin
MONGODB_PASSWORD=dev_password

# AI Service Configuration
OPENAI_API_KEY=your_openai_api_key
AI_MODEL=gpt-4
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2000

# Authentication Configuration
JWT_SECRET=your_random_jwt_secret_for_development
JWT_EXPIRATION=3600

# Logging Configuration
LOG_LEVEL=INFO
```

Make sure to replace `your_openai_api_key` with your actual OpenAI API key and set a strong random string for `JWT_SECRET`.

## Backend Setup

### Setup with Docker (Recommended)

The backend service is included in Docker Compose. You can access it at `http://localhost:5000` once Docker Compose is running.

### Manual Setup (Alternative)

If you prefer to run the backend outside of Docker:

```bash
# Navigate to backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy the example environment file
cp .env.example .env
# Edit the .env file with your settings

# Run the development server
python run.py
```

### Backend API Testing

You can test that the backend is working by accessing the health check endpoint:

```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## Frontend Setup

### Setup with Docker (Recommended)

The frontend service is included in Docker Compose. You can access it at `http://localhost:3000` once Docker Compose is running.

### Manual Setup (Alternative)

If you prefer to run the frontend outside of Docker:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy the example environment file
cp .env.example .env
# Edit the .env file with your settings

# Start the development server
npm start
```

The frontend development server includes:
- Hot reloading for immediate feedback during development
- React DevTools integration
- Redux DevTools integration (for state management debugging)

## Database Configuration

### MongoDB with Docker Compose

MongoDB is automatically set up when using Docker Compose. The database will be accessible at:
- Host: `localhost` (or `mongodb` from within Docker containers)
- Port: `27017`
- Database name: `ai_writing` (default)
- Authentication: Configured via environment variables

### MongoDB Express Admin Interface

A MongoDB Express admin interface is also included in the Docker Compose setup and accessible at `http://localhost:8081`.

### Manual MongoDB Setup (Alternative)

If you prefer to install MongoDB locally:

```bash
# On macOS (using Homebrew)
brew install mongodb-community
brew services start mongodb-community

# On Ubuntu
sudo apt-get install -y mongodb
sudo systemctl start mongodb

# On Windows
# Download and install from https://www.mongodb.com/try/download/community
```

After installation, create the database and user:

```bash
# Connect to MongoDB
mongo

# Create database and user
use ai_writing
db.createUser({
  user: "admin",
  pwd: "dev_password",
  roles: ["readWrite", "dbAdmin"]
})
```

## External Service Configuration

### OpenAI API Setup

The application requires an OpenAI API key to function properly:

1. Create an account at [OpenAI](https://openai.com)
2. Navigate to the API keys section and create a new key
3. Add the key to your `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

### Rate Limits and Token Usage

Be aware that the OpenAI API has rate limits and token usage limits. For development:

- Use a lower-tier model (`gpt-3.5-turbo` instead of `gpt-4`) to reduce costs
- Implement caching for repeated requests
- Monitor your usage in the OpenAI dashboard

## Environment Variables

The following table lists all environment variables used in the application:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| APP_ENV | Application environment | development | Yes |
| DEBUG | Enable debug mode | true | No |
| BACKEND_PORT | Port for backend service | 5000 | Yes |
| FRONTEND_PORT | Port for frontend service | 3000 | Yes |
| MONGODB_URI | MongoDB connection string | mongodb://mongodb:27017/ai_writing | Yes |
| MONGODB_USER | MongoDB username | admin | Yes |
| MONGODB_PASSWORD | MongoDB password | dev_password | Yes |
| OPENAI_API_KEY | OpenAI API key | None | Yes |
| AI_MODEL | AI model to use | gpt-4 | Yes |
| AI_TEMPERATURE | AI generation temperature | 0.7 | No |
| AI_MAX_TOKENS | Maximum tokens for AI response | 2000 | No |
| JWT_SECRET | Secret for JWT signing | None | Yes |
| JWT_EXPIRATION | JWT expiration time in seconds | 3600 | No |
| LOG_LEVEL | Logging level | INFO | No |

## Port Allocations

The following ports are used by default:

| Service | Container Port | Host Port | Description |
|---------|---------------|-----------|-------------|
| Frontend | 3000 | 3000 | React development server |
| Backend | 5000 | 5000 | Flask API server |
| MongoDB | 27017 | 27017 | MongoDB database |
| MongoDB Express | 8081 | 8081 | MongoDB admin interface |

If you need to change these ports (e.g., due to conflicts with other services), modify the port mappings in the `docker-compose.yml` file and update the corresponding environment variables.

## Development Workflow

### Running Services

```bash
# Start all services
docker-compose up

# Start a specific service
docker-compose up frontend

# Rebuild and start services after dependency changes
docker-compose up --build

# Restart a specific service
docker-compose restart backend

# Stop all services
docker-compose down

# Stop all services and remove volumes (will delete database data)
docker-compose down -v
```

### Code Changes

When using Docker Compose:
- Frontend code changes should apply automatically with hot reloading
- Backend code changes require restarting the backend service:
  ```bash
  docker-compose restart backend
  ```

When running services manually:
- Frontend: Changes apply automatically with hot reloading
- Backend: Most changes require restarting the Flask development server

### Accessing Logs

```bash
# View logs for all services
docker-compose logs -f

# View logs for a specific service
docker-compose logs -f backend
```

### Running Tests

```bash
# Run backend tests
docker-compose exec backend pytest

# Run frontend tests
docker-compose exec frontend npm test
```

### Working with the Database

```bash
# Access MongoDB shell
docker-compose exec mongodb mongo -u admin -p dev_password ai_writing

# Import sample data
docker-compose exec backend python -m scripts.seed_data
```

## Troubleshooting

Common issues and their solutions:

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Docker Compose fails to start | Port conflict | Check if ports 3000, 5000, or 27017 are already in use |
| MongoDB connection error | Incorrect credentials or MongoDB not running | Verify MongoDB is running and credentials are correct |
| OpenAI API errors | Invalid API key or rate limit exceeded | Verify your API key and check usage limits |
| Frontend fails to connect to backend | CORS or network issue | Check CORS settings and ensure backend is running |
| "Module not found" errors | Missing dependencies | Run `npm install` in frontend or `pip install -r requirements.txt` in backend |
| Changes not reflecting | Caching issue | Hard refresh browser (Ctrl+F5) or restart the service |

### Common Error Messages and Solutions

#### Connection to Backend Failed

```
Failed to fetch: http://localhost:5000/api/health
```

Solutions:
- Ensure the backend service is running
- Check if the port is correctly mapped in Docker Compose
- Verify there are no CORS issues in the backend configuration

#### MongoDB Connection Error

```
MongoNetworkError: failed to connect to server [mongodb:27017]
```

Solutions:
- Ensure MongoDB is running
- Check MongoDB credentials in the environment variables
- Verify network connectivity between services

#### OpenAI API Error

```
Error: Authentication error: Invalid API key provided
```

Solution:
- Verify your OpenAI API key in the `.env` file
- Ensure the API key has not expired or been revoked

#### Docker Disk Space Issue

```
ERROR: no space left on device
```

Solution:
- Free up disk space
- Clean up unused Docker resources:
  ```bash
  docker system prune -a
  ```

## Next Steps

After setting up your development environment, you can:

1. Explore the codebase to understand the application architecture
2. Review the technical specifications in `docs/technical-specifications.md`
3. Check out the API documentation in `docs/api/`
4. Try implementing a small feature or fixing a bug
5. Set up your IDE for the project (recommended extensions for VSCode are listed in `.vscode/extensions.json`)

For more information or assistance:
- Check the project wiki on GitHub
- Join the developer Slack channel
- Attend weekly developer meetings (schedule in the wiki)

Happy coding!