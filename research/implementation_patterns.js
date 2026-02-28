/**
 * REAL-TIME FINANCIAL DASHBOARD - IMPLEMENTATION PATTERNS
 * Ready-to-use code snippets for NorthStar Synergy P&L pipeline
 * 
 * Components:
 * 1. API Aggregator (multi-source data collection)
 * 2. P&L Engine (calculation & normalization)
 * 3. Cache Manager (Redis)
 * 4. WebSocket Server
 * 5. Database Layer (SQLite)
 */

// ============================================================================
// 1. API AGGREGATOR - Fetch from Kalshi, Anthropic, John's APIs
// ============================================================================

class APIAggregator {
  constructor(config) {
    this.kalshiApi = config.kalshi; // API client
    this.anthropicApi = config.anthropic;
    this.johnApi = config.john;
    this.cache = config.cache;
    this.logger = config.logger;
  }

  /**
   * Fetch all data sources in parallel with timeout & retry
   */
  async fetchAllData() {
    const timeout = 5000; // 5 second timeout per source

    const results = await Promise.allSettled([
      this.fetchKalshiTrades(timeout),
      this.fetchAnthropicCosts(timeout),
      this.fetchJohnRevenue(timeout)
    ]);

    return {
      trades: results[0].status === 'fulfilled' ? results[0].value : [],
      costs: results[1].status === 'fulfilled' ? results[1].value : [],
      revenue: results[2].status === 'fulfilled' ? results[2].value : [],
      errors: results
        .map((r, i) => r.status === 'rejected' ? { source: ['kalshi', 'anthropic', 'john'][i], error: r.reason } : null)
        .filter(Boolean)
    };
  }

  /**
   * KALSHI: Fetch open positions & recent trades
   * API: GET /v2/markets/{ticker}/orders
   */
  async fetchKalshiTrades(timeout) {
    try {
      const startTime = Date.now();

      // Attempt cache first
      const cached = await this.cache.get('kalshi:trades:live');
      if (cached && (Date.now() - cached.fetchedAt < 30000)) { // 30s cache
        return cached.data;
      }

      // Live fetch
      const [positions, recentOrders] = await Promise.all([
        this.withTimeout(
          this.kalshiApi.get('/v2/portfolio/positions'),
          timeout
        ),
        this.withTimeout(
          this.kalshiApi.get('/v2/orders', { status: 'active,filled' }),
          timeout
        )
      ]);

      const trades = [];

      // Open positions
      for (const position of positions.data) {
        trades.push({
          id: position.id,
          symbol: position.market_ticker,
          side: position.side, // 'long' or 'short'
          quantity: position.quantity,
          entryPrice: position.average_fill_price,
          currentPrice: position.market_price, // or live tick
          status: 'open',
          realizedP&L: 0,
          unrealizedP&L: (position.market_price - position.average_fill_price) * position.quantity,
          timestamp: Date.now(),
          source: 'kalshi'
        });
      }

      // Closed orders (last 24h for realized P&L)
      for (const order of recentOrders.data) {
        if (order.status === 'filled') {
          trades.push({
            id: order.id,
            symbol: order.market_ticker,
            side: order.side,
            quantity: order.quantity,
            entryPrice: order.average_fill_price,
            currentPrice: order.average_fill_price,
            status: 'closed',
            realizedP&L: order.pnl, // Provided by Kalshi
            timestamp: new Date(order.filled_at).getTime(),
            source: 'kalshi'
          });
        }
      }

      const latency = Date.now() - startTime;
      this.logger.info(`Kalshi API: ${trades.length} trades fetched in ${latency}ms`);

      // Cache result
      await this.cache.set('kalshi:trades:live', {
        data: trades,
        fetchedAt: Date.now()
      }, { ttl: 30 });

      return trades;
    } catch (err) {
      this.logger.error(`Kalshi fetch error: ${err.message}`);
      throw err;
    }
  }

