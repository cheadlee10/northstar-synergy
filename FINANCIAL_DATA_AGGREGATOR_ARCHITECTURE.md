# Financial Data Aggregator Backend Architecture
## Node.js + Express Real-Time Data Integration

**Document Version:** 1.0  
**Created:** 2026-02-26  
**Target Environment:** Production (Linux/Docker)  
**Primary Use Case:** Real-time P&L tracking, agent attribution, market data aggregation

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [API Integration Patterns](#api-integration-patterns)
4. [Data Normalization Schema](#data-normalization-schema)
5. [4-Tier Caching Strategy](#4-tier-caching-strategy)
6. [Circuit Breaker Pattern](#circuit-breaker-pattern)
7. [Real-Time Streaming](#real-time-streaming)
8. [Database Design](#database-design)
9. [Error Handling Strategy](#error-handling-strategy)
10. [Code Examples](#code-examples)
11. [Deployment Guide](#deployment-guide)

---

## Executive Summary

This architecture provides a fault-tolerant, high-performance backend for aggregating real-time financial data from three heterogeneous sources:
- **Kalshi API**: Prediction market data (WebSocket-native)
- **Anthropic Claude API**: Financial analysis & insights (HTTP streaming/SSE)
- **John Revenue System**: Internal business metrics (custom REST endpoints)

**Key Design Principles:**
- **Resilience**: Circuit breaker + multi-tier fallback caching
- **Performance**: Parallel API calls with 5-10s timeout windows
- **Real-Time**: WebSocket primary, SSE fallback, 100-500ms update latency
- **Observability**: Per-API metrics, agent attribution, request tracing
- **Scalability**: Stateless Express instances, Redis-backed sessions, SQLite for persistence

---

## System Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER (Browser/App)                   │
│  ┌──────────────────┐  ┌────────────────────────┐               │
│  │  WebSocket       │  │  EventSource (SSE)     │               │
│  │  Connection      │  │  Fallback             │               │
│  └────────┬─────────┘  └──────────┬─────────────┘               │
└───────────┼──────────────────────┼──────────────────────────────┘
            │                      │
┌───────────▼──────────────────────▼──────────────────────────────┐
│                  EXPRESS SERVER (Node.js)                        │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Router Layer (Express Routes)                            │  │
│  │  - GET /api/data/aggregated          (current snapshot)   │  │
│  │  - GET /api/data/historical          (time-series)        │  │
│  │  - GET /events (SSE endpoint)                             │  │
│  │  - WebSocket /ws (real-time updates)                      │  │
│  │  - GET /api/health (service status)                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│  ┌────────────────────────▼────────────────────────────────┐    │
│  │  Service Layer (Business Logic)                         │    │
│  │  ┌──────────────────────────────────────────────────┐   │    │
│  │  │ DataAggregatorService                            │   │    │
│  │  │ - Orchestrates parallel API calls                │   │    │
│  │  │ - Implements timeout/retry logic                 │   │    │
│  │  │ - Normalizes heterogeneous responses             │   │    │
│  │  │ - Manages real-time subscriptions                │   │    │
│  │  └──────────────────────────────────────────────────┘   │    │
│  │                                                           │    │
│  │  ┌──────────────────────────────────────────────────┐   │    │
│  │  │ CacheManager (4-tier orchestration)              │   │    │
│  │  │ L1: Process Memory (TTL 5-30s)                   │   │    │
│  │  │ L2: Redis (TTL 30-300s)                          │   │    │
│  │  │ L3: SQLite (permanent snapshots)                 │   │    │
│  │  │ L4: Fallback JSON files                          │   │    │
│  │  └──────────────────────────────────────────────────┘   │    │
│  │                                                           │    │
│  │  ┌──────────────────────────────────────────────────┐   │    │
│  │  │ CircuitBreakerManager                            │   │    │
│  │  │ - Manages 3 circuit breakers (one per API)       │   │    │
│  │  │ - State: CLOSED → OPEN → HALF_OPEN → CLOSED     │   │    │
│  │  │ - Fallback to cache on OPEN                      │   │    │
│  │  └──────────────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────────┘    │
│                            │                                    │
└────────────────┼───────────┼───────────┼───────────────────────┘
                 │           │           │
        ┌────────▼─┐  ┌──────▼──┐  ┌────▼────────┐
        │  KALSHI  │  │ANTHROPIC│  │ JOHN SYSTEM │
        │   API    │  │  API    │  │   (REST)    │
        │(WebSocket)  │(HTTP SSE) │  └─────────────┘
        └──────────┘  └─────────┘
```

### Service Architecture (Container View)

```
┌─────────────────────────────────────────────────────────────┐
│  Docker Container: express-api-server                       │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Process      │  │ Redis        │  │ SQLite       │     │
│  │ Memory Cache │  │ (optional,   │  │ (local)      │     │
│  │ (LRU)        │  │ docker-link) │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Node.js v18+ Runtime                               │   │
│  │ ├─ Express.js 4.18+                                 │   │
│  │ ├─ ws (WebSocket library)                           │   │
│  │ ├─ axios (HTTP client)                              │   │
│  │ ├─ redis (client library)                           │   │
│  │ ├─ better-sqlite3 (sync SQLite)                     │   │
│  │ ├─ opossum (Circuit Breaker)                        │   │
│  │ ├─ pino (structured logging)                        │   │
│  │ └─ @anthropic-ai/sdk (if using official SDK)        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## API Integration Patterns

### 1. Kalshi API Integration

**Characteristics:**
- Primary protocol: **WebSocket** (real-time order book, trades)
- Secondary: HTTP REST (historical, markets list)
- Authentication: API Key (header or query param)
- Response format: JSON

**Typical Response Structure:**
```json
{
  "id": "SMUSD-260226",
  "ticker": "SMUSD",
  "title": "Will SM > $150 by Feb 26?",
  "strike_price": 150,
  "bid": 0.45,
  "ask": 0.55,
  "last_price": 0.48,
  "open_interest": 50000,
  "volume_24h": 120000,
  "event_date": "2026-02-26T20:00:00Z",
  "created_at": "2026-02-01T10:00:00Z",
  "status": "open"
}
```

**WebSocket Subscription Example:**
```json
{
  "action": "subscribe",
  "type": "order_book",
  "market_id": "SMUSD-260226"
}

// Response stream:
{
  "type": "delta",
  "market_id": "SMUSD-260226",
  "bids": [
    {"price": 0.45, "size": 5000},
    {"price": 0.44, "size": 3000}
  ],
  "asks": [
    {"price": 0.55, "size": 4000},
    {"price": 0.56, "size": 2000}
  ],
  "timestamp": "2026-02-26T08:15:30.123Z"
}
```

**Implementation Strategy:**
- Use `ws` library for WebSocket connection pooling
- Implement auto-reconnect with exponential backoff (3s → 30s)
- Parse order book deltas, maintain local L2 cache
- Emit normalized events to subscribers

### 2. Anthropic Claude API Integration

**Characteristics:**
- Protocol: **HTTP/SSE** (streaming completions)
- Authentication: API Key (header: `x-api-key`)
- Response format: Server-Sent Events (SSE)
- Use case: Real-time financial analysis on aggregated data

**Typical Request:**
```json
{
  "model": "claude-3.5-sonnet",
  "max_tokens": 2048,
  "stream": true,
  "messages": [
    {
      "role": "user",
      "content": "Analyze this market data: {aggregated_data_json}. Provide sentiment and key insights."
    }
  ]
}
```

**SSE Response Stream:**
```
event: message_start
data: {"type":"message_start","message":{"id":"msg_123","type":"message","role":"assistant","model":"claude-3.5-sonnet"}}

event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"The market shows"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":" strong bullish"}}

...

event: message_stop
data: {"type":"message_stop"}
```

**Implementation Strategy:**
- Use `axios` with `responseType: 'stream'` OR official `@anthropic-ai/sdk`
- Parse SSE events using regex or streaming parser
- Buffer chunks, emit complete insights every 5-10s
- Cache sentiment scores in Redis (TTL: 5min)

### 3. John Revenue System Integration

**Characteristics:**
- Protocol: **HTTP REST** (custom endpoints)
- Authentication: Bearer token or API key
- Response format: JSON (custom schema)
- Polling interval: 10-30s recommended

**Typical Response Structure:**
```json
{
  "agent_id": "agent:john:main",
  "period": "2026-02-26T08:00:00Z",
  "metrics": {
    "revenue_usd": 125000,
    "deals_closed": 3,
    "pipeline_value": 500000,
    "conversion_rate": 0.42,
    "avg_deal_size": 41667,
    "active_prospects": 12
  },
  "timestamp": "2026-02-26T08:15:30Z",
  "status": "active"
}
```

**Implementation Strategy:**
- Poll every 15s with 5s timeout
- Implement aggressive retry on 5xx (3 attempts with 1s backoff)
- Cache in Redis (TTL: 30s) to smooth polling
- Track agent attribution separately

---

## Data Normalization Schema

### Unified Financial Data Schema

All three APIs normalize to this internal format:

```typescript
interface NormalizedFinancialData {
  // Metadata
  id: string;                    // Unique identifier across all sources
  source: 'kalshi' | 'anthropic' | 'john';
  timestamp: ISO8601Timestamp;
  agent_id?: string;             // e.g., "agent:john:main"
  
  // Market/Asset Data (Kalshi, market prices)
  asset?: {
    ticker: string;              // e.g., "SMUSD-260226"
    type: 'prediction' | 'stock' | 'commodity' | 'metric';
    description: string;
    underlying?: string;          // e.g., "USD/SM"
  };
  
  // Pricing Data
  prices?: {
    bid: number;                 // Best bid price
    ask: number;                 // Best ask price
    last: number;                // Last trade price
    open?: number;               // Open price (if available)
    high?: number;               // 24h high
    low?: number;                // 24h low
  };
  
  // Market Activity
  volume?: {
    volume_24h: number;          // 24h trading volume
    open_interest?: number;       // Open interest (for derivatives)
    trades_24h?: number;         // Number of trades
  };
  
  // AI/Sentiment Data (from Anthropic)
  analysis?: {
    sentiment: 'bullish' | 'neutral' | 'bearish';
    sentiment_score: number;      // -1.0 to +1.0
    key_factors: string[];
    risk_level: 'low' | 'medium' | 'high';
    confidence: number;           // 0.0 to 1.0
  };
  
  // Business Metrics (from John system)
  business_metrics?: {
    metric_name: string;
    metric_value: number;
    metric_unit: string;          // "USD", "count", "%", etc.
    period: ISO8601Timestamp;
    comparison_period_value?: number;
  };
  
  // Event/Maturity Info
  event_date?: ISO8601Timestamp;
  expiry_date?: ISO8601Timestamp;
  
  // Data Quality Indicators
  quality: {
    freshness_ms: number;         // Milliseconds since last update
    source_reliability: number;   // 0.0 to 1.0
    is_from_cache: boolean;
    cache_tier: 'L1' | 'L2' | 'L3' | 'L4' | 'live';
  };
}
```

### Normalization Functions

```typescript
// Kalshi → Normalized
function normalizeKalshi(raw: KalshiMarket): NormalizedFinancialData {
  return {
    id: `kalshi_${raw.id}_${Date.now()}`,
    source: 'kalshi',
    timestamp: new Date(raw.created_at).toISOString(),
    asset: {
      ticker: raw.ticker,
      type: 'prediction',
      description: raw.title,
    },
    prices: {
      bid: raw.bid,
      ask: raw.ask,
      last: raw.last_price,
    },
    volume: {
      volume_24h: raw.volume_24h,
      open_interest: raw.open_interest,
    },
    event_date: raw.event_date,
    quality: {
      freshness_ms: 0,
      source_reliability: 0.95,
      is_from_cache: false,
      cache_tier: 'live',
    },
  };
}

// Anthropic → Normalized
function normalizeAnthropicInsight(raw: AnthropicResponse): NormalizedFinancialData {
  // Parse sentiment from response text using regex or ML model
  const sentimentScore = extractSentimentScore(raw.content);
  const sentiment = sentimentScore > 0.2 ? 'bullish' : sentimentScore < -0.2 ? 'bearish' : 'neutral';
  
  return {
    id: `anthropic_insight_${Date.now()}`,
    source: 'anthropic',
    timestamp: new Date().toISOString(),
    analysis: {
      sentiment,
      sentiment_score: sentimentScore,
      key_factors: extractKeyFactors(raw.content),
      risk_level: 'medium',
      confidence: 0.85,
    },
    quality: {
      freshness_ms: 0,
      source_reliability: 0.90,
      is_from_cache: false,
      cache_tier: 'live',
    },
  };
}

// John System → Normalized
function normalizeJohnMetrics(raw: JohnResponse): NormalizedFinancialData {
  return {
    id: `john_${raw.agent_id}_${Date.now()}`,
    source: 'john',
    timestamp: new Date(raw.timestamp).toISOString(),
    agent_id: raw.agent_id,
    business_metrics: {
      metric_name: 'revenue',
      metric_value: raw.metrics.revenue_usd,
      metric_unit: 'USD',
      period: raw.period,
    },
    quality: {
      freshness_ms: 0,
      source_reliability: 0.98,
      is_from_cache: false,
      cache_tier: 'live',
    },
  };
}
```

---

## 4-Tier Caching Strategy

### Cache Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Request → Is data in L1 (Process Memory)?               │
│           YES → Return (0-1ms latency)                  │
│           NO → Check L2                                 │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────▼─────────────────────────────┐
│ Is data in L2 (Redis)?                                    │
│ YES → Return + repopulate L1 (1-5ms latency)              │
│ NO → Check L3                                             │
└──────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────▼─────────────────────────────┐
│ Is data in L3 (SQLite)?                                   │
│ YES → Return + repopulate L2/L1 (10-50ms latency)         │
│ NO → Check L4                                             │
└──────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────▼─────────────────────────────┐
│ Is data in L4 (Fallback JSON files)?                      │
│ YES → Return (last resort, likely stale)                  │
│ NO → Fetch from live API                                  │
└──────────────────────────────────────────────────────────┘
```

### L1: Process Memory Cache (LRU)

**Purpose:** Sub-millisecond access for hot data  
**Implementation:** Node.js `Map` with TTL + LRU eviction  
**TTL:** 5-30s (configurable per data type)  
**Max Size:** 500 entries (~50MB)

```typescript
class L1Cache {
  private cache = new Map<string, CacheEntry>();
  private maxSize = 500;
  private accessQueue: string[] = [];

  set(key: string, value: any, ttl_ms: number) {
    if (this.cache.size >= this.maxSize) {
      const lru_key = this.accessQueue.shift();
      if (lru_key) this.cache.delete(lru_key);
    }
    
    this.cache.set(key, {
      value,
      expires_at: Date.now() + ttl_ms,
    });
    
    this.accessQueue.push(key);
  }

  get(key: string): any | null {
    const entry = this.cache.get(key);
    
    if (!entry) return null;
    if (Date.now() > entry.expires_at) {
      this.cache.delete(key);
      return null;
    }
    
    // Move to end (most recently accessed)
    this.accessQueue = this.accessQueue.filter(k => k !== key);
    this.accessQueue.push(key);
    
    return entry.value;
  }

  clear() {
    this.cache.clear();
    this.accessQueue = [];
  }
}
```

### L2: Redis Cache

**Purpose:** Distributed cache across multiple instances  
**Implementation:** Redis (external service)  
**TTL:** 30-300s (configurable)  
**Key Naming:** `data:{source}:{id}:{version}`

```typescript
class L2Cache {
  constructor(private redis: Redis.Redis) {}

  async set(
    key: string,
    value: any,
    ttl_s: number = 60
  ) {
    const serialized = JSON.stringify(value);
    await this.redis.setex(
      `data:${key}`,
      ttl_s,
      serialized
    );
  }

  async get(key: string): Promise<any | null> {
    const cached = await this.redis.get(`data:${key}`);
    if (!cached) return null;
    
    return JSON.parse(cached);
  }

  async invalidate(pattern: string) {
    const keys = await this.redis.keys(`data:${pattern}`);
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }
}
```

### L3: SQLite Persistent Store

**Purpose:** Durable storage of snapshots, audit trail  
**Implementation:** better-sqlite3 (synchronous)  
**Retention:** 90 days (configurable)  
**Size:** ~1GB for 1M snapshots

```typescript
class L3Cache {
  private db: Database;

  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    this.initializeSchema();
  }

  private initializeSchema() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS data_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cache_key TEXT UNIQUE NOT NULL,
        data_json TEXT NOT NULL,
        source TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NOT NULL,
        INDEX idx_source (source),
        INDEX idx_expires (expires_at)
      );

      CREATE TABLE IF NOT EXISTS snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date DATE NOT NULL,
        timestamp DATETIME NOT NULL,
        aggregated_data_json TEXT NOT NULL,
        agent_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_date (snapshot_date),
        INDEX idx_agent (agent_id)
      );

      CREATE TRIGGER IF NOT EXISTS cleanup_expired_cache
      AFTER INSERT ON data_cache
      BEGIN
        DELETE FROM data_cache WHERE expires_at < CURRENT_TIMESTAMP;
      END;
    `);
  }

  set(
    key: string,
    value: any,
    ttl_s: number = 3600
  ) {
    const expires_at = new Date(Date.now() + ttl_s * 1000);
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO data_cache (cache_key, data_json, source, expires_at)
      VALUES (?, ?, ?, ?)
    `);
    stmt.run(
      key,
      JSON.stringify(value),
      value.source || 'unknown',
      expires_at.toISOString()
    );
  }

  get(key: string): any | null {
    const stmt = this.db.prepare(`
      SELECT data_json FROM data_cache
      WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP
    `);
    const row = stmt.get(key) as any;
    if (!row) return null;
    
    return JSON.parse(row.data_json);
  }

  saveSnapshot(data: AggregatedData, agent_id?: string) {
    const stmt = this.db.prepare(`
      INSERT INTO snapshots (snapshot_date, timestamp, aggregated_data_json, agent_id)
      VALUES (?, ?, ?, ?)
    `);
    stmt.run(
      new Date().toISOString().split('T')[0],
      new Date().toISOString(),
      JSON.stringify(data),
      agent_id || null
    );
  }
}
```

### L4: Fallback JSON Files

**Purpose:** Last-resort fallback when all systems fail  
**Implementation:** JSON files in `/cache/fallback/`  
**Update Frequency:** Every 60s (background job)  
**Recovery:** Manual or automatic on startup

```typescript
class L4Cache {
  private basePath = './cache/fallback';

  constructor() {
    fs.mkdirSync(this.basePath, { recursive: true });
  }

  write(key: string, value: any) {
    const path = `${this.basePath}/${key}.json`;
    fs.writeFileSync(path, JSON.stringify(value, null, 2));
  }

  read(key: string): any | null {
    const path = `${this.basePath}/${key}.json`;
    try {
      const data = fs.readFileSync(path, 'utf-8');
      return JSON.parse(data);
    } catch {
      return null;
    }
  }

  async writeAllCachesAsync(caches: Map<string, any>) {
    const promises = Array.from(caches.entries()).map(
      ([key, value]) => {
        return new Promise((resolve) => {
          const path = `${this.basePath}/${key}.json`;
          fs.writeFile(path, JSON.stringify(value), (err) => {
            if (err) console.error(`L4 write failed for ${key}:`, err);
            resolve(null);
          });
        });
      }
    );
    await Promise.all(promises);
  }
}
```

### Cache Manager (Orchestration)

```typescript
class CacheManager {
  constructor(
    private l1: L1Cache,
    private l2: L2Cache,
    private l3: L3Cache,
    private l4: L4Cache
  ) {}

  async get(key: string): Promise<any> {
    // Try L1 (fastest)
    let value = this.l1.get(key);
    if (value) {
      metrics.recordCacheHit('L1');
      return value;
    }

    // Try L2
    value = await this.l2.get(key);
    if (value) {
      metrics.recordCacheHit('L2');
      this.l1.set(key, value, 15000); // Repopulate L1
      return value;
    }

    // Try L3
    value = this.l3.get(key);
    if (value) {
      metrics.recordCacheHit('L3');
      this.l1.set(key, value, 15000);
      await this.l2.set(key, value, 60);
      return value;
    }

    // Try L4
    value = this.l4.read(key);
    if (value) {
      metrics.recordCacheHit('L4');
      this.l1.set(key, value, 5000);
      await this.l2.set(key, value, 30);
      return value;
    }

    // Cache miss
    metrics.recordCacheMiss();
    return null;
  }

  async set(
    key: string,
    value: any,
    ttl_l1: number = 15000,
    ttl_l2: number = 60,
    ttl_l3: number = 3600
  ) {
    this.l1.set(key, value, ttl_l1);
    await this.l2.set(key, value, ttl_l2);
    this.l3.set(key, value, ttl_l3);
  }

  // Periodic sync to L4 (fallback)
  async syncToL4(dataMap: Map<string, any>) {
    await this.l4.writeAllCachesAsync(dataMap);
  }
}
```

---

## Circuit Breaker Pattern

### State Machine

```
            ┌─────────────────────┐
            │      CLOSED         │ (Normal operation)
            │ Requests pass       │
            │ Failures tracked    │
            └──────────┬──────────┘
                       │
          Failure count > threshold
          (e.g., 5 failures in 30s)
                       │
                       ▼
            ┌─────────────────────┐
            │       OPEN          │ (Service failing)
            │ Requests rejected   │ Timeout: 30s
            │ Return cached data  │
            └──────────┬──────────┘
                       │
            Timeout expires
                       │
                       ▼
            ┌─────────────────────┐
            │   HALF_OPEN         │ (Testing)
            │ One request allowed │ Timeout: 10s
            │ If succeeds→CLOSED  │
            │ If fails→OPEN       │
            └─────────────────────┘
```

### Implementation (Opossum Library)

```typescript
import CircuitBreaker from 'opossum';

interface CircuitBreakerConfig {
  timeout: number;           // ms before timeout
  errorThresholdPercentage: number; // 50
  resetTimeout: number;      // ms before half-open
  name: string;
}

class APICircuitBreaker {
  private breakers: Map<string, CircuitBreaker> = new Map();

  createBreaker(
    apiName: string,
    fn: (...args: any[]) => Promise<any>,
    config: CircuitBreakerConfig
  ) {
    const breaker = new CircuitBreaker(fn, {
      timeout: config.timeout,
      errorThresholdPercentage: config.errorThresholdPercentage,
      resetTimeout: config.resetTimeout,
      name: config.name,
    });

    // Event handlers
    breaker.on('open', () => {
      logger.warn(`[CircuitBreaker] ${apiName} opened`, {
        timestamp: new Date().toISOString(),
      });
      metrics.recordCircuitBreakerOpen(apiName);
    });

    breaker.on('halfOpen', () => {
      logger.info(`[CircuitBreaker] ${apiName} half-open`, {
        timestamp: new Date().toISOString(),
      });
    });

    breaker.on('close', () => {
      logger.info(`[CircuitBreaker] ${apiName} closed`, {
        timestamp: new Date().toISOString(),
      });
      metrics.recordCircuitBreakerClose(apiName);
    });

    breaker.fallback(() => {
      logger.warn(`[CircuitBreaker] ${apiName} fallback activated`);
      return null; // Return null to trigger cache fallback
    });

    this.breakers.set(apiName, breaker);
    return breaker;
  }

  async execute(
    apiName: string,
    fn: (...args: any[]) => Promise<any>,
    ...args: any[]
  ) {
    const breaker = this.breakers.get(apiName);
    if (!breaker) {
      return fn(...args);
    }

    try {
      return await breaker.fire(...args);
    } catch (error) {
      logger.error(`[CircuitBreaker] ${apiName} execution failed`, {
        error: error instanceof Error ? error.message : String(error),
      });
      throw error;
    }
  }

  getStatus(apiName: string): string {
    const breaker = this.breakers.get(apiName);
    return breaker ? breaker.opened ? 'OPEN' : 'CLOSED' : 'UNKNOWN';
  }
}

// Usage
const kalshiBreaker = new APICircuitBreaker();
kalshiBreaker.createBreaker(
  'kalshi',
  fetchKalshiData,
  {
    timeout: 10000,
    errorThresholdPercentage: 50,
    resetTimeout: 30000,
    name: 'Kalshi API',
  }
);
```

---

## Real-Time Streaming

### Option 1: WebSocket (Bidirectional)

**Best for:** Browser dashboards, real-time updates, low latency requirement

```typescript
import { WebSocketServer, WebSocket } from 'ws';
import { Server as HTTPServer } from 'http';

class WebSocketManager {
  private wss: WebSocketServer;
  private subscriptions: Map<string, Set<WebSocket>> = new Map();
  private clients: Map<WebSocket, ClientSession> = new Map();

  constructor(httpServer: HTTPServer) {
    this.wss = new WebSocketServer({ server: httpServer });
    this.setupConnections();
  }

  private setupConnections() {
    this.wss.on('connection', (ws: WebSocket) => {
      const clientId = generateUUID();
      const session: ClientSession = {
        id: clientId,
        subscriptions: new Set(),
        connectedAt: Date.now(),
      };

      this.clients.set(ws, session);

      ws.on('message', (data: string) => {
        try {
          const message = JSON.parse(data);
          this.handleClientMessage(ws, message);
        } catch (error) {
          ws.send(
            JSON.stringify({
              type: 'error',
              message: 'Invalid JSON',
            })
          );
        }
      });

      ws.on('close', () => {
        const session = this.clients.get(ws);
        if (session) {
          // Cleanup subscriptions
          session.subscriptions.forEach((sub) => {
            const subscribers = this.subscriptions.get(sub);
            if (subscribers) {
              subscribers.delete(ws);
            }
          });
          this.clients.delete(ws);
        }
      });

      ws.on('error', (error) => {
        logger.error('WebSocket error', { error, clientId });
      });
    });
  }

  private handleClientMessage(ws: WebSocket, message: any) {
    const { type, channel } = message;

    if (type === 'subscribe') {
      const session = this.clients.get(ws);
      if (session) {
        session.subscriptions.add(channel);
        if (!this.subscriptions.has(channel)) {
          this.subscriptions.set(channel, new Set());
        }
        this.subscriptions.get(channel)!.add(ws);

        // Send confirmation
        ws.send(
          JSON.stringify({
            type: 'subscribed',
            channel,
            timestamp: new Date().toISOString(),
          })
        );
      }
    } else if (type === 'unsubscribe') {
      const session = this.clients.get(ws);
      if (session) {
        session.subscriptions.delete(channel);
        this.subscriptions.get(channel)?.delete(ws);
      }
    }
  }

  broadcast(channel: string, data: any) {
    const subscribers = this.subscriptions.get(channel);
    if (!subscribers) return;

    const message = JSON.stringify({
      type: 'data',
      channel,
      data,
      timestamp: new Date().toISOString(),
    });

    const deadClients: WebSocket[] = [];

    subscribers.forEach((ws) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(message);
      } else {
        deadClients.push(ws);
      }
    });

    // Cleanup dead clients
    deadClients.forEach((ws) => {
      const session = this.clients.get(ws);
      if (session) {
        session.subscriptions.forEach((ch) => {
          this.subscriptions.get(ch)?.delete(ws);
        });
        this.clients.delete(ws);
      }
    });
  }

  async broadcastAggregatedData(data: NormalizedFinancialData) {
    this.broadcast('financial-data', {
      source: data.source,
      asset: data.asset,
      prices: data.prices,
      analysis: data.analysis,
      timestamp: data.timestamp,
    });
  }

  getClientCount(): number {
    return this.clients.size;
  }

  getSubscriberCount(channel: string): number {
    return this.subscriptions.get(channel)?.size || 0;
  }
}

// Express setup
import express from 'express';
import { createServer } from 'http';

const app = express();
const httpServer = createServer(app);
const wsManager = new WebSocketManager(httpServer);

// Emit updates to all subscribers
setInterval(async () => {
  const data = await aggregatedDataService.getLatest();
  if (data) {
    wsManager.broadcastAggregatedData(data);
  }
}, 500); // 2Hz update rate

httpServer.listen(3000, () => {
  console.log('Server with WebSocket listening on port 3000');
});
```

### Option 2: Server-Sent Events (Unidirectional, SSE)

**Best for:** Simpler deployments, firewall-friendly, HTTP/1.1 compatible

```typescript
import express, { Request, Response } from 'express';

class SSEManager {
  private clients: Map<string, Response> = new Map();
  private subscriptions: Map<string, Set<string>> = new Map();

  registerClient(
    clientId: string,
    channels: string[],
    res: Response
  ) {
    // Set SSE headers
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('Access-Control-Allow-Origin', '*');

    // Send initial connection message
    this.sendSSE(res, {
      type: 'connected',
      clientId,
      timestamp: new Date().toISOString(),
    });

    this.clients.set(clientId, res);

    // Subscribe to channels
    channels.forEach((channel) => {
      if (!this.subscriptions.has(channel)) {
        this.subscriptions.set(channel, new Set());
      }
      this.subscriptions.get(channel)!.add(clientId);
    });

    // Handle client disconnect
    res.on('close', () => {
      this.clients.delete(clientId);
      channels.forEach((channel) => {
        this.subscriptions.get(channel)?.delete(clientId);
      });
      logger.info(`SSE client ${clientId} disconnected`);
    });

    res.on('error', (error) => {
      logger.error(`SSE error for ${clientId}`, { error });
      this.clients.delete(clientId);
    });
  }

  private sendSSE(res: Response, data: any) {
    const event = JSON.stringify(data);
    res.write(`data: ${event}\n\n`);
  }

  broadcast(channel: string, data: any) {
    const subscribers = this.subscriptions.get(channel);
    if (!subscribers) return;

    const payload = {
      type: 'data',
      channel,
      data,
      timestamp: new Date().toISOString(),
    };

    const deadClients: string[] = [];

    subscribers.forEach((clientId) => {
      const res = this.clients.get(clientId);
      if (res && !res.writableEnded) {
        this.sendSSE(res, payload);
      } else {
        deadClients.push(clientId);
      }
    });

    deadClients.forEach((clientId) => {
      this.clients.delete(clientId);
      this.subscriptions.get(channel)?.delete(clientId);
    });
  }

  getClientCount(): number {
    return this.clients.size;
  }
}

// Express routes
const app = express();
const sseManager = new SSEManager();

app.get('/events', (req: Request, res: Response) => {
  const clientId = `client_${Date.now()}_${Math.random().toString(36)}`;
  const channels = (req.query.channels as string)?.split(',') || ['financial-data'];

  sseManager.registerClient(clientId, channels, res);
});

// Broadcast aggregated data every 500ms
setInterval(async () => {
  const data = await aggregatedDataService.getLatest();
  if (data) {
    sseManager.broadcast('financial-data', {
      source: data.source,
      asset: data.asset,
      prices: data.prices,
      analysis: data.analysis,
    });
  }
}, 500);

export { app, sseManager };
```

---

## Database Design

### SQLite Schema

```sql
-- Core data storage
CREATE TABLE IF NOT EXISTS raw_api_responses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  api_endpoint TEXT NOT NULL,
  request_id TEXT,
  response_json TEXT NOT NULL,
  response_status INTEGER,
  fetch_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  ttl_seconds INTEGER DEFAULT 3600,
  INDEX idx_source_timestamp (source, fetch_timestamp)
);

-- Normalized financial data
CREATE TABLE IF NOT EXISTS normalized_data (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data_id TEXT UNIQUE NOT NULL,
  source TEXT NOT NULL,
  ticker TEXT,
  asset_type TEXT,
  normalized_json TEXT NOT NULL,
  cache_tier TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME,
  INDEX idx_source_ticker (source, ticker),
  INDEX idx_created (created_at)
);

-- P&L Snapshots
CREATE TABLE IF NOT EXISTS pnl_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_date DATE NOT NULL,
  snapshot_time DATETIME NOT NULL,
  agent_id TEXT,
  aggregated_json TEXT NOT NULL,
  kalshi_data_json TEXT,
  anthropic_analysis_json TEXT,
  john_metrics_json TEXT,
  metadata_json TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_date_agent (snapshot_date, agent_id),
  INDEX idx_agent (agent_id),
  INDEX idx_snapshot_time (snapshot_time)
);

