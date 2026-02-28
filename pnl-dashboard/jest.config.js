/**
 * Jest Configuration for P&L Frontend Test Suite
 */

export default {
  // Test environment
  testEnvironment: 'jsdom',

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/__tests__/setup.js'],

  // Module name mapping
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(gif|ttf|eot|svg|png|jpg|jpeg)$': '<rootDir>/__tests__/__mocks__/fileMock.js'
  },

  // Transform files
  transform: {
    '^.+\\.(js|jsx)$': ['babel-jest', { presets: ['@babel/preset-react'] }]
  },

  // Test match patterns
  testMatch: [
    '**/__tests__/**/?(*.)+(spec|test).{js,jsx}',
    '**/?(*.)+(spec|test).{js,jsx}'
  ],

  // Coverage configuration
  collectCoverageFrom: [
    'components/**/*.{js,jsx}',
    'pnlStore.js',
    '!components/**/*.test.{js,jsx}',
    '!**/node_modules/**'
  ],

  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 65,
      functions: 70,
      lines: 75,
      statements: 75
    },
    './components/': {
      branches: 70,
      functions: 75,
      lines: 80,
      statements: 80
    }
  },

  // Test timeout (10 seconds)
  testTimeout: 10000,

  // Verbose output
  verbose: true,

  // Clear mocks between tests
  clearMocks: true,

  // Restore mocks between tests
  restoreMocks: true,

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

  // Paths to ignore
  testPathIgnorePatterns: [
    '/node_modules/',
    '/coverage/',
    '/__tests__/e2e/'
  ],

  // Module paths
  moduleDirectories: ['node_modules', '<rootDir>'],

  // Watch plugins
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname'
  ],

  // Max workers
  maxWorkers: '50%',

  // Bail after N failures
  bail: 0,

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
