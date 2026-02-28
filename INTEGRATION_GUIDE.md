# P&L Integration Layer — Complete Guide

This integration layer connects your React frontend to the Node.js backend via WebSocket, providing real-time P&L updates with full state management, error handling, and development tools.

## 📦 Files Included

1. **`hooks/socket.js`** — Low-level Socket.io client management
2. **`hooks/usePnL.js`** — Zustand store + high-level P&L hook with selectors
3. **`utils/dataTransform.js`** — Currency formatting, timestamp normalization, validation
4. **`components/ErrorBoundary.jsx`** — Error boundary for WebSocket and React errors
5. **`providers/MockDataProvider.jsx`** — Mock data generator for development/testing
6. **`INTEGRATION_GUIDE.md`** — This file

## 🚀 Quick Start

### 1. Installation

```bash
npm install zustand socket.io-client
```

### 2. Set Up Error Boundary

Wrap your app with `ErrorBoundary`:

```jsx
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary showDetails={process.env.NODE_ENV === 'development'}>
      <YourApp />
    </ErrorBoundary>
  );
}
```

### 3. Use P&L Hook in Components

```jsx
import { usePnL, useRevenueOnly, useTrendsOnly } from './hooks/usePnL';
import { formatCurrency } from './utils/dataTransform';

function Dashboard() {
  const { pnl, trends, isLoading, error, dataSource } = usePnL({
    source: 'live', // or 'mock' for development
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>P&L Dashboard</h1>
      <p>Revenue: {formatCurrency(pnl.revenue)}</p>
      <p>Expenses: {formatCurrency(pnl.expenses)}</p>
      <p>Net: {formatCurrency(pnl.net)}</p>
      <p>Margin: {pnl.marginPercent.toFixed(2)}%</p>
      <p>Source: {dataSource}</p>
    </div>
  );
}
```

## 🎯 Architecture & Patterns

### Zustand Store Pattern (Selective Subscriptions)

The store uses `subscribeWithSelector` to enable fine-grained subscriptions. Components only re-render when their specific data changes:

```jsx
// Only re-renders when revenue changes
const { revenue } = useRevenueOnly();

// Only re-renders when trends change
const { trends } = useTrendsOnly();

// Re-renders only when net profit or margin changes
const { net, marginPercent } = useNetProfitOnly();

// Re-renders on all P&L changes
const pnl = usePnL();
```

### Socket.io Connection Management

The `useSocket` hook handles:
- Connection lifecycle (connect, disconnect, reconnect)
- Selective event subscriptions
- Automatic re-subscription after reconnection
- Connection state tracking

```jsx
const { subscribe, emit, isConnected, connectionId } = useSocket(
  onConnect,
  onDisconnect,
  options
);

// Subscribe to event
const unsubscribe = subscribe('pnl:update', (data) => {
  console.log('Update:', data);
});

// Emit event
emit('pnl:request', { period: 'daily' });

// Cleanup
unsubscribe();
```

### Data Transformation Layer

All data flowing through the system is normalized:

```jsx
import {
  formatCurrency,          // "$1,234.56"
  normalizeTimestamp,      // ISO strings
  calculatePercentage,     // Safe percentage math
  normalizePnLData,        // Validate & normalize from backend
  validatePnLData,         // Check data integrity
  generateMockPnL,         // Testing data
} from './utils/dataTransform';
```

### Error Boundary

Catches two types of errors:

1. **WebSocket Errors** — Network/connection failures
   - Shows friendly message with retry button
   - Auto-attempts reconnection

2. **Component Errors** — React render errors
   - Shows full error details in development
   - Provides recovery options

```jsx
<ErrorBoundary
  onError={(error, errorInfo, context) => {
    if (context.isWebSocketError) {
      // Handle connection error
    }
  }}
  logErrors={process.env.NODE_ENV === 'production'}
  showDetails={process.env.NODE_ENV === 'development'}
>
  <Dashboard />
</ErrorBoundary>
```

### Local Storage Persistence

The store automatically saves/recovers from localStorage:

```jsx
// Data automatically saves after updates
const { pnl } = usePnL();

// On page reload, persisted data is restored automatically
// Loading spinner shows while fresh data syncs
```

## 📚 Usage Examples

### Example 1: Simple Revenue Display

