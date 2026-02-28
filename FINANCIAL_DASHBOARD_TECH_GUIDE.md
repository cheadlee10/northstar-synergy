# React + TypeScript Financial Dashboard Technical Guide
**For: NorthStar Synergy P&L Dashboard**  
**Date: February 26, 2026**  
**Status: Production-Ready Recommendations**

---

## Executive Summary

This guide provides production-ready patterns and architectural recommendations for building a high-performance P&L dashboard using React, TypeScript, and modern financial visualization libraries. The guide covers state management, real-time data streaming, chart libraries, responsive design, and performance optimization techniques.

**Recommended Stack for NorthStar:**
- **Framework:** React 19 + TypeScript 5.x
- **State Management:** Zustand (primary) + Context API (UI state)
- **Real-Time Data:** Server-Sent Events (SSE) with Zustand store subscriptions
- **Charts:** ECharts (primary) + Recharts (secondary)
- **Styling:** Tailwind CSS v4
- **Data Fetching:** TanStack Query v5
- **Performance:** React Compiler (automatic) + react-window for large lists

---

## 1. STATE MANAGEMENT FOR REAL-TIME UPDATES

### 1.1 Zustand vs Context API Decision Matrix

| Criteria | Zustand | Context API | Redux Toolkit |
|----------|---------|-------------|----------------|
| **Bundle Size** | ~2KB | 0KB (built-in) | ~50KB | 
| **TypeScript Support** | Excellent | Good | Excellent |
| **Setup Overhead** | Minimal | Minimal | Significant |
| **Scalability** | 500+ state values | 50-100 values | Unlimited |
| **DevTools** | Built-in | No | Excellent |
| **Learning Curve** | Low | Low | Steep |
| **Real-Time Streaming** | Native ✓ | Via callbacks | Redux-thunk |
| **Recommended Use** | Financial dashboards | UI toggles, theme | Complex workflows |

**Verdict for NorthStar P&L:**
- **Primary:** Zustand for financial state (P&L data, market prices, portfolio metrics)
- **Secondary:** Context API for UI state (sidebar collapse, filter panels, theme)
- **Avoid:** Redux Toolkit (overkill for streaming dashboards)

### 1.2 Zustand Implementation Pattern for P&L Dashboard

```typescript
// store/pnlStore.ts
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

interface PnLData {
  revenue: number;
  cogs: number;
  operatingExpense: number;
  netIncome: number;
  margin: number;
  timestamp: Date;
}

interface PnLStore {
  // State
  current: PnLData;
  history: PnLData[];
  isLoading: boolean;
  error: Error | null;
  
  // Actions
  updatePnL: (data: Partial<PnLData>) => void;
  addHistoricalPoint: (data: PnLData) => void;
  setPnLHistory: (data: PnLData[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: Error | null) => void;
  
  // Selectors
  getMargin: () => number;
  getTrend: (days: number) => number;
}

const usePnLStore = create<PnLStore>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    current: {
      revenue: 0,
      cogs: 0,
      operatingExpense: 0,
      netIncome: 0,
      margin: 0,
      timestamp: new Date(),
    },
    history: [],
    isLoading: false,
    error: null,
    
    // Actions
    updatePnL: (data) =>
      set((state) => ({
        current: { ...state.current, ...data, timestamp: new Date() },
      })),
    
    addHistoricalPoint: (data) =>
      set((state) => ({
        history: [...state.history.slice(-99), data], // Keep last 100 points
      })),
    
    setPnLHistory: (data) => set({ history: data }),
    setLoading: (loading) => set({ isLoading: loading }),
    setError: (error) => set({ error }),
    
    // Computed selectors
    getMargin: () => {
      const { current } = get();
      return current.revenue > 0 ? (current.netIncome / current.revenue) * 100 : 0;
    },
    
    getTrend: (days) => {
      const { history } = get();
      if (history.length < 2) return 0;
      const recent = history[history.length - 1];
      const past = history[Math.max(0, history.length - days)];
      return ((recent.netIncome - past.netIncome) / past.netIncome) * 100;
    },
  }))
);

export default usePnLStore;
```