-- Timestamps for tracking data freshness
CREATE TABLE IF NOT EXISTS data_freshness (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL UNIQUE,
  last_successful_fetch DATETIME,
  last_failed_fetch DATETIME,
  consecutive_failures INTEGER DEFAULT 0,
  circuit_breaker_state TEXT DEFAULT 'CLOSED',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_source (source)
);

-- Audit log for debugging
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL,
  source TEXT,
  agent_id TEXT,
  details_json TEXT,
  error_message TEXT,
  logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_event_type (event_type),
  INDEX idx_logged_at (logged_at)
);

-- Cache invalidation triggers
CREATE TRIGGER IF NOT EXISTS expire_old_cache
AFTER INSERT ON normalized_data
WHEN NEW.expires_at IS NOT NULL
BEGIN
  DELETE FROM normalized_data 
  WHERE expires_at < CURRENT_TIMESTAMP;
END;

-- Aggregate functions for reporting
CREATE VIEW IF NOT EXISTS daily_snapshots AS
SELECT 
  snapshot_date,
  agent_id,
  COUNT(*) as snapshot_count,
  MIN(snapshot_time) as first_snapshot,
  MAX(snapshot_time) as last_snapshot
FROM pnl_snapshots
GROUP BY snapshot_date, agent_id;
```

### Data Insertion Example

```typescript
interface DatabaseService {
  db: Database;