```jsx
import { useRevenueOnly } from './hooks/usePnL';
import { formatCurrency } from './utils/dataTransform';

function RevenueCard() {
  const { revenue, lastUpdated } = useRevenueOnly();

  return (
    <div className="card">
      <h3>Total Revenue</h3>
      <p className="amount">{formatCurrency(revenue)}</p>
      <p className="timestamp">Updated: {lastUpdated}</p>
    </div>
  );
}
```

### Example 2: Development with Mock Data

```jsx
import { useMockDataProvider } from './providers/MockDataProvider';
import Dashboard from './Dashboard';

function App() {
  if (process.env.NODE_ENV === 'development') {
    // Use mock data provider in dev
    useMockDataProvider({
      updateInterval: 3000,
      baseRevenue: 100000,
      baseExpenses: 60000,
      trending: 'up',
      autoStart: true,
    });
  }

  return <Dashboard />;
}
```

### Example 3: Custom Error Handler

```jsx
function App() {
  const handleError = (error, errorInfo, context) => {
    // Log to analytics
    analytics.logError({
      message: error.message,
      component: errorInfo.componentStack,
      type: context.isWebSocketError ? 'network' : 'render',
      timestamp: new Date().toISOString(),
    });

    // Alert user if critical
    if (context.isWebSocketError) {
      notify.warning('Connection lost. Retrying...');
    }
  };

  return (
    <ErrorBoundary onError={handleError} logErrors={true}>
      <Dashboard />
    </ErrorBoundary>
  );
}
```

### Example 4: Trend Analysis Component

```jsx
import { useTrendsOnly } from './hooks/usePnL';
import { LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';

function TrendChart() {
  const { trends } = useTrendsOnly();

  // Transform for charting library
  const chartData = trends.dates.map((date, i) => ({
    date,
    revenue: trends.revenue[i],
    expenses: trends.expenses[i],
    net: trends.net[i],
  }));

  return (
    <LineChart data={chartData}>
      <CartesianGrid />
      <XAxis dataKey="date" />
      <YAxis />
      <Line type="monotone" dataKey="revenue" stroke="#8884d8" />
      <Line type="monotone" dataKey="expenses" stroke="#82ca9d" />
      <Line type="monotone" dataKey="net" stroke="#ffc658" />
    </LineChart>
  );
}
```

### Example 5: Manual Data Refresh

```jsx
function Dashboard() {
  const { pnl, refresh, isLoading } = usePnL();

  return (
    <div>
      {isLoading && <Spinner />}
      <button onClick={refresh} disabled={isLoading}>
        Refresh Now
      </button>
      <p>Revenue: {formatCurrency(pnl.revenue)}</p>
    </div>
  );
}
```

## 🔧 Environment Variables

Create `.env` file:

```bash
REACT_APP_SOCKET_URL=http://localhost:3001
REACT_APP_ENV=development  # or production
```

## 🧪 Testing with Mock Data

### Mock Data in Storybook

```jsx
import { MockDataProvider } from './providers/MockDataProvider';

export const Dashboard = () => {
  return (
    <MockDataProvider
      options={{
        baseRevenue: 50000,
        baseExpenses: 30000,
        trending: 'up',
        updateInterval: 2000,
      }}
      showStatus={true}
    >
      <DashboardComponent />
    </MockDataProvider>
  );
};
```

### Generate Test Data

```jsx
import { generateMockPnL, generateStressTestData } from './providers/MockDataProvider';

// Get 30 days of mock data
const mockData = generateMockPnL({
  baseRevenue: 50000,
  baseExpenses: 30000,
  trendPoints: 30,
  volatility: 0.15,
});

// Get stress test data with spikes/drops
const stressData = generateStressTestData(30);
```

## 🔐 State Management Reference

### Full Store State

```typescript
interface PnLState {
  // Current values
  revenue: number;
  expenses: number;
  net: number;
  marginPercent: number;

  // Trends (arrays for charts)
  trends: {
    revenue: number[];
    expenses: number[];
    net: number[];
    dates: string[];
  };

  // Metadata
  lastUpdated: string | null;
  dataSource: 'live' | 'mock' | 'error';
  isLoading: boolean;
  error: string | null;

  // Actions
  setPnL(data): void;
  addTrendPoint(data): void;
  updateTrends(data): void;
  setError(error): void;
  clearError(): void;
  reset(): void;
}
```

### Available Selectors