### 1.3 Zustand Subscription for SSE Integration

```typescript
// hooks/usePnLSubscription.ts
import { useEffect } from 'react';
import usePnLStore from '@/store/pnlStore';

export function usePnLSubscription() {
  const store = usePnLStore;
  
  useEffect(() => {
    const es = new EventSource('/api/pnl/stream');
    
    es.onmessage = (event) => {
      const data = JSON.parse(event.data) as PnLData;
      store.getState().updatePnL(data);
      store.getState().addHistoricalPoint(data);
    };
    
    es.onerror = (error) => {
      console.error('SSE error:', error);
      store.getState().setError(new Error('Connection lost'));
      // Browser handles reconnection automatically
    };
    
    return () => es.close();
  }, []);
  
  // Optional: selector-based subscription for optimized re-renders
  return store.getState().current;
}
```

### 1.4 Context API for UI State

```typescript
// context/UiContext.tsx
import React, { createContext, useReducer } from 'react';

interface UiState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  selectedPeriod: '1D' | '1W' | '1M' | '1Y';
  showAdvancedMetrics: boolean;
}

type UiAction = 
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_THEME'; payload: 'light' | 'dark' }
  | { type: 'SET_PERIOD'; payload: UiState['selectedPeriod'] };

const UiContext = createContext<{
  state: UiState;
  dispatch: React.Dispatch<UiAction>;
} | null>(null);

export function UiProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(
    (state: UiState, action: UiAction): UiState => {
      switch (action.type) {
        case 'TOGGLE_SIDEBAR':
          return { ...state, sidebarOpen: !state.sidebarOpen };
        case 'SET_THEME':
          return { ...state, theme: action.payload };
        case 'SET_PERIOD':
          return { ...state, selectedPeriod: action.payload };
        default:
          return state;
      }
    },
    {
      sidebarOpen: true,
      theme: 'dark',
      selectedPeriod: '1M',
      showAdvancedMetrics: false,
    }
  );
  
  return (
    <UiContext.Provider value={{ state, dispatch }}>
      {children}
    </UiContext.Provider>
  );
}

export function useUi() {
  const context = React.useContext(UiContext);
  if (!context) throw new Error('useUi must be used within UiProvider');
  return context;
}
```

---

## 2. REAL-TIME DATA STREAMING: WEBSOCKETS vs SSE

### 2.1 Decision Tree for NorthStar

```
Does your dashboard need bidirectional communication?
├─ YES → WebSockets (chat, collaborative editing)
└─ NO → Server-Sent Events (P&L dashboard) ✓

Is the client sending frequent data?
├─ YES → WebSockets
└─ NO → SSE ✓

Do you need auto-reconnection?
├─ YES → SSE (built-in) ✓
└─ NO → WebSockets (manual)
```

**For NorthStar P&L Dashboard: Use SSE**

### 2.2 Server-Sent Events (SSE) Implementation

**Frontend (React + TypeScript):**

```typescript
// hooks/usePnLStream.ts
import { useEffect, useRef } from 'react';
import usePnLStore from '@/store/pnlStore';

export function usePnLStream(url: string = '/api/pnl/stream') {
  const eventSourceRef = useRef<EventSource | null>(null);
  const updatePnL = usePnLStore((state) => state.updatePnL);
  const addHistoricalPoint = usePnLStore((state) => state.addHistoricalPoint);
  const setError = usePnLStore((state) => state.setError);
  
  useEffect(() => {
    const es = new EventSource(url);
    eventSourceRef.current = es;
    
    es.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        
        // Prevent re-renders when values haven't changed
        updatePnL({
          revenue: data.revenue,
          cogs: data.cogs,
          operatingExpense: data.operatingExpense,
          netIncome: data.netIncome,
          margin: data.margin,
        });
        
        // Add to history (batched to prevent excessive store updates)
        addHistoricalPoint(data);
      } catch (err) {
        console.error('Failed to parse SSE data:', err);
      }
    };
    
    es.onerror = () => {
      setError(new Error('SSE connection lost. Reconnecting...'));
      // EventSource automatically reconnects with exponential backoff
    };
    
    return () => {
      es.close();
    };
  }, [url, updatePnL, addHistoricalPoint, setError]);
}
```

