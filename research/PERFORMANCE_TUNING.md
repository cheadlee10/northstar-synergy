# Real-Time P&L Dashboard — Performance Tuning Guide

## Target Latency: <500ms End-to-End

This guide optimizes the pipeline for maximum throughput and minimum latency.

---

## 1. DATABASE OPTIMIZATION

### 1.1 SQLite Configuration

```javascript
// In DatabaseLayer.js, optimize pragmas:
const pragmas = [
  'PRAGMA journal_mode = WAL;',           // Write-Ahead Logging (concurrent reads)
  'PRAGMA synchronous = NORMAL;',         // Faster writes, still safe
  'PRAGMA cache_size = 10000;',           // 10MB in-memory cache
  'PRAGMA temp_store = MEMORY;',          // Temporary tables in RAM
  'PRAGMA mmap_size = 30000000;',         // Memory-mapped I/O (30MB)
  'PRAGMA query_only = OFF;',             // Allow writes
  'PRAGMA busy_timeout = 5000;',          // Retry on lock for 5s
  'PRAGMA foreign_keys = OFF;'            // Skip FK checks if not needed
];

for (const pragma of pragmas) {
  db.run(pragma);
}
```

### 1.2 Index Strategy

```sql
-- PRIMARY: Timestamp-based lookups
CREATE INDEX idx_pnl_timestamp 
  ON pnl_snapshots(timestamp DESC);

-- Speed up historical queries
CREATE INDEX idx_pnl_bucket
  ON pnl_snapshots(
    CAST(timestamp / 60000 AS INTEGER) DESC  -- Minute bucket
  );

-- Trade lookups
CREATE INDEX idx_trades_status_time
  ON kalshi_trades(status, timestamp DESC);

-- Cost lookups
CREATE INDEX idx_costs_month
  ON anthropic_costs(month DESC);

-- Revenue lookups
CREATE INDEX idx_revenue_date
  ON john_revenue(closed_date DESC);

-- Analyze & optimize
ANALYZE;
PRAGMA optimize;
```

### 1.3 Batch Writes (Critical for Throughput)

```javascript
class BatchWriter {
  constructor(db, batchSize = 100, flushIntervalMs = 5000) {
    this.db = db;
    this.batch = [];
    this.batchSize = batchSize;
    this.flushInterval = flushIntervalMs;
    this.startBatchTimer();
  }

  add(snapshot) {
    this.batch.push(snapshot);
    if (this.batch.length >= this.batchSize) {
      this.flush();
    }
  }

  flush() {
    if (this.batch.length === 0) return;

    const snapshots = this.batch;
    this.batch = [];

    // Bulk insert (transaction)
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO pnl_snapshots
      (timestamp, kalshi_pnl, total_costs, total_revenue, net_pnl, trade_count)
      VALUES (?, ?, ?, ?, ?, ?)
    `);

    const insertTx = this.db.transaction(() => {
      for (const snap of snapshots) {
        stmt.run(
          snap.timestamp,
          snap.kalshiP&L,
          snap.totalCosts,
          snap.totalRevenue,
          snap.netP&L,
          snap.components?.openTradeCount || 0
        );
      }
    });

    const start = Date.now();
    insertTx();
    const latency = Date.now() - start;

    console.log(`[DB] Batch insert: ${snapshots.length} records in ${latency}ms`);
    if (latency > 500) console.warn('⚠️  Slow batch write');
  }

  startBatchTimer() {
    setInterval(() => this.flush(), this.flushInterval);
  }
}
```

### 1.4 Query Performance Monitoring

```javascript
class QueryMonitor {
  constructor(db) {
    this.db = db;
    this.queries = [];
  }

  timeQuery(sql, params = []) {
    const start = Date.now();
    const result = this.db.prepare(sql).all(...params);
    const latency = Date.now() - start;

    this.queries.push({ sql, latency, timestamp: Date.now() });

    if (latency > 100) {
      console.warn(`[SLOW QUERY] ${latency}ms: ${sql.slice(0, 50)}...`);
    }

    return result;
  }

  getSlowQueries(threshold = 100) {
    return this.queries.filter(q => q.latency > threshold);
  }

  getStats() {
    const latencies = this.queries.map(q => q.latency);
    return {
      count: latencies.length,
      avg: (latencies.reduce((a, b) => a + b, 0) / latencies.length).toFixed(2),
      p50: this.percentile(latencies, 50),
      p95: this.percentile(latencies, 95),
      p99: this.percentile(latencies, 99),
      max: Math.max(...latencies)
    };
  }

