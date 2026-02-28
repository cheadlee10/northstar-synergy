# Real-Time P&L Dashboard — Deployment Guide

## Overview
Complete setup for NorthStar Synergy's real-time P&L dashboard with live updates from Kalshi, Anthropic, and John's revenue.

**Stack:**
- Backend: Node.js (Express + WebSocket)
- Database: SQLite (with WAL mode)
- Cache: Redis (optional but recommended)
- Frontend: React
- Protocols: WebSocket → SSE → HTTP Polling (graceful fallback)

---

## PHASE 1: SETUP (30 minutes)

### 1.1 Install Dependencies

```bash
# Backend
npm install express ws redis sqlite3 cors dotenv

# Frontend (if starting fresh)
npx create-react-app northstar-dashboard
cd northstar-dashboard
npm install axios
```

### 1.2 Project Structure

```
northstar-dashboard/
├── server.js                    # Main backend entry
├── lib/
│   ├── APIAggregator.js        # Data fetching
│   ├── P&LEngine.js            # Calculations
│   ├── CacheManager.js         # Redis layer
│   └── DatabaseLayer.js        # SQLite
├── routes/
│   ├── api.js                  # REST endpoints
│   └── ws.js                   # WebSocket handlers
├── src/
│   └── components/
│       └── P&LDashboard.jsx    # React component
├── data/
│   └── northstar.db            # SQLite database
├── .env                        # API keys & config
└── package.json
```

### 1.3 Environment Configuration

Create `.env`:
```env
# API Keys
KALSHI_API_KEY=your_kalshi_key
KALSHI_API_SECRET=your_kalshi_secret
ANTHROPIC_API_KEY=your_anthropic_key
JOHN_API_BASE_URL=https://api.john-domain.com

# Server
PORT=8080
NODE_ENV=production

# Redis (optional)
REDIS_URL=redis://localhost:6379
USE_REDIS=true

# Database
DB_PATH=./data/northstar.db

# Aggregation
AGGREGATION_INTERVAL_MS=10000  # 10 seconds
```

### 1.4 Install & Start Redis (Optional but Recommended)

**macOS:**
```bash
brew install redis
brew services start redis
# Test: redis-cli ping → PONG
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
redis-cli ping
```

**Windows (Docker):**
```bash
docker run -d -p 6379:6379 redis:latest
```

---

## PHASE 2: BACKEND SETUP (45 minutes)

### 2.1 Create `server.js`