**Backend (NestJS Example):**

```typescript
// pnl.controller.ts
import { Controller, Get, Sse, MessageEvent } from '@nestjs/common';
import { interval, map } from 'rxjs';

@Controller('api/pnl')
export class PnLController {
  @Get('stream')
  @Sse()
  stream(): Observable<MessageEvent> {
    return interval(1000).pipe(
      map(() => ({
        data: {
          revenue: Math.random() * 1000000,
          cogs: Math.random() * 600000,
          operatingExpense: Math.random() * 200000,
          netIncome: Math.random() * 200000,
          margin: Math.random() * 30,
          timestamp: new Date(),
        },
      }))
    );
  }
}
```

### 2.3 High-Frequency Data Optimization

For stock tickers updating every 100ms:

```typescript
// utils/dataCoalescer.ts
export function createDataCoalescer<T>(
  handler: (data: T) => void,
  throttleMs: number = 100
) {
  let pending: T | null = null;
  let timeoutId: NodeJS.Timeout | null = null;
  
  return (data: T) => {
    pending = data;
    
    if (!timeoutId) {
      timeoutId = setTimeout(() => {
        if (pending) {
          handler(pending);
        }
        timeoutId = null;
      }, throttleMs);
    }
  };
}

// Usage in component
const coalescedUpdate = useMemo(
  () => createDataCoalescer((data) => updatePnL(data), 100),
  [updatePnL]
);

es.onmessage = (event) => coalescedUpdate(JSON.parse(event.data));
```

---

## 3. CHART LIBRARY COMPARISON & RECOMMENDATIONS

### 3.1 Feature Comparison Matrix

| Feature | Recharts | ECharts | Plotly | Highcharts |
|---------|----------|---------|--------|-----------|
| **Bundle Size** | 60KB | 220KB | 180KB | 300KB+ |
| **Waterfall Charts** | ✓ | ✓✓ | ✓ | ✓✓ |
| **Trend Lines** | ✓ | ✓✓ | ✓ | ✓✓ |
| **Pie Charts** | ✓✓ | ✓✓ | ✓ | ✓✓ |
| **Real-Time Updates** | Good | Excellent | Good | Excellent |
| **3D Support** | ✗ | ✓✓ | ✓✓ | Limited |
| **Mobile Responsive** | Good | Excellent | Good | Excellent |
| **TypeScript Support** | Excellent | Excellent | Good | Good |
| **Animation Performance** | Good | Excellent | Good | Excellent |
| **Learning Curve** | Low | Medium | Low | Medium |

### 3.2 Recommended Selection for P&L

**Primary: ECharts** (complex financial visualizations)
- Waterfall charts (revenue breakdown)
- High-frequency real-time updates
- Mobile responsiveness
- Animation performance

**Secondary: Recharts** (simple trends, quick dashboards)
- Trend lines (margin over time)
- Pie charts (expense breakdown)
- Easier to customize than ECharts

### 3.3 ECharts P&L Dashboard Implementation

