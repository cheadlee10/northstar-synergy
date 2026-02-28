---
name: data-source-integration
description: Integrate external data sources (Kalshi API, Anthropic, revenue tracking) into P&L dashboards. Use when connecting live trading data, API costs, or business revenue to real-time dashboards. Includes API clients, error handling, caching, rate limiting, and authentication patterns.
---

# Data Source Integration Skill

Production patterns for integrating live financial data sources with reliability and performance.

## Kalshi API Integration

### Client Setup
```javascript
class KalshiClient {
  constructor(apiKey, baseUrl = 'https://api.kalshi.com') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.rateLimit = { calls: 0, resetAt: Date.now() };
  }

  async request(endpoint, options = {}) {
    await this.checkRateLimit();
    
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    return response.json();
  }

  async getBalance() {
    return this.request('/users/me/balance');
  }

  async getPositions() {
    return this.request('/users/me/positions');
  }

  async getTrades() {
    return this.request('/users/me/trades');
  }

  async checkRateLimit() {
    const now = Date.now();
    if (now > this.rateLimit.resetAt) {
      this.rateLimit = { calls: 0, resetAt: now + 60000 };
    }
    
    if (this.rateLimit.calls >= 100) {  // 100 calls/min
      const waitTime = this.rateLimit.resetAt - now;
      await new Promise(resolve => setTimeout(resolve, waitTime));
      this.rateLimit = { calls: 0, resetAt: Date.now() + 60000 };
    }
    
    this.rateLimit.calls++;
  }
}
```

### Data Normalization
```javascript
function normalizeKalshiData(raw) {
  return {
    balance: raw.balance_cents / 100,
    positions: raw.positions.map(p => ({
      symbol: p.ticker,
      quantity: p.quantity,
      entryPrice: p.cost_basis_cents / 100 / p.quantity,
      currentPrice: p.market_price_cents / 100,
      pnl: (p.market_price_cents - p.cost_basis_cents) / 100,
      pnlPercent: ((p.market_price_cents / p.cost_basis_cents) - 1) * 100
    })),
    totalPnL: raw.realized_pnl_cents / 100
  };
}
```

## Anthropic API Costs

### Cost Tracking
```javascript
class AnthropicCostTracker {
  constructor(db) {
    this.db = db;
  }

  async logCall(model, inputTokens, outputTokens) {
    const cost = this.calculateCost(model, inputTokens, outputTokens);
    
    await this.db.insert('api_costs', {
      timestamp: new Date(),
      provider: 'anthropic',
      model,
      input_tokens: inputTokens,
      output_tokens: outputTokens,
      cost_usd: cost
    });

    return cost;
  }

  calculateCost(model, inputTokens, outputTokens) {
    const rates = {
      'claude-opus-4-6': { input: 0.015, output: 0.075 },
      'claude-sonnet-4': { input: 0.003, output: 0.015 },
      'claude-haiku-4': { input: 0.00080, output: 0.004 }
    };

    const rate = rates[model] || { input: 0, output: 0 };
    return (inputTokens / 1000000 * rate.input) + 
           (outputTokens / 1000000 * rate.output);
  }

  async getDailyCost(date) {
    return this.db.query(`
      SELECT SUM(cost_usd) as total, model
      FROM api_costs
      WHERE DATE(timestamp) = ? AND provider = 'anthropic'
      GROUP BY model
    `, [date]);
  }
}
```

### Integration with LLM Router
```javascript
const tracker = new AnthropicCostTracker(db);

// Hook into every API call
const originalCall = anthropic.messages.create;
anthropic.messages.create = async function(params) {
  const response = await originalCall.call(this, params);
  
  await tracker.logCall(
    params.model,
    response.usage.input_tokens,
    response.usage.output_tokens
  );
  
  return response;
};
```

## John's Revenue Integration

