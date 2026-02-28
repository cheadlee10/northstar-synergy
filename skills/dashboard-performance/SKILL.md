---
name: dashboard-performance
description: Optimize P&L dashboard performance (latency, render time, memory, bundle size). Use when dashboard is slow, needs to handle high-frequency updates, or requires mobile optimization. Includes profiling, caching strategies, code splitting, and performance monitoring.
---

# Dashboard Performance Optimization Skill

Advanced techniques for building lightning-fast financial dashboards.

## Performance Metrics (Targets)

| Metric | Target | Tool |
|--------|--------|------|
| First Contentful Paint | <1s | Lighthouse |
| Time to Interactive | <2s | Lighthouse |
| WebSocket Latency | <200ms | Custom |
| Chart Render | <100ms | React DevTools |
| Memory Usage | <100MB | Chrome DevTools |
| Bundle Size | <50KB gzip | Webpack Bundle Analyzer |

## Bundle Size Optimization

### Code Splitting
```javascript
// Before: 300KB bundle
import WaterfallChart from '@ant-design/charts';
import LineChart from 'recharts';

// After: 50KB + lazy-loaded
const WaterfallChart = lazy(() => 
  import('@ant-design/charts')
);
const LineChart = lazy(() => 
  import('recharts')
);

<Suspense fallback={<ChartSkeleton />}>
  <WaterfallChart />
</Suspense>
```

### Tree Shaking
```javascript
// Bad: imports entire library
import * as recharts from 'recharts';

// Good: imports only needed exports
import { LineChart, Line } from 'recharts';
```

### Dynamic Imports for Heavy Charts
```javascript
const loadChart = (type) => {
  switch(type) {
    case 'waterfall':
      return import('./charts/Waterfall');
    case 'heatmap':
      return import('./charts/Heatmap');
    default:
      return import('./charts/Line');
  }
};
```

## Render Performance

### Memoization
```javascript
import { memo, useMemo, useCallback } from 'react';

// Prevent unnecessary re-renders
const KPICard = memo(({ value, label }) => (
  <div>{label}: {value}</div>
), (prevProps, nextProps) => prevProps.value === nextProps.value);

// Memoize expensive calculations
const DashboardView = ({ data }) => {
  const processedData = useMemo(() => 
    aggregateData(data),
    [data]
  );

  const handleUpdate = useCallback((newData) => {
    setData(newData);
  }, []);

  return <Dashboard data={processedData} />;
};
```

### Virtual Scrolling (Large Lists)
```javascript
import { FixedSizeList as List } from 'react-window';

const TradeList = ({ trades }) => (
  <List
    height={600}
    itemCount={trades.length}
    itemSize={50}
    width="100%"
  >
    {({ index, style }) => (
      <div style={style}>
        {trades[index].symbol} {trades[index].pnl}
      </div>
    )}
  </List>
);
```

## Data Update Optimization

### Batch Updates
```javascript
// Problem: 100 updates = 100 re-renders
socket.on('price', (price) => setPrice(price));

// Solution: batch updates every 500ms
const batchUpdates = debounce((updates) => {
  setMetrics(prev => ({ ...prev, ...updates }));
}, 500);

socket.on('price', (price) => {
  pendingUpdates.price = price;
  batchUpdates(pendingUpdates);
});
```

### Selective Updates (Zustand)
```javascript
import create from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

const usePnL = create(
  subscribeWithSelector((set) => ({
    revenue: 0,
    expenses: 0,
    setRevenue: (rev) => set({ revenue: rev }),
    setExpenses: (exp) => set({ expenses: exp })
  }))
);

// Component only re-renders if revenue changes
const RevenueCard = () => {
  const revenue = usePnL(
    state => state.revenue,
    (a, b) => a === b  // Equality check
  );
  
  return <div>{revenue}</div>;
};
```

## Memory Management

### Memory Leak Prevention
```javascript
// Problem: listener not removed
useEffect(() => {
  socket.on('update', handleUpdate);
});

// Solution: cleanup
useEffect(() => {
  socket.on('update', handleUpdate);
  
  return () => {
    socket.off('update', handleUpdate);
  };
}, []);
```

