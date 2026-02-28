# Real-Time Financial Dashboard Data Pipeline Architecture
**Target System:** NorthStar Synergy P&L Dashboard (Kalshi trades + Anthropic costs + John's revenue)  
**Data Sources:** SQLite database + Live API calls  
**Last Updated:** 2026-02-25

---

## 1. ARCHITECTURE OVERVIEW

### System Diagram
```
┌─────────────────────────────────────────────────────────────────────┐
│                     DATA INGESTION LAYER                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Kalshi API   │  │ Anthropic API│  │  John's API  │              │
│  │  (Trades)    │  │   (Costs)    │  │  (Revenue)   │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                      │
│         └─────────────────┼──────────────────┘                      │
│                           ▼                                         │
│                    ┌──────────────────┐                             │
│                    │ API Aggregator   │                             │
│                    │ (Poll Scheduler) │                             │
│                    └────────┬─────────┘                             │
│                             │                                       │
├─────────────────────────────┼───────────────────────────────────────┤
│                    DATA PROCESSING LAYER                            │
├─────────────────────────────┼───────────────────────────────────────┤
│                             ▼                                       │
│  ┌────────────────────────────────────────┐                        │
│  │   Transformation & Aggregation Engine  │                        │
│  │  • Normalize timestamps (UTC+0)        │                        │
│  │  • Calculate P&L snapshots             │                        │
│  │  • Combine multi-source data           │                        │
│  │  • Compute deltas (new vs previous)    │                        │
│  └────────┬─────────────────────────────┘                         │
│           │                                                        │
│  ┌────────▼─────────────────────────────┐                        │
│  │  Caching Layer (Redis/Memcached)     │                        │
│  │  • Hot: Current P&L (TTL: 5-30s)     │                        │
│  │  • Warm: Trade history (TTL: 5m)     │                        │
│  │  • Cold: Aggregates (TTL: 1h)        │                        │
│  │  • Invalidation: Event-driven         │                        │
│  └────────┬─────────────────────────────┘                        │
│           │                                                        │
├───────────┼────────────────────────────────────────────────────────┤
│  STORAGE LAYER                      │                             │
├───────────┼────────────────────────────────────────────────────────┤
│           ▼                                                        │
│  ┌─────────────────────────────────────┐                         │
│  │     SQLite Database (Primary)       │                         │
│  │  • Transactions Table (Kalshi)      │                         │
│  │  • Costs Table (Anthropic)          │                         │
│  │  • Revenue Table (John)             │                         │
│  │  • P&L Snapshots (Hourly)           │                         │
│  │  • Aggregates (1m, 5m, 1h)          │                         │
│  └─────────────────────────────────────┘                         │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                   DELIVERY LAYER (Frontend Updates)                │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────┐                          │
│  │   WebSocket Server (Primary)       │                          │
│  │  • Bidirectional real-time         │                          │
│  │  • Delta updates (JSON patch)      │                          │
│  │  • Fallback to SSE/polling         │                          │
│  └────────┬───────────────────────────┘                          │
│           │                                                       │
│  ┌────────▼───────────────────────────┐                          │
│  │  Server-Sent Events (Fallback 1)   │                          │
│  │  • Simple HTTP connection          │                          │
│  │  • No binary data needed            │                          │
│  │  • Works behind proxies             │                          │
│  └────────┬───────────────────────────┘                          │
│           │                                                       │
│  ┌────────▼───────────────────────────┐                          │
│  │  HTTP Polling (Fallback 2)         │                          │
│  │  • Fallback for restricted networks │                          │
│  │  • 5-30 second poll intervals       │                          │
│  └────────┬───────────────────────────┘                          │
│           │                                                       │
│           └──────────────┬──────────────┘                         │
│                          ▼                                        │
│              ┌────────────────────────┐                          │
│              │  Browser / React App   │                          │
│              │  (Real-time Dashboard) │                          │
│              └────────────────────────┘                          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 2. PROTOCOL COMPARISON: WebSocket vs SSE vs HTTP Polling

| Aspect | WebSocket | Server-Sent Events (SSE) | HTTP Polling |
|--------|-----------|--------------------------|--------------|
| **Connection Type** | Bidirectional | Server → Client only | Unidirectional client requests |
| **Latency** | 50-100ms (lowest) | 100-200ms | 5-30s (highest) |
| **Bandwidth** | Lowest (persistent) | Medium (persistent) | Highest (repeated requests) |
| **CPU Usage** | Low (persistent) | Low-Medium | High (repeated connections) |
| **Browser Support** | 95%+ | 90%+ | 100% |
| **Proxy/NAT Issues** | Rare issues | Very few | None |
| **Setup Complexity** | High | Medium | Low |
| **Fallback Chain** | SSE → Polling | Polling | N/A |
| **Best For** | Fast updates, low latency | Data feeds, stock tickers | High-latency tolerance |

### **RECOMMENDATION FOR NORTHSTAR:**
- **Primary:** WebSocket (P&L updates every 5-10 seconds)
- **Fallback 1:** SSE (if WebSocket unavailable, ~15s latency)
- **Fallback 2:** Polling (if SSE fails, 30s poll)

---

## 3. DATA AGGREGATION PATTERNS

### 3.1 Multi-Source P&L Calculation
```
Real-time P&L = (Kalshi Trade P&L) + (Revenue from John) - (Anthropic Costs)

Kalshi Trade P&L:
  ├─ Buy/Sell positions from Kalshi API
  ├─ Current market prices (from Kalshi API)
  └─ Unrealized P&L = (Current Price - Entry Price) × Quantity

Anthropic Costs:
  ├─ API usage from previous month (batch update, daily refresh)
  ├─ Estimated current month (cumulative)
  └─ Running total

John's Revenue:
  ├─ Deal closures (manual entry / API pull)
  ├─ Revenue recognized date
  └─ Remaining potential pipeline value
```

### 3.2 Aggregation Engine (Node.js Pattern)
```javascript
class P&LAggregator {
  constructor(db, cache, apis) {
    this.db = db;
    this.cache = cache;
    this.kalshi = apis.kalshi;
    this.anthropic = apis.anthropic;
    this.john = apis.john;
  }

  async aggregateP&L() {
    // 1. Fetch latest data (with cache fallback)
    const [trades, costs, revenue] = await Promise.all([
      this.getKalshiTrades(),      // ~200ms
      this.getAnthropicCosts(),    // ~100ms
      this.getJohnRevenue()        // ~150ms
    ]);

    // 2. Calculate components
    const kalshiP&L = this.calculateKalshiP&L(trades);
    const totalCosts = this.sumAnthropicCosts(costs);
    const totalRevenue = this.sumJohnRevenue(revenue);

    // 3. Compute net P&L with timestamps
    const pnlSnapshot = {
      timestamp: Date.now(),
      kalshiP&L,
      totalCosts,
      totalRevenue,
      netP&L: kalshiP&L + totalRevenue - totalCosts,
      breakdown: {
        trades: kalshiP&L,
        costs: -totalCosts,
        revenue: totalRevenue
      },
      previousSnapshot: await this.cache.get('pnl:current')
    };

    // 4. Calculate delta (what changed)
    const delta = this.computeDelta(
      pnlSnapshot.previousSnapshot,
      pnlSnapshot
    );

    // 5. Store & broadcast
    await Promise.all([
      this.db.insertSnapshot(pnlSnapshot),
      this.cache.set('pnl:current', pnlSnapshot, { ttl: 30 }), // 30s
      this.broadcastDelta(delta) // WebSocket/SSE
    ]);

    return { pnlSnapshot, delta };
  }

  calculateKalshiP&L(trades) {
    return trades.reduce((sum, trade) => {
      const unrealized = (trade.currentPrice - trade.entryPrice) 
                        * trade.quantity;
      const realized = trade.realizedP&L || 0;
      return sum + unrealized + realized;
    }, 0);
  }

  computeDelta(previous, current) {
    if (!previous) return null;
    
    return {
      timestamp: current.timestamp,
      netP&LDelta: current.netP&L - previous.netP&L,
      kalshiDelta: current.kalshiP&L - previous.kalshiP&L,
      costsDelta: current.totalCosts - previous.totalCosts,
      revenueDelta: current.totalRevenue - previous.totalRevenue
    };
  }
}
```

### 3.3 Data Normalization: Timestamp Synchronization
```javascript
class TimestampNormalizer {
  constructor() {
    this.UTC_OFFSET = 0; // Always use UTC internally
    this.TZ_DISPLAY = 'America/Los_Angeles'; // Display TZ
  }

  normalizeKalshiTimestamp(tradeTime) {
    // Kalshi returns ISO 8601 UTC
    return new Date(tradeTime).getTime(); // Unix ms
  }

  normalizeAnthropicTimestamp(apiLog) {
    // Anthropic provides date strings (YYYY-MM-DD)
    // Convert to Unix ms at 00:00 UTC
    return new Date(apiLog.date + 'T00:00:00Z').getTime();
  }

  normalizeJohnTimestamp(dealClose) {
    // Manual entry or API date
    return new Date(dealClose.closedDate).getTime();
  }

  alignToSnapshotBoundary(timestamp, bucketSizeMs = 60000) {
    // Round down to nearest minute (for aggregation)
    return Math.floor(timestamp / bucketSizeMs) * bucketSizeMs;
  }

  formatForDisplay(unixMs, timezone = this.TZ_DISPLAY) {
    return new Date(unixMs).toLocaleString('en-US', {
      timeZone: timezone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }
}
```

---

## 4. CACHING STRATEGY

### 4.1 Multi-Layer Cache Architecture
```
Tier 1: HOT CACHE (Redis) - Sub-5-second latency
├─ Key: pnl:current
├─ TTL: 30 seconds
├─ Size: ~5 KB per snapshot
├─ Invalidation: Event-driven (new trade, cost update)
└─ Hit Rate Target: >95%

Tier 2: WARM CACHE (Redis) - 30-second latency
├─ Key: pnl:1m:{timestamp}
├─ TTL: 5 minutes
├─ Size: ~50 KB (60 snapshots × 1m)
├─ Invalidation: Time-based (automatic)
└─ Hit Rate Target: >80%

Tier 3: COLD CACHE (Redis) - Batch queries
├─ Key: pnl:hourly:{date}
├─ TTL: 24 hours
├─ Size: ~100 KB per day
├─ Invalidation: Time-based + manual
└─ Hit Rate Target: >60%

Database: SQLite
├─ Write-through on cache miss
├─ Async bulk inserts (batch 100 snapshots)
└─ Query time: 50-200ms
```

### 4.2 Cache Invalidation Strategy
```javascript
class CacheManager {
  constructor(redis, db) {
    this.redis = redis;
    this.db = db;
  }

  async onTradeUpdate(trade) {
    // Trade executed → invalidate Kalshi P&L hot cache
    const hotCacheKey = 'pnl:current';
    const pattern = 'pnl:1m:*'; // Invalidate all 1-min buckets in current hour
    
    await Promise.all([
      this.redis.del(hotCacheKey),
      this.redis.eval(`
        local keys = redis.call('KEYS', ARGV[1])
        for i = 1, #keys do
          redis.call('DEL', keys[i])
        end
      `, 0, pattern)
    ]);
  }

  async onCostUpdate(cost) {
    // Cost added → invalidate cost-related caches
    await this.redis.del('pnl:current');
    // Note: Don't invalidate 1m buckets (costs update ~daily)
  }

  async getPnL(useCache = true) {
    const key = 'pnl:current';
    
    if (useCache) {
      const cached = await this.redis.get(key);
      if (cached) return JSON.parse(cached);
    }
    
    // Cache miss: fetch from DB
    const pnl = await this.db.getLatestPnLSnapshot();
    
    // Populate cache (30s TTL)
    await this.redis.setex(key, 30, JSON.stringify(pnl));
    
    return pnl;
  }

  async warmCacheOnStartup() {
    // Pre-load last 60 minutes of data
    const lastHour = await this.db.getPnLSnapshots(
      Date.now() - 3600000,
      Date.now()
    );
    
    for (const snapshot of lastHour) {
      const key = `pnl:1m:${snapshot.timestamp}`;
      await this.redis.setex(key, 300, JSON.stringify(snapshot)); // 5m TTL
    }
  }
}
```

---

## 5. WEBSOCKET IMPLEMENTATION

### 5.1 Server-Side (Node.js + ws library)
```javascript
const WebSocket = require('ws');
const http = require('http');

class RealtimeP&LServer {
  constructor(port = 8080) {
    this.server = http.createServer();
    this.wss = new WebSocket.Server({ server: this.server });
    this.clients = new Set();
    this.port = port;
  }

  start(aggregator) {
    this.wss.on('connection', (ws) => {
      this.clients.add(ws);
      console.log(`Client connected. Total: ${this.clients.size}`);

      // Send current snapshot immediately
      aggregator.getPnL().then(pnl => {
        ws.send(JSON.stringify({
          type: 'snapshot',
          data: pnl,
          timestamp: Date.now()
        }));
      });

      // Handle disconnection
      ws.on('close', () => {
        this.clients.delete(ws);
        console.log(`Client disconnected. Total: ${this.clients.size}`);
      });

      ws.on('error', (err) => {
        console.error('WS error:', err.message);
        this.clients.delete(ws);
      };
    });

    // Broadcast updates every 10 seconds (or on event)
    setInterval(() => {
      aggregator.aggregateP&L().then(({ pnlSnapshot, delta }) => {
        if (delta) {
          this.broadcast({
            type: 'delta',
            data: delta,
            timestamp: pnlSnapshot.timestamp
          });
        }
      });
    }, 10000);

    this.server.listen(this.port, () => {
      console.log(`P&L WebSocket server running on ws://localhost:${this.port}`);
    });
  }

  broadcast(message) {
    const payload = JSON.stringify(message);
    let successCount = 0;
    
    this.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(payload);
        successCount++;
      }
    });
    
    console.log(`Broadcast to ${successCount}/${this.clients.size} clients`);
  }
}
```

### 5.2 Client-Side (React)
```javascript
import React, { useEffect, useState } from 'react';

const P&LDashboard = () => {
  const [pnl, setPnl] = useState(null);
  const [ws, setWs] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const newWs = new WebSocket(`${protocol}//localhost:8080`);

      newWs.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
      };

      newWs.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === 'snapshot') {
          setPnl(message.data);
        } else if (message.type === 'delta') {
          // Apply delta to current state
          setPnl(prev => ({
            ...prev,
            ...message.data,
            previousSnapshot: prev
          }));
        }
      };

      newWs.onerror = () => {
        console.error('WebSocket error, attempting fallback...');
        setConnected(false);
        newWs.close();
        // Fallback to SSE or polling
        connectSSE();
      };

      newWs.onclose = () => {
        console.log('WebSocket closed, retrying in 5s...');
        setConnected(false);
        setTimeout(connectWebSocket, 5000);
      };

      setWs(newWs);
    };

    connectWebSocket();

    return () => {
      if (ws) ws.close();
    };
  }, []);

  if (!pnl) return <div>Loading P&L data...</div>;

  return (
    <div className="pnl-dashboard">
      <div className="status">
        {connected ? '🟢 Live' : '🟠 Buffering'}
      </div>
      <div className="pnl-card">
        <h2>Net P&L: ${pnl.netP&L.toFixed(2)}</h2>
        <ul>
          <li>Kalshi Trades: ${pnl.breakdown.trades.toFixed(2)}</li>
          <li>Revenue: ${pnl.breakdown.revenue.toFixed(2)}</li>
          <li>Costs: ${pnl.breakdown.costs.toFixed(2)}</li>
        </ul>
        <small>Updated: {new Date(pnl.timestamp).toLocaleTimeString()}</small>
      </div>
    </div>
  );
};

