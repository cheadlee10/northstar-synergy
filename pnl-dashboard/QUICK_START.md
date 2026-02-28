# Quick Start Guide - NorthStar P&L Dashboard

Get the dashboard up and running in 3 minutes.

## Prerequisites

- **Node.js**: v16 or higher
- **npm**: v8 or higher
- **Git**: (optional, for version control)

Verify installation:
```bash
node --version  # Should be v16+
npm --version   # Should be v8+
```

## Installation (2 minutes)

### Step 1: Install Dependencies

```bash
cd pnl-dashboard
npm install
```

This installs:
- React 18
- Vite (build tool)
- Tailwind CSS
- Recharts
- Ant Design Charts
- DaisyUI

### Step 2: Start Development Server

```bash
npm run dev
```

Output will show:
```
  ➜  Local:   http://localhost:5173/
  ➜  press h + enter to show help
```

### Step 3: Open in Browser

Visit: **http://localhost:5173**

✅ Dashboard is now running with mock data!

---

## What You're Seeing

### Dashboard Layout
```
┌─────────────────────────────────────────┐
│  NorthStar Synergy | P&L Dashboard      │
├─────────────────────────────────────────┤
│  [Revenue] [Expenses] [Net P&L] Cards   │
├─────────────────────────────────────────┤
│  [P&L Waterfall Chart] (full width)     │
├────────────────────┬────────────────────┤
│  [Trend Chart]     │  [Cost Breakdown]  │
├─────────────────────────────────────────┤
│  [Agent Attribution Bar Chart]          │
└─────────────────────────────────────────┘
```

### Features Working

✅ **KPI Cards**
- Revenue: $125,450 (animated counter)
- Expenses: $48,320 (animated counter)
- Net P&L: $77,130 (animated counter)
- Each shows change vs previous period

✅ **Charts**
1. Waterfall - Revenue flows to Expenses to Net
2. Trend Line - 30-day historical data
3. Cost Pie - Expense distribution (4 categories)
4. Agent Bar - Scalper/John/Cliff performance

✅ **Responsive Design**
- Resize browser to test mobile layout
- Changes from 4-col → 2-col → 1-col

