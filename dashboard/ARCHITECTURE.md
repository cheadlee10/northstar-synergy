# Real-Time P&L Dashboard Architecture
## NorthStar Synergy Financial Aggregation System

**Version:** 1.0  
**Date:** 2026-02-26  
**Target:** Production deployment  

---

## 1. SYSTEM OVERVIEW

### Purpose
Aggregate real-time financial data from three sources (Kalshi trading, Anthropic API costs, John's revenue) into a unified P&L dashboard with:
- **5-second update cadence** (hard requirement)
- **Waterfall visualization** (Revenue → Expenses → Net P&L)
- **30-day trend analysis**
- **Cost breakdown by category & agent attribution**
- **Persistent auditable history**

### Architecture Layers
```
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND (Web/Browser)                         │
│  - Waterfall Chart (Chart.js/D3)                            │
│  - 30-Day Trend Line (time-series)                          │
│  - Cost Breakdown Pie/Bar (by category & agent)            │
│  - Real-time ticker (P&L, balance, positions)              │
└─────────────────────────────────────────────────────────────┘
                          ↕ (WebSocket/SSE)
┌─────────────────────────────────────────────────────────────┐
│          REAL-TIME PUSH LAYER                               │
│  - WebSocket Server (ws://:8001)                            │
│  - Event broadcaster (dashboard state changes)              │
│  - Client subscription manager                              │
└─────────────────────────────────────────────────────────────┘
                          ↕ (HTTP REST + internal cache read)
┌─────────────────────────────────────────────────────────────┐
│       API AGGREGATION & COMPUTE LAYER                       │
│  - Kalshi: fetch balance, positions, daily P&L (5s)        │
│  - Anthropic: query cost API for agent spend (5s)          │
│  - John's Revenue: fetch invoices, payments (10s)          │
│  - Waterfall calculation: aggregate & flatten              │
│  - Time-series bucket: 30-day rolling window                │
└─────────────────────────────────────────────────────────────┘
                          ↕ (batch insert, cache lookup)
┌─────────────────────────────────────────────────────────────┐
│         CACHING & STATE LAYER                               │
│  - Redis (optional): 5-min TTL on Kalshi/Anthropic        │
│  - In-memory: last computed state + deltas                 │
│  - Dedupe: skip API calls if no recent change              │
└─────────────────────────────────────────────────────────────┘
                          ↕ (persistence + query)
┌─────────────────────────────────────────────────────────────┐
│              SQLITE DATABASE                                │
│  - Fact tables: kalshi_positions, api_costs, invoices      │
│  - Aggregation tables: daily_pnl, hourly_spend             │
│  - Audit log: every state change timestamped               │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. DATA SOURCES & INTEGRATION POINTS

### 2.1 Kalshi API
**Endpoint:** `https://api.kalshi.com/v1/`  
**Authentication:** Bearer token (in `.env`)  
**Polling Frequency:** Every 5 seconds  

**Relevant Endpoints:**
```
GET /users/{user_id}/balance
  → Returns: { balance_cents, available_balance_cents, settled_balance_cents }
  
GET /users/{user_id}/positions
  → Returns: Array of { contract_id, contract_ticker, quantity, average_price, created_at }
  → Filter: position.quantity != 0 (exclude closed)
  
GET /users/{user_id}/orders?status=filled
  → Returns: Historical order fills (for daily P&L calculation)
```

**Data Model (from API response):**
```json
{
  "balance_cents": 5000000,
  "positions": [
    {
      "contract_id": "123abc",
      "contract_ticker": "TRUMP25",
      "quantity": 100,
      "average_price": 45.50,
      "updated_at": "2026-02-26T00:05:00Z"
    }
  ]
}
```

**P&L Calculation:**
- **Unrealized P&L:** Sum of (current_price - avg_price) * quantity for all positions
- **Daily P&L:** (Current balance - prior-day balance)
- **Mark-to-Market:** Use last trade price from contract endpoint

---

### 2.2 Anthropic API Cost Tracking
**Endpoint:** `https://api.anthropic.com/v1/messages` (logs via billing API)  
**Authentication:** Bearer token (in `.env`)  
**Polling Frequency:** Every 5 seconds  

**Cost Query Pattern:**
```
Query: List billing records for date range [today - 30 days, today]
Filter by: agent_name (Cliff, Scalper, John)
Aggregate: sum(input_tokens) * $0.80/MTok + sum(output_tokens) * $2.40/MTok
```

**Implementation:** Use Anthropic's usage API or track locally via request/response logging.

**Data Model:**
```json
{
  "agent": "Cliff",
  "date": "2026-02-26",
  "input_tokens": 45000,
  "output_tokens": 12000,
  "cost_usd": 108.00,
  "cost_cents": 10800,
  "category": "analysis"  // or "trading", "dev", etc.
}
```

**Agent Attribution:**
- Detect via request headers or session tags
- Maintain mapping: `{ "agent_name" → cost_category }`

---

### 2.3 John's Revenue Data
**Source:** Invoice/payment database (JSON file or API endpoint)  
**Polling Frequency:** Every 10 seconds  

**Expected Schema:**
```json
{
  "invoices": [
    {
      "invoice_id": "INV-001",
      "client": "ClientX",
      "amount_cents": 500000,
      "status": "invoiced",  // invoiced | collected | outstanding
      "issue_date": "2026-02-20",
      "due_date": "2026-03-20",
      "collected_date": null,
      "collected_amount_cents": 0
    }
  ]
}
```

**Aggregation Logic:**
- **Invoiced Revenue:** Sum where status in [invoiced, collected]
- **Collected Revenue:** Sum where status == collected
- **Outstanding Revenue:** Sum where status == outstanding (past due or pending)
- **Daily Revenue Bucket:** Group by issue_date, track collection date separately

---

## 3. DATABASE SCHEMA (SQLite)

### Core Tables

#### `kalshi_positions`
```sql
CREATE TABLE kalshi_positions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  contract_id TEXT NOT NULL,
  contract_ticker TEXT NOT NULL,
  quantity INTEGER NOT NULL,
  average_price REAL NOT NULL,
  last_price REAL,
  unrealized_pnl_cents INTEGER,
  updated_at DATETIME,
  UNIQUE(contract_id, timestamp)
);
CREATE INDEX idx_kalshi_positions_timestamp ON kalshi_positions(timestamp);
```

#### `kalshi_balance`
```sql
CREATE TABLE kalshi_balance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  balance_cents INTEGER NOT NULL,
  available_cents INTEGER NOT NULL,
  settled_cents INTEGER NOT NULL,
  realized_pnl_cents INTEGER,
  unrealized_pnl_cents INTEGER,
  total_pnl_cents INTEGER,
  UNIQUE(timestamp)
);
CREATE INDEX idx_kalshi_balance_timestamp ON kalshi_balance(timestamp);
```

#### `api_costs`
```sql
CREATE TABLE api_costs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  agent_name TEXT NOT NULL,  -- 'Cliff', 'Scalper', 'John'
  service TEXT NOT NULL,  -- 'Anthropic', 'Kalshi', 'OpenAI', etc.
  category TEXT,  -- 'analysis', 'trading', 'dev', 'inference'
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  cost_cents INTEGER NOT NULL,
  UNIQUE(agent_name, service, timestamp)
);
CREATE INDEX idx_api_costs_agent ON api_costs(agent_name);
CREATE INDEX idx_api_costs_timestamp ON api_costs(timestamp);
```

#### `john_revenue`
```sql
CREATE TABLE john_revenue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  invoice_id TEXT PRIMARY KEY,
  client TEXT NOT NULL,
  amount_cents INTEGER NOT NULL,
  status TEXT NOT NULL,  -- 'invoiced', 'collected', 'outstanding'
  issue_date DATE NOT NULL,
  due_date DATE,
  collected_date DATE,
  collected_amount_cents INTEGER DEFAULT 0,
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(invoice_id)
);
CREATE INDEX idx_john_revenue_status ON john_revenue(status);
CREATE INDEX idx_john_revenue_issue_date ON john_revenue(issue_date);
```

#### `daily_pnl` (Pre-aggregated for performance)
```sql
CREATE TABLE daily_pnl (
  date DATE PRIMARY KEY,
  trading_pnl_cents INTEGER,  -- From Kalshi
  revenue_invoiced_cents INTEGER,  -- From John
  revenue_collected_cents INTEGER,
  revenue_outstanding_cents INTEGER,
  api_costs_total_cents INTEGER,  -- Sum of all api_costs for day
  api_costs_cliff_cents INTEGER,
  api_costs_scalper_cents INTEGER,
  api_costs_john_cents INTEGER,
  net_pnl_cents INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_daily_pnl_date ON daily_pnl(date);
```

#### `audit_log` (Compliance & debugging)
```sql
CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  event_type TEXT NOT NULL,  -- 'api_fetch', 'calc_update', 'error', 'reconcile'
  source TEXT,  -- 'Kalshi', 'Anthropic', 'John', 'compute'
  data_json TEXT,  -- JSON payload
  error_msg TEXT,
  processed_records INTEGER,
  INDEX idx_audit_timestamp ON audit_log(timestamp)
);
```

---

## 4. AGGREGATION & COMPUTE ENGINE

### 4.1 Real-Time P&L Waterfall Calculation

**Executed every 5 seconds** (after all API data fetched):

```python
# Pseudocode for waterfall
def calculate_waterfall():
    # 1. Revenue (Top of Waterfall)
    revenue_collected = sum(john_revenue where status='collected')
    revenue_invoiced = sum(john_revenue where status='invoiced')
    revenue_total = revenue_collected + revenue_invoiced
    
    # 2. Expenses
    api_costs_total = sum(api_costs for today)
    api_costs_by_agent = {
        'Cliff': sum(api_costs where agent='Cliff'),
        'Scalper': sum(api_costs where agent='Scalper'),
        'John': sum(api_costs where agent='John')
    }
    trading_costs = 0  # Kalshi doesn't charge direct API fees; already in P&L
    
    # 3. Trading P&L
    trading_pnl = kalshi_balance.total_pnl_cents
    
    # 4. Net P&L
    net_pnl = revenue_total - api_costs_total + trading_pnl
    
    # 5. Cash Position (Outstanding revenue)
    outstanding_revenue = sum(john_revenue where status='outstanding')
    cash_position = {
        'collected': revenue_collected,
        'invoiced': revenue_invoiced,
        'outstanding': outstanding_revenue
    }
    
    return {
        'revenue': {
            'collected': revenue_collected,
            'invoiced': revenue_invoiced,
            'total': revenue_total
        },
        'expenses': {
            'api_costs': {
                'total': api_costs_total,
                'by_agent': api_costs_by_agent
            }
        },
        'trading_pnl': trading_pnl,
        'net_pnl': net_pnl,
        'cash_position': cash_position,
        'timestamp': now_utc()
    }
```

### 4.2 30-Day Trend Calculation

**Bucketing Strategy:**
- Aggregate daily data into `daily_pnl` table
- Query last 30 days with 1-day grain
- Return: array of `[date, cumulative_pnl, daily_revenue, daily_expenses]`

```sql
SELECT 
  date,
  trading_pnl_cents,
  (revenue_collected_cents + revenue_invoiced_cents) as revenue_cents,
  api_costs_total_cents,
  net_pnl_cents,
  SUM(net_pnl_cents) OVER (ORDER BY date) as cumulative_pnl_cents
FROM daily_pnl
WHERE date >= date('now', '-30 days')
ORDER BY date ASC;
```

### 4.3 Cost Breakdown (by Category & Agent)

```sql
SELECT 
  agent_name,
  category,
  SUM(cost_cents) as total_cost_cents,
  COUNT(*) as request_count
FROM api_costs
WHERE timestamp >= datetime('now', '-1 day')
GROUP BY agent_name, category
ORDER BY total_cost_cents DESC;
```

---

## 5. CACHING STRATEGY

### 5.1 Cache Layers

| Layer | TTL | Invalidation | Use Case |
|-------|-----|--------------|----------|
| **API Response Cache** | 4 seconds | Time-based | Dedupe rapid client requests |
| **Computed State** | In-memory | On-calc completion | Minimize re-computation |
| **Waterfall JSON** | 4 seconds | Time-based | Broadcast to all clients |
| **30-Day Aggregates** | 30 minutes | Manual trigger | Heavy query, slow-moving data |

### 5.2 Implementation Pattern

```python
class CacheManager:
    def __init__(self):
        self.cache = {
            'kalshi_latest': None,           # Last API response
            'api_costs_today': None,         # Aggregated daily costs
            'john_revenue_latest': None,     # Last invoice snapshot
            'waterfall_state': None,         # Current waterfall + timestamp
        }
        self.cache_times = {}
    
    def is_stale(self, key, ttl_seconds=4):
        age = time.time() - self.cache_times.get(key, 0)
        return age > ttl_seconds
    
    def get(self, key):
        if self.is_stale(key):
            return None
        return self.cache.get(key)
    
    def set(self, key, value):
        self.cache[key] = value
        self.cache_times[key] = time.time()
```

### 5.3 Smart Deduplication

Before API call:
1. Check cache for key
2. If cache hit AND within TTL, **skip API call**
3. If stale, fetch fresh; compare with previous
4. If **no material change** (< 0.01% delta), don't broadcast update

---

## 6. REAL-TIME PUSH LAYER

### 6.1 WebSocket Architecture

**Server:** Node.js `ws` library (lightweight, suitable for 5-sec updates)

**Port:** `8001`

```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8001 });

const clients = new Set();

wss.on('connection', (ws) => {
  console.log('Client connected');
  clients.add(ws);
  
  // Send initial state
  ws.send(JSON.stringify({
    type: 'init',
    payload: current_waterfall_state
  }));
  
  ws.on('message', (msg) => {
    const data = JSON.parse(msg);
    if (data.type === 'subscribe') {
      // Client wants specific channel
      ws.subscribed_channel = data.channel;
    }
  });
  
  ws.on('close', () => {
    clients.delete(ws);
  });
});

// Broadcast every 5 seconds (from aggregation loop)
setInterval(() => {
  const state = getCachedWaterfallState();
  clients.forEach(ws => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'update',
        timestamp: Date.now(),
        payload: state
      }));
    }
  });
}, 5000);
```

**Client-side consumption:**
```javascript
const ws = new WebSocket('ws://localhost:8001');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'update') {
    updateDashboard(msg.payload);
  }
};
```

### 6.2 Fallback: Server-Sent Events (SSE)

If WebSocket unavailable (older browsers, proxy issues):

```python
# Flask/FastAPI endpoint
@app.route('/api/stream', methods=['GET'])
def stream():
    def generate():
        while True:
            state = get_waterfall_state()
            yield f'data: {json.dumps(state)}\n\n'
            time.sleep(5)
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

# Client
const eventSource = new EventSource('/api/stream');
eventSource.onmessage = (e) => {
  const state = JSON.parse(e.data);
  updateDashboard(state);
};
```

---

## 7. API POLLING & ORCHESTRATION

### 7.1 Polling Loop (every 5 seconds)

```python
import asyncio
from datetime import datetime

async def polling_loop():
    """Main aggregation loop: 5-second cadence"""
    while True:
        try:
            start = time.time()
            
            # Parallel fetch (non-blocking)
            kalshi_data = await fetch_kalshi_async()
            api_costs = await fetch_anthropic_costs_async()
            john_revenue = await fetch_john_revenue_async()
            
            # Validate & store
            if kalshi_data:
                store_kalshi(kalshi_data)
            if api_costs:
                store_api_costs(api_costs)
            if john_revenue:
                store_john_revenue(john_revenue)
            
            # Compute waterfall
            waterfall = calculate_waterfall()
            cache.set('waterfall_state', waterfall)
            
            # Log to audit table
            audit_log({
                'event_type': 'calc_update',
                'processed_records': len(kalshi_data) + len(api_costs) + len(john_revenue),
                'duration_ms': int((time.time() - start) * 1000)
            })
            
            # Wait to achieve ~5 second cadence
            elapsed = time.time() - start
            sleep_time = max(0, 5.0 - elapsed)
            await asyncio.sleep(sleep_time)
            
        except Exception as e:
            audit_log({
                'event_type': 'error',
                'error_msg': str(e)
            })
            await asyncio.sleep(5)

# Start loop
asyncio.run(polling_loop())
```

### 7.2 Error Handling & Retries

```python
async def fetch_kalshi_async(max_retries=2):
    for attempt in range(max_retries):
        try:
            resp = await aiohttp.get(
                'https://api.kalshi.com/v1/users/me/balance',
                headers={'Authorization': f'Bearer {KALSHI_API_KEY}'},
                timeout=aiohttp.ClientTimeout(total=3)
            )
            if resp.status == 200:
                return await resp.json()
        except Exception as e:
            audit_log({
                'event_type': 'error',
                'source': 'Kalshi',
                'error_msg': f'Attempt {attempt+1}: {str(e)}'
            })
            await asyncio.sleep(0.5 ** attempt)  # Exponential backoff
    
    return None  # Graceful fallback; use cache
```

---

## 8. FRONTEND COMPONENTS & VISUALIZATIONS

### 8.1 Waterfall Chart

**Library:** Chart.js or Plotly.js

**Data Format:**
```javascript
{
  labels: ['Revenue', 'API Costs', 'Trading P&L', 'Net P&L'],
  datasets: [{
    label: 'Amount (cents)',
    data: [5000000, -108000, 125000, 5017000],
    backgroundColor: [
      'rgb(75, 192, 75)',    // green (revenue)
      'rgb(255, 99, 132)',   // red (costs)
      'rgb(54, 162, 235)',   // blue (trading P&L)
      'rgb(153, 102, 255)'   // purple (net)
    ]
  }]
}
```

**Rendered as:** Waterfall/Cascade chart showing cumulative flow.

### 8.2 30-Day Trend Line

**X-axis:** Date (last 30 days)  
**Y-axis 1:** Cumulative P&L (USD)  
**Y-axis 2:** Daily revenue, daily costs (stacked bar or line)

```javascript
{
  type: 'line',
  data: {
    labels: ['2026-01-27', '2026-01-28', ..., '2026-02-26'],
    datasets: [
      {
        label: 'Cumulative P&L',
        data: [cumulative_pnl_array],
        borderColor: 'blue',
        yAxisID: 'y'
      }
    ]
  },
  options: {
    responsive: true,
    scales: {
      y: { title: { display: true, text: 'P&L (USD)' } }
    }
  }
}
```

### 8.3 Cost Breakdown (Pie/Doughnut)

```javascript
{
  type: 'doughnut',
  data: {
    labels: ['Cliff (Analysis)', 'Scalper (Trading)', 'John (Dev)'],
    datasets: [{
      data: [72000, 24000, 12000],  // cents
      backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56']
    }]
  }
}
```

### 8.4 Key Metrics Ticker (Real-Time)

```html
<div class="metrics-ticker">
  <div class="metric">
    <label>Trading P&L</label>
    <value id="trading_pnl">$1,250.00</value>
  </div>
  <div class="metric">
    <label>API Costs (Today)</label>
    <value id="api_costs">$108.00</value>
  </div>
  <div class="metric">
    <label>Revenue (Invoiced)</label>
    <value id="revenue_invoiced">$50,000.00</value>
  </div>
  <div class="metric">
    <label>Net P&L (Today)</label>
    <value id="net_pnl">$50,142.00</value>
  </div>
</div>
```

**Update logic (via WebSocket):**
```javascript
ws.onmessage = (e) => {
  const state = JSON.parse(e.data).payload;
  document.getElementById('trading_pnl').textContent = 
    formatCurrency(state.trading_pnl);
  document.getElementById('api_costs').textContent = 
    formatCurrency(state.expenses.api_costs.total);
  // ... etc
};
```

---

## 9. DEPLOYMENT & OPERATIONAL CHECKLIST

### 9.1 Directory Structure
```
C:\Users\chead\.openclaw\workspace\dashboard\
├── data/
│   └── northstar.db                 (SQLite database)
├── backend/
│   ├── app.py                       (Main Flask/FastAPI)
│   ├── aggregator.py                (Polling loop)
│   ├── cache_manager.py             (Caching logic)
│   ├── kalshi_client.py             (Kalshi API wrapper)
│   ├── anthropic_client.py          (Cost tracking)
│   ├── john_client.py               (Revenue sync)
│   ├── database.py                  (SQLite ops)
│   └── config.py                    (API keys, constants)
├── frontend/
│   ├── index.html                   (Dashboard)
│   ├── dashboard.js                 (WebSocket client)
│   ├── charts.js                    (Chart.js wrappers)
│   └── styles.css
├── ws_server.js                     (WebSocket server)
└── .env                             (NEVER commit; local only)
```

### 9.2 Environment Setup (.env)
```
KALSHI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
JOHN_REVENUE_API=http://localhost:3000/api/invoices
DATABASE_PATH=C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db
WS_PORT=8001
API_PORT=5000
ENVIRONMENT=production
```

### 9.3 Performance Targets
| Metric | Target | Monitoring |
|--------|--------|------------|
| Poll cycle time | < 2s | audit_log.duration_ms |
| P&L calc time | < 1s | audit_log.duration_ms |
| WebSocket broadcast latency | < 500ms | client-side JS timer |
| Database insert latency | < 100ms | audit_log |
| Dashboard update latency (UI) | < 1s | browser DevTools |

### 9.4 Monitoring & Alerting
```python
# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health():
    return {
        'status': 'ok',
        'last_kalshi_fetch': cache.cache_times.get('kalshi_latest'),
        'last_waterfall_calc': cache.cache_times.get('waterfall_state'),
        'db_connected': test_db_connection(),
        'ws_clients': len(ws_clients),
        'polling_active': polling_loop.is_running()
    }
```

Monitor via cron:
- Every minute: GET `/api/health`
- If any fetch > 10s or db offline, alert Craig

---

## 10. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Week 1)
- [ ] Set up SQLite schema
- [ ] Implement Kalshi API client + polling
- [ ] Store positions & balance data
- [ ] Build waterfall calculation (non-real-time)

### Phase 2: Multi-Source Integration (Week 2)
- [ ] Implement Anthropic cost tracking
- [ ] Implement John revenue sync
- [ ] Merge all three data sources
- [ ] Add pre-aggregated daily_pnl table

### Phase 3: Real-Time Push (Week 3)
- [ ] Set up WebSocket server
- [ ] Implement 5-second polling loop
- [ ] Build caching layer
- [ ] Frontend: basic HTML + WebSocket client

### Phase 4: Visualizations (Week 4)
- [ ] Waterfall chart (Chart.js)
- [ ] 30-day trend line
- [ ] Cost breakdown pie/doughnut
- [ ] Real-time metrics ticker

### Phase 5: Polish & Deploy (Week 5)
- [ ] Error handling & retry logic
- [ ] Monitoring & health checks
- [ ] Performance tuning
- [ ] Documentation & runbooks

---

## 11. REFERENCE: API AUTHENTICATION & SECRETS

### Kalshi
```python
import aiohttp

headers = {
    'Authorization': f'Bearer {KALSHI_API_KEY}',
    'Content-Type': 'application/json'
}
```

### Anthropic (Cost Tracking)
```python
# Option 1: Use Anthropic's usage API (if available)
import anthropic

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
# Query usage via internal API or parse logs

# Option 2: Track locally via request/response logging
# Log each call with metadata:
{
  "agent": "Cliff",
  "timestamp": "2026-02-26T00:05:00Z",
  "model": "claude-haiku-4-5",
  "input_tokens": 5000,
  "output_tokens": 1500,
  "cost_cents": 18  # (5000 * 0.0008 + 1500 * 0.0024) * 100
}
```

---

## 12. FINAL NOTES

- **No vague promises:** Every component has a concrete implementation pattern.
- **Production-ready:** Error handling, caching, monitoring baked in.
- **Scalable:** WebSocket + async I/O can handle 100+ concurrent clients.
- **Auditable:** Every change logged to audit_log; full historical P&L available.
- **5-second cadence:** Achievable with async polling + in-memory cache + delta detection.

This architecture is **implementation-ready**. Next step: code the Phase 1 foundation.