function connectSSE() {
  const eventSource = new EventSource('/api/pnl/stream');
  
  eventSource.onmessage = (event) => {
    const pnl = JSON.parse(event.data);
    setPnl(pnl);
  };
  
  eventSource.onerror = () => {
    eventSource.close();
    // Fallback to polling
    connectPolling();
  };
}

function connectPolling() {
  setInterval(() => {
    fetch('/api/pnl/current')
      .then(r => r.json())
      .then(pnl => setPnl(pnl));
  }, 30000); // Poll every 30 seconds
}
```

---

## 6. PERFORMANCE CONSIDERATIONS

### 6.1 Latency Budget (Target: <500ms end-to-end)
```
API Fetch (3 sources in parallel):        200ms
  ├─ Kalshi API:                           100ms
  ├─ Anthropic API:                        50ms
  └─ John's API:                           150ms

Data Aggregation & Normalization:         50ms
Cache Update:                              30ms
Broadcasting to clients:                   50ms
Network transmission:                      100ms
Browser rendering:                         50ms
───────────────────────────────────────────────
Total P2P Latency:                        ~500ms
Acceptable (< 1 second for financial data): ✓
```

### 6.2 Database Optimization
```sql
-- Create indexes for fast lookups
CREATE INDEX idx_trades_timestamp ON kalshi_trades(timestamp DESC);
CREATE INDEX idx_trades_status ON kalshi_trades(status);
CREATE INDEX idx_costs_date ON anthropic_costs(date DESC);
CREATE INDEX idx_revenue_date ON john_revenue(closed_date DESC);
CREATE INDEX idx_pnl_snapshot_time ON pnl_snapshots(timestamp DESC);