  /**
   * ANTHROPIC: Fetch API costs (updated daily/monthly)
   * Note: Anthropic API doesn't expose real-time usage, so we track manually
   * API: GET /v1/usage (if available) or manual billing
   */
  async fetchAnthropicCosts(timeout) {
    try {
      const startTime = Date.now();

      // Try cache first (costs don't change often)
      const cached = await this.cache.get('anthropic:costs');
      if (cached && (Date.now() - cached.fetchedAt < 3600000)) { // 1h cache
        return cached.data;
      }

      // Option 1: Fetch from dashboard API (if exposed)
      let costs = [];
      try {
        const response = await this.withTimeout(
          this.anthropicApi.get('/v1/usage/current_month'),
          timeout
        );
        costs = [{
          id: 'anthropic:current',
          month: new Date().toISOString().slice(0, 7), // YYYY-MM
          totalCost: response.data.total_cost,
          tokensUsed: response.data.input_tokens + response.data.output_tokens,
          timestamp: Date.now()
        }];
      } catch (e) {
        // Fallback: Use database of recorded costs
        costs = await this.cache.get('anthropic:costs:db') || [];
      }

      const latency = Date.now() - startTime;
      this.logger.info(`Anthropic costs: ${costs.length} entries in ${latency}ms`);

      await this.cache.set('anthropic:costs', {
        data: costs,
        fetchedAt: Date.now()
      }, { ttl: 3600 }); // 1h cache

      return costs;
    } catch (err) {
      this.logger.error(`Anthropic fetch error: ${err.message}`);
      throw err;
    }
  }

  /**
   * JOHN: Fetch revenue/deals (custom API or database)
   * Assume John has an API endpoint: GET /v1/deals
   */
  async fetchJohnRevenue(timeout) {
    try {
      const startTime = Date.now();

      // Cache with longer TTL (deals close infrequently)
      const cached = await this.cache.get('john:revenue');
      if (cached && (Date.now() - cached.fetchedAt < 300000)) { // 5m cache
        return cached.data;
      }

      const response = await this.withTimeout(
        this.johnApi.get('/v1/deals', { status: 'all' }),
        timeout
      );

      const revenue = response.data.map(deal => ({
        id: deal.id,
        dealName: deal.name,
        closedDate: deal.closed_date,
        revenue: deal.amount,
        status: deal.status, // 'recognized', 'pending', 'pipeline'
        timestamp: new Date(deal.closed_date).getTime(),
        source: 'john'
      }));

      const latency = Date.now() - startTime;
      this.logger.info(`John revenue: ${revenue.length} deals in ${latency}ms`);

      await this.cache.set('john:revenue', {
        data: revenue,
        fetchedAt: Date.now()
      }, { ttl: 300 }); // 5m cache

      return revenue;
    } catch (err) {
      this.logger.error(`John revenue fetch error: ${err.message}`);
      throw err;
    }
  }

  /**
   * Utility: Wrap promise with timeout
   */
  withTimeout(promise, timeoutMs) {
    return Promise.race([
      promise,
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error(`Timeout after ${timeoutMs}ms`)), timeoutMs)
      )
    ]);
  }
}

// ============================================================================
// 2. P&L ENGINE - Calculate, aggregate, normalize timestamps
// ============================================================================

class P&LEngine {
  constructor(db, cache, logger) {
    this.db = db;
    this.cache = cache;
    this.logger = logger;
  }

  /**
   * Main aggregation function
   * Input: Raw data from APIs
   * Output: P&L snapshot with breakdown
   */
  async computeP&LSnapshot(trades, costs, revenue) {
    const timestamp = Date.now();

    // Component 1: Kalshi P&L
    const kalshiP&L = this.calculateKalshiP&L(trades);

    // Component 2: Anthropic Costs
    const totalCosts = this.sumCosts(costs);

    // Component 3: John's Revenue
    const totalRevenue = this.sumRevenue(revenue);

    // Net P&L
    const netP&L = kalshiP&L + totalRevenue - totalCosts;

    // Current snapshot
    const snapshot = {
      timestamp,
      kalshiP&L,
      totalCosts,
      totalRevenue,
      netP&L,
      breakdown: {
        trades: kalshiP&L,
        costs: -totalCosts,
        revenue: totalRevenue
      },
      components: {
        openTradeCount: trades.filter(t => t.status === 'open').length,
        closedTradeCount: trades.filter(t => t.status === 'closed').length,
        recentDeals: revenue.filter(r => r.status === 'recognized').length
      },
      metadata: {
        dataPoints: trades.length + costs.length + revenue.length,
        computedAt: Date.now()
      }
    };

    // Fetch previous snapshot for delta calculation
    const prevSnapshot = await this.cache.get('pnl:current');

    // Calculate delta (what changed from last snapshot)
    let delta = null;
    if (prevSnapshot) {
      delta = {
        timestamp,
        netP&LDelta: netP&L - prevSnapshot.netP&L,
        kalshiDelta: kalshiP&L - prevSnapshot.kalshiP&L,
        costsDelta: totalCosts - prevSnapshot.totalCosts,
        revenueDelta: totalRevenue - prevSnapshot.totalRevenue,
        changePercent: ((netP&L - prevSnapshot.netP&L) / Math.abs(prevSnapshot.netP&L)) * 100 || 0
      };
    }

    return { snapshot, delta, prevSnapshot };
  }