  percentile(arr, p) {
    const sorted = arr.sort((a, b) => a - b);
    const idx = Math.ceil((p / 100) * sorted.length) - 1;
    return sorted[Math.max(0, idx)];
  }
}
```

---

## 2. CACHE OPTIMIZATION

### 2.1 Redis Configuration (production)

```bash
# redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru  # LRU eviction
timeout 300                    # Close idle clients
tcp-backlog 511               # Connection queue
```

### 2.2 Layered Caching Strategy

```javascript
class SmartCache {
  constructor(redis, db) {
    this.redis = redis;
    this.db = db;
    this.localCache = new Map(); // L1: Process memory
  }

  /**
   * L1 (Process): ~100-500 items, 100-500ms TTL
   * L2 (Redis):  ~10k items, 5-30m TTL
   * L3 (DB):     Unlimited, persistent
   */
  async get(key) {
    // L1: Check process cache first (fastest)
    const l1 = this.localCache.get(key);
    if (l1 && !this.isExpired(l1)) {
      return l1.value;
    }

    // L2: Check Redis (fast)
    const l2 = await this.redis.get(key);
    if (l2) {
      const value = JSON.parse(l2);
      this.localCache.set(key, { value, expiry: Date.now() + 100 }); // L1 TTL
      return value;
    }

    // L3: Query database (slow)
    const l3 = await this.fetchFromDB(key);
    if (l3) {
      await this.redis.setex(key, 300, JSON.stringify(l3)); // L2 TTL
      this.localCache.set(key, { value: l3, expiry: Date.now() + 100 });
      return l3;
    }

    return null;
  }

  isExpired(item) {
    return Date.now() > item.expiry;
  }

  async fetchFromDB(key) {
    // Parse cache key to query
    const match = key.match(/pnl:(\d+)/);
    if (!match) return null;

    const timestamp = match[1];
    return this.db.prepare(`
      SELECT * FROM pnl_snapshots WHERE timestamp = ?
    `).get(timestamp);
  }

  async set(key, value, ttl = 300) {
    this.localCache.set(key, { value, expiry: Date.now() + 100 });
    await this.redis.setex(key, ttl, JSON.stringify(value));
  }

  getStats() {
    return {
      l1Size: this.localCache.size,
      l1Items: Array.from(this.localCache.keys())
    };
  }
}
```

### 2.3 Cache Invalidation Patterns

```javascript
class CacheInvalidator {
  constructor(redis, publisher) {
    this.redis = redis;
    this.publisher = publisher; // For pub/sub
  }

  /**
   * Invalidate P&L cache on trade update
   * Pattern: Cascade invalidation (narrow first, then wide)
   */
  async onTradeExecuted(trade) {
    const now = Date.now();
    const currentMinute = Math.floor(now / 60000) * 60000;
    const currentHour = Math.floor(now / 3600000) * 3600000;

    // Narrow: Current snapshot
    await this.redis.del('pnl:current');

    // Medium: Last 10 minutes
    for (let i = 0; i < 10; i++) {
      const time = currentMinute - (i * 60000);
      await this.redis.del(`pnl:1m:${time}`);
    }

    // Publish event (for other services)
    await this.publisher.publish('events:trade', JSON.stringify({
      type: 'trade.executed',
      trade,
      timestamp: now
    }));

    console.log('[CACHE] Invalidated on trade:', trade.id);
  }

  async onCostUpdate(cost) {
    // Costs are infrequent, only invalidate current P&L
    await this.redis.del('pnl:current');
    console.log('[CACHE] Invalidated on cost update');
  }

  /**
   * Proactive cache warming (after DB insert)
   */
  async warmCurrentP&L(snapshot) {
    await this.redis.setex('pnl:current', 30, JSON.stringify(snapshot));
    console.log('[CACHE] Warmed pnl:current');
  }
}
```

---

## 3. API AGGREGATION OPTIMIZATION

### 3.1 Parallel Requests with Timeout

```javascript
class OptimizedAggregator {
  constructor(apis) {
    this.apis = apis;
    this.timeout = 3000; // 3s per API
    this.circuitBreaker = new Map(); // Track API health
  }

  /**
   * Fetch all 3 sources in parallel
   * Timeout: 3000ms per source → fail gracefully
   * Fallback: Use cached data if API fails
   */
  async fetchAllParallel(cache) {
    const requests = [
      this.fetchWithTimeout('kalshi', () => this.apis.kalshi.getTrades(), 3000),
      this.fetchWithTimeout('anthropic', () => this.apis.anthropic.getCosts(), 3000),
      this.fetchWithTimeout('john', () => this.apis.john.getRevenue(), 3000)
    ];

    const results = await Promise.allSettled(requests);

    return {
      trades: results[0].status === 'fulfilled' ? results[0].value : await cache.get('kalshi:trades:fallback'),
      costs: results[1].status === 'fulfilled' ? results[1].value : await cache.get('anthropic:costs:fallback'),
      revenue: results[2].status === 'fulfilled' ? results[2].value : await cache.get('john:revenue:fallback'),
      health: {
        kalshi: results[0].status,
        anthropic: results[1].status,
        john: results[2].status
      }
    };
  }

