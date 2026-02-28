# NorthStar Synergy P&L Dashboard

Real-time Profit & Loss dashboard for NorthStar Synergy's trading analytics and agent attribution.

## 🎯 Features

- **KPI Cards** - Real-time Revenue, Expenses, and Net P&L with animated counters
- **P&L Waterfall Chart** - Visual breakdown of Revenue → Expenses → Net using Ant Design Charts
- **30-Day Trend Chart** - Daily P&L trends with Recharts
- **Cost Breakdown Pie Chart** - Expense distribution by category
- **Agent Attribution Bar Chart** - Performance metrics for Scalper, John, and Cliff
- **Dark Theme** - NorthStar branding with cyan (#00d4ff) and dark (#1a1a2e) colors
- **Responsive Design** - 4-column desktop layout, 1-column mobile
- **Real-time Updates** - WebSocket-ready for live data streaming

## 📦 Tech Stack

- **React 18** - Modern UI framework
- **Vite** - Lightning-fast build tool
- **Tailwind CSS** - Utility-first styling
- **DaisyUI** - Component library
- **Recharts** - Composable charting library
- **@ant-design/charts** - High-level chart components

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Development Server

```bash
npm run dev
```

The dashboard will be available at `http://localhost:5173`

### 3. Build for Production

```bash
npm run build
```

Production files will be in the `dist/` folder.

## 📁 Project Structure

```
pnl-dashboard/
├── App.jsx                          # Main app component with grid layout
├── components/
│   ├── KPICard.jsx                 # Revenue/Expenses/Net P&L cards with counters
│   ├── WaterfallChart.jsx          # P&L waterfall visualization
│   ├── TrendLineChart.jsx          # 30-day trend analysis
│   ├── CostBreakdownPie.jsx        # Expense distribution
│   └── AgentAttributionBar.jsx     # Agent performance breakdown
├── main.jsx                        # React entry point
├── index.html                      # HTML template
├── index.css                       # Global styles and animations
├── package.json                    # Dependencies
├── vite.config.js                  # Vite configuration
├── tailwind.config.js              # Tailwind CSS config
└── postcss.config.js               # PostCSS config

```

## 🔌 WebSocket Integration

### Current Mock Data Setup

The app currently uses mock data in `App.jsx`. To integrate with a real WebSocket stream:

```javascript
// In App.jsx useEffect()
useEffect(() => {
  const ws = new WebSocket('ws://your-server/pnl-stream');
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // Update state with real data
    setPnlData({
      revenue: data.revenue,
      expenses: data.expenses,
      netPnL: data.netPnL,
      previousRevenue: data.previousRevenue,
      previousExpenses: data.previousExpenses,
      previousNetPnL: data.previousNetPnL,
    });
    
    setTrendsData(data.trendsData);
    setCostBreakdown(data.costBreakdown);
    setAgentAttribution(data.agentAttribution);
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  return () => ws.close();
}, []);
```

### Expected WebSocket Message Format

```json
{
  "revenue": 125450,
  "expenses": 48320,
  "netPnL": 77130,
  "previousRevenue": 118200,
  "previousExpenses": 45600,
  "previousNetPnL": 72600,
  "trendsData": [
    {
      "date": "2026-02-25",
      "revenue": 125450,
      "expenses": 48320,
      "net": 77130
    }
  ],
  "costBreakdown": [
    {
      "name": "Trading Fees",
      "value": 18500,
      "percentage": 38.3
    }
  ],
  "agentAttribution": [
    {
      "agent": "Scalper",
      "revenue": 75000,
      "expenses": 28500,
      "net": 46500
    }
  ]
}
```

## 🎨 Customization

### NorthStar Color Scheme

Update colors in `tailwind.config.js`:

```javascript
colors: {
  northstar: {
    dark: '#1a1a2e',      // Dark background
    cyan: '#00d4ff',      // Primary accent
    secondary: '#16213e', // Secondary bg
    accent: '#0f3460',    // Accent bg
  }
}
```

### Component Styling

All components use Tailwind CSS with the dark theme. Modify gradient colors in component files:

```jsx
// Example: Change card background
className="bg-gradient-to-br from-emerald-900/20 to-emerald-800/10"
```

## 📊 Data Flow

```
WebSocket Server
       ↓
   App.jsx (State)
       ↓
    ├─→ KPICard (Real-time counters)
    ├─→ WaterfallChart (Revenue breakdown)
    ├─→ TrendLineChart (30-day trends)
    ├─→ CostBreakdownPie (Expenses)
    └─→ AgentAttributionBar (Agent stats)
```

## ⚙️ Performance Optimization

### Lazy Loading

For large datasets, consider lazy loading components:

```jsx
import { lazy, Suspense } from 'react';

const TrendLineChart = lazy(() => import('./components/TrendLineChart'));

<Suspense fallback={<div>Loading chart...</div>}>
  <TrendLineChart data={trendsData} />
</Suspense>
```

### Memoization

Components are optimized with memoization:

```jsx
export default React.memo(KPICard);
```

## 🔐 Security

- **No sensitive data** in frontend code
- API keys should be stored in `.env` files
- WebSocket connections should use secure WSS protocol in production

## 📱 Responsive Behavior

- **Desktop (lg)**: 4-column KPI cards, side-by-side charts
- **Tablet (md)**: 2-column KPI cards, stacked charts
- **Mobile (sm)**: 1-column layout, optimized chart sizes

## 🐛 Troubleshooting

### Charts Not Rendering

Ensure `recharts` and `@ant-design/charts` are installed:

```bash
npm install recharts @ant-design/charts
```

### Tailwind Styles Not Applied

Run the dev server to ensure Tailwind processes CSS:

```bash
npm run dev
```

### WebSocket Connection Issues

Check browser console for errors and ensure:
- WebSocket URL is correct
- Server is running
- CORS is configured if needed

## 📚 References

- [React Documentation](https://react.dev)
- [Vite Guide](https://vitejs.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Recharts](https://recharts.org)
- [@ant-design/charts](https://charts.ant.design)

## 🤝 Contributing

This dashboard is maintained by the NorthStar Synergy team. For updates or feature requests, contact the development team.

## 📄 License

Internal use only - NorthStar Synergy

---

**Last Updated**: February 25, 2026
**Status**: Ready for WebSocket Integration
