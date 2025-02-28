import { defineConfig } from 'vite'; // Version ^4.3.0
import react from '@vitejs/plugin-react'; // Version ^4.0.0
import tsconfigPaths from 'vite-tsconfig-paths'; // Version ^4.2.0
import svgr from 'vite-plugin-svgr'; // Version ^3.2.0
import EnvironmentPlugin from 'vite-plugin-environment'; // Version ^1.1.3

/**
 * Vite configuration for the AI-powered writing enhancement interface
 * Configures build settings, development server, plugins, and optimizations
 * to support the document editor with track changes functionality.
 */
export default defineConfig(({ mode }) => {
  // Determine API URL from environment or use default for development
  const apiUrl = process.env.VITE_API_URL || 'http://localhost:5000';
  const isProd = mode === 'production';
  
  return {
    plugins: [
      // Add React support with Fast Refresh for better development experience
      react(),
      // Resolve imports using TypeScript path mapping
      tsconfigPaths(),
      // Transform SVGs into React components
      svgr(),
      // Handle environment variables for different build environments
      EnvironmentPlugin('all')
    ],
    
    // Development server configuration with API proxies
    server: {
      port: 3000,
      open: true,
      proxy: {
        // Proxy API endpoints to backend services for authentication
        '/api/auth': {
          target: apiUrl,
          changeOrigin: true,
          secure: false,
        },
        // Proxy for document management operations
        '/api/documents': {
          target: apiUrl,
          changeOrigin: true,
          secure: false,
        },
        // Proxy for AI-powered suggestions
        '/api/suggestions': {
          target: apiUrl,
          changeOrigin: true,
          secure: false,
        },
        // Proxy for chat functionality with WebSocket support
        '/api/chat': {
          target: apiUrl,
          changeOrigin: true,
          secure: false,
          ws: true, // Enable WebSocket proxy for real-time suggestions
        }
      }
    },
    
    // Build optimization settings
    build: {
      outDir: 'dist',
      sourcemap: !isProd,
      minify: isProd,
      rollupOptions: {
        output: {
          manualChunks: {
            // Split code into logical chunks for better loading performance
            vendor: ['react', 'react-dom', 'react-router-dom'],
            // ProseMirror dependencies for the document editor
            editor: [
              'prosemirror-model', 
              'prosemirror-state', 
              'prosemirror-view', 
              'prosemirror-transform',
              'prosemirror-commands'
            ],
            // Track changes functionality
            trackChanges: ['diff-match-patch'],
            // State management
            stateManagement: ['@reduxjs/toolkit', 'react-redux']
          }
        }
      }
    },
    
    // Path alias configuration
    resolve: {
      alias: {
        '@': '/src' // Allow using @ to refer to the src directory
      }
    },
    
    // Dependency optimization
    optimizeDeps: {
      include: [
        // ProseMirror packages for document editing with track changes
        'prosemirror-model',
        'prosemirror-state',
        'prosemirror-view',
        'prosemirror-transform',
        'prosemirror-commands',
        // Core libraries
        'react',
        'react-dom',
        'react-router-dom',
        '@reduxjs/toolkit',
        'react-redux',
        // Utilities for track changes functionality
        'diff-match-patch'
      ]
    },
    
    // Worker configuration for client-side AI processing
    worker: {
      format: 'es',
      plugins: [
        tsconfigPaths()
      ]
    }
  };
});