import type { Config } from '@jest/types'; // @jest/types ^29.6.1

/**
 * Creates and returns the Jest configuration object
 * @returns Complete Jest configuration options
 */
const createJestConfig = (): Config.InitialOptions => {
  return {
    // Use ts-jest preset for TypeScript support
    preset: 'ts-jest',
    
    // Use jsdom for browser-like testing environment
    testEnvironment: 'jsdom',
    
    // Setup files to run after the testing environment is set up
    setupFilesAfterEnv: ['<rootDir>/src/__tests__/setup.ts'],
    
    // Map path aliases from tsconfig.json to Jest
    moduleNameMapper: {
      '^@/(.*)$': '<rootDir>/src/$1',
      '^@components/(.*)$': '<rootDir>/src/components/$1',
      '^@hooks/(.*)$': '<rootDir>/src/hooks/$1',
      '^@utils/(.*)$': '<rootDir>/src/utils/$1',
      '^@store/(.*)$': '<rootDir>/src/store/$1',
      '^@api/(.*)$': '<rootDir>/src/api/$1',
      '^@types/(.*)$': '<rootDir>/src/types/$1',
      '^@lib/(.*)$': '<rootDir>/src/lib/$1',
      '^@assets/(.*)$': '<rootDir>/src/assets/$1',
      '^@contexts/(.*)$': '<rootDir>/src/contexts/$1',
      // Handle static assets and styles with mock files
      '\\.(css|less|scss|sass)$': '<rootDir>/src/__tests__/mocks/styleMock.js',
      '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/src/__tests__/mocks/fileMock.js',
    },
    
    // Transform TypeScript and TSX files using ts-jest
    transform: {
      '^.+\\.tsx?$': ['ts-jest', { tsconfig: 'tsconfig.json' }],
    },
    
    // Patterns to identify test files
    testMatch: ['**/__tests__/**/*.(test|spec).(ts|tsx)'],
    
    // File extensions Jest will look for
    moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
    
    // Files to collect coverage from
    collectCoverageFrom: [
      'src/**/*.{ts,tsx}',
      '!src/**/*.d.ts',
      '!src/main.tsx',
      '!src/vite-env.d.ts',
      '!src/__tests__/**/*',
      '!src/**/index.{ts,tsx}',
      '!**/node_modules/**',
    ],
    
    // Coverage thresholds - higher requirements for critical components
    coverageThreshold: {
      global: {
        statements: 80,
        functions: 85,
        branches: 75,
        lines: 80,
      },
      './src/components/editor/': {
        statements: 85,
        functions: 90,
        branches: 80,
        lines: 85,
      },
      './src/components/ai/': {
        statements: 90,
        functions: 90,
        branches: 85,
        lines: 90,
      },
    },
    
    // Directory where coverage reports will be saved
    coverageDirectory: '<rootDir>/coverage',
    
    // Watch plugins for better CLI experience during development
    watchPlugins: [
      'jest-watch-typeahead/filename',
      'jest-watch-typeahead/testname',
    ],
    
    // Global settings for ts-jest
    globals: {
      'ts-jest': {
        isolatedModules: true,
      },
    },
    
    // Test timeout in milliseconds
    testTimeout: 10000,
    
    // Mock behavior configuration
    clearMocks: true,
    resetMocks: false,
    restoreMocks: true,
  };
};

// Export the Jest configuration
export default createJestConfig();