```javascript
const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const redis = require('redis');
require('dotenv').config();

const APIAggregator = require('./lib/APIAggregator');
const P&LEngine = require('./lib/P&LEngine');
const CacheManager = require('./lib/CacheManager');
const DatabaseLayer = require('./lib/DatabaseLayer');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Middleware
app.use(express.json());
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET,POST');
  next();
});

// Initialize components
const db = new DatabaseLayer(process.env.DB_PATH);
const redisClient = redis.createClient(process.env.REDIS_URL);
const cache = new CacheManager(redisClient, console);

const aggregator = new APIAggregator({
  kalshi: {
    baseURL: 'https://api.kalshi.com',
    headers: {
      'Authorization': `Bearer ${process.env.KALSHI_API_KEY}`,
      'User-Agent': 'NorthStar-Dashboard/1.0'
    }
  },
  anthropic: {
    baseURL: 'https://api.anthropic.com',
    headers: {
      'Authorization': `Bearer ${process.env.ANTHROPIC_API_KEY}`,
      'Content-Type': 'application/json'
    }
  },
  john: {
    baseURL: process.env.JOHN_API_BASE_URL
  },
  cache,
  logger: console
});

const engine = new P&LEngine(db, cache, console);

// =====================================================
// WebSocket Handlers
// =====================================================

let connectedClients = new Set();

wss.on('connection', (ws) => {
  connectedClients.add(ws);
  console.log(`[WS] Client connected (${connectedClients.size} total)`);

  // Send current P&L immediately
  (async () => {
    try {
      const current = await cache.get('pnl:current');
      if (current) {
        ws.send(JSON.stringify({
          type: 'snapshot',
          data: current,
          timestamp: Date.now()
        }));
      }
    } catch (err) {
      console.error('[WS] Initial snapshot error:', err);
    }
  })();

  ws.on('message', (data) => {
    try {
      const msg = JSON.parse(data);
      if (msg.type === 'ping') {
        ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
      }
    } catch (e) {
      console.error('[WS] Message parse error:', e);
    }
  });

  ws.on('close', () => {
    connectedClients.delete(ws);
    console.log(`[WS] Client disconnected (${connectedClients.size} total)`);
  });

  ws.on('error', (err) => {
    console.error('[WS] Error:', err.message);
    connectedClients.delete(ws);
  });
});

function broadcastUpdate(message) {
  const payload = JSON.stringify(message);
  let count = 0;

  connectedClients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(payload);
      count++;
    }
  });

  if (count > 0) {
    console.log(`[BROADCAST] Sent to ${count}/${connectedClients.size} clients`);
  }
}

// =====================================================
// REST API Endpoints
// =====================================================

// GET /api/pnl/current - Latest P&L snapshot
app.get('/api/pnl/current', async (req, res) => {
  try {
    const pnl = await cache.get('pnl:current');
    if (!pnl) {
      return res.status(404).json({ error: 'No P&L data available' });
    }
    res.json(pnl);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/pnl/stream - Server-Sent Events fallback
app.get('/api/pnl/stream', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive'
  });

  // Send current snapshot
  (async () => {
    try {
      const current = await cache.get('pnl:current');
      if (current) {
        res.write(`data: ${JSON.stringify(current)}\n\n`);
      }
    } catch (err) {
      console.error('[SSE] Error:', err);
    }
  })();

  // Send updates every 15 seconds
  const interval = setInterval(() => {
    (async () => {
      try {
        const current = await cache.get('pnl:current');
        if (current) {
          res.write(`data: ${JSON.stringify(current)}\n\n`);
        }
      } catch (err) {
        console.error('[SSE] Error:', err);
      }
    })();
  }, 15000);

  req.on('close', () => {
    clearInterval(interval);
    res.end();
  });
});

// GET /api/pnl/history - Historical data for charts
app.get('/api/pnl/history', async (req, res) => {
  try {
    const { from, to, resolution = '1m' } = req.query;
    const fromTime = parseInt(from) || Date.now() - 3600000; // Default 1h
    const toTime = parseInt(to) || Date.now();

    const history = await engine.getHistoricalP&L(fromTime, toTime, resolution);
    res.json(history);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/health - Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: Date.now(),
    connectedClients: connectedClients.size,
    cacheStats: cache.getStats(),
    uptime: process.uptime()
  });
});

// =====================================================
// Main Aggregation Loop
// =====================================================

let lastP&L = null;

async function runAggregationLoop() {
  const interval = parseInt(process.env.AGGREGATION_INTERVAL_MS) || 10000;

  setInterval(async () => {
    try {
      console.log('[LOOP] Starting aggregation cycle...');

      // 1. Fetch all data sources
      const data = await aggregator.fetchAllData();
      
      if (data.errors.length > 0) {
        console.warn('[LOOP] Some API errors:', data.errors);
      }

      // 2. Compute P&L
      const { snapshot, delta, prevSnapshot } = await engine.computeP&LSnapshot(
        data.trades,
        data.costs,
        data.revenue
      );

      // 3. Persist to database
      await db.insertSnapshot(snapshot);

      // 4. Update cache
      await cache.set('pnl:current', snapshot, { ttl: 30 });

      // 5. Broadcast if changed
      if (delta && Math.abs(delta.netP&LDelta) > 0.01) {
        broadcastUpdate({
          type: 'delta',
          data: delta,
          timestamp: snapshot.timestamp
        });
      }

      lastP&L = snapshot;
      console.log(`[LOOP] ✓ P&L: $${snapshot.netP&L.toFixed(2)}`);

    } catch (err) {
      console.error('[LOOP] Aggregation error:', err);
    }
  }, interval);

  console.log(`[LOOP] Started (${interval}ms intervals)`);
}

// =====================================================
// Start Server
// =====================================================

const PORT = process.env.PORT || 8080;

server.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════╗
║  NorthStar P&L Dashboard               ║
║  WebSocket: ws://localhost:${PORT}     ║
║  REST API:  http://localhost:${PORT}   ║
╚════════════════════════════════════════╝
  `);

  runAggregationLoop();
});