### Large Data Cleanup
```javascript
// Problem: keeps all historical data
const historicalData = useRef([]);

useEffect(() => {
  historicalData.current.push(newData);
}, [newData]);

// Solution: keep only last 100 points
useEffect(() => {
  historicalData.current = 
    historicalData.current.slice(-100);
}, [newData]);
```

## Monitoring Performance

### Web Vitals
```javascript
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

getCLS(console.log);      // Cumulative Layout Shift
getFID(console.log);      // First Input Delay
getFCP(console.log);      // First Contentful Paint
getLCP(console.log);      // Largest Contentful Paint
getTTFB(console.log);     // Time to First Byte
```

### Custom Performance Marks
```javascript
performance.mark('chart-render-start');

render(<WaterfallChart data={data} />);

performance.mark('chart-render-end');
performance.measure('chart-render', 'chart-render-start', 'chart-render-end');

const measure = performance.getEntriesByName('chart-render')[0];
console.log(`Render time: ${measure.duration}ms`);
```

### React DevTools Profiler
```javascript
import { Profiler } from 'react';

<Profiler id="Dashboard" onRender={logRenderMetrics}>
  <Dashboard />
</Profiler>

function logRenderMetrics(id, phase, actualDuration) {
  console.log(`${id} (${phase}) took ${actualDuration}ms`);
}
```

## Network Optimization

### Compression
```javascript
// Gzip compression (handled by server)
app.use(compression());

// Manual compression for large payloads
import pako from 'pako';

const compressData = (data) => {
  const json = JSON.stringify(data);
  return pako.gzip(json);
};

const decompressData = (binary) => {
  return JSON.parse(pako.ungzip(binary, { to: 'string' }));
};
```

### Request Deduplication
```javascript
const requestCache = new Map();

async function fetchWithCache(url) {
  if (requestCache.has(url)) {
    return requestCache.get(url);
  }

  const promise = fetch(url).then(r => r.json());
  requestCache.set(url, promise);

  return promise;
}
```

## Database Query Optimization

### Indexes
```sql
CREATE INDEX idx_pnl_timestamp ON pnl_snapshots(timestamp DESC);
CREATE INDEX idx_api_costs_provider ON api_costs(provider, created_at);
```

### Query Optimization
```javascript
// Bad: N+1 query problem
const jobs = await getJobs();
for (const job of jobs) {
  job.invoices = await getInvoices(job.id);  // 1 + N queries
}

// Good: Join
const jobs = await db.query(`
  SELECT j.*, i.amount FROM jobs j
  LEFT JOIN invoices i ON j.id = i.job_id
`);
```

## Caching Strategy

### HTTP Caching Headers
```javascript
app.get('/api/pnl', (req, res) => {
  res.set('Cache-Control', 'public, max-age=300');  // 5 min
  res.json(getPnL());
});
```

### Service Worker Caching
```javascript
// Cache API responses for offline support
caches.open('pnl-v1').then(cache => {
  cache.addAll([
    '/api/pnl',
    '/api/kalshi/balance',
    '/static/dashboard.js'
  ]);
});
```

## Load Testing

### Benchmark Script
```javascript
async function benchmark() {
  const start = performance.now();
  
  for (let i = 0; i < 1000; i++) {
    await fetch('/api/pnl');
  }
  
  const duration = performance.now() - start;
  console.log(`1000 requests: ${duration}ms (${duration/1000}ms each)`);
}
```

### Load Testing with Apache Bench
```bash
ab -n 1000 -c 100 http://localhost:3001/api/pnl
# 1000 requests, 100 concurrent
```

## Production Checklist

- [ ] Bundle size <50KB gzipped
- [ ] First paint <1s
- [ ] TTI <2s
- [ ] WebSocket latency <200ms
- [ ] Memory usage <100MB
- [ ] 60 FPS on chart updates
- [ ] No console errors/warnings
- [ ] Mobile load time <3s
- [ ] Lighthouse score >90
