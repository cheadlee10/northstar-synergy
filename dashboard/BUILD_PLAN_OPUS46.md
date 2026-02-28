# P&L Dashboard Build Plan — Opus 4.6 Unlimited Mode
**Deadline: Tonight (Wednesday 2026-02-25)**
**Mission: Enterprise-class real-time P&L dashboard**

---

## NORTH STAR VISION

When Craig opens the dashboard, he should see in 3 seconds:
- **Current net P&L** (huge, colored: green/red)
- **Revenue vs Expenses waterfall** (how we got here)
- **Today's P&L trend** (is it getting better or worse?)
- **Agent attribution** (who's burning budget, who's making money)
- **Red flags** (expenses spike, revenue drop, margin compression)

**Design Philosophy:**
- Dark theme (NorthStar cyan #00d4ff on #1a1a2e)
- Zero clutter (only metrics that drive decisions)
- Real-time without lag (sub-second updates)
- Mobile-first (works on phone at 4 AM)
- Enterprise polish (Bloomberg/Stripe quality)

---

## DATA ARCHITECTURE

### Sources (Real-Time Sync)
```
Database: northstar.db (SQLite)
├── API Costs (Anthropic SDK, OpenRouter, etc)
├── Kalshi Trades (Scalper - live balance, P&L, positions)
├── John's Revenue (jobs, invoices, collections)
└── Operational Costs (infrastructure, subscriptions)

Cron Jobs (Auto-Populate):
├── 8 AM PT: Sync all sources → northstar.db
├── 12 PM PT: Update P&L snapshots
├── 6 PM PT: Generate daily report
└── 10 PM PT: Backup + archive
```

### Real-Time Data Flow
```
northstar.db (source of truth)
    ↓
Flask API (/api/pnl-stream)
    ↓
WebSocket or Server-Sent Events
    ↓
React Dashboard (live counter updates)
```

---

## FRONTEND ARCHITECTURE

### Tech Stack
- **Framework:** React 18 (hooks, context for state)
- **Styling:** Tailwind CSS + custom CSS modules
- **Charts:** Recharts (lightweight, React-native, real-time)
- **Real-time:** Socket.io or Server-Sent Events (WebSocket fallback)
- **Build:** Vite (fast HMR, sub-2s refresh)
- **Icons:** Heroicons (clean, professional)

### Component Structure
```
App
├── Header (NorthStar logo, timestamp, status)
├── MainMetrics
│   ├── RevenueBig (animated counter)
│   ├── ExpensesBig (animated counter)
│   └── NetPLBig (GREEN/RED, animated counter)
├── Waterfall
│   └── WaterfallChart (Revenue → Expenses → Net)
├── TimeSeries
│   └── PnlTrend (last 30 days, moving average)
├── Breakdown
│   ├── ByAgent (Cliff, Scalper, John)
│   ├── BySource (Kalshi, John, Anthropic costs)
│   └── ByCost (API, Infrastructure, other)
├── Alerts
│   └── RedFlags (margin drop >5%, expense spike, etc)
└── Footer (last updated, data source, refresh button)
```

---

## KEY METRICS TO DISPLAY

### Tier 1 (Hero Section)
- **Total Revenue (YTD)** — All sources combined
- **Total Expenses (YTD)** — All costs combined
- **Net P&L (YTD)** — Revenue minus expenses
- **Gross Margin %** — (Revenue - Expenses) / Revenue

### Tier 2 (By Source)
- **Kalshi P&L** — Live balance, today's P&L, month P&L
- **John's Revenue** — Invoiced, collected, outstanding
- **API Costs** — Anthropic, OpenRouter, other (breakdown by provider)

### Tier 3 (Trends)
- **Daily P&L** — Last 30 days (line chart with moving average)
- **Weekly P&L** — Last 12 weeks (bar chart)
- **Monthly P&L** — YTD (stacked bar: revenue vs expenses)

### Tier 4 (Alerts)
- Expense spike (>20% above avg)
- Revenue drop (>15% below avg)
- Margin compression (<5% net margin)
- Large individual trades (Scalper positions >$100)

---

## CHART SPECIFICATIONS

### 1. P&L Waterfall (Main Chart)
```
Logic: Revenue → Subtract Expenses → Net P&L
Visual: Left-aligned revenue bar (green)
        Individual expense bars (red, stacked or separate)
        Right-aligned net bar (green if +, red if -)
```

### 2. Daily Trend (Time Series)
```
X-axis: Last 30 days (daily)
Y-axis: Cumulative P&L ($)
Line: Blue, smooth curve
Fill: Light blue with opacity
Hover: Show date, value, % change from prev day
```

### 3. Cost Breakdown (Pie or Donut)
```
Slices: API Costs, Kalshi Losses, Operational
Colors: Different shades of red
Hover: Show dollar amount + % of total
```

### 4. Agent Attribution (Stacked Bar)
```
X-axis: Last 7 days (daily)
Y-axis: P&L ($)
Stacks: Cliff (blue), Scalper (green), John (purple)
Legend: Toggle on/off to isolate agents
```

---

## REAL-TIME UPDATE STRATEGY

### Option A: WebSocket (Best)
```javascript
// Backend: Flask
@app.websocket("/ws/pnl")
async def websocket_endpoint(websocket):
    await websocket.accept()
    while True:
        data = get_latest_pnl()  # Fetch from DB
        await websocket.send_json(data)
        await asyncio.sleep(5)  # Update every 5 seconds

// Frontend: React
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8765/ws/pnl');
  ws.onmessage = (e) => setPnlData(JSON.parse(e.data));
}, []);
```

### Option B: Server-Sent Events (Fallback)
```javascript
// Backend
@app.get("/api/pnl-stream")
async def pnl_stream():
    async def event_generator():
        while True:
            yield f"data: {json.dumps(get_latest_pnl())}\n\n"
            await asyncio.sleep(5)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

// Frontend
useEffect(() => {
  const sse = new EventSource('/api/pnl-stream');
  sse.onmessage = (e) => setPnlData(JSON.parse(e.data));
}, []);
```

---

## DEPLOYMENT & PERFORMANCE

### Local Development
```bash
# Backend: Flask with hot reload
python dashboard/app.py --reload

# Frontend: React with Vite
npm run dev

# Test: localhost:3000 (React) ↔ localhost:8765 (Flask)
```

### Production (Railway)
```
Vite build → static/ folder
Flask serves React bundle + API endpoints
WebSocket persistent connection
Fallback: SSE if WebSocket blocked
```

### Performance Targets
- **First paint:** <1 second
- **Data update latency:** <500ms from DB to UI
- **Chart render:** <100ms on update
- **Mobile load:** <2 seconds
- **Dashboard responsiveness:** 60 FPS on update

---

## BUILD PHASES (Tonight)

### Phase 1: Foundation (Now)
- [ ] Setup React + Tailwind + Recharts
- [ ] Create main layout (header, footer, grid)
- [ ] Style NorthStar branding (colors, fonts, logo)

### Phase 2: Core Metrics (2 hours)
- [ ] Build hero section (Revenue, Expenses, Net P&L cards)
- [ ] Animated counters (number ticks on update)
- [ ] Color coding (green/red by sign)

### Phase 3: Charts (2 hours)
- [ ] Waterfall chart (revenue - expenses = net)
- [ ] Daily P&L trend (last 30 days)
- [ ] Cost breakdown pie chart
- [ ] Agent attribution stacked bar

### Phase 4: Real-Time (1 hour)
- [ ] WebSocket endpoint (Flask)
- [ ] Data subscription (React)
- [ ] Live counter animation
- [ ] Error handling + reconnection

### Phase 5: Polish (1 hour)
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Accessibility (colorblind mode, ARIA labels)
- [ ] Performance optimization (memoization, lazy loading)
- [ ] Deploy to Railway

---

## DATA SOURCES TO INTEGRATE

### Source 1: Kalshi (Scalper)
```sql
SELECT 
  balance,
  SUM(pnl) as daily_pnl,
  COUNT(*) as positions
FROM kalshi_snapshots
WHERE date = TODAY()
```

### Source 2: API Costs (LLM Router)
```sql
SELECT 
  provider,
  SUM(cost_estimate) as total_cost,
  COUNT(*) as calls
FROM api_usage
WHERE date >= DATE('now', '-30 days')
GROUP BY provider, DATE(timestamp)
```

### Source 3: John's Revenue
```sql
SELECT 
  SUM(CASE WHEN status='invoiced' THEN amount ELSE 0 END) as invoiced,
  SUM(CASE WHEN status='collected' THEN amount ELSE 0 END) as collected,
  SUM(CASE WHEN status='pending' THEN amount ELSE 0 END) as pending
FROM john_jobs
```

---

## SUCCESS CRITERIA

✅ When Craig opens the dashboard:
1. **Metrics load in <1 second** (hero section visible)
2. **Numbers are correct** (match local calculations)
3. **Charts tell a story** (can see profit/loss trends)
4. **Mobile works** (readable on phone)
5. **Updates live** (new data appears without refresh)
6. **No errors** (console clean, all APIs working)

❌ Failure = any of the above not met by end of night.

---

## RESEARCH AGENTS SPAWNED (PARALLEL)

- [x] PNL Dashboard Patterns (Bloomberg, Stripe, enterprise)
- [x] Web Development Stack (React, real-time, styling)
- [x] Charting Libraries (Recharts, D3, alternatives)
- [x] Data Pipeline Architecture (WebSocket, SSE, streaming)
- [x] Enterprise Design (visual hierarchy, mobile, accessibility)

**Results will auto-announce when complete.**

---

## NEXT IMMEDIATE ACTION

1. Wait for research results (5-10 min)
2. Spawn build agents for frontend components
3. Spawn build agent for real-time backend
4. Integrate with existing Flask app
5. Test live on localhost
6. Deploy to Railway
7. Verify with Craig

**Status: IN PROGRESS** 🚀