```jsx
import {
  selectPnL,        // { revenue, expenses, net, marginPercent, lastUpdated }
  selectTrends,      // { revenue[], expenses[], net[], dates[] }
  selectStatus,      // { isLoading, error, dataSource, lastUpdated }
  selectSummary,     // Formatted { revenue, expenses, net, marginPercent }
} from './hooks/usePnL';

// Use with store directly
const pnl = usePnLStore(selectPnL);
const summary = usePnLStore(selectSummary);
```

## 🛡️ Error Handling Strategy

1. **WebSocket Disconnection** → Auto-reconnect, fallback to cached data
2. **Data Validation Failure** → Log error, keep previous state, show warning
3. **Component Render Error** → Show Error Boundary UI, offer recovery
4. **Invalid Timestamps** → Normalize to current time
5. **Missing Data** → Use sensible defaults (0)

## 📊 Performance Optimization

- **Selective Subscriptions** — Only re-render components when their data changes
- **Batched Updates** — Socket.io auto-batches multiple events
- **Data Caching** — localStorage keeps data available offline
- **Trend Windowing** — Only keeps last 100 data points to limit memory

## 🚨 Troubleshooting

### Socket Not Connecting

```jsx
// Check environment variable
console.log(process.env.REACT_APP_SOCKET_URL);

// Add debug logging
const { socket } = useSocket(
  () => console.log('Connected!'),
  () => console.log('Disconnected!'),
  { transports: ['websocket'] } // Force websocket only
);
```

### State Not Updating

```jsx
// Check if source is 'mock' instead of 'live'
const { dataSource } = usePnL();
console.log('Data source:', dataSource);

// Verify store state
usePnLStore.subscribe(
  (state) => state.revenue,
  (revenue) => console.log('Revenue changed:', revenue)
);
```

### High Re-render Count

```jsx
// Use selective subscriptions instead of full hook
// ❌ Bad: Full hook re-renders on any change
const { pnl } = usePnL();

// ✅ Good: Only re-renders when revenue changes
const { revenue } = useRevenueOnly();
```

## 📖 API Reference

### usePnL(options)

```jsx
const {
  // Data
  pnl,              // { revenue, expenses, net, marginPercent, lastUpdated }
  trends,           // { revenue[], expenses[], net[], dates[] }

  // Status
  isConnected,      // boolean
  isLoading,        // boolean
  error,            // string | null
  dataSource,       // 'live' | 'mock' | 'error'
  lastUpdated,      // string | null

  // Methods
  refresh,          // () => void
  reset,            // () => void
  clearError,       // () => void
} = usePnL({
  source: 'live',   // or 'mock'
  onError: (error) => {},
});
```

### Socket Events

Backend should emit/listen for:

```javascript
// Backend → Frontend
socket.emit('pnl:update', { revenue, expenses, margin_percent, updated_at });
socket.emit('pnl:trends', { revenue[], expenses[], net[], dates[] });
socket.emit('pnl:initial', { /* initial P&L data */ });

// Frontend → Backend
socket.emit('pnl:request', { period: 'daily' });
```

## ✅ Implementation Checklist

- [ ] Install dependencies (`zustand`, `socket.io-client`)
- [ ] Copy all 4 main files to your project
- [ ] Set `REACT_APP_SOCKET_URL` in `.env`
- [ ] Wrap app with `<ErrorBoundary>`
- [ ] Use `usePnL()` hook in dashboard component
- [ ] Test with mock data provider
- [ ] Verify Socket.io connection on backend
- [ ] Set up error logging service (optional)
- [ ] Monitor performance with React DevTools Profiler

## 🎓 Best Practices

1. **Use Selective Subscriptions** — Minimize re-renders with focused selectors
2. **Handle Errors Gracefully** — Always provide fallback UI
3. **Test with Mock Data** — Develop without backend dependency
4. **Persist State** — localStorage provides offline capability
5. **Log Errors** — Capture production issues for analysis
6. **Validate Data** — Check incoming data before storing
7. **Clean Up Subscriptions** — Prevent memory leaks
8. **Monitor Connection** — Track connection health in UI

## 🤝 Integration Points

The integration layer is ready to connect with:
- Any Express/Socket.io backend
- Any React component architecture
- Any charting library (Recharts, Chart.js, etc.)
- Any analytics service (Sentry, LogRocket, etc.)
- Any state aggregation service

Simply emit the expected Socket.io events from your backend, and the frontend will handle the rest.

---

**Ready to use!** Start with the quick start example above.