  /**
   * Calculate total P&L from Kalshi trades
   */
  calculateKalshiP&L(trades) {
    return trades.reduce((sum, trade) => {
      const pnl = trade.status === 'open'
        ? trade.unrealizedP&L || 0
        : trade.realizedP&L || 0;
      return sum + pnl;
    }, 0);
  }

  /**
   * Sum all Anthropic costs (current month + YTD)
   */
  sumCosts(costs) {
    return costs.reduce((sum, cost) => sum + cost.totalCost, 0);
  }

  /**
   * Sum all John's revenue (recognized only, not pipeline)
   */
  sumRevenue(revenue) {
    return revenue
      .filter(r => r.status === 'recognized')
      .reduce((sum, r) => sum + r.revenue, 0);
  }

  /**
   * Normalize all timestamps to UTC
   */
  normalizeTimestamps(data) {
    return {
      kalshi: data.trades.map(t => ({
        ...t,
        timestamp: new Date(t.timestamp).getTime() // Ensure Unix ms
      })),
      anthropic: data.costs.map(c => ({
        ...c,
        timestamp: new Date(c.month + '-01T00:00:00Z').getTime()
      })),
      john: data.revenue.map(r => ({
        ...r,
        timestamp: new Date(r.closedDate + 'T00:00:00Z').getTime()
      }))
    };
  }

  /**
   * Get historical P&L for charts (1m, 5m, 1h aggregates)
   */
  async getHistoricalP&L(fromTime, toTime, resolution = '1m') {
    const cacheKey = `pnl:history:${resolution}:${fromTime}:${toTime}`;
    
    // Check cache first
    const cached = await this.cache.get(cacheKey);
    if (cached) return cached;

    // Query database
    const data = await this.db.query(`
      SELECT 
        timestamp,
        kalshi_pnl,
        total_costs,
        total_revenue,
        net_pnl
      FROM pnl_snapshots
      WHERE timestamp BETWEEN ? AND ?
      ORDER BY timestamp ASC
    `, [fromTime, toTime]);

    // Aggregate if needed (e.g., 1m → 5m)
    const aggregated = this.aggregateByResolution(data, resolution);

    // Cache result
    await this.cache.set(cacheKey, aggregated, { ttl: 300 });

    return aggregated;
  }

  aggregateByResolution(snapshots, resolution) {
    const bucketMap = new Map();
    const bucketSize = this.resolutionToMs(resolution);

    for (const snap of snapshots) {
      const bucket = Math.floor(snap.timestamp / bucketSize) * bucketSize;
      if (!bucketMap.has(bucket)) {
        bucketMap.set(bucket, { snapshots: [], sum: { netP&L: 0, kalshiP&L: 0, costs: 0, revenue: 0 } });
      }
      bucketMap.get(bucket).snapshots.push(snap);
      bucketMap.get(bucket).sum.netP&L += snap.net_pnl;
      bucketMap.get(bucket).sum.kalshiP&L += snap.kalshi_pnl;
      bucketMap.get(bucket).sum.costs += snap.total_costs;
      bucketMap.get(bucket).sum.revenue += snap.total_revenue;
    }

    const result = [];
    for (const [bucket, data] of bucketMap.entries()) {
      const count = data.snapshots.length;
      result.push({
        timestamp: bucket,
        netP&L: data.sum.netP&L / count,
        kalshiP&L: data.sum.kalshiP&L / count,
        costs: data.sum.costs / count,
        revenue: data.sum.revenue / count
      });
    }

    return result;
  }

  resolutionToMs(resolution) {
    const map = { '1m': 60000, '5m': 300000, '1h': 3600000 };
    return map[resolution] || 60000;
  }
}

// ============================================================================
// 3. CACHE MANAGER - Redis layer with TTL & invalidation
// ============================================================================