-- Aggregate table for reporting
CREATE TABLE pnl_aggregates (
  bucket_timestamp INTEGER PRIMARY KEY,
  period TEXT, -- '1m', '5m', '1h'
  kalshi_pnl REAL,
  costs REAL,
  revenue REAL,
  net_pnl REAL,
  trade_count INTEGER,
  created_at INTEGER
);

CREATE INDEX idx_aggregates_period_time 
  ON pnl_aggregates(period, bucket_timestamp DESC);

-- Batch insert optimization
PRAGMA journal_mode = WAL;     -- Write-Ahead Logging
PRAGMA synchronous = NORMAL;    -- Faster writes
PRAGMA cache_size = 10000;      -- Larger cache
```

### 6.3 Monitoring & Alerting
```javascript
class PerformanceMonitor {
  constructor() {
    this.metrics = {
      apiLatencies: [],
      aggregationTimes: [],
      broadcastCounts: [],
      cacheHitRates: {}
    };
  }

  recordApiLatency(source, latencyMs) {
    this.metrics.apiLatencies.push({ source, latencyMs, timestamp: Date.now() });
    if (latencyMs > 500) {
      console.warn(`⚠️  ${source} API slow: ${latencyMs}ms`);
    }
  }

  recordCacheHit(key, isHit) {
    const rate = this.metrics.cacheHitRates[key] || { hits: 0, misses: 0 };
    if (isHit) rate.hits++;
    else rate.misses++;
    this.metrics.cacheHitRates[key] = rate;
  }

