---
name: pnl-dashboard-core
description: Build enterprise-grade P&L dashboards with real-time data, waterfall charts, and accessibility. Use when creating financial dashboards, tracking profit/loss metrics, building real-time analytics, or integrating multiple data sources (Kalshi, costs, revenue). Includes React components, color systems, animations, WCAG AA compliance, and WebSocket patterns.
---

# P&L Dashboard Core Skill

Complete reference for building world-class financial dashboards with real-time data streaming, waterfall decomposition, and enterprise design patterns.

## Quick Start

### 1. Setup (5 minutes)
```bash
npm install react recharts @ant-design/charts socket.io-client zustand tailwindcss daisyui
```

### 2. Minimal P&L Component
```jsx
import { useSocket } from './hooks/useSocket';
import KPICard from './components/KPICard';
import Waterfall from './components/WaterfallChart';

export default function Dashboard() {
  const { revenue, expenses, netPL } = useSocket('pnl');

  return (
    <div className="grid grid-cols-3 gap-4">
      <KPICard label="Revenue" value={revenue} type="positive" />
      <KPICard label="Expenses" value={expenses} type="negative" />
      <KPICard label="Net P&L" value={netPL} type={netPL > 0 ? 'positive' : 'negative'} />
      <Waterfall data={[revenue, -expenses, netPL]} />
    </div>
  );
}
```

### 3. Color System
```javascript
const colors = {
  positive: '#16A34A',  // Green (gains, profit)
  negative: '#DC2626',  // Red (losses, spend)
  neutral: '#6B7280',   // Gray (break-even)
  alert: '#EA580C',     // Orange (anomalies)
  primary: '#2563EB',   // Blue (trust, stability)
};
```

### 4. WebSocket Setup
```javascript
// Backend
const io = require('socket.io')(3001);
io.on('connection', (socket) => {
  setInterval(() => {
    const pnl = calculatePnL();
    socket.emit('pnl-update', pnl);
  }, 5000);
});

// Frontend
import { io } from 'socket.io-client';
const socket = io('http://localhost:3001');
socket.on('pnl-update', (pnl) => setPnlData(pnl));
```

## Core Components

### KPICard (Hero Metric)
```jsx
<KPICard 
  label="Net P&L" 
  value={1250000} 
  type="positive"
  trend="+12.5%"
  animate={true}
/>
```

### Waterfall Chart
```jsx
<WaterfallChart 
  data={[
    { label: 'Revenue', value: 500000 },
    { label: 'COGS', value: -300000 },
    { label: 'OpEx', value: -120000 },
    { label: 'Tax', value: -25000 }
  ]}
  color={{ positive: '#16A34A', negative: '#DC2626' }}
/>
```

### Time Series
```jsx
<TimeSeriesChart 
  data={dailyData} 
  metric="net_pnl"
  days={30}
  animate={true}
/>
```

## Real-Time Patterns

### Selective Re-Rendering (Zustand)
```javascript
const usePnL = create((set) => ({
  revenue: 0,
  expenses: 0,
  subscribe: (socket) => {
    socket.on('pnl-update', (data) => {
      set(data);  // Only re-render components subscribed to changed fields
    });
  }
}));

// In component
const revenue = usePnL((state) => state.revenue);  // Only re-renders if revenue changes
```

### Counter Animation
```javascript
const AnimatedCounter = ({ value, duration = 500 }) => {
  const [display, setDisplay] = useState(0);
  
  useEffect(() => {
    const start = Date.now();
    const timer = setInterval(() => {
      const progress = (Date.now() - start) / duration;
      setDisplay(Math.floor(value * progress));
    }, 16);
    return () => clearInterval(timer);
  }, [value]);

  return <span>${display.toLocaleString()}</span>;
};
```

## Data Aggregation

### Three-Source P&L
```javascript
const calculatePnL = async (kalshiApi, anthropicApi, johnApi) => {
  const [kalshi, anthropic, john] = await Promise.all([
    kalshiApi.getBalance(),
    anthropicApi.getCosts(),
    johnApi.getRevenue()
  ]);

  return {
    revenue: john.total,
    expenses: anthropic.total,
    trading_pl: kalshi.pnl,
    net_pl: john.total - anthropic.total + kalshi.pnl,
    margin_pct: ((john.total - anthropic.total) / john.total) * 100
  };
};
```

## Mobile Responsiveness

### Responsive Grid
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {/* Cards auto-stack on mobile */}
</div>
```

### Touch-Friendly Chart
```jsx
<LineChart data={data} width="100%" height={300}>
  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
</LineChart>
```

## Accessibility (WCAG AA)

### Color + Symbol
```jsx
// ✅ Good: color + symbol
<span style={{ color: '#16A34A' }}>↑ +$1,250K</span>

// ❌ Bad: color only
<span style={{ color: '#16A34A' }}>$1,250K</span>
```

### Semantic HTML
```jsx
<article role="region" aria-label="P&L Summary">
  <h2>Net P&L</h2>
  <dl>
    <dt>Revenue</dt>
    <dd>$500K</dd>
  </dl>
</article>
```

### Keyboard Navigation
```jsx
<button 
  onClick={refresh}
  onKeyDown={(e) => e.key === 'Enter' && refresh()}
  aria-label="Refresh P&L data"
>
  Refresh
</button>
```

## Performance Optimization

### Memoization
```javascript
const KPICard = memo(({ value, label }) => {
  return <div>{label}: {value}</div>;
});
```

### Data Windowing (Last 100 Points)
```javascript
const recentData = allData.slice(-100);  // Only render visible points
```

### Throttled Updates
```javascript
const throttle = (fn, ms) => {
  let last = 0;
  return (...args) => {
    if (Date.now() - last >= ms) {
      fn(...args);
      last = Date.now();
    }
  };
};

socket.on('pnl-update', throttle((data) => setPnl(data), 500));
```

## Common Patterns

### Error Boundary
```jsx
<ErrorBoundary fallback={<div>Dashboard error</div>}>
  <PnLDashboard />
</ErrorBoundary>
```

### Loading State
```jsx
{loading ? (
  <div className="animate-shimmer bg-gray-300 h-24" />
) : (
  <KPICard value={pnl} />
)}
```

### Fallback Data
```javascript
const pnl = liveData || cachedData || mockData;
```

## Testing

### Unit Test Example
```javascript
test('calculates net P&L correctly', () => {
  const result = calculatePnL(
    { revenue: 1000, expenses: 600 }
  );
  expect(result.netPL).toBe(400);
});
```

### WebSocket Mock
```javascript
const mockSocket = {
  on: jest.fn(),
  emit: jest.fn(),
  disconnect: jest.fn()
};
```

## Deployment Checklist

- [ ] Color contrast verified (WCAG AA, 4.5:1)
- [ ] Mobile layout tested (responsive, 44px touch targets)
- [ ] WebSocket fallback working (SSE, polling)
- [ ] Accessibility audit passed (keyboard nav, screen reader)
- [ ] Performance: <500ms end-to-end latency
- [ ] Error handling: all API failures graceful
- [ ] Data validation: all inputs sanitized
- [ ] Monitoring: metrics + alerting configured

## Resources

- **Charts:** Recharts docs (https://recharts.org)
- **State:** Zustand (https://zustand-demo.vercel.app/)
- **Real-time:** Socket.io (https://socket.io/docs/)
- **Design:** DaisyUI (https://daisyui.com/)
- **Accessibility:** WCAG (https://www.w3.org/WAI/WCAG21/quickref/)
