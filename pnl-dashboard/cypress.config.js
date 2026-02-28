/**
 * Cypress Configuration for P&L Dashboard E2E Tests
 */

import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    // Base URL
    baseUrl: 'http://localhost:5173',

    // Viewport
    viewportWidth: 1280,
    viewportHeight: 720,

    // Video
    video: true,
    videoOnFailed: true,

    // Screenshots
    screenshotOnRunFailure: true,

    // Command timeout (5 seconds)
    commandTimeout: 5000,

    // Request timeout (5 seconds)
    requestTimeout: 5000,

    // Response timeout (5 seconds)
    responseTimeout: 5000,

    // Wait for animations
    waitForAnimations: true,

    // Check for uncaught exceptions
    uncaught: true,

    // Browser
    browser: 'chrome',

    // Headless mode
    headless: false,

    // Video compression
    videoCompression: 32,

    // Setup node events
    setupNodeEvents(on, config) {
      // Implement node event listeners here
      on('task', {
        log(message) {
          console.log(message);
          return null;
        }
      });
    }
  },

  // Component testing (optional)
  component: {
    devServer: {
      framework: 'react',
      bundler: 'vite'
    }
  },

  // Globals
  globals: {
    Cypress: true,
    expect: true,
    assert: true,
    cy: true
  },

  // File patterns
  specPattern: '__tests__/e2e/**/*.cy.js',

  // Support file
  supportFile: '__tests__/e2e/support/e2e.js',

  // Downloads folder
  downloadsFolder: '__tests__/e2e/downloads',

  // Fixtures folder
  fixturesFolder: '__tests__/e2e/fixtures',

  // Screenshots folder
  screenshotsFolder: '__tests__/e2e/screenshots',

  // Videos folder
  videosFolder: '__tests__/e2e/videos'
});