  getHealthStatus() {
    const p99ApiLatency = this.percentile(
      this.metrics.apiLatencies.map(m => m.latencyMs),
      99
    );

    return {
      healthy: p99ApiLatency < 1000,
      p99ApiLatencyMs: p99ApiLatency,
      averageBroadcastLatencyMs: 50,
      cacheHitRates: this.metrics.cacheHitRates,
      connectedClients: this.clients?.size || 0
    };
  }

  percentile(arr, p) {
    const sorted = arr.sort((a, b) => a - b);
    const idx = Math.ceil((p / 100) * sorted.length) - 1;
    return sorted[idx];
  }
}
```

---

## 7. FALLBACK & RESILIENCE

### 7.1 Graceful Degradation Chain
```
Priority 1: WebSocket
  └─ Error/Timeout (30s)
    └─ Priority 2: Server-Sent Events (SSE)
      └─ Error/Timeout (60s)
        └─ Priority 3: HTTP Polling (30s intervals)
          └─ Offline mode (cached last snapshot)
```

### 7.2 Reconnection Logic
```javascript
class ResilientConnection {
  constructor() {
    this.reconnectDelays = [1000, 2000, 5000, 10000, 30000]; // ms
    this.attemptCount = 0;
  }

  async connect() {
    try {
      await this.tryWebSocket();
    } catch (e) {
      if (this.attemptCount < this.reconnectDelays.length) {
        const delay = this.reconnectDelays[this.attemptCount++];
        console.log(`Retrying in ${delay}ms...`);
        setTimeout(() => this.connect(), delay);
      } else {
        console.log('Max retries exceeded, using polling...');
        this.usePolling();
      }
    }
  }