  // Insert raw API response
  insertRawResponse(
    source: string,
    endpoint: string,
    responseJson: any,
    status: number,
    ttl_s: number = 3600
  ) {
    const stmt = this.db.prepare(`
      INSERT INTO raw_api_responses 
      (source, api_endpoint, response_json, response_status, ttl_seconds)
      VALUES (?, ?, ?, ?, ?)
    `);

    stmt.run(
      source,
      endpoint,
      JSON.stringify(responseJson),
      status,
      ttl_s
    );
  }

  // Insert normalized data
  insertNormalizedData(
    dataId: string,
    source: string,
    normalized: NormalizedFinancialData,
    cacheTier: string,
    ttl_s: number = 3600
  ) {
    const expires_at = new Date(Date.now() + ttl_s * 1000);
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO normalized_data 
      (data_id, source, ticker, asset_type, normalized_json, cache_tier, expires_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      dataId,
      source,
      normalized.asset?.ticker || null,
      normalized.asset?.type || null,
      JSON.stringify(normalized),
      cacheTier,
      expires_at.toISOString()
    );
  }

  // Save P&L snapshot
  savePnLSnapshot(
    aggregatedData: AggregatedData,
    components: {
      kalshi?: any;
      anthropic?: any;
      john?: any;
    },
    agent_id?: string
  ) {
    const now = new Date();
    const stmt = this.db.prepare(`
      INSERT INTO pnl_snapshots 
      (snapshot_date, snapshot_time, agent_id, aggregated_json, 
       kalshi_data_json, anthropic_analysis_json, john_metrics_json, metadata_json)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      now.toISOString().split('T')[0],
      now.toISOString(),
      agent_id || null,
      JSON.stringify(aggregatedData),
      components.kalshi ? JSON.stringify(components.kalshi) : null,
      components.anthropic ? JSON.stringify(components.anthropic) : null,
      components.john ? JSON.stringify(components.john) : null,
      JSON.stringify({
        sources: Object.keys(components),
        timestamp: now.toISOString(),
        version: '1.0',
      })
    );
  }

  // Query snapshots for a date range
  getPnLSnapshots(
    startDate: string,
    endDate: string,
    agent_id?: string
  ): any[] {
    const query = `
      SELECT * FROM pnl_snapshots
      WHERE snapshot_date >= ? AND snapshot_date <= ?
      ${agent_id ? 'AND agent_id = ?' : ''}
      ORDER BY snapshot_time DESC
    `;

    const stmt = this.db.prepare(query);
    const params = agent_id
      ? [startDate, endDate, agent_id]
      : [startDate, endDate];

    return stmt.all(...params) as any[];
  }

  // Log audit event
  logAuditEvent(
    eventType: string,
    source?: string,
    details?: any,
    error?: Error
  ) {
    const stmt = this.db.prepare(`
      INSERT INTO audit_log 
      (event_type, source, details_json, error_message)
      VALUES (?, ?, ?, ?)
    `);

    stmt.run(
      eventType,
      source || null,
      details ? JSON.stringify(details) : null,
      error ? error.message : null
    );
  }
}
```

---

## Error Handling Strategy

### Error Classification

```typescript
enum ErrorSeverity {
  CRITICAL = 'critical',   // System unavailable
  HIGH = 'high',          // API unreachable, data loss risk
  MEDIUM = 'medium',      // Degraded performance
  LOW = 'low',           // Minor data inconsistency
}

enum ErrorCategory {
  NETWORK = 'network',        // Connection, timeout
  AUTHENTICATION = 'auth',    // API key, token
  DATA = 'data',             // Parsing, validation
  RATE_LIMIT = 'rate_limit', // 429 Too Many Requests
  SERVICE = 'service',       // 5xx, service down
  CIRCUIT_BREAKER = 'circuit_breaker',
  DATABASE = 'database',
}

interface ErrorContext {
  category: ErrorCategory;
  severity: ErrorSeverity;
  timestamp: string;
  requestId: string;
  source: string;
  statusCode?: number;
  message: string;
  retryable: boolean;
  fallbackAvailable: boolean;
}
```

### Error Handling Middleware

```typescript
class APIClient {
  async fetchWithRetry<T>(
    url: string,
    options: any,
    maxRetries: number = 3,
    timeout: number = 10000
  ): Promise<T> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(
          () => controller.abort(),
          timeout
        );

        const response = await axios({
          url,
          ...options,
          signal: controller.signal,
          timeout, // Axios also supports timeout
        });

        clearTimeout(timeoutId);

        if (!response.data) {
          throw new Error('Empty response from API');
        }

        return response.data as T;
      } catch (error) {
        clearTimeout(timeoutId);
        lastError = error as Error;

        const context = this.classifyError(error, url);

        logger.warn(`[Fetch] Attempt ${attempt + 1}/${maxRetries + 1} failed`, {
          ...context,
          retrying: attempt < maxRetries,
        });

        // Don't retry non-retryable errors
        if (!context.retryable) {
          throw error;
        }

        // Exponential backoff
        if (attempt < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
          await new Promise((resolve) => setTimeout(resolve, delay));
        }
      }
    }

    throw lastError || new Error('Max retries exceeded');
  }

  private classifyError(error: any, source: string): ErrorContext {
    let category = ErrorCategory.NETWORK;
    let severity = ErrorSeverity.MEDIUM;
    let retryable = true;
    let statusCode: number | undefined;

    if (error.response) {
      statusCode = error.response.status;

      if (statusCode === 401 || statusCode === 403) {
        category = ErrorCategory.AUTHENTICATION;
        severity = ErrorSeverity.CRITICAL;
        retryable = false;
      } else if (statusCode === 429) {
        category = ErrorCategory.RATE_LIMIT;
        severity = ErrorSeverity.MEDIUM;
        retryable = true; // Retry with backoff
      } else if (statusCode >= 500) {
        category = ErrorCategory.SERVICE;
        severity = ErrorSeverity.HIGH;
        retryable = true;
      } else if (statusCode >= 400) {
        category = ErrorCategory.DATA;
        severity = ErrorSeverity.MEDIUM;
        retryable = false;
      }
    } else if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
      category = ErrorCategory.NETWORK;
      severity = ErrorSeverity.HIGH;
      retryable = true;
    } else if (error.message?.includes('JSON')) {
      category = ErrorCategory.DATA;
      severity = ErrorSeverity.LOW;
      retryable = false;
    }

    return {
      category,
      severity,
      timestamp: new Date().toISOString(),
      requestId: generateRequestId(),
      source,
      statusCode,
      message: error.message || String(error),
      retryable,
      fallbackAvailable: true, // Assume cache available
    };
  }
}
```

### Global Error Handler

```typescript
app.use(
  (
    error: Error,
    req: express.Request,
    res: express.Response,
    next: express.NextFunction
  ) => {
    const context: ErrorContext = {
      category: ErrorCategory.SERVICE,
      severity: ErrorSeverity.HIGH,
      timestamp: new Date().toISOString(),
      requestId: req.get('x-request-id') || generateRequestId(),
      source: req.path,
      message: error.message,
      retryable: true,
      fallbackAvailable: true,
    };

    logger.error('[Global Error Handler]', context);

    // Attempt cache fallback
    const cached = cacheManager.get(`fallback:${req.path}`);
    if (cached) {
      return res.status(200).json({
        data: cached,
        status: 'cached',
        warning: 'Service temporarily unavailable, serving cached data',
        requestId: context.requestId,
      });
    }

    // Return error response
    res.status(503).json({
      error: {
        message: 'Service temporarily unavailable',
        category: context.category,
        requestId: context.requestId,
      },
    });
  }
);
```

---

## Code Examples

### Complete Aggregation Service

```typescript
import axios from 'axios';
import CircuitBreaker from 'opossum';
import { WebSocketManager } from './websocket';
import { CacheManager } from './cache';

class DataAggregatorService {
  private kalshiBreaker: CircuitBreaker;
  private anthropicBreaker: CircuitBreaker;
  private johnBreaker: CircuitBreaker;
  private lastAggregatedData: AggregatedData | null = null;

  constructor(
    private cacheManager: CacheManager,
    private wsManager: WebSocketManager,
    private dbService: DatabaseService
  ) {
    this.initializeCircuitBreakers();
    this.startAggregationLoop();
  }

  private initializeCircuitBreakers() {
    this.kalshiBreaker = new CircuitBreaker(
      this.fetchKalshiData.bind(this),
      {
        timeout: 10000,
        errorThresholdPercentage: 50,
        resetTimeout: 30000,
        name: 'Kalshi API',
      }
    );

    this.anthropicBreaker = new CircuitBreaker(
      this.fetchAnthropicAnalysis.bind(this),
      {
        timeout: 15000,
        errorThresholdPercentage: 50,
        resetTimeout: 30000,
        name: 'Anthropic API',
      }
    );

    this.johnBreaker = new CircuitBreaker(
      this.fetchJohnMetrics.bind(this),
      {
        timeout: 5000,
        errorThresholdPercentage: 50,
        resetTimeout: 15000,
        name: 'John System',
      }
    );

    [this.kalshiBreaker, this.anthropicBreaker, this.johnBreaker].forEach(
      (breaker) => {
        breaker.on('open', () => this.onCircuitBreakerOpen(breaker.name));
        breaker.on('close', () => this.onCircuitBreakerClose(breaker.name));
      }
    );
  }

  async aggregateData(): Promise<AggregatedData> {
    const requestId = generateRequestId();
    const startTime = Date.now();

    logger.info('[Aggregator] Starting parallel API fetch', { requestId });

    // Parallel fetch with fallback
    const [kalshi, anthropic, john] = await Promise.allSettled([
      this.kalshiBreaker.fire().catch(() => null),
      this.anthropicBreaker.fire().catch(() => null),
      this.johnBreaker.fire().catch(() => null),
    ]);

    const duration = Date.now() - startTime;

    // Handle settled results
    const kalshiData = kalshi.status === 'fulfilled' ? kalshi.value : null;
    const anthropicData = anthropic.status === 'fulfilled' ? anthropic.value : null;
    const johnData = john.status === 'fulfilled' ? john.value : null;

    // Attempt cache fallback for failures
    const kalshiCached =
      !kalshiData &&
      (await this.cacheManager.get('latest:kalshi:data'));
    const anthropicCached =
      !anthropicData &&
      (await this.cacheManager.get('latest:anthropic:analysis'));
    const johnCached =
      !johnData &&
      (await this.cacheManager.get('latest:john:metrics'));

    // Combine into aggregated view
    const aggregated: AggregatedData = {
      timestamp: new Date().toISOString(),
      requestId,
      components: {
        kalshi: {
          data: kalshiData || kalshiCached,
          status: kalshiData ? 'live' : kalshiCached ? 'cached' : 'unavailable',
          source_reliability:
            kalshiData && !kalshiCached ? 0.95 : kalshiCached ? 0.7 : 0,
        },
        anthropic: {
          data: anthropicData || anthropicCached,
          status: anthropicData ? 'live' : anthropicCached ? 'cached' : 'unavailable',
          source_reliability:
            anthropicData && !anthropicCached ? 0.9 : anthropicCached ? 0.6 : 0,
        },
        john: {
          data: johnData || johnCached,
          status: johnData ? 'live' : johnCached ? 'cached' : 'unavailable',
          source_reliability:
            johnData && !johnCached ? 0.98 : johnCached ? 0.8 : 0,
        },
      },
      metadata: {
        fetch_duration_ms: duration,
        availability_score: this.calculateAvailabilityScore({
          kalshi: !!kalshiData,
          anthropic: !!anthropicData,
          john: !!johnData,
        }),
        circuit_breaker_states: {
          kalshi: this.getCircuitBreakerState(this.kalshiBreaker),
          anthropic: this.getCircuitBreakerState(this.anthropicBreaker),
          john: this.getCircuitBreakerState(this.johnBreaker),
        },
      },
    };

    // Store in cache & DB
    await Promise.all([
      this.cacheManager.set(
        'latest:aggregated',
        aggregated,
        15000, // L1: 15s
        60, // L2: 60s
        3600 // L3: 1h
      ),
      this.dbService.savePnLSnapshot(aggregated, {
        kalshi: kalshiData,
        anthropic: anthropicData,
        john: johnData,
      }),
    ]);

    this.lastAggregatedData = aggregated;

    logger.info('[Aggregator] Aggregation complete', {
      requestId,
      duration,
      availability: aggregated.metadata.availability_score,
    });

    return aggregated;
  }

  private async fetchKalshiData(): Promise<NormalizedFinancialData[]> {
    try {
      const response = await axios.get('https://api.kalshi.com/v2/markets', {
        params: { limit: 10, status: 'open' },
        timeout: 8000,
      });

      const normalized = response.data.data.map((market: any) =>
        normalizeKalshi(market)
      );

      await this.cacheManager.set(
        'latest:kalshi:data',
        normalized,
        10000,
        30,
        900
      );

      this.dbService.insertRawResponse(
        'kalshi',
        '/v2/markets',
        response.data,
        200,
        900
      );

      return normalized;
    } catch (error) {
      logger.error('[Kalshi] Fetch failed', { error });
      this.dbService.logAuditEvent(
        'API_ERROR',
        'kalshi',
        {},
        error instanceof Error ? error : new Error(String(error))
      );
      throw error;
    }
  }

  private async fetchAnthropicAnalysis(): Promise<NormalizedFinancialData> {
    try {
      // First, get aggregated data to analyze
      const currentData = this.lastAggregatedData || (await this.aggregateData());

      const prompt = `
        Analyze the following market data and provide:
        1. Sentiment (bullish/neutral/bearish)
        2. Key risk factors
        3. Confidence level in analysis
        
        Data: ${JSON.stringify(currentData.components.kalshi.data)}
      `;

      const response = await axios.post(
        'https://api.anthropic.com/v1/messages',
        {
          model: 'claude-3.5-sonnet',
          max_tokens: 1024,
          stream: false,
          messages: [
            {
              role: 'user',
              content: prompt,
            },
          ],
        },
        {
          headers: {
            'x-api-key': process.env.ANTHROPIC_API_KEY,
          },
          timeout: 12000,
        }
      );

      const normalized = normalizeAnthropicInsight(response.data);

      await this.cacheManager.set(
        'latest:anthropic:analysis',
        normalized,
        15000,
        120,
        1800
      );

      return normalized;
    } catch (error) {
      logger.error('[Anthropic] Fetch failed', { error });
      throw error;
    }
  }

  private async fetchJohnMetrics(): Promise<NormalizedFinancialData> {
    try {
      const response = await axios.get(
        'https://internal.northstar.local/api/john/metrics',
        {
          headers: {
            Authorization: `Bearer ${process.env.JOHN_API_TOKEN}`,
          },
          timeout: 4000,
        }
      );

      const normalized = normalizeJohnMetrics(response.data);

      await this.cacheManager.set(
        'latest:john:metrics',
        normalized,
        20000,
        30,
        300
      );

      return normalized;
    } catch (error) {
      logger.error('[John] Fetch failed', { error });
      throw error;
    }
  }

  private startAggregationLoop() {
    // Poll every 500ms (2Hz) for real-time feel
    setInterval(async () => {
      try {
        const data = await this.aggregateData();
        this.wsManager.broadcastAggregatedData(data);
      } catch (error) {
        logger.error('[Aggregation Loop] Error', { error });
      }
    }, 500);
  }

  private onCircuitBreakerOpen(name: string) {
    logger.warn(`[CircuitBreaker] ${name} opened`, {
      timestamp: new Date().toISOString(),
    });
    this.dbService.logAuditEvent('CIRCUIT_BREAKER_OPEN', name);
  }

  private onCircuitBreakerClose(name: string) {
    logger.info(`[CircuitBreaker] ${name} closed`, {
      timestamp: new Date().toISOString(),
    });
    this.dbService.logAuditEvent('CIRCUIT_BREAKER_CLOSE', name);
  }

  private getCircuitBreakerState(breaker: CircuitBreaker): string {
    return breaker.opened ? 'OPEN' : 'CLOSED';
  }

  private calculateAvailabilityScore(sources: {
    kalshi: boolean;
    anthropic: boolean;
    john: boolean;
  }): number {
    const available = Object.values(sources).filter(Boolean).length;
    return available / 3; // 0.0 to 1.0
  }
}

export { DataAggregatorService };
```

---

## Deployment Guide

### Docker Setup

**Dockerfile:**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

CMD ["node", "dist/index.js"]
```

**docker-compose.yml:**
```yaml
version: '3.9'

services:
  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      NODE_ENV: production
      REDIS_URL: redis://redis:6379
      DATABASE_URL: sqlite:///data/northstar.db
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      JOHN_API_TOKEN: ${JOHN_API_TOKEN}
      KALSHI_API_KEY: ${KALSHI_API_KEY}
    depends_on:
      - redis
    volumes:
      - ./data:/app/data
      - ./cache:/app/cache
    restart: always

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: always

volumes:
  redis-data:
```

### Environment Variables

```bash
# .env.production
NODE_ENV=production
PORT=3000

# APIs
ANTHROPIC_API_KEY=sk-...
JOHN_API_TOKEN=bearer_...
KALSHI_API_KEY=key_...

# Cache
REDIS_URL=redis://redis:6379
CACHE_L1_TTL_MS=15000
CACHE_L2_TTL_S=60
CACHE_L3_TTL_S=3600

# Database
DATABASE_URL=sqlite:///data/northstar.db
DATABASE_MAX_CONNECTIONS=10

# Logging
LOG_LEVEL=info
LOG_FORMAT=json

# Circuit Breakers
CB_TIMEOUT_MS=10000
CB_ERROR_THRESHOLD=50
CB_RESET_TIMEOUT_MS=30000

# Aggregation
AGGREGATION_INTERVAL_MS=500
AVAILABILITY_THRESHOLD=0.5
```

### Monitoring & Observability

```typescript
import pino from 'pino';
import prometheus from 'prom-client';

// Structured logging
const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  transport: {
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'SYS:standard',
      ignore: 'pid,hostname',
    },
  },
});