class CacheManager {
  constructor(redisClient, logger) {
    this.redis = redisClient;
    this.logger = logger;
    this.stats = { hits: 0, misses: 0 };
  }

  /**
   * Get with automatic miss tracking
   */
  async get(key) {
    try {
      const value = await this.redis.get(key);
      if (value) {
        this.stats.hits++;
        return JSON.parse(value);
      }
      this.stats.misses++;
      return null;
    } catch (err) {
      this.logger.error(`Cache get error: ${key}`, err);
      return null;
    }
  }

  /**
   * Set with TTL
   */
  async set(key, value, options = {}) {
    try {
      const ttl = options.ttl || 300; // Default 5m
      const serialized = JSON.stringify(value);
      await this.redis.setex(key, ttl, serialized);
    } catch (err) {
      this.logger.error(`Cache set error: ${key}`, err);
    }
  }

  /**
   * Invalidate on trade update
   */
  async invalidateOnTrade() {
    await Promise.all([
      this.redis.del('pnl:current'),
      this.redis.eval(`
        local keys = redis.call('KEYS', 'pnl:1m:*')
        for i = 1, #keys do
          redis.call('DEL', keys[i])
        end
      `, 0),
      this.redis.del('kalshi:trades:live')
    ]);
    this.logger.info('Cache invalidated: Trade update');
  }

  /**
   * Invalidate on cost update
   */
  async invalidateOnCost() {
    await this.redis.del('pnl:current');
    this.logger.info('Cache invalidated: Cost update');
  }

  /**
   * Get cache health stats
   */
  getStats() {
    const total = this.stats.hits + this.stats.misses;
    return {
      hitRate: total > 0 ? (this.stats.hits / total * 100).toFixed(2) + '%' : 'N/A',
      hits: this.stats.hits,
      misses: this.stats.misses,
      total
    };
  }
}

// ============================================================================
// 4. DATABASE LAYER - SQLite persistence
// ============================================================================

class DatabaseLayer {
  constructor(dbPath, logger) {
    const sqlite3 = require('sqlite3').verbose();
    this.db = new sqlite3.Database(dbPath);
    this.logger = logger;
    this.init();
  }