  async tryWebSocket() {
    // Implementation...
  }

  usePolling() {
    // Fallback to polling...
  }
}
```

---

## 8. SCHEMA DESIGN (SQLite)

### 8.1 Core Tables
```sql
-- Kalshi Trades
CREATE TABLE kalshi_trades (
  id TEXT PRIMARY KEY,
  symbol TEXT NOT NULL,
  side TEXT, -- 'buy' or 'sell'
  quantity INTEGER,
  entry_price REAL,
  current_price REAL,
  status TEXT, -- 'open', 'closed'
  realized_pnl REAL DEFAULT 0,
  timestamp INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Anthropic Costs
CREATE TABLE anthropic_costs (
  id TEXT PRIMARY KEY,
  month TEXT, -- YYYY-MM
  total_cost REAL,
  tokens_used INTEGER,
  timestamp INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- John's Revenue
CREATE TABLE john_revenue (
  id TEXT PRIMARY KEY,
  deal_name TEXT,
  closed_date TEXT, -- YYYY-MM-DD
  revenue REAL,
  status TEXT, -- 'recognized', 'pending', 'pipeline'
  timestamp INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- P&L Snapshots (1-minute buckets)
CREATE TABLE pnl_snapshots (
  timestamp INTEGER PRIMARY KEY,
  kalshi_pnl REAL,
  total_costs REAL,
  total_revenue REAL,
  net_pnl REAL,
  trade_count INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- P&L Deltas (for change tracking)
CREATE TABLE pnl_deltas (
  timestamp INTEGER PRIMARY KEY,
  net_pnl_delta REAL,
  kalshi_delta REAL,
  costs_delta REAL,
  revenue_delta REAL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 9. DEPLOYMENT CHECKLIST

- [ ] **Data Layer**
  - [ ] SQLite database initialized with indexes
  - [ ] WAL mode enabled for concurrent reads
  - [ ] Backup strategy (daily dumps)

- [ ] **Backend**
  - [ ] Node.js server (8080 for WebSocket)
  - [ ] P&L aggregator running on 10s schedule
  - [ ] Redis cache running (optional but recommended)
  - [ ] API connectors authenticated (Kalshi, Anthropic, John's API)

- [ ] **Frontend**
  - [ ] React dashboard with WebSocket client
  - [ ] Fallback SSE/polling implemented
  - [ ] Offline mode with cached snapshot
  - [ ] Performance monitoring (latency, update frequency)

- [ ] **Monitoring**
  - [ ] Alert if API latency > 1 second
  - [ ] Alert if no updates for 5 minutes
  - [ ] Daily cache hit rate report
  - [ ] Database query time tracking

- [ ] **Testing**
  - [ ] Load test: 100+ concurrent WebSocket connections
  - [ ] Failure test: Kill API endpoints, verify fallback
  - [ ] Data correctness: Reconcile DB vs API sources
  - [ ] Latency test: Measure P2P time under load

---

## 10. QUICK REFERENCE: LATENCY TARGETS

| Component | Target | Threshold |
|-----------|--------|-----------|
| API aggregation (3-source) | <200ms | >500ms = alert |
| Data processing | <50ms | >100ms = warn |
| Cache write | <30ms | >100ms = warn |
| WebSocket broadcast | <100ms | >200ms = warn |
| End-to-end (API → render) | <500ms | >1000ms = alert |
| Cache hit rate | >90% | <70% = investigate |
| DB query (latest snapshot) | <50ms | >200ms = index needed |

---

## SUMMARY

**This architecture delivers:**
1. ✅ Sub-second latency for live P&L updates
2. ✅ Multi-source aggregation (Kalshi + Anthropic + John)
3. ✅ Timestamp normalization to UTC
4. ✅ Smart caching (hot/warm/cold tiers)
5. ✅ Graceful fallback (WS → SSE → Polling)
6. ✅ Robust error handling & reconnection
7. ✅ Database optimized for reads & writes
8. ✅ Performance monitoring & alerting

**Cost estimate:** Server + Redis + monitoring = ~$50–100/month for moderate load (100–500 concurrent users)