  async fetchWithTimeout(source, fn, timeoutMs) {
    // Check circuit breaker
    const breaker = this.circuitBreaker.get(source) || { failures: 0, lastFail: 0 };
    if (breaker.failures > 3 && Date.now() - breaker.lastFail < 60000) {
      throw new Error(`[CIRCUIT BREAK] ${source} is failing, skipping`);
    }

    try {
      const result = await Promise.race([
        fn(),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error(`Timeout after ${timeoutMs}ms`)), timeoutMs)
        )
      ]);

      // Success: reset circuit breaker
      this.circuitBreaker.set(source, { failures: 0, lastFail: 0 });
      return result;
    } catch (err) {
      // Failure: increment breaker
      breaker.failures++;
      breaker.lastFail = Date.now();
      this.circuitBreaker.set(source, breaker);
      throw err;
    }
  }
}
```

### 3.2 Connection Pooling

```javascript
const axios = require('axios');

const apiClients = {
  kalshi: axios.create({
    baseURL: 'https://api.kalshi.com',
    timeout: 3000,
    httpAgent: new (require('http').Agent)({ keepAlive: true, maxSockets: 5 }),
    httpsAgent: new (require('https').Agent)({ keepAlive: true, maxSockets: 5 })
  }),
  anthropic: axios.create({
    baseURL: 'https://api.anthropic.com',
    timeout: 3000,
    httpAgent: new (require('http').Agent)({ keepAlive: true, maxSockets: 5 }),
    httpsAgent: new (require('https').Agent)({ keepAlive: true, maxSockets: 5 })
  })
};
```

---

## 4. WEBSOCKET OPTIMIZATION

### 4.1 Delta Compression

```javascript
class DeltaCompressor {
  /**
   * Instead of sending full snapshot (5KB), send only changed fields (100-500B)
   */
  compress(current, previous) {
    const delta = {};

    // Only include fields that changed
    for (const key in current) {
      if (current[key] !== previous[key]) {
        delta[key] = current[key];
      }
    }

    return {
      type: 'delta',
      data: delta,
      timestamp: current.timestamp
    };
  }
}

// Broadcasting optimized:
broadcastUpdate({
  type: 'delta',
  data: {
    netP&L: -1234.56,   // Only changed value
    timestamp: 1708893456789
  }
  // Skip unchanged fields: kalshiP&L, totalCosts, totalRevenue
});
```

### 4.2 Broadcast Batching

```javascript
class BatchedBroadcaster {
  constructor(wss, batchSize = 100, flushIntervalMs = 100) {
    this.wss = wss;
    this.batch = [];
    this.batchSize = batchSize;
    this.flushInterval = flushIntervalMs;
    this.startTimer();
  }

  queue(message) {
    this.batch.push(message);
    if (this.batch.length >= this.batchSize) {
      this.flush();
    }
  }

  flush() {
    if (this.batch.length === 0) return;

    // Send all batched messages at once
    const payload = JSON.stringify(this.batch);
    const start = Date.now();

    const wss = this.wss;
    let count = 0;
    wss.clients.forEach((client) => {
      if (client.readyState === 1) {
        client.send(payload);
        count++;
      }
    });

    const latency = Date.now() - start;
    console.log(`[WS] Broadcast batch: ${this.batch.length} msgs to ${count} clients in ${latency}ms`);
    this.batch = [];
  }

  startTimer() {
    setInterval(() => this.flush(), this.flushInterval);
  }
}
```

---

## 5. FRONTEND OPTIMIZATION

### 5.1 Memoization (Prevent Re-renders)

```javascript
import React, { useCallback, useMemo } from 'react';

const P&LDashboard = memo(({ wsUrl }) => {
  const [pnl, setPnl] = useState(null);

  // Memoize expensive calculations
  const breakdown = useMemo(() => {
    if (!pnl) return {};
    return {
      trades: pnl.netP&L - pnl.totalRevenue + pnl.totalCosts,
      profitMargin: (pnl.netP&L / Math.abs(pnl.totalRevenue)) * 100 || 0
    };
  }, [pnl?.netP&L, pnl?.totalRevenue, pnl?.totalCosts]);

  // Memoize callbacks to prevent child re-renders
  const handleUpdate = useCallback((data) => {
    setPnl(data);
  }, []);

  return (
    <div>
      <P&LValue value={pnl?.netP&L} />
      <Breakdown data={breakdown} />
    </div>
  );
});
```

### 5.2 Virtual Scrolling (for large lists)

```javascript
import { FixedSizeList } from 'react-window';

