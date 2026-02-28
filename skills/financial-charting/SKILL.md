---
name: financial-charting
description: Build professional financial charts (waterfall, gauges, heatmaps, time series) for P&L dashboards. Use when creating P&L decomposition visuals, tracking profit/loss trends, displaying cost breakdowns, or building real-time trading dashboards. Includes Recharts, ECharts, and Ant Design patterns with mobile optimization and accessibility.
---

# Financial Charting Skill

Production-ready patterns for financial data visualization with real-time updates, mobile responsiveness, and enterprise design.

## Chart Selection Guide

| Chart Type | Best For | Library | Latency |
|-----------|----------|---------|---------|
| **Waterfall** | P&L decomposition | ECharts, Ant Design | <100ms |
| **Line (Time Series)** | Trend tracking | Recharts | <50ms |
| **Stacked Bar** | Composition over time | Recharts | <50ms |
| **Gauge** | Single metric indicator | react-d3-speedometer | <100ms |
| **Heatmap** | Cost breakdown by category | ECharts | <150ms |
| **Pie/Donut** | Percentage mix | Recharts | <50ms |

## Waterfall Chart (Core P&L Visual)

### Recharts Approach (Custom)
```jsx
import { ComposedChart, Bar, Line, XAxis, YAxis, Tooltip } from 'recharts';

const data = [
  { name: 'Revenue', uv: 500000, pv: 500000, amt: 500000 },
  { name: 'COGS', uv: -300000, pv: 200000, amt: 200000 },
  { name: 'OpEx', uv: -120000, pv: 80000, amt: 80000 },
  { name: 'Tax', uv: -25000, pv: 55000, amt: 55000 }
];

export const RechartsWaterfall = () => (
  <ComposedChart data={data} width={600} height={400}>
    <XAxis dataKey="name" />
    <YAxis />
    <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
    <Bar dataKey="pv" stackId="stack" fill="#16A34A" />
    <Bar dataKey="uv" stackId="stack" fill="#DC2626" />
  </ComposedChart>
);
```

### ECharts Approach (Native Waterfall)
```jsx
import ECharts from 'echarts-for-react';

const option = {
  title: { text: 'P&L Waterfall' },
  xAxis: { type: 'category', data: ['Revenue', 'COGS', 'OpEx', 'Tax', 'Net'] },
  yAxis: { type: 'value' },
  series: [
    {
      name: 'P&L',
      type: 'waterfall',
      data: [
        { value: 500000, itemStyle: { color: '#16A34A' } },
        { value: -300000, itemStyle: { color: '#DC2626' } },
        { value: -120000, itemStyle: { color: '#DC2626' } },
        { value: -25000, itemStyle: { color: '#DC2626' } },
        { value: 0, itemStyle: { color: '#16A34A' } }
      ],
      label: { show: true, formatter: '{b}' }
    }
  ]
};

export const EchartsWaterfall = () => (
  <ECharts option={option} style={{ width: '100%', height: 400 }} />
);
```

### Ant Design Charts Approach (Production-Ready)
```jsx
import { Waterfall } from '@ant-design/charts';

const data = [
  { category: 'Revenue', value: 500000 },
  { category: 'COGS', value: -300000 },
  { category: 'OpEx', value: -120000 },
  { category: 'Tax', value: -25000 }
];

export const AntWaterfall = () => (
  <Waterfall
    data={data}
    xField="category"
    yField="value"
    seriesField="category"
    color={['#16A34A', '#DC2626']}
  />
);
```

## Time Series Chart (Trend Tracking)

### Real-Time P&L Trend
```jsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useEffect, useState } from 'react';

export const PnLTrend = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    // Simulate real-time updates
    const interval = setInterval(() => {
      setData(prev => {
        const newPoint = {
          date: new Date().toLocaleDateString(),
          pnl: (prev[prev.length - 1]?.pnl || 0) + (Math.random() * 10000 - 5000)
        };
        return [...prev.slice(-99), newPoint];  // Keep last 100 points
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip 
          contentStyle={{ backgroundColor: 'rgba(0,0,0,0.7)' }}
          formatter={(value) => `$${value.toLocaleString()}`}
        />
        <Line 
          type="monotone" 
          dataKey="pnl" 
          stroke="#2563EB" 
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}  // Disable animation for real-time
        />
      </LineChart>
    </ResponsiveContainer>
  );
};
```

## Gauge Chart (Profit/Loss Indicator)

### react-d3-speedometer
```jsx
import ReactSpeedometer from 'react-d3-speedometer';

export const ProfitGauge = ({ pnlValue }) => (
  <ReactSpeedometer
    minValue={-100000}
    maxValue={100000}
    value={pnlValue}
    needleColor="#2563EB"
    startColor="#DC2626"
    segments={5}
    segmentColors={['#DC2626', '#EA580C', '#FCD34D', '#86EFAC', '#16A34A']}
    textColor="#000"
    customSegmentStops={[-100000, -50000, 0, 50000, 100000]}
    customSegmentLabels={['Large Loss', 'Loss', 'Break-Even', 'Profit', 'Large Profit']}
  />
);
```

## Heatmap (Cost Breakdown)