// Prometheus metrics
const httpRequestDuration = new prometheus.Histogram({
  name: 'http_request_duration_ms',
  help: 'Duration of HTTP requests in ms',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.1, 5, 15, 50, 100, 500],
});

const cacheHitRate = new prometheus.Counter({
  name: 'cache_hits_total',
  help: 'Total cache hits',
  labelNames: ['tier'],
});

const apiCallDuration = new prometheus.Histogram({
  name: 'api_call_duration_ms',
  help: 'Duration of API calls in ms',
  labelNames: ['api', 'status'],
  buckets: [10, 100, 500, 1000, 5000, 10000, 30000],
});

const circuitBreakerState = new prometheus.Gauge({
  name: 'circuit_breaker_state',
  help: 'Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)',
  labelNames: ['api'],
});

// Metrics endpoint
app.get('/metrics', (req, res) => {
  res.set('Content-Type', prometheus.register.contentType);
  res.end(prometheus.register.metrics());
});

export { logger, httpRequestDuration, cacheHitRate, apiCallDuration };
```

### Scaling Considerations

1. **Horizontal Scaling:**
   - Stateless Express instances behind load balancer (nginx, HAProxy)
   - Redis for distributed cache (single instance or cluster)
   - SQLite → PostgreSQL for horizontal scalability (if needed)

2. **Performance Tuning:**
   - Increase aggregation frequency (500ms currently) based on load
   - Adjust cache TTLs per performance SLOs
   - Consider read replicas for reporting queries

3. **High Availability:**
   - Run 3+ API instances with health checks
   - Redis Sentinel for automatic failover
   - Database backups every 6 hours

---

## Summary

This architecture provides:

✅ **Resilience**: Circuit breaker + 4-tier fallback caching  
✅ **Performance**: Parallel API calls, <1s aggregate latency  
✅ **Real-Time**: WebSocket + SSE streaming, 500ms updates  
✅ **Observability**: Structured logging, Prometheus metrics  
✅ **Scalability**: Stateless services, Redis distribution  
✅ **Durability**: SQLite snapshots, audit trails  

Ready for production deployment with Docker + Kubernetes support.
