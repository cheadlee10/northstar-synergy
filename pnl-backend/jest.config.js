/**
 * Jest Configuration for P&L Backend Test Suite
 */

module.exports = {
  // Test environment
  testEnvironment: 'node',

  // Coverage configuration
  collectCoverageFrom: [
    'lib/**/*.js',
    'middleware/**/*.js',
    'server.js',
    '!**/*.test.js',
    '!**/*.spec.js',
    '!**/node_modules/**'
  ],

  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 75,
      lines: 80,
      statements: 80
    },
    './lib/': {
      branches: 75,
      functions: 80,
      lines: 85,
      statements: 85
    }
  },

  // Test timeout (10 seconds)
  testTimeout: 10000,

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/__tests__/setup.js'],

  // Test match patterns
  testMatch: [
    '**/__tests__/**/?(*.)+(spec|test).js',
    '**/?(*.)+(spec|test).js'
  ],

  // Paths to ignore
  testPathIgnorePatterns: [
    '/node_modules/',
    '/coverage/'
  ],

  // Module paths
  moduleDirectories: ['node_modules', '<rootDir>'],

  // Transform files
  transform: {
    '^.+\\.js$': ['babel-jest', { rootMode: 'upward' }]
  },

  // Verbose output
  verbose: true,

  // Bail after N failures
  bail: 0,

  // Show coverage
  collectCoverage: false,

  // Coverage directory
  coverageDirectory: '<rootDir>/coverage',

  // Coverage reporters
  coverageReporters: [
    'text',
    'text-summary',
    'html',
    'lcov',
    'json',
    'cobertura'
  ],

  // Watch plugins
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname'
  ],

  // Max workers
  maxWorkers: '50%',

  // Globals
  globals: {
    'ts-jest': {
      tsconfig: {
        esModuleInterop: true
      }
    }
  },

  // Clear mocks between tests
  clearMocks: true,

  // Restore mocks between tests
  restoreMocks: true,

  // Test report configuration
  reporters: [
    'default',
    [
      'jest-junit',
      {
        outputDirectory: '<rootDir>/test-results',
        outputName: 'junit.xml',
        classNameTemplate: '{classname}',
        titleTemplate: '{title}',
        ancestorSeparator: ' › ',
        usePathAsClassName: false
      }
    ]
  ]
};