### Job Tracking
```javascript
class JobTracker {
  constructor(db) {
    this.db = db;
  }

  async createJob(data) {
    return this.db.insert('jobs', {
      created_at: new Date(),
      title: data.title,
      client: data.client,
      estimated_value: data.estimatedValue,
      status: 'pending',  // pending, in_progress, completed, invoiced, paid
      ...data
    });
  }

  async updateJobStatus(jobId, status) {
    return this.db.update('jobs', 
      { status },
      { id: jobId }
    );
  }

  async createInvoice(jobId, amount) {
    const invoice = await this.db.insert('invoices', {
      job_id: jobId,
      amount,
      status: 'pending',
      due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
    });

    // Update job status
    await this.updateJobStatus(jobId, 'invoiced');
    
    return invoice;
  }

  async getRevenueSummary(days = 30) {
    const since = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    
    return this.db.query(`
      SELECT 
        SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) as collected,
        SUM(CASE WHEN status = 'invoiced' THEN amount ELSE 0 END) as outstanding,
        COUNT(*) as jobs_completed
      FROM jobs
      WHERE completed_at >= ? AND status != 'pending'
    `, [since]);
  }
}
```

## Caching & Fallback

### Resilient Data Fetch
```javascript
class ResilientDataFetcher {
  constructor(cache, db) {
    this.cache = cache;
    this.db = db;
  }

  async fetch(key, fetcher, options = {}) {
    const { ttl = 300, fallbackToDb = true } = options;

    // L1: Redis cache
    let data = await this.cache.get(key);
    if (data) return JSON.parse(data);

    // L2: API call
    try {
      data = await fetcher();
      await this.cache.setex(key, ttl, JSON.stringify(data));
      return data;
    } catch (error) {
      // L3: Database fallback
      if (fallbackToDb) {
        data = await this.db.query(`
          SELECT data FROM cache WHERE key = ?
          ORDER BY created_at DESC LIMIT 1
        `, [key]);
        
        if (data) return JSON.parse(data[0].data);
      }

      throw error;
    }
  }
}
```

## Error Handling & Retry

### Exponential Backoff
```javascript
async function fetchWithRetry(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      const delay = Math.pow(2, i) * 1000;  // 1s, 2s, 4s
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

// Usage
const balance = await fetchWithRetry(
  () => kalshi.getBalance(),
  3
);
```

## Monitoring & Alerting

### Data Freshness Check
```javascript
async function checkDataFreshness() {
  const checks = {
    kalshi: await getKalshiFreshness(),
    anthropic: await getAnthropicFreshness(),
    jobs: await getJobsFreshness()
  };

  for (const [source, age] of Object.entries(checks)) {
    if (age > 300000) {  // >5 min old
      alert(`${source} data stale: ${age}ms old`);
    }
  }

  return checks;
}

async function getKalshiFreshness() {
  const lastUpdate = await db.query(`
    SELECT MAX(timestamp) FROM kalshi_snapshots
  `);
  return Date.now() - lastUpdate[0].timestamp;
}
```

## Rate Limiting

### Token Bucket Algorithm
```javascript
class RateLimiter {
  constructor(capacity = 100, refillRate = 100) {
    this.capacity = capacity;
    this.tokens = capacity;
    this.refillRate = refillRate;  // tokens per minute
    this.lastRefill = Date.now();
  }

  async acquire() {
    this.refillTokens();
    
    if (this.tokens < 1) {
      const waitTime = (60000 / this.refillRate) * (1 - this.tokens);
      await new Promise(resolve => setTimeout(resolve, waitTime));
      this.refillTokens();
    }

    this.tokens--;
  }

  refillTokens() {
    const now = Date.now();
    const elapsed = now - this.lastRefill;
    const refill = (elapsed / 60000) * this.refillRate;
    
    this.tokens = Math.min(this.capacity, this.tokens + refill);
    this.lastRefill = now;
  }
}
```

## Testing Data Integrations

```javascript
test('kalshi integration fetches balance', async () => {
  const mockResponse = { balance_cents: 1000000 };
  fetch.mockResolvedValueOnce(
    new Response(JSON.stringify(mockResponse))
  );

  const client = new KalshiClient('test-key');
  const balance = await client.getBalance();
  
  expect(balance).toEqual(mockResponse);
});

test('anthropic cost tracking logs calls', async () => {
  const tracker = new AnthropicCostTracker(mockDb);
  await tracker.logCall('claude-opus-4-6', 1000, 500);

  expect(mockDb.insert).toHaveBeenCalledWith('api_costs', expect.objectContaining({
    model: 'claude-opus-4-6',
    input_tokens: 1000
  }));
});
```