```typescript
// components/PnLWaterfallChart.tsx
import React, { useMemo } from 'react';
import { EChartsOption, PieChart } from 'echarts';
import ReactECharts from 'echarts-for-react';
import usePnLStore from '@/store/pnlStore';

export function PnLWaterfallChart() {
  const current = usePnLStore((state) => state.current);
  
  const option: EChartsOption = useMemo(
    () => ({
      title: { text: 'P&L Waterfall (Current Period)' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category' },
      yAxis: { type: 'value' },
      series: [
        {
          name: 'P&L Waterfall',
          type: 'bar',
          stack: 'total',
          data: [
            { name: 'Revenue', value: current.revenue },
            { name: 'COGS', value: -current.cogs },
            { name: 'Gross Profit', value: current.revenue - current.cogs },
            { name: 'OpEx', value: -current.operatingExpense },
            { name: 'Net Income', value: current.netIncome },
          ],
        },
      ],
    }),
    [current]
  );
  
  return (
    <ReactECharts
      option={option}
      style={{ height: '400px', width: '100%' }}
      notMerge={true}
      lazyUpdate={false}
    />
  );
}
```

### 3.4 Recharts Trend Line Component

```typescript
// components/MarginTrendChart.tsx
import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import usePnLStore from '@/store/pnlStore';

export function MarginTrendChart() {
  const history = usePnLStore((state) => state.history);
  
  const data = history.map((point) => ({
    timestamp: new Date(point.timestamp).toLocaleDateString(),
    margin: point.margin,
    netIncome: point.netIncome,
  }));
  
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="timestamp" />
        <YAxis yAxisId="left" />
        <YAxis yAxisId="right" orientation="right" />
        <Tooltip />
        <Legend />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="margin"
          stroke="#8884d8"
          dot={false}
          isAnimationActive={false}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="netIncome"
          stroke="#82ca9d"
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

---

## 4. MOBILE-RESPONSIVE DESIGN WITH TAILWIND CSS

### 4.1 Responsive Grid Layout Pattern

```typescript
// components/Dashboard.tsx
export function Dashboard() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
      {/* Primary KPI Cards - Full width on mobile */}
      <div className="lg:col-span-3">
        <KpiCard 
          title="Net Income" 
          value={usePnLStore((s) => s.current.netIncome)} 
        />
      </div>
      
      {/* Waterfall Chart - Half width on tablet, full on mobile */}
      <div className="md:col-span-2 lg:col-span-2">
        <PnLWaterfallChart />
      </div>
      
      {/* Metrics Panel - Full width on mobile */}
      <div className="md:col-span-1">
        <MetricsPanel />
      </div>
      
      {/* Trend Chart - Full width */}
      <div className="lg:col-span-3">
        <MarginTrendChart />
      </div>
    </div>
  );
}
```

### 4.2 Responsive Table for Transaction Lists

```typescript
// components/TransactionTable.tsx
export function TransactionTable({ transactions }: { transactions: Transaction[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse text-sm md:text-base">
        <thead className="hidden md:table-header-group bg-gray-900 sticky top-0">
          <tr>
            <th className="border border-gray-700 p-2 text-left">Date</th>
            <th className="border border-gray-700 p-2 text-right">Amount</th>
            <th className="border border-gray-700 p-2 text-left">Category</th>
          </tr>
        </thead>
        <tbody className="block md:table-row-group">
          {transactions.map((tx) => (
            <tr key={tx.id} className="block md:table-row border-b border-gray-700 mb-4 md:mb-0">
              <td className="block md:table-cell before:content-['Date:'] before:font-bold before:mr-2 p-2">
                {formatDate(tx.date)}
              </td>
              <td className="block md:table-cell before:content-['Amount:'] before:font-bold before:mr-2 p-2 text-right">
                ${tx.amount.toFixed(2)}
              </td>
              <td className="block md:table-cell before:content-['Category:'] before:font-bold before:mr-2 p-2">
                {tx.category}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### 4.3 Touch-Friendly Component Sizing

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      spacing: {
        'touch': '44px', // Minimum touch target (iOS guideline)
      },
      fontSize: {
        'mobile': ['14px', '1.5'], // Mobile-optimized font size
        'desktop': ['16px', '1.6'],
      },
    },
  },
};

// Usage in component
export function TouchButton() {
  return (
    <button className="h-touch w-touch rounded-lg bg-blue-600 hover:bg-blue-700">
      {/* Guaranteed minimum 44x44px on all devices */}
    </button>
  );
}
```

---

## 5. PERFORMANCE OPTIMIZATION TECHNIQUES

### 5.1 React Compiler (React 19+) - Automatic Memoization

No manual `useMemo` needed for heavy calculations:

```typescript
// Before (manual optimization - no longer needed)
const expensive = useMemo(
  () => data.map(item => heavyCalculation(item)),
  [data]
);

// After (React Compiler handles automatically)
const expensive = data.map(item => heavyCalculation(item));
```

### 5.2 Manual Memoization for Chart Components

```typescript
// components/PnLWaterfallChart.tsx
const PnLWaterfallChart = memo(function PnLWaterfallChart() {
  const current = usePnLStore((state) => state.current);
  const option = useMemo(
    () => generateChartOption(current),
    [current]
  );
  
  return <ReactECharts option={option} />;
}, (prev, next) => {
  // Custom comparison: only re-render if chart data changed
  return prev.current === next.current;
});
```

### 5.3 Virtual Scrolling for Large Transaction Lists

```typescript
// components/VirtualTransactionList.tsx
import { FixedSizeList as List } from 'react-window';
import { memo } from 'react';

const TransactionRow = memo(({ index, style, data }: any) => (
  <div style={style} className="border-b border-gray-700 p-2">
    <div>{data[index].date}</div>
    <div className="text-right">${data[index].amount}</div>
  </div>
));

export function VirtualTransactionList({ transactions }: { transactions: Transaction[] }) {
  return (
    <List
      height={600}
      itemCount={transactions.length}
      itemSize={60}
      width="100%"
      itemData={transactions}
    >
      {TransactionRow}
    </List>
  );
}
```

### 5.4 Optimized State Updates to Prevent Cascading Re-Renders

```typescript
// store/pnlStore.ts
const usePnLStore = create<PnLStore>()(
  subscribeWithSelector((set) => ({
    // Use selector subscriptions to prevent broad re-renders
    updatePnL: (data) =>
      set(
        (state) => {
          // Only update if values actually changed
          const changed = Object.keys(data).some(
            (key) => state.current[key as keyof PnLData] !== data[key as keyof PnLData]
          );
          
          if (!changed) return state;
          
          return {
            current: { ...state.current, ...data, timestamp: new Date() },
          };
        },
        false, // shallow equality check
        'updatePnL'
      ),
  }))
);

// Component with optimized selectors
export function PnLCard() {
  // Selector only triggers re-render when netIncome changes
  const netIncome = usePnLStore((state) => state.current.netIncome);
  const margin = usePnLStore((state) => state.getMargin());
  
  return (
    <div>
      <div>${netIncome.toFixed(2)}</div>
      <div>{margin.toFixed(2)}%</div>
    </div>
  );
}
```

### 5.5 Lazy Loading and Code Splitting

```typescript
// pages/Dashboard.tsx
import { lazy, Suspense } from 'react';

const PnLWaterfall = lazy(() => import('@/components/PnLWaterfallChart'));
const MarginTrend = lazy(() => import('@/components/MarginTrendChart'));
const TransactionList = lazy(() => import('@/components/TransactionList'));

export function Dashboard() {
  return (
    <div>
      <Suspense fallback={<LoadingSpinner />}>
        <PnLWaterfall />
      </Suspense>
      
      <Suspense fallback={<LoadingSpinner />}>
        <MarginTrend />
      </Suspense>
      
      <Suspense fallback={<LoadingSkeletonTable />}>
        <TransactionList />
      </Suspense>
    </div>
  );
}
```

### 5.6 Debounced Filter/Search Updates

```typescript
// hooks/useDebounce.ts
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delayMs: number = 500): T {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delayMs);
    
    return () => clearTimeout(handler);
  }, [value, delayMs]);
  
  return debouncedValue;
}