✅ **Dark Theme**
- Cyan accents (#00d4ff)
- Dark background (#1a1a2e)
- Gradient card styles

---

## Mock Data Explained

Current data is in `App.jsx`:

```javascript
const mockPnLData = {
  revenue: 125450,
  expenses: 48320,
  netPnL: 77130,
};

const mock30DaysTrend = [
  { date: '2026-01-27', revenue: 108000, ... },
  // ... 30 days of data
];
```

### To Change Mock Data:

Edit `App.jsx` and update:
```javascript
mockPnLData       // KPI card values
mock30DaysTrend   // Trend line chart data
mockCostBreakdown // Cost pie chart
mockAgentAttribution // Agent bar chart
```

All charts will update automatically!

---

## Development Commands

### Run Development Server
```bash
npm run dev
```
- Hot reload enabled
- Runs on port 5173
- Press `q` to quit

### Build for Production
```bash
npm run build
```
- Output: `dist/` folder
- Optimized bundle
- Ready to deploy

### Preview Production Build
```bash
npm run preview
```
- Test production build locally
- Runs on port 4173

---

## Next Steps: WebSocket Integration

Once your backend server is ready:

### 1. Update Environment

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env`:
```
VITE_WS_URL=ws://your-server.com/pnl-stream
VITE_WS_SECURE=true
VITE_API_URL=https://your-server.com/api
```

### 2. Uncomment WebSocket Code

In `App.jsx`, find the `useEffect` and uncomment:

```jsx
useEffect(() => {
  const ws = new WebSocket('ws://your-server/pnl-stream');
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    setPnlData(data.pnl);
    setTrendsData(data.trends);
    // ... update all state
  };
  
  return () => ws.close();
}, []);
```

### 3. Expected Data Format

Server should send:
```json
{
  "revenue": 125450,
  "expenses": 48320,
  "netPnL": 77130,
  "previousRevenue": 118200,
  "previousExpenses": 45600,
  "previousNetPnL": 72600,
  "trendsData": [...],
  "costBreakdown": [...],
  "agentAttribution": [...]
}
```

See `INTEGRATION_GUIDE.md` for complete examples.

---

## Customization Quick Tips

### Change Colors

**Tailwind Config** (`tailwind.config.js`):
```javascript
colors: {
  northstar: {
    dark: '#1a1a2e',      // Dark background
    cyan: '#00d4ff',      // Primary accent
  }
}
```

### Change Animation Speed

**KPI Card** (`components/KPICard.jsx`):
```jsx
<AnimatedCounter value={value} duration={800} />
// Change 800 to desired ms (faster = lower number)
```

### Add More Agents

**App.jsx**:
```javascript
mockAgentAttribution.push({
  agent: "NewAgent",
  revenue: 50000,
  expenses: 20000,
  net: 30000,
});
```

### Change Chart Heights

**Components** (e.g., `TrendLineChart.jsx`):
```jsx
<ResponsiveContainer width="100%" height={300}>
// Change 300 to desired height in pixels
```

---

## Troubleshooting

### npm install fails
```bash
# Clear npm cache
npm cache clean --force

# Try again
npm install
```

### Port 5173 already in use
```bash
# Kill process on port 5173, or specify different port
npm run dev -- --port 5174
```

### Charts not rendering
```bash
# Ensure all packages installed
npm list recharts @ant-design/charts

# If missing, install:
npm install recharts @ant-design/charts
```

### Tailwind styles not applied
```bash
# Make sure dev server is running (it processes Tailwind)
# Don't use static file serving - use `npm run dev`
```

### Hot reload not working
- Ensure you're in the project directory
- Check that file changes are being detected
- Try restarting dev server

---

## Browser DevTools

### Check WebSocket (when connected)
1. Open DevTools (F12)
2. Go to Network tab
3. Filter by "WS"
4. Should see your WebSocket connection
5. Click it → Messages tab to see data flow

### Check Component Render
1. Install React DevTools extension
2. Open Components tab
3. Inspect component tree
4. View props being passed

### Check Network Performance
1. Go to Network tab
2. Build size should be ~100-150 KB
3. Chunking: recharts and ant-charts separate

---

## Deployment Options

### Option 1: Netlify (Recommended)
```bash
npm run build
# Drag & drop dist/ folder to Netlify
```

### Option 2: Vercel
```bash
npm install -g vercel
vercel
```

### Option 3: Docker
```bash
# Uses included Dockerfile
docker build -t pnl-dashboard .
docker run -p 5173:5173 pnl-dashboard
```

### Option 4: Node Server
```bash
npm run build
npm install -g serve
serve -s dist -l 3000
```

---

## File Locations Reference

| File | Purpose | Edit for |
|------|---------|----------|
| `App.jsx` | Main app | Data, layout |
| `components/*.jsx` | Individual charts | Chart styling |
| `tailwind.config.js` | Color theme | Brand colors |
| `index.css` | Global styles | Global CSS |
| `.env` | Server config | Backend URLs |

---

## Getting Help

### Documentation Files
- **README.md** - Full feature overview
- **INTEGRATION_GUIDE.md** - WebSocket setup
- **DELIVERABLES.md** - Complete inventory
- **FILE_STRUCTURE.txt** - File reference

### Common Issues
See INTEGRATION_GUIDE.md "Troubleshooting" section

### Support
For NorthStar team: Contact development lead

---

## What's Next?

1. ✅ **Running**: Dashboard is live on http://localhost:5173
2. 📊 **Explore**: Click around, test responsive design
3. 🔌 **Integrate**: Connect WebSocket when backend ready
4. 🚀 **Deploy**: Build and deploy to production

---

**Enjoy your new P&L Dashboard! 🚀**

Questions? See the full documentation files in this folder.