### ECharts Heatmap
```jsx
import ECharts from 'echarts-for-react';

const costData = [
  ['Q1', 'Labor', 45000],
  ['Q1', 'Equipment', 25000],
  ['Q1', 'Facilities', 18000],
  ['Q2', 'Labor', 48000],
  ['Q2', 'Equipment', 22000],
  ['Q2', 'Facilities', 20000]
];

const option = {
  title: { text: 'Cost Breakdown by Category & Quarter' },
  xAxis: { type: 'category', data: ['Q1', 'Q2', 'Q3', 'Q4'] },
  yAxis: { type: 'category', data: ['Labor', 'Equipment', 'Facilities'] },
  visualMap: { min: 0, max: 50000, color: ['#16A34A', '#DC2626'] },
  series: [
    {
      data: costData,
      type: 'heatmap',
      emphasis: { itemStyle: { borderColor: '#000', borderWidth: 1 } }
    }
  ]
};

export const CostHeatmap = () => (
  <ECharts option={option} style={{ width: '100%', height: 400 }} />
);
```

## Stacked Bar (Agent Attribution)

### Agent P&L Contribution
```jsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const data = [
  { date: '2026-02-20', cliff: -50, scalper: 1200, john: 300 },
  { date: '2026-02-21', cliff: -75, scalper: 850, john: 400 },
  { date: '2026-02-22', cliff: -60, scalper: 1050, john: 250 }
];

export const AgentAttributionChart = () => (
  <ResponsiveContainer width="100%" height={400}>
    <BarChart data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="date" />
      <YAxis />
      <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
      <Legend />
      <Bar dataKey="cliff" stackId="a" fill="#2563EB" name="Cliff (Costs)" />
      <Bar dataKey="scalper" stackId="a" fill="#16A34A" name="Scalper (Trading)" />
      <Bar dataKey="john" stackId="a" fill="#8B5CF6" name="John (Revenue)" />
    </BarChart>
  </ResponsiveContainer>
);
```

## Mobile Optimization

### Responsive Container Pattern
```jsx
export const ResponsiveChart = ({ children }) => (
  <ResponsiveContainer width="100%" height={300}>
    {children}
  </ResponsiveContainer>
);
```

### Data Reduction on Mobile
```javascript
const getChartData = () => {
  const isMobile = window.innerWidth < 768;
  const allData = fetchData();
  
  // Show every other point on mobile
  return isMobile ? allData.filter((_, i) => i % 2 === 0) : allData;
};
```

### Touch-Friendly Tooltip
```jsx
<Tooltip 
  contentStyle={{ 
    backgroundColor: 'rgba(0,0,0,0.85)',
    borderRadius: '8px',
    padding: '12px'
  }}
  cursor={{ strokeDasharray: '3 3' }}
/>
```

## Performance Optimization

### Memoization
```jsx
import { useMemo } from 'react';

const PnLChart = memo(({ data }) => {
  const memoizedData = useMemo(() => processData(data), [data]);
  return <LineChart data={memoizedData} />;
});
```

### Lazy Loading
```jsx
import { lazy, Suspense } from 'react';

const WaterfallChart = lazy(() => import('./WaterfallChart'));

export const Dashboard = () => (
  <Suspense fallback={<div>Loading chart...</div>}>
    <WaterfallChart />
  </Suspense>
);
```

## Accessibility

### Color + Label
```jsx
// ✅ Good: color + label + symbol
<Bar dataKey="profit" fill="#16A34A" name="Profit ↑" />
<Bar dataKey="loss" fill="#DC2626" name="Loss ↓" />

// ❌ Bad: color only
<Bar dataKey="value" fill={value > 0 ? '#16A34A' : '#DC2626'} />
```

### ARIA Labels
```jsx
<div role="img" aria-label="P&L trend: $1.2M gain over 30 days">
  <PnLTrendChart />
</div>
```

## Color Palette

```javascript
const chartColors = {
  profit: '#16A34A',      // Green
  loss: '#DC2626',        // Red
  neutral: '#6B7280',     // Gray
  alert: '#EA580C',       // Orange
  primary: '#2563EB',     // Blue
  secondary: '#8B5CF6',   // Purple
  tertiary: '#06B6D4'     // Cyan
};
```

## Testing Charts

```javascript
test('renders waterfall with correct data', () => {
  const { getByText } = render(
    <WaterfallChart data={mockData} />
  );
  expect(getByText('Revenue')).toBeInTheDocument();
});

test('updates on data change', () => {
  const { rerender } = render(<PnLChart data={data1} />);
  rerender(<PnLChart data={data2} />);
  expect(getByText('Updated Value')).toBeInTheDocument();
});
```

## Performance Benchmarks

| Chart | Library | 1K Points | 10K Points | Mobile |
|-------|---------|-----------|------------|--------|
| Waterfall | ECharts | 80ms | 250ms | Good |
| Line | Recharts | 40ms | 150ms | Good |
| Heatmap | ECharts | 100ms | 400ms | Fair |
| Gauge | Speedometer | 50ms | N/A | Excellent |
| Pie | Recharts | 30ms | 100ms | Good |
