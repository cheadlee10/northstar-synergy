---
name: dashboard-testing
description: Build comprehensive test suites for P&L dashboards (unit, integration, E2E, performance, accessibility). Use when ensuring dashboard reliability, preventing regressions, validating data accuracy, or preparing for production deployment. Includes Jest, React Testing Library, Cypress, and performance benchmarking.
---

# Dashboard Testing Skill

Complete testing patterns for financial dashboards with high confidence and zero regressions.

## Unit Tests (Components)

### KPI Card Test
```javascript
import { render, screen } from '@testing-library/react';
import KPICard from '../KPICard';

describe('KPICard', () => {
  test('renders with correct label and value', () => {
    render(<KPICard label="Net P&L" value={1250000} type="positive" />);
    expect(screen.getByText('Net P&L')).toBeInTheDocument();
    expect(screen.getByText('$1,250,000')).toBeInTheDocument();
  });

  test('applies correct color class based on type', () => {
    const { container } = render(<KPICard value={-500} type="negative" />);
    expect(container.querySelector('.text-red-600')).toBeInTheDocument();
  });

  test('animates counter on value change', async () => {
    const { rerender } = render(<KPICard value={0} />);
    rerender(<KPICard value={1000} />);
    
    await waitFor(() => {
      expect(screen.getByText('$1,000')).toBeInTheDocument();
    });
  });
});
```

### Waterfall Chart Test
```javascript
test('renders waterfall with correct bar order', () => {
  const data = [
    { label: 'Revenue', value: 500000 },
    { label: 'COGS', value: -300000 }
  ];
  
  render(<WaterfallChart data={data} />);
  const bars = screen.getAllByRole('img');
  expect(bars).toHaveLength(2);
});

test('formats currency correctly', () => {
  render(<WaterfallChart data={mockData} />);
  expect(screen.getByText('$500,000')).toBeInTheDocument();
});
```

## Integration Tests (Data Flow)

### WebSocket Integration Test
```javascript
import { render, screen, waitFor } from '@testing-library/react';
import { io } from 'socket.io-client';
import Dashboard from '../Dashboard';

jest.mock('socket.io-client');

test('updates dashboard on WebSocket message', async () => {
  const mockSocket = {
    on: jest.fn(),
    emit: jest.fn(),
    disconnect: jest.fn()
  };
  io.mockReturnValue(mockSocket);

  render(<Dashboard />);

  // Simulate incoming data
  const callback = mockSocket.on.mock.calls.find(
    call => call[0] === 'pnl-update'
  )[1];

  callback({ revenue: 500000, expenses: 300000, netPL: 200000 });

  await waitFor(() => {
    expect(screen.getByText('$200,000')).toBeInTheDocument();
  });
});
```

### Data Aggregation Test
```javascript
test('aggregates P&L from multiple sources', async () => {
  const pnl = await aggregatePnL({
    kalshi: { getBalance: () => ({ trading_pl: 500 }) },
    anthropic: { getCosts: () => ({ total: 200 }) },
    john: { getRevenue: () => ({ total: 1000 }) }
  });

  expect(pnl.netPL).toBe(1300);  // 1000 - 200 + 500
});
```

## End-to-End Tests (Cypress)

### Full Dashboard Flow
```javascript
describe('P&L Dashboard E2E', () => {
  beforeEach(() => {
    cy.visit('http://localhost:3000');
  });

  test('loads dashboard and displays P&L metrics', () => {
    cy.contains('Net P&L').should('be.visible');
    cy.get('[data-testid="pnl-value"]').should('contain', '$');
  });

  test('updates metrics in real-time', () => {
    cy.get('[data-testid="net-pnl"]').then($el => {
      const initialValue = $el.text();
      
      cy.wait(5000);  // Wait for WebSocket update
      cy.get('[data-testid="net-pnl"]').should('not.have.text', initialValue);
    });
  });

  test('charts render without errors', () => {
    cy.get('.waterfall-chart').should('be.visible');
    cy.get('.trend-chart').should('be.visible');
    cy.get('.heatmap-chart').should('be.visible');
  });

  test('responsive design works on mobile', () => {
    cy.viewport('iphone-x');
    cy.get('.grid-cols-1').should('be.visible');
    cy.get('[data-testid="pnl-card"]').each(($card) => {
      cy.wrap($card).should('be.visible');
    });
  });
});
```

