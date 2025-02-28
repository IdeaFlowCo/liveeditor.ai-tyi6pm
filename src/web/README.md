# AI Writing Enhancement Interface - Frontend

![React](https://img.shields.io/badge/React-18.2.0-blue) ![TypeScript](https://img.shields.io/badge/TypeScript-5.1.6-blue) ![ProseMirror](https://img.shields.io/badge/ProseMirror-1.19.0-green) ![Redux Toolkit](https://img.shields.io/badge/Redux%20Toolkit-1.9.5-purple) ![License](https://img.shields.io/badge/license-MIT-green)

This is the frontend application for an AI-powered writing enhancement interface that enables users to improve written content through intelligent suggestions and edits, using Microsoft Word-like track changes functionality.

## Project Overview

The AI Writing Enhancement Interface provides a browser-based document editor with integrated AI capabilities that suggest improvements directly within the text. Key features include:

- Rich text editor with familiar Microsoft Word-like interface
- AI-powered writing suggestions displayed as track changes
- Dual interaction modes: guided improvement prompts and free-form AI chat
- Anonymous usage without login requirement
- User account system with document storage capabilities

The frontend application is built with React, TypeScript, and ProseMirror, providing a responsive and intuitive user experience for both casual and professional writers.

## Getting Started

### Prerequisites

- Node.js >= 16.0.0
- npm >= 8.0.0
- Modern web browser (Chrome 83+, Firefox 78+, Safari 14+, Edge 84+)

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd src/web
```

2. Install dependencies
```bash
npm install
```

3. Create a `.env` file based on `.env.example` and configure environment variables

4. Start the development server
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Available Scripts

All available scripts are defined in `package.json`:

- `npm run dev` - Start the development server with hot reload using Vite
- `npm run build` - Build the application for production
- `npm run preview` - Locally preview the production build
- `npm run test` - Run the test suite with Jest
- `npm run test:watch` - Run tests in watch mode
- `npm run test:coverage` - Run tests with coverage report
- `npm run lint` - Lint the codebase using ESLint
- `npm run lint:fix` - Fix linting issues automatically
- `npm run format` - Format code with Prettier
- `npm run typecheck` - Check TypeScript types without emitting code

## Project Structure

The project follows a feature-based structure with clear separation of concerns:

```
src/
├── api/               # API client configurations and service calls
├── assets/            # Static assets like images, fonts, etc.
├── components/        # Reusable UI components
│   ├── common/        # Generic components used across the app
│   ├── editor/        # ProseMirror editor components
│   ├── sidebar/       # AI sidebar components
│   └── track-changes/ # Track changes implementation
├── contexts/          # React context providers
├── hooks/             # Custom React hooks
├── lib/               # Third-party library wrappers and adapters
├── pages/             # Top-level pages/routes
├── store/             # Redux store configuration
│   ├── slices/        # Redux slices for feature-based state
│   └── middleware/    # Custom Redux middleware
├── styles/            # Global styles and Tailwind configuration
├── types/             # TypeScript type definitions
├── utils/             # Utility functions and helpers
├── App.tsx            # Main application component
└── main.tsx           # Application entry point
```

The application uses TypeScript path aliases for cleaner imports, configured in `tsconfig.json`. For example:

```typescript
// Instead of this:
import Button from '../../../components/common/Button';

// You can use this:
import Button from '@components/common/Button';
```

## Core Features

### Document Editor

The document editor is built with ProseMirror, providing a Microsoft Word-like editing experience. It supports:

- Rich text formatting (bold, italic, headings, lists, etc.)
- Document content management
- Selection and cursor positioning
- Integration with track changes system

### Track Changes System

The track changes system shows AI suggestions inline with the document text:

- Visual highlighting of suggested additions and deletions
- Individual accept/reject controls for each change
- Batch accept/reject functionality
- Change explanation and context

### AI Sidebar

The sidebar provides access to AI capabilities:

- Predefined improvement prompts (e.g., "Make it shorter", "More professional")
- Custom prompt input for specific requests
- Free-form chat with AI assistant
- Contextual awareness of document content

### User Authentication

The authentication system supports:

- Anonymous usage without account creation
- User registration and login
- Secure authentication using JWT
- User profile management
- Transition from anonymous to authenticated use

## Key Technologies

### Frontend Core

- **React (18.2.0)**: UI framework for component-based architecture
- **TypeScript (5.1.6)**: Type-safe JavaScript for improved developer experience
- **ProseMirror (1.19.0)**: Rich text editor framework with document model
- **Redux Toolkit (1.9.5)**: State management for complex application state
- **React Router (6.15.0)**: Routing and navigation

### UI and Styling

- **TailwindCSS (3.3.0)**: Utility-first CSS framework
- **Framer Motion (6.3.0)**: Animation library
- **HeroIcons/React Icons**: Icon libraries

### Utilities and Tools

- **diff-match-patch (1.0.5)**: Text differencing for track changes
- **DOMPurify (3.0.5)**: HTML sanitization for security
- **Axios (1.4.0)**: HTTP client for API requests
- **React Query (4.29.19)**: Data fetching and caching
- **Vite (4.4.6)**: Build tool and development server

## Environment Variables

The application uses environment variables for configuration. Create a `.env` file in the root directory with the following variables:

```
# API Configuration
VITE_API_URL=http://localhost:5000

# Authentication
VITE_AUTH_DOMAIN=your-auth-domain
VITE_AUTH_CLIENT_ID=your-client-id

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_OFFLINE_MODE=true

# Monitoring
VITE_SENTRY_DSN=your-sentry-dsn
```

In development, the application proxies API requests to the backend server, configured in `vite.config.ts`.

## Browser Support

The application supports modern web browsers. Specific compatibility:

- Chrome 83+
- Firefox 78+
- Safari 14+
- Edge 84+
- Mobile Chrome 83+
- Mobile Safari 14+

The browser compatibility is configured in `package.json` using the `browserslist` field.

## Testing

The project uses Jest and React Testing Library for testing:

### Unit Tests

Unit tests focus on individual components and utility functions. Run them with:

```bash
npm run test
```

### Component Tests

Component tests verify the behavior of UI components in isolation:

```bash
npm run test -- --testPathPattern=components
```

### Integration Tests

Integration tests check how components work together:

```bash
npm run test -- --testPathPattern=integration
```

### End-to-End Tests

End-to-end tests verify complete user flows and are located in a separate e2e directory.

## Build and Deployment

### Production Build

Create a production build with:

```bash
npm run build
```

This generates optimized assets in the `dist` directory, ready for deployment.

### Optimization Strategies

The build process includes:

- Code splitting for improved loading performance
- Tree shaking to eliminate unused code
- Asset optimization and minification
- Chunk separation for editor, track changes, and vendor code

### Deployment

For deployment, upload the contents of the `dist` directory to your web server or cloud hosting service.

The application requires API endpoints as configured in the environment variables.

## Additional Documentation

More detailed documentation can be found in the `docs` directory:

- [Architecture Overview](docs/architecture.md)
- [Component API Documentation](docs/components.md)
- [Editor Implementation](docs/editor.md)
- [Track Changes System](docs/track-changes.md)
- [AI Integration](docs/ai-integration.md)
- [State Management](docs/state-management.md)
- [Accessibility Guidelines](docs/accessibility.md)

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.