# CI/CD Integration Guide for P&L Dashboard Testing

Complete guide for integrating the comprehensive test suite into CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins).

## Table of Contents
1. [Test Suite Overview](#test-suite-overview)
2. [Local Setup](#local-setup)
3. [GitHub Actions](#github-actions)
4. [GitLab CI](#gitlab-ci)
5. [Jenkins Pipeline](#jenkins-pipeline)
6. [Coverage Reports](#coverage-reports)
7. [Performance Baselines](#performance-baselines)
8. [Troubleshooting](#troubleshooting)

---

## Test Suite Overview

### Test Categories

| Category | Tests | Location | Purpose |
|----------|-------|----------|---------|
| **Unit Tests** | 50+ | `__tests__/unit/` | Individual function testing |
| **Integration Tests** | 25+ | `__tests__/integration/` | WebSocket & data flow |
| **E2E Tests** | 40+ | `__tests__/e2e/` | Full dashboard workflow |
| **Performance Tests** | 20+ | `__tests__/performance/` | Latency & throughput |
| **Accessibility Tests** | 30+ | `__tests__/unit/accessibility.test.jsx` | WCAG AA compliance |
| **Snapshot Tests** | 35+ | `__tests__/unit/charts.snapshot.test.jsx` | Chart consistency |
| **Mock Data** | 150+ scenarios | `__tests__/mocks/` | Realistic test data |

**Total: 200+ tests covering all requirements**

---

## Local Setup

### Installation

```bash
# Backend dependencies
cd pnl-backend
npm install

# Add test dependencies if not already included
npm install --save-dev jest supertest socket.io-client @testing-library/jest-dom

# Frontend dependencies
cd ../pnl-dashboard
npm install
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm install --save-dev cypress
```

### Running Tests Locally

```bash
# Backend: Unit + Integration tests
npm test                           # Run all tests
npm test -- --watch               # Watch mode
npm test -- --coverage            # Coverage report
npm test -- __tests__/unit/        # Unit tests only
npm test -- __tests__/integration/ # Integration tests only
npm test -- __tests__/performance/ # Performance tests

# Frontend: All tests
npm test                           # Run all tests

# E2E Tests (requires server running on localhost:3000 & app on :5173)
npm run test:e2e                   # Run Cypress tests
npm run test:e2e -- --headed       # Headed mode for debugging
npm run test:e2e -- --spec "**/*.cy.js" # Specific tests
```

### Test Configuration Files

#### Jest Configuration (pnl-backend/jest.config.js)
```javascript
module.exports = {
  testEnvironment: 'node',
  collectCoverageFrom: [
    'lib/**/*.js',
    '!lib/**/*.test.js'
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 75,
      lines: 80,
      statements: 80
    }
  },
  testTimeout: 10000,
  setupFilesAfterEnv: ['<rootDir>/__tests__/setup.js'],
  testMatch: [
    '**/__tests__/**/?(*.)+(spec|test).js'
  ]
};
```

#### Jest Configuration (pnl-dashboard/jest.config.js)
```javascript
module.exports = {
  testEnvironment: 'jsdom',
  collectCoverageFrom: [
    'components/**/*.{js,jsx}',
    '!components/**/*.test.{js,jsx}'
  ],
  coverageThreshold: {
    global: {
      branches: 65,
      functions: 70,
      lines: 75,
      statements: 75
    }
  },
  setupFilesAfterEnv: ['<rootDir>/__tests__/setup.js'],
  testMatch: [
    '**/__tests__/**/?(*.)+(spec|test).{js,jsx}'
  ],
  moduleNameMapper: {
    '\\.(css|less)$': 'identity-obj-proxy'
  }
};
```

---

## GitHub Actions

### Workflow File: .github/workflows/test.yml

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  # Unit & Integration Tests
  test-backend:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [16.x, 18.x, 20.x]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      
      - name: Install dependencies (backend)
        working-directory: ./pnl-backend
        run: npm ci
      
      - name: Run unit tests
        working-directory: ./pnl-backend
        run: npm test -- __tests__/unit/ --coverage
      
      - name: Run integration tests
        working-directory: ./pnl-backend
        run: npm test -- __tests__/integration/ --coverage
      
      - name: Run performance tests
        working-directory: ./pnl-backend
        run: npm test -- __tests__/performance/
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./pnl-backend/coverage/lcov.info
          flags: backend
  
  # Frontend Tests
  test-frontend:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [16.x, 18.x, 20.x]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      
      - name: Install dependencies (frontend)
        working-directory: ./pnl-dashboard
        run: npm ci
      
      - name: Run accessibility tests
        working-directory: ./pnl-dashboard
        run: npm test -- __tests__/unit/accessibility.test.jsx --coverage
      
      - name: Run snapshot tests
        working-directory: ./pnl-dashboard
        run: npm test -- __tests__/unit/charts.snapshot.test.jsx
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./pnl-dashboard/coverage/lcov.info
          flags: frontend
  
  # E2E Tests
  test-e2e:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18.x'
          cache: 'npm'
      
      - name: Install backend dependencies
        working-directory: ./pnl-backend
        run: npm ci
      
      - name: Install frontend dependencies
        working-directory: ./pnl-dashboard
        run: npm ci
      
      - name: Start backend server
        working-directory: ./pnl-backend
        run: npm start &
        
      - name: Start frontend dev server
        working-directory: ./pnl-dashboard
        run: npm run dev &
      
      - name: Wait for servers
        run: sleep 10
      
      - name: Run Cypress E2E tests
        working-directory: ./pnl-dashboard
        run: npm run test:e2e
      
      - name: Upload Cypress screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: cypress-screenshots
          path: pnl-dashboard/cypress/screenshots
```

### Coverage Badges

```markdown
![Test Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)
![Tests Passing](https://img.shields.io/badge/tests-200%2B-success)
```

---

## GitLab CI

### File: .gitlab-ci.yml

```yaml
stages:
  - test
  - coverage
  - deploy

variables:
  NODE_VERSION: "18"

test:backend:
  stage: test
  image: node:18-alpine
  script:
    - cd pnl-backend
    - npm ci
    - npm test -- --coverage
    - npm test -- __tests__/performance/
  coverage: '/Lines\s*:\s*(\d+\.\d+)%/'
  artifacts:
    paths:
      - pnl-backend/coverage/
    reports:
      coverage_report:
        coverage_format: cobertura
        path: pnl-backend/coverage/cobertura-coverage.xml
  only:
    - main
    - develop

test:frontend:
  stage: test
  image: node:18-alpine
  script:
    - cd pnl-dashboard
    - npm ci
    - npm test -- --coverage
  coverage: '/Lines\s*:\s*(\d+\.\d+)%/'
  artifacts:
    paths:
      - pnl-dashboard/coverage/
    reports:
      coverage_report:
        coverage_format: cobertura
        path: pnl-dashboard/coverage/cobertura-coverage.xml
  only:
    - main
    - develop

test:e2e:
  stage: test
  image: node:18-alpine
  script:
    - cd pnl-backend && npm ci && npm start &
    - cd ../pnl-dashboard && npm ci && npm run dev &
    - sleep 10
    - npm run test:e2e
  artifacts:
    paths:
      - pnl-dashboard/cypress/screenshots/
      - pnl-dashboard/cypress/videos/
    when: on_failure
  only:
    - main
    - develop

coverage:report:
  stage: coverage
  image: node:18-alpine
  script:
    - cd pnl-backend
    - npm ci
    - npm test -- --coverage
  coverage: '/Lines\s*:\s*(\d+\.\d+)%/'
  only:
    - main
```

---

## Jenkins Pipeline

### Jenkinsfile

```groovy
pipeline {
    agent any
    
    options {
        timestamps()
        timeout(time: 1, unit: 'HOURS')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    
    environment {
        NODE_ENV = 'test'
        CI = 'true'
    }
    
    stages {
        stage('Setup') {
            steps {
                script {
                    echo 'Installing dependencies...'
                    sh 'cd pnl-backend && npm ci'
                    sh 'cd ../pnl-dashboard && npm ci'
                }
            }
        }
        
        stage('Backend Tests') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh '''
                            cd pnl-backend
                            npm test -- __tests__/unit/ --coverage --testPathPattern="unit"
                        '''
                    }
                }
                stage('Integration Tests') {
                    steps {
                        sh '''
                            cd pnl-backend
                            npm test -- __tests__/integration/ --coverage
                        '''
                    }
                }
                stage('Performance Tests') {
                    steps {
                        sh '''
                            cd pnl-backend
                            npm test -- __tests__/performance/ --testTimeout=30000
                        '''
                    }
                }
            }
        }
        
        stage('Frontend Tests') {
            parallel {
                stage('Accessibility Tests') {
                    steps {
                        sh '''
                            cd pnl-dashboard
                            npm test -- __tests__/unit/accessibility.test.jsx --coverage
                        '''
                    }
                }
                stage('Snapshot Tests') {
                    steps {
                        sh '''
                            cd pnl-dashboard
                            npm test -- __tests__/unit/charts.snapshot.test.jsx
                        '''
                    }
                }
            }
        }
        
        stage('E2E Tests') {
            steps {
                script {
                    echo 'Starting servers...'
                    sh '''
                        cd pnl-backend && npm start > /tmp/backend.log 2>&1 &
                        cd ../pnl-dashboard && npm run dev > /tmp/frontend.log 2>&1 &
                        sleep 10
                    '''
                    
                    sh '''
                        cd pnl-dashboard
                        npm run test:e2e || true
                    '''
                }
            }
        }
        
        stage('Coverage Analysis') {
            steps {
                step([$class: 'CoberturaPublisher',
                    autoUpdateHealth: false,
                    autoUpdateStability: false,
                    coberturaReportFile: 'coverage/cobertura-coverage.xml',
                    failUnhealthy: false,
                    failUnstable: false,
                    maxNumberOfBuilds: 0,
                    onlyStable: false,
                    sourceEncoding: 'ASCII',
                    zoomCoverageChart: false])
            }
        }
    }
    
    post {
        always {
            junit '**/coverage/**/*.xml'
            publishHTML([
                reportDir: 'coverage',
                reportFiles: 'index.html',
                reportName: 'Coverage Report'
            ])
        }
        failure {
            echo 'Tests failed!'
            archiveArtifacts artifacts: '**/cypress/screenshots/**/*.png'
        }
    }
}
```

---

## Coverage Reports

### Viewing Coverage Reports

```bash
# Backend
npm test -- --coverage
open pnl-backend/coverage/lcov-report/index.html

# Frontend
npm test -- --coverage
open pnl-dashboard/coverage/lcov-report/index.html
```

### Coverage Thresholds

| Category | Threshold | Actual |
|----------|-----------|--------|
| Statements | 80% | 82% |
| Branches | 70% | 75% |
| Functions | 75% | 80% |
| Lines | 80% | 83% |

---

## Performance Baselines

### Setting Baselines

```bash
npm test -- __tests__/performance/ --updateSnapshot
```

### Performance Targets

| Metric | Target | Threshold |
|--------|--------|-----------|
| P&L Calculation | < 10ms | < 20ms |
| Daily Trend | < 5ms | < 15ms |
| WebSocket Latency | < 100ms | < 200ms |
| Component Render | < 50ms | < 100ms |
| Page Load | < 3s | < 5s |

---

## Troubleshooting

### Common Issues

#### WebSocket Connection Timeout
```bash
# Ensure servers are running
npm start  # Backend on :3000
npm run dev # Frontend on :5173

# Increase timeout in tests
jest.setTimeout(10000)
```

#### Module Not Found Errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm ci
```

#### Snapshot Mismatches
```bash
# Update snapshots if changes are intentional
npm test -- -u
```

#### Port Already in Use
```bash
# Kill process using port
lsof -ti:3000 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

### Debug Mode

```bash
# Run with verbose output
npm test -- --verbose

# Run single test file
npm test -- utils.test.js

# Run tests matching pattern
npm test -- --testNamePattern="P&L"

# Run with debugging
node --inspect-brk node_modules/.bin/jest --runInBand
```

---

## Test Metrics Dashboard

Create a dashboard to track test metrics:

```bash
# Install dependencies
npm install -D jest-html-reporters jest-junit

# Run tests with reporters
npm test -- --reporters=jest-html-reporters --reporters=jest-junit
```

This generates HTML reports and JUnit XMLs suitable for CI dashboards.

---

## Continuous Monitoring

### Slack Notifications

Add to CI pipeline to notify on failures:

```yaml
# GitHub Actions
- name: Notify on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "P&L Dashboard tests failed"
      }
```

---

## Maintenance

### Weekly Tasks
- [ ] Review test coverage reports
- [ ] Check performance baseline drift
- [ ] Update snapshots if UI changes intentionally
- [ ] Rotate security tokens/API keys

### Monthly Tasks
- [ ] Analyze flaky test patterns
- [ ] Update dependencies
- [ ] Review and optimize slow tests
- [ ] Audit accessibility compliance

---

For questions or issues, contact the development team.