## Performance Tests

### Latency Benchmark
```javascript
test('WebSocket update latency < 500ms', async () => {
  const start = Date.now();
  
  socket.emit('request-update');
  
  await new Promise(resolve => {
    socket.on('pnl-update', () => {
      const latency = Date.now() - start;
      expect(latency).toBeLessThan(500);
      resolve();
    });
  });
});
```

### Chart Render Performance
```javascript
test('waterfall chart renders <100ms', () => {
  const start = performance.now();
  
  render(<WaterfallChart data={largeDataset} />);
  
  const renderTime = performance.now() - start;
  expect(renderTime).toBeLessThan(100);
});
```

### Memory Leak Detection
```javascript
test('no memory leaks on component unmount', () => {
  const { unmount } = render(<Dashboard />);
  
  const memBefore = performance.memory.usedJSHeapSize;
  unmount();
  
  const memAfter = performance.memory.usedJSHeapSize;
  expect(memAfter - memBefore).toBeLessThan(1000000);  // < 1MB
});
```

## Accessibility Tests

### WCAG AA Compliance
```javascript
import { axe } from 'jest-axe';

test('dashboard passes WCAG AA accessibility audit', async () => {
  const { container } = render(<Dashboard />);
  const results = await axe(container);
  
  expect(results).toHaveNoViolations();
});
```

### Keyboard Navigation
```javascript
test('all controls keyboard accessible', () => {
  render(<Dashboard />);
  
  // Tab through all interactive elements
  const button = screen.getByRole('button', { name: /refresh/i });
  button.focus();
  expect(button).toHaveFocus();
  
  fireEvent.keyDown(button, { key: 'Enter' });
  // Verify action triggered
});
```

### Colorblind Mode
```javascript
test('dashboard readable in colorblind mode', () => {
  render(<Dashboard />);
  
  // Verify text labels exist (not just colors)
  expect(screen.getByText('Loss ↓')).toBeInTheDocument();
  expect(screen.getByText('Profit ↑')).toBeInTheDocument();
});
```

## Mock Data Generators

### Kalshi Mock
```javascript
const generateKalshiData = (overrides = {}) => ({
  balance: 10000,
  positions: [
    { symbol: 'WEATHER', quantity: 100, pnl: 500, price: 0.45 }
  ],
  pnl: 500,
  fills: 50,
  ...overrides
});
```

### Anthropic Costs Mock
```javascript
const generateAnthropicCosts = (overrides = {}) => ({
  total: 125.50,
  by_model: {
    'claude-opus-4-6': 100,
    'claude-sonnet-4': 25.50
  },
  ...overrides
});
```

### John Revenue Mock
```javascript
const generateJohnRevenue = (overrides = {}) => ({
  total: 5000,
  jobs: [
    { id: 1, title: 'Excel Audit', amount: 2500, status: 'completed' }
  ],
  invoiced: 5000,
  collected: 3500,
  outstanding: 1500,
  ...overrides
});
```

## Snapshot Testing

### Dashboard Snapshot
```javascript
test('dashboard snapshot matches', () => {
  const { container } = render(<Dashboard />);
  expect(container).toMatchSnapshot();
});

test('waterfall chart snapshot matches', () => {
  const { container } = render(<WaterfallChart data={mockData} />);
  expect(container).toMatchSnapshot();
});
```

## Test Coverage Targets

| Component | Target | Current |
|-----------|--------|---------|
| KPI Cards | 90% | - |
| Charts | 85% | - |
| WebSocket | 95% | - |
| Calculations | 100% | - |
| **Overall** | **90%** | - |

## CI/CD Integration

### GitHub Actions Test Job
```yaml
- name: Run Tests
  run: npm test -- --coverage --watchAll=false

- name: Run E2E Tests
  run: npm run test:e2e

- name: Check Coverage
  run: npx nyc --reporter=text npm test
  
- name: Performance Test
  run: npm run test:performance
```

## Test Utilities

### Custom Render with Providers
```javascript
export function renderWithProviders(component) {
  return render(
    <SocketProvider>
      <PnLProvider>
        {component}
      </PnLProvider>
    </SocketProvider>
  );
}
```

### Wait for Data
```javascript
export async function waitForData() {
  return waitFor(() => {
    expect(screen.getByTestId('pnl-value')).toBeInTheDocument();
  }, { timeout: 3000 });
}
```