  init() {
    // Enable WAL mode for concurrent reads
    this.db.run('PRAGMA journal_mode = WAL');
    this.db.run('PRAGMA synchronous = NORMAL');
    this.db.run('PRAGMA cache_size = 10000');

    // Create tables
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS pnl_snapshots (
        timestamp INTEGER PRIMARY KEY,
        kalshi_pnl REAL,
        total_costs REAL,
        total_revenue REAL,
        net_pnl REAL,
        trade_count INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      CREATE INDEX IF NOT EXISTS idx_pnl_time 
        ON pnl_snapshots(timestamp DESC);

      CREATE TABLE IF NOT EXISTS kalshi_trades (
        id TEXT PRIMARY KEY,
        symbol TEXT,
        side TEXT,
        quantity INTEGER,
        entry_price REAL,
        current_price REAL,
        status TEXT,
        realized_pnl REAL,
        timestamp INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      CREATE INDEX IF NOT EXISTS idx_trades_time 
        ON kalshi_trades(timestamp DESC);

      CREATE TABLE IF NOT EXISTS anthropic_costs (
        id TEXT PRIMARY KEY,
        month TEXT,
        total_cost REAL,
        tokens_used INTEGER,
        timestamp INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      CREATE INDEX IF NOT EXISTS idx_costs_date 
        ON anthropic_costs(month DESC);

      CREATE TABLE IF NOT EXISTS john_revenue (
        id TEXT PRIMARY KEY,
        deal_name TEXT,
        closed_date TEXT,
        revenue REAL,
        status TEXT,
        timestamp INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      CREATE INDEX IF NOT EXISTS idx_revenue_date 
        ON john_revenue(closed_date DESC);
    `);
  }

  /**
   * Insert P&L snapshot
   */
  insertSnapshot(snapshot) {
    return new Promise((resolve, reject) => {
      this.db.run(`
        INSERT OR REPLACE INTO pnl_snapshots
        (timestamp, kalshi_pnl, total_costs, total_revenue, net_pnl, trade_count)
        VALUES (?, ?, ?, ?, ?, ?)
      `, [
        snapshot.timestamp,
        snapshot.kalshiP&L,
        snapshot.totalCosts,
        snapshot.totalRevenue,
        snapshot.netP&L,
        snapshot.components?.openTradeCount || 0
      ], function(err) {
        if (err) reject(err);
        else resolve(this.lastID);
      });
    });
  }

  /**
   * Get latest snapshot
   */
  getLatestSnapshot() {
    return new Promise((resolve, reject) => {
      this.db.get(`
        SELECT * FROM pnl_snapshots
        ORDER BY timestamp DESC
        LIMIT 1
      `, (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
  }

  /**
   * Query snapshots by time range
   */
  query(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.all(sql, params, (err, rows) => {
        if (err) reject(err);
        else resolve(rows || []);
      });
    });
  }

  close() {
    this.db.close();
  }
}

// ============================================================================
// 5. WEBSOCKET SERVER - Real-time broadcasting
// ============================================================================

class RealtimeServer {
  constructor(port = 8080) {
    const WebSocket = require('ws');
    const http = require('http');
    
    this.server = http.createServer();
    this.wss = new WebSocket.Server({ server: this.server });
    this.clients = new Set();
    this.port = port;
  }

  start(aggregator, aggregationInterval = 10000) {
    this.wss.on('connection', (ws) => {
      this.clients.add(ws);
      console.log(`✓ Client connected (${this.clients.size} total)`);

      // Send current snapshot immediately
      aggregator.getP&L().then(pnl => {
        if (pnl) {
          ws.send(JSON.stringify({
            type: 'snapshot',
            data: pnl,
            timestamp: Date.now()
          }));
        }
      }).catch(err => console.error('Snapshot send error:', err));

      ws.on('close', () => {
        this.clients.delete(ws);
        console.log(`✗ Client disconnected (${this.clients.size} total)`);
      });

      ws.on('error', (err) => {
        console.error('WebSocket error:', err.message);
        this.clients.delete(ws);
      });

      // Optional: Handle client messages
      ws.on('message', (data) => {
        try {
          const msg = JSON.parse(data);
          if (msg.type === 'ping') {
            ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
          }
        } catch (e) {
          console.error('Message parse error:', e);
        }
      });
    });

    // Broadcast P&L updates every N seconds
    setInterval(() => {
      aggregator.aggregateP&L().then(({ snapshot, delta }) => {
        if (delta) {
          this.broadcast({
            type: 'delta',
            data: delta,
            timestamp: snapshot.timestamp
          });
        }
      }).catch(err => console.error('Aggregation error:', err));
    }, aggregationInterval);

    this.server.listen(this.port, () => {
      console.log(`🚀 P&L WebSocket server: ws://localhost:${this.port}`);
    });
  }

  /**
   * Broadcast message to all connected clients
   */
  broadcast(message) {
    const payload = JSON.stringify(message);
    let count = 0;

    this.clients.forEach((client) => {
      if (client.readyState === 1) { // OPEN
        client.send(payload);
        count++;
      }
    });

    if (count > 0) {
      console.log(`📤 Broadcast to ${count}/${this.clients.size} clients`);
    }
  }

  close() {
    this.wss.close();
    this.server.close();
  }
}

// ============================================================================
// USAGE EXAMPLE
// ============================================================================

/*
const redis = require('redis');
const logger = console;

// Initialize components
const redisClient = redis.createClient();
const db = new DatabaseLayer('./northstar.db', logger);
const cache = new CacheManager(redisClient, logger);
const engine = new P&LEngine(db, cache, logger);

const aggregator = new APIAggregator({
  kalshi: kalshiClient,
  anthropic: anthropicClient,
  john: johnClient,
  cache,
  logger
});

// Main loop
async function run() {
  const server = new RealtimeServer(8080);

  setInterval(async () => {
    const data = await aggregator.fetchAllData();
    const { snapshot, delta } = await engine.computeP&LSnapshot(
      data.trades,
      data.costs,
      data.revenue
    );

    // Persist
    await db.insertSnapshot(snapshot);

    // Cache
    await cache.set('pnl:current', snapshot, { ttl: 30 });

    // Broadcast
    if (delta) {
      server.broadcast({ type: 'delta', data: delta });
    }
  }, 10000); // Every 10 seconds

  server.start(aggregator);
}

run().catch(console.error);
*/

module.exports = {
  APIAggregator,
  P&LEngine,
  CacheManager,
  DatabaseLayer,
  RealtimeServer
};
