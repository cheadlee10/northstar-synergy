---
name: realtime-data-streaming
description: Implement real-time data streaming for financial dashboards using WebSocket, Server-Sent Events, and polling fallbacks. Use when building live feeds, monitoring metrics, tracking P&L updates, or aggregating multiple data sources with sub-second latency. Includes Socket.io patterns, caching strategies, error handling, and performance optimization.
---

# Real-Time Data Streaming Skill

Production patterns for streaming live financial data from backend to frontend with guaranteed delivery and automatic fallback chains.

## Architecture Overview

```
Data Sources (Kalshi, APIs, DB)
        ↓
API Aggregator (parallel fetch, cache)
        ↓
Message Bus (WebSocket primary)
        ↓
Fallback 1: Server-Sent Events (if WebSocket fails)
        ↓
Fallback 2: Long polling (if SSE fails)
        ↓
React Dashboard (renders updates)
```

## WebSocket Pattern (Primary)

### Backend Setup
```javascript
const io = require('socket.io')(3001);
const Redis = require('redis');
const redis = Redis.createClient();

io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);
  
  // Send initial snapshot
  socket.emit('snapshot', getCurrentPnL());
  
  // Subscribe to live updates
  const interval = setInterval(() => {
    const update = calculatePnL();
    socket.emit('update', update);
    
    // Broadcast to all clients
    io.emit('broadcast', update);
  }, 5000);

  socket.on('disconnect', () => clearInterval(interval));
});
```

### Frontend Setup
```javascript
import { io } from 'socket.io-client';

const socket = io('http://backend:3001', {
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: 5
});

socket.on('connect', () => console.log('Connected'));
socket.on('snapshot', (data) => setPnl(data));
socket.on('update', (data) => setPnl(prev => ({ ...prev, ...data })));
socket.on('disconnect', () => console.log('Disconnected'));
```

## Fallback Chain Pattern

### Backend SSE Fallback
```javascript
app.get('/api/pnl-stream', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const interval = setInterval(() => {
    const data = calculatePnL();
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  }, 5000);

  req.on('close', () => clearInterval(interval));
});
```

### Frontend SSE Fallback
```javascript
const useEventStream = () => {
  useEffect(() => {
    const sse = new EventSource('/api/pnl-stream');
    
    sse.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setPnl(data);
    };
    
    sse.onerror = () => {
      sse.close();
      startPolling();  // Fallback to polling
    };

    return () => sse.close();
  }, []);
};
```

### Polling Fallback
```javascript
const usePolling = (interval = 5000) => {
  useEffect(() => {
    const timer = setInterval(async () => {
      const res = await fetch('/api/pnl');
      const data = await res.json();
      setPnl(data);
    }, interval);

    return () => clearInterval(timer);
  }, []);
};
```

## Caching Strategy (4-Tier)

### L1: Process Cache (In-Memory)
```javascript
let cachedPnL = null;
let cacheTime = 0;
const CACHE_DURATION = 1000;  // 1 second

function getPnLCached() {
  const now = Date.now();
  if (cachedPnL && now - cacheTime < CACHE_DURATION) {
    return cachedPnL;
  }
  cachedPnL = calculatePnL();
  cacheTime = now;
  return cachedPnL;
}
```

### L2: Redis Cache
```javascript
const Redis = require('redis');
const redis = Redis.createClient();

async function getPnLWithRedis() {
  // Try Redis first
  let cached = await redis.get('pnl:current');
  if (cached) return JSON.parse(cached);

  // Calculate if not cached
  const pnl = await calculatePnL();
  
  // Store in Redis (10 second expiry)
  await redis.setex('pnl:current', 10, JSON.stringify(pnl));
  
  return pnl;
}
```

### L3: Database Cache (SQLite)
```javascript
const db = require('sqlite3').verbose();

function cacheToDatabase(pnl) {
  db.run(
    'INSERT INTO pnl_cache (timestamp, data) VALUES (?, ?)',
    [Date.now(), JSON.stringify(pnl)]
  );
}

function getCachedFromDatabase() {
  return new Promise((resolve) => {
    db.get(
      'SELECT data FROM pnl_cache ORDER BY timestamp DESC LIMIT 1',
      (err, row) => resolve(row ? JSON.parse(row.data) : null)
    );
  });
}
```

### L4: Fallback (Last Known Value)
```javascript
let lastKnownPnL = { revenue: 0, expenses: 0, netPL: 0 };

async function getPnLWithFallback() {
  try {
    const pnl = await getPnLWithRedis();
    lastKnownPnL = pnl;
    return pnl;
  } catch (err) {
    console.error('Failed to fetch P&L:', err);
    return lastKnownPnL;
  }
}
```

## Data Aggregation (Multi-Source)