process.on('SIGTERM', () => {
  console.log('Shutting down...');
  server.close(() => {
    db.close();
    process.exit(0);
  });
});
```

### 2.2 Copy Implementation Files

Copy these files from `research/` to `lib/`:
- `APIAggregator` → `lib/APIAggregator.js`
- `P&LEngine` → `lib/P&LEngine.js`
- `CacheManager` → `lib/CacheManager.js`
- `DatabaseLayer` → `lib/DatabaseLayer.js`

(The implementation_patterns.js file contains all four classes)

---

## PHASE 3: FRONTEND SETUP (30 minutes)

### 3.1 Copy React Component

Copy `P&LDashboard.jsx` to `src/components/P&LDashboard.jsx`

### 3.2 Create CSS

`src/components/P&LDashboard.css`:
```css
.pnl-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.pnl-dashboard.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.dashboard-header h1 {
  font-size: 28px;
  margin: 0;
}

.connection-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f3f4f6;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}

.connection-badge .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.connection-badge .dot.green { background: #22c55e; }
.connection-badge .dot.red { background: #ef4444; }
.connection-badge .dot.yellow { background: #eab308; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.pnl-main {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  margin-bottom: 30px;
}

.pnl-value {
  font-size: 56px;
  font-weight: 700;
  margin-bottom: 10px;
  font-family: 'Courier New', monospace;
}

.pnl-label {
  font-size: 14px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.pnl-updated {
  margin-top: 15px;
  font-size: 12px;
  color: #9ca3af;
}

.pnl-breakdown {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.breakdown-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
}

.breakdown-card .card-title {
  font-size: 12px;
  color: #6b7280;
  text-transform: uppercase;
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.breakdown-card .card-value {
  font-size: 24px;
  font-weight: 600;
  font-family: 'Courier New', monospace;
  margin-bottom: 8px;
}

.breakdown-card .card-meta {
  font-size: 12px;
  color: #9ca3af;
}

.pnl-history {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.history-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 15px;
}

.sparkline {
  width: 100%;
  height: 100px;
  display: block;
}

.offline-notice {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  text-align: center;
}

@media (max-width: 768px) {
  .pnl-value {
    font-size: 36px;
  }
  
  .pnl-breakdown {
    grid-template-columns: 1fr;
  }
}
```

### 3.3 Update `src/App.js`

```javascript
import P&LDashboard from './components/P&LDashboard';

function App() {
  return (
    <div className="App">
      <P&LDashboard wsUrl="ws://localhost:8080" />
    </div>
  );
}

export default App;
```

---

## PHASE 4: TESTING & VALIDATION (45 minutes)

### 4.1 Start Services

```bash
# Terminal 1: Backend
node server.js

# Terminal 2: Frontend (dev server)
npm start

# Terminal 3: Monitor Redis (optional)
redis-cli monitor
```

### 4.2 Validation Checklist

- [ ] **Backend starts** without errors
  ```
  curl http://localhost:8080/api/health
  # Should return: { "status": "ok", ... }
  ```

- [ ] **WebSocket connects**
  - Open http://localhost:3000 (React dev server)
  - Browser DevTools → Network → WS
  - Should see "connected" badge

- [ ] **Data flows**
  - Monitor database: `sqlite3 data/northstar.db "SELECT * FROM pnl_snapshots DESC LIMIT 1;"`
  - Should see records appearing

- [ ] **Cache works**
  - Check Redis: `redis-cli GET pnl:current`
  - Should see P&L data (JSON)

- [ ] **REST API works**
  ```bash
  curl http://localhost:8080/api/pnl/current
  curl "http://localhost:8080/api/pnl/history?from=1234567890&to=1234567900"
  ```

- [ ] **Fallback mechanisms**
  - Kill backend: Frontend should switch to SSE/polling
  - Restart backend: Frontend should reconnect

### 4.3 Load Testing (Optional)

```bash
# Install artillery
npm install -g artillery

# Create test.yml
cat > test.yml << 'EOF'
config:
  target: "http://localhost:8080"
  phases:
    - duration: 60
      arrivalRate: 10

scenarios:
  - name: "Health Check"
    flow:
      - get:
          url: "/api/health"
EOF

artillery quick --count 100 --num 1000 test.yml
```

---

## PHASE 5: PRODUCTION DEPLOYMENT

### 5.1 Environment Variables

Use a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault):
```bash
export KALSHI_API_KEY=xxx
export ANTHROPIC_API_KEY=xxx
export JOHN_API_BASE_URL=xxx
export REDIS_URL=redis://prod-redis:6379
export DB_PATH=/var/lib/northstar/northstar.db
export NODE_ENV=production
export PORT=8080
```

### 5.2 Docker Deployment (Recommended)

**Dockerfile:**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 8080

CMD ["node", "server.js"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  backend:
    build: .
    ports:
      - "8080:8080"
    environment:
      - NODE_ENV=production
      - REDIS_URL=redis://redis:6379
      - DB_PATH=/data/northstar.db
      - KALSHI_API_KEY=${KALSHI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - redis
    volumes:
      - ./data:/data

  frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8080

volumes:
  redis-data:
```

**Deploy:**
```bash
docker-compose up -d
```

### 5.3 Monitoring & Alerts

```javascript
// Add to server.js
const StatsD = require('node-statsd');
const client = new StatsD();

// Track metrics
setInterval(() => {
  client.gauge('pnl.connected_clients', connectedClients.size);
  client.gauge('pnl.cache_hit_rate', cache.getStats().hitRate);
  client.gauge('pnl.uptime', process.uptime());
}, 10000);

// Alert on slow aggregation
const startTime = Date.now();
// ... aggregation code ...
const latency = Date.now() - startTime;
if (latency > 1000) {
  console.error(`⚠️  Slow aggregation: ${latency}ms`);
  client.increment('pnl.slow_aggregations');
}
```

### 5.4 Backup Strategy

```bash
# Daily database backup
0 2 * * * sqlite3 /data/northstar.db ".backup /backups/northstar-$(date +\%Y\%m\%d).db"

# Monitor disk space
df -h /data

# Retention: Keep last 30 days
find /backups -name "northstar-*.db" -mtime +30 -delete
```

---

## TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| WebSocket connection fails | Check firewall/proxy, ensure /api/pnl/current works, try SSE |
| No data appearing | Verify API credentials, check aggregator logs, test APIs manually |
| High latency (>1s) | Check database query times, add indexes, scale Redis |
| Cache not working | Verify Redis is running, check REDIS_URL env var |
| Database growing too fast | Implement data retention (delete >30d old snapshots) |
| Memory leak | Monitor with `node --inspect` and Chrome DevTools |

---

## MONITORING DASHBOARD

Monitor key metrics:
```javascript
// GET /api/health returns:
{
  "status": "ok",
  "timestamp": 1708893456789,
  "connectedClients": 23,
  "cacheStats": {
    "hitRate": "94.23%",
    "hits": 1523,
    "misses": 93,
    "total": 1616
  },
  "uptime": 86400.123
}
```

Use Grafana + Prometheus for long-term monitoring:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'northstar-pnl'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
```

---

## COST ESTIMATE (Monthly)

| Component | Cost | Notes |
|-----------|------|-------|
| AWS t3.micro (server) | $8 | 1 vCPU, 1GB RAM |
| RDS Redis | $15 | 256MB cache |
| S3 backups | $5 | 30 days retention |
| Data transfer | $5 | Egress fees |
| **Total** | **~$33/month** | For 100-500 concurrent users |

---

## FINAL CHECKLIST

- [ ] Environment variables configured
- [ ] Redis running
- [ ] Database initialized (indexes created)
- [ ] Backend server started
- [ ] Frontend client running
- [ ] WebSocket connection confirmed
- [ ] P&L data flowing to database
- [ ] Cache populated
- [ ] REST APIs responding
- [ ] Fallback mechanisms tested
- [ ] Monitoring configured
- [ ] Backups scheduled

**Congratulations! Your real-time P&L dashboard is live.** 🚀