const TradeList = ({ trades }) => (
  <FixedSizeList
    height={400}
    itemCount={trades.length}
    itemSize={50}
    width="100%"
  >
    {({ index, style }) => (
      <div style={style}>
        {/* Render only visible trades */}
        <TradeRow trade={trades[index]} />
      </div>
    )}
  </FixedSizeList>
);
```

---

## 6. MONITORING & PROFILING

### 6.1 Instrumentation

```javascript
class Profiler {
  constructor() {
    this.timers = {};
    this.metrics = {};
  }

  start(label) {
    this.timers[label] = Date.now();
  }

  end(label) {
    if (!this.timers[label]) return;
    const latency = Date.now() - this.timers[label];
    
    if (!this.metrics[label]) {
      this.metrics[label] = { count: 0, total: 0, max: 0, min: Infinity };
    }
    
    const m = this.metrics[label];
    m.count++;
    m.total += latency;
    m.max = Math.max(m.max, latency);
    m.min = Math.min(m.min, latency);

    if (latency > 500) {
      console.warn(`⚠️  Slow operation: ${label} = ${latency}ms`);
    }

    delete this.timers[label];
    return latency;
  }

  report(label) {
    const m = this.metrics[label];
    if (!m) return null;
    return {
      count: m.count,
      avg: (m.total / m.count).toFixed(2),
      min: m.min,
      max: m.max
    };
  }

  reportAll() {
    const report = {};
    for (const label in this.metrics) {
      report[label] = this.report(label);
    }
    return report;
  }
}

// Usage
const profiler = new Profiler();

profiler.start('api_aggregate');
const data = await aggregator.fetchAllData();
profiler.end('api_aggregate');

profiler.start('compute_pnl');
const { snapshot } = await engine.computeP&LSnapshot(...);
profiler.end('compute_pnl');

// Report every minute
setInterval(() => {
  console.log('=== Performance Report ===');
  console.log(JSON.stringify(profiler.reportAll(), null, 2));
}, 60000);
```

### 6.2 Metrics Collection (Prometheus)

```javascript
const prometheus = require('prom-client');

// Histograms
const aggregationLatency = new prometheus.Histogram({
  name: 'pnl_aggregation_latency_ms',
  help: 'P&L aggregation latency',
  buckets: [50, 100, 200, 500, 1000]
});

const wsMessageLatency = new prometheus.Histogram({
  name: 'pnl_ws_message_latency_ms',
  help: 'WebSocket message latency',
  buckets: [10, 50, 100, 200]
});

// Gauges
const connectedClientsGauge = new prometheus.Gauge({
  name: 'pnl_connected_clients',
  help: 'Number of connected WebSocket clients'
});

const cacheHitRateGauge = new prometheus.Gauge({
  name: 'pnl_cache_hit_rate',
  help: 'Cache hit rate percentage'
});

// Counters
const broadcastCounter = new prometheus.Counter({
  name: 'pnl_broadcasts_total',
  help: 'Total P&L broadcasts',
  labelNames: ['type']
});

// Expose metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', prometheus.register.contentType);
  res.end(await prometheus.register.metrics());
});
```

---

## 7. LATENCY CHECKLIST

| Component | Target | Actual | Status |
|-----------|--------|--------|--------|
| Kalshi API fetch | <200ms | ? | ⬜ |
| Anthropic API fetch | <100ms | ? | ⬜ |
| John API fetch | <150ms | ? | ⬜ |
| Data aggregation | <50ms | ? | ⬜ |
| P&L calculation | <30ms | ? | ⬜ |
| Cache write | <20ms | ? | ⬜ |
| DB insert | <50ms | ? | ⬜ |
| WebSocket broadcast | <100ms | ? | ⬜ |
| Network transmission | <100ms | ? | ⬜ |
| Browser render | <50ms | ? | ⬜ |
| **Total (API → render)** | **<500ms** | **?** | **⬜** |

---

## 8. QUICK WINS

1. **Enable SQLite WAL mode** → 3x faster writes
2. **Add indexes** → 10-100x faster queries
3. **Use Redis** → 10x faster cache lookups
4. **Batch writes** → 5x faster DB throughput
5. **Parallel API calls** → 3x faster aggregation
6. **Delta compression** → 10x smaller payloads
7. **Memoization** → Prevent unnecessary re-renders
8. **Connection pooling** → Reuse HTTP connections

**Implement these 8 changes = ~10-50x overall speedup**

---

## 9. Capacity Planning

| Load | Recommendations |
|------|-----------------|
| <100 concurrent users | Single t3.micro, SQLite |
| 100-500 users | t3.small + Redis, batch writes |
| 500-5000 users | t3.medium + Redis, read replicas |
| 5000+ users | Multi-region, database sharding |

---

## Next Steps

1. Profile current implementation with `node --inspect`
2. Identify slowest components using logs
3. Implement highest-impact optimizations first
4. Monitor improvements with Prometheus/Grafana
5. Test under load (artillery, k6)
6. Re-profile and iterate