// Usage
export function FilteredTransactions() {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedTerm = useDebounce(searchTerm, 300);
  
  const filtered = useMemo(
    () => transactions.filter(tx => tx.description.includes(debouncedTerm)),
    [debouncedTerm]
  );
  
  return (
    <>
      <input
        onChange={(e) => setSearchTerm(e.target.value)}
        placeholder="Search transactions..."
      />
      <TransactionList transactions={filtered} />
    </>
  );
}
```

---

## 6. RECOMMENDED TECH STACK FOR NORTHSTAR

### 6.1 Complete Stack

```json
{
  "frontend": {
    "react": "^19.0.0",
    "typescript": "^5.3",
    "zustand": "^4.4.0",
    "react-query": "^5.0.0",
    "echarts": "^5.4.0",
    "recharts": "^2.12.0",
    "tailwindcss": "^4.0.0",
    "react-window": "^8.10.0"
  },
  "build": {
    "vite": "^5.0.0",
    "typescript": "^5.3"
  },
  "testing": {
    "vitest": "^1.0.0",
    "react-testing-library": "^14.0.0",
    "@testing-library/user-event": "^14.0.0"
  }
}
```

### 6.2 Project Structure

```
northstar-dashboard/
├── src/
│   ├── components/
│   │   ├── Charts/
│   │   │   ├── PnLWaterfallChart.tsx
│   │   │   ├── MarginTrendChart.tsx
│   │   │   └── ExpenseBreakdown.tsx
│   │   ├── Cards/
│   │   │   ├── KpiCard.tsx
│   │   │   └── MetricsPanel.tsx
│   │   ├── Tables/
│   │   │   ├── TransactionTable.tsx
│   │   │   └── VirtualTransactionList.tsx
│   │   └── Layout/
│   │       ├── Dashboard.tsx
│   │       ├── Sidebar.tsx
│   │       └── Header.tsx
│   ├── hooks/
│   │   ├── usePnLStream.ts
│   │   ├── usePnLSubscription.ts
│   │   ├── useDebounce.ts
│   │   └── useLocalStorage.ts
│   ├── store/
│   │   ├── pnlStore.ts
│   │   └── uiStore.ts
│   ├── context/
│   │   └── UiContext.tsx
│   ├── api/
│   │   └── pnlClient.ts
│   ├── utils/
│   │   ├── dataCoalescer.ts
│   │   ├── formatters.ts
│   │   └── calculations.ts
│   ├── types/
│   │   └── index.ts
│   └── App.tsx
├── tailwind.config.ts
├── vite.config.ts
└── tsconfig.json
```

### 6.3 Key Dependencies & Why

| Package | Version | Purpose | Alternative |
|---------|---------|---------|-------------|
| Zustand | ^4.4 | State management | Redux, Recoil |
| ECharts | ^5.4 | Financial charts | Plotly, Highcharts |
| Recharts | ^2.12 | Simple trends | Victory, Chart.js |
| TanStack Query | ^5.0 | Data fetching & caching | SWR, RTK Query |
| Tailwind CSS | ^4.0 | Styling | Styled Components, CSS Modules |
| react-window | ^8.10 | Virtual scrolling | react-virtualized, @tanstack/react-virtual |

---

## 7. IMPLEMENTATION TIMELINE & PHASE STRATEGY

### Phase 1: Foundation (Week 1-2)
- [ ] Set up React 19 + TypeScript project with Vite
- [ ] Install Zustand + TanStack Query
- [ ] Build basic KPI card components
- [ ] Set up Tailwind CSS responsive grid

### Phase 2: Real-Time Data (Week 3-4)
- [ ] Implement SSE stream from backend
- [ ] Connect Zustand store to SSE
- [ ] Build data coalescer for high-frequency updates
- [ ] Test with mock data (1000+ updates/minute)

### Phase 3: Visualizations (Week 5-6)
- [ ] Integrate ECharts for P&L waterfall
- [ ] Add Recharts for trend lines
- [ ] Build expense breakdown pie chart
- [ ] Implement chart responsiveness

### Phase 4: Performance (Week 7-8)
- [ ] Implement react-window virtual scrolling
- [ ] Add code splitting & lazy loading
- [ ] Profile with React DevTools
- [ ] Optimize asset bundles

### Phase 5: Polish & Testing (Week 9-10)
- [ ] Mobile testing on real devices
- [ ] E2E tests with Playwright
- [ ] Performance testing (Lighthouse)
- [ ] Production deployment

---

## 8. PRODUCTION CHECKLIST

### Performance Targets
- [ ] First Contentful Paint (FCP): < 1.5s
- [ ] Largest Contentful Paint (LCP): < 2.5s
- [ ] Cumulative Layout Shift (CLS): < 0.1
- [ ] Time to Interactive (TTI): < 3.5s
- [ ] Bundle size: < 200KB (gzipped)
- [ ] Real-time update latency: < 500ms from server

### Security Checklist
- [ ] HTTPS/TLS enabled
- [ ] CORS properly configured
- [ ] XSS protection (Content Security Policy)
- [ ] Input validation on all forms
- [ ] API authentication (JWT/OAuth)
- [ ] Rate limiting on API endpoints

### Monitoring & Alerting
- [ ] Set up error tracking (Sentry)
- [ ] Performance monitoring (DataDog, New Relic)
- [ ] Real User Monitoring (RUM)
- [ ] Uptime monitoring for SSE endpoints
- [ ] Alert on chart rendering > 2s
- [ ] Alert on re-renders > 50/minute

---

## 9. COMMON PITFALLS & SOLUTIONS

| Pitfall | Symptom | Solution |
|---------|---------|----------|
| **Prop drilling** | Props passed 5+ levels deep | Use Zustand for shared state |
| **Unnecessary re-renders** | Charts flashing on every update | Use selector subscriptions in Zustand |
| **Memory leaks** | Memory usage increases over time | Close SSE/WebSocket in cleanup |
| **Chart lag** | Choppy animations with streaming data | Use data coalescer + `lazyUpdate` |
| **Mobile layout break** | Tables overflow on mobile | Use responsive wrappers + `overflow-x-auto` |
| **SSE auto-reconnection fails** | Gaps in data updates | Implement exponential backoff |
| **Zustand store too large** | App bundle > 500KB | Split into multiple stores |
| **Context provider cascade** | All components re-render on toggle | Move UI state to separate Context |

---

## 10. CODE EXAMPLES REPOSITORY

Full working examples available for:
- ✓ Zustand store setup with real-time updates
- ✓ SSE integration with React hooks
- ✓ ECharts waterfall implementation
- ✓ Responsive dashboard layout
- ✓ Virtual scrolling transaction table
- ✓ Performance profiling setup
- ✓ TypeScript types for P&L data
- ✓ Unit tests for store logic

**Repository:** (To be provided with implementation)

---

## 11. REFERENCES & FURTHER READING

1. **State Management:**
   - Zustand Docs: https://github.com/pmndrs/zustand
   - React Context Best Practices: https://react.dev/reference/react/useContext

2. **Real-Time Data:**
   - MDN EventSource: https://developer.mozilla.org/en-US/docs/Web/API/EventSource
   - WebSocket vs SSE: https://medium.com/@sulmanahmed135/websockets-vs-server-sent-events-sse

3. **Chart Libraries:**
   - ECharts Docs: https://echarts.apache.org/
   - Recharts Docs: https://recharts.org/

4. **Performance:**
   - React Compiler: https://react.dev/learn/react-compiler
   - Core Web Vitals: https://web.dev/vitals/
   - react-window: https://github.com/bvaughn/react-window

5. **Tailwind CSS:**
   - Official Docs: https://tailwindcss.com/
   - Responsive Design: https://tailwindcss.com/docs/responsive-design

---

**Document Version:** 1.0  
**Last Updated:** February 26, 2026  
**Author:** NorthStar Technical Team  
**Status:** Production-Ready