### Parallel API Calls
```javascript
async function aggregatePnL(sources) {
  const timeout = 5000;
  
  const [kalshi, anthropic, john] = await Promise.allSettled([
    Promise.race([
      sources.kalshi.getBalance(),
      new Promise((_, reject) => setTimeout(() => reject('timeout'), timeout))
    ]),
    Promise.race([
      sources.anthropic.getCosts(),
      new Promise((_, reject) => setTimeout(() => reject('timeout'), timeout))
    ]),
    Promise.race([
      sources.john.getRevenue(),
      new Promise((_, reject) => setTimeout(() => reject('timeout'), timeout))
    ])
  ]);

  return {
    kalshiPL: kalshi.status === 'fulfilled' ? kalshi.value : { balance: 0 },
    apiCosts: anthropic.status === 'fulfilled' ? anthropic.value : { total: 0 },
    johnRevenue: john.status === 'fulfilled' ? john.value : { total: 0 }
  };
}
```

### Circuit Breaker (Fail-Safe)
```javascript
class CircuitBreaker {
  constructor(fn, threshold = 5, timeout = 60000) {
    this.fn = fn;
    this.failures = 0;
    this.threshold = threshold;
    this.timeout = timeout;
    this.state = 'CLOSED';  // CLOSED, OPEN, HALF_OPEN
  }

  async execute() {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailure > this.timeout) {
        this.state = 'HALF_OPEN';
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await this.fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  onSuccess() {
    this.failures = 0;
    this.state = 'CLOSED';
  }

  onFailure() {
    this.failures++;
    this.lastFailure = Date.now();
    if (this.failures >= this.threshold) {
      this.state = 'OPEN';
    }
  }
}

const kalshiBreaker = new CircuitBreaker(async () => {
  return await kalshiApi.getBalance();
});
```

## Timestamp Normalization

```javascript
function normalizeTimestamp(ts, timezone = 'UTC') {
  // Convert all timestamps to UTC for consistency
  const date = new Date(ts);
  return date.toISOString();
}

function syncTimestamps(data) {
  return {
    ...data,
    timestamp: normalizeTimestamp(data.timestamp),
    apiTimestamp: normalizeTimestamp(data.apiTimestamp),
    dbTimestamp: normalizeTimestamp(data.dbTimestamp)
  };
}
```

## Error Handling & Recovery

### Retry with Exponential Backoff
```javascript
async function fetchWithRetry(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      const delay = Math.pow(2, i) * 1000;  // 1s, 2s, 4s
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw error;
      }
    }
  }
}
```

### Graceful Degradation
```javascript
async function getPnLSafely() {
  try {
    return await getPnLComplete();
  } catch {
    try {
      return await getPnLPartial();  // Try with fewer sources
    } catch {
      return getCachedOrDefault();   // Use cache
    }
  }
}
```

## Performance Optimization

### Batch Updates (Debounce)
```javascript
const batched = debounce((update) => {
  socket.emit('batch-update', update);
}, 500);

onDataChange((update) => {
  batched(update);
});
```

### Delta Compression (Send Only Changes)
```javascript
function getDelta(current, previous) {
  const delta = {};
  for (const key in current) {
    if (current[key] !== previous[key]) {
      delta[key] = current[key];
    }
  }
  return delta;
}

socket.emit('delta', getDelta(currentPnL, previousPnL));
```

## Monitoring & Metrics

```javascript
const metrics = {
  messageCount: 0,
  errorCount: 0,
  latency: [],
  uptime: Date.now()
};

function recordMessage() {
  metrics.messageCount++;
}

function recordError() {
  metrics.errorCount++;
}

function recordLatency(ms) {
  metrics.latency.push(ms);
  if (metrics.latency.length > 100) {
    metrics.latency.shift();
  }
}

function getHealth() {
  const avgLatency = metrics.latency.reduce((a, b) => a + b) / metrics.latency.length;
  return {
    messages: metrics.messageCount,
    errors: metrics.errorCount,
    avgLatency: Math.round(avgLatency),
    uptime: Date.now() - metrics.uptime
  };
}
```

## Testing

```javascript
// Mock Socket.io
const mockSocket = {
  emit: jest.fn(),
  on: jest.fn(),
  disconnect: jest.fn()
};

test('sends initial snapshot on connect', () => {
  const io = require('socket.io');
  io.on('connection', (socket) => {
    expect(socket.emit).toHaveBeenCalledWith('snapshot', expect.any(Object));
  });
});
```

## Deployment Checklist

- [ ] WebSocket properly configured (CORS, auth)
- [ ] Fallback chain tested (SSE, polling)
- [ ] Caching strategy validated (Redis working)
- [ ] Circuit breaker active (prevents cascading failures)
- [ ] Error handling complete (all edge cases)
- [ ] Monitoring in place (metrics collection)
- [ ] Load testing done (concurrent users verified)
- [ ] Security audit passed (auth, data validation)
