# Real-Time P&L Streaming Backend

A production-ready Node.js + Express backend for streaming real-time P&L (Profit & Loss) metrics with WebSocket support and SSE fallback.

## 📋 Features

✅ **Real-Time Streaming**
- WebSocket server using Socket.io (primary transport)
- Server-Sent Events (SSE) fallback when WebSocket unavailable
- 5-second update interval for P&L metrics
- Automatic reconnection with exponential backoff

✅ **Multi-Source Data Aggregation**
- **Kalshi**: Trading balance, positions, and P&L
- **Anthropic API**: Daily spending/API costs
- **John's Revenue**: Invoiced and collected revenue
- Automatic data validation and error handling

✅ **Advanced Caching (4-Tier)**
1. **Process Memory**: Fastest, in-memory cache (LRU eviction)
2. **Redis**: Distributed cache for multi-instance deployments
3. **SQLite**: Persistent cache with TTL support
4. **Fallback**: Graceful degradation when all caches fail

✅ **Resilience & Fault Tolerance**
- Circuit breaker pattern for external API calls
- Automatic service recovery
- Per-service failure tracking
- Graceful degradation with sensible defaults

✅ **Enterprise Ready**
- Comprehensive error handling
- Request logging and monitoring
- Health check endpoints
- Rate limiting middleware
- CORS and CSRF protection

## 🚀 Quick Start

### Installation

```bash
cd pnl-backend
npm install
```

### Environment Setup

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Run Server

```bash
# Development (with auto-reload)
npm run dev

# Production
npm start
```

Server will start on `http://localhost:3000`

## 🔌 API Endpoints

### REST API

#### Health Check
```http
GET /health
```
Returns server health status and service connectivity.

#### Current P&L Snapshot
```http
GET /api/pnl/current
Headers: x-api-key: your-api-key
```
Response:
```json
{
  "success": true,
  "data": {
    "totalRevenue": 1500.00,
    "totalExpenses": 125.50,
    "netPnL": 1374.50,
    "grossMargin": 91.63,
    "dailyTrend": 5.25,
    "components": {
      "kalshi": { "balance": 10000, "positions": 3, "pnl": 500 },
      "anthropic": { "dailySpend": 5.25 },
      "johns": { "invoiced": 2000, "collected": 1000 }
    },
    "timestamp": "2024-02-25T22:24:00.000Z"
  }
}
```

#### P&L History
```http
GET /api/pnl/history?limit=100
Headers: x-api-key: your-api-key
```

#### Component Breakdown
```http
GET /api/pnl/breakdown
Headers: x-api-key: your-api-key
```

#### Circuit Breaker Status
```http
GET /api/circuit-breaker/status
```

#### Cache Statistics
```http
GET /api/cache/stats
```

### WebSocket (Socket.io)

#### Connection
```javascript
const socket = io('http://localhost:3000', {
  auth: { apiKey: 'your-api-key' }
});

socket.on('connect_success', (data) => {
  console.log('Connected:', data);
});
```

#### Subscribe to P&L Updates
```javascript
socket.emit('subscribe_pnl');

socket.on('pnl_update', (data) => {
  console.log('P&L Update:', data.data);
});
```

#### Subscribe to Component Updates
```javascript
socket.emit('subscribe_components');

socket.on('components_update', (data) => {
  console.log('Components:', data.data);
});
```

#### Error Handling
```javascript
socket.on('error', (error) => {
  console.error('Socket error:', error);
});

socket.on('stream_error', (error) => {
  console.error('Stream error:', error);
});
```

## 🛠️ Configuration

### Environment Variables

```bash
# Server
PORT=3000
NODE_ENV=development
LOG_LEVEL=info

# API Keys & Security
API_KEY=your-secret-key
CORS_ORIGIN=*
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# External APIs
KALSHI_API_URL=https://api.kalshi.com/v1
KALSHI_API_KEY=your-kalshi-key
ANTHROPIC_API_KEY=your-anthropic-key
JOHNS_REVENUE_URL=http://localhost:5000/api/revenue

# Cache
REDIS_URL=redis://localhost:6379
CACHE_TTL=300000

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RESET_TIMEOUT=60000
```

## 📊 Data Models

### P&L Metrics
```typescript
{
  totalRevenue: number;        // Sum of revenue from all sources
  totalExpenses: number;       // Sum of expenses
  netPnL: number;              // totalRevenue - totalExpenses
  grossMargin: number;         // (Revenue - Expenses) / Revenue * 100
  dailyTrend: number;          // % change from previous snapshot
  components: {
    kalshi: { balance, positions, pnl };
    anthropic: { dailySpend };
    johns: { invoiced, collected };
  };
  timestamp: string;           // ISO 8601 UTC timestamp
  calculatedAt: number;        // Milliseconds since epoch
}
```

## 🔄 Data Flow

```
External APIs
     ↓
Circuit Breaker (handles failures)
     ↓
Data Aggregator (validates & combines)
     ↓
Cache Manager (4-tier caching)
     ↓
Real-time Stream (5s interval)
     ↓
Socket.io (WebSocket + SSE fallback)
     ↓
Client (Zustand store)
```

## 🛡️ Error Handling

### Circuit Breaker States

- **CLOSED**: Normal operation, requests go through
- **OPEN**: Service failing, requests use fallback immediately
- **HALF_OPEN**: Testing recovery, allowing single request through

### Graceful Degradation

When external APIs fail:
1. Circuit breaker opens to prevent cascading failures
2. Cached data is served if available
3. Sensible defaults returned if cache unavailable
4. Error is logged and reported

## 📈 Client Integration (React)

### Setup Zustand Store
```javascript
import { usePnLSocket, usePnLMetrics } from './pnlStore';

function App() {
  const { initSocket } = usePnLSocket();
  const metrics = usePnLMetrics();

  useEffect(() => {
    initSocket();
  }, [initSocket]);

  return <div>P&L: ${metrics.netPnL}</div>;
}
```

### Use Custom Hooks
```javascript
// Individual metric hooks
import {
  usePnLMetrics,
  usePnLComponents,
  usePnLConnection,
  useLastUpdate
} from './pnlStore';
```

## 🔐 Security

- API key validation on all endpoints
- CORS protection configured
- Helmet.js for HTTP headers
- Rate limiting middleware
- Error details hidden in production
- Socket.io authentication

## 📝 Logging

Logs are written to:
- **Console**: Real-time development feedback
- **`logs/combined.log`**: All events
- **`logs/error.log`**: Errors only

## 🧪 Testing

```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage
```

## 📦 Project Structure

```
pnl-backend/
├── server.js                 # Main Express + Socket.io server
├── lib/
│   ├── aggregator.js        # Data aggregation logic
│   ├── cache.js             # 4-tier cache manager
│   ├── circuitBreaker.js    # Circuit breaker pattern
│   ├── logger.js            # Logging setup
│   └── utils.js             # Utility functions
├── middleware/
│   ├── errorHandler.js      # Error handling
│   └── auth.js              # Authentication/authorization
├── client/
│   ├── pnlStore.js          # Zustand store
│   └── components/          # React components
├── data/
│   └── cache.db             # SQLite cache (auto-created)
├── logs/
│   ├── combined.log         # All logs
│   └── error.log            # Error logs
├── package.json
├── .env.example
└── README.md
```

## 🚨 Troubleshooting

### WebSocket Connection Failed
- Check CORS_ORIGIN environment variable
- Verify API key is correct
- Check browser console for specific errors

### Cache Not Working
- Verify Redis is running (if enabled)
- Check SQLite file permissions
- Review logs for cache errors

### Circuit Breaker Open
- Check external API status
- Review circuit breaker logs
- Wait for reset timeout or manually reset

### Missing Data
- Verify API credentials in .env
- Check external API URLs are correct
- Review application logs for specific errors

## 🤝 Integration with Flask/Python Backend

To integrate with a Python backend:

1. **Set John's Revenue URL** in `.env`:
   ```bash
   JOHNS_REVENUE_URL=http://your-python-backend:5000/api/revenue
   ```

2. **Implement Python endpoint** returning:
   ```json
   {
     "invoiced": 5000.00,
     "collected": 3500.00
   }
   ```

3. **Restart Node server** for changes to take effect

## 📞 Support

For issues or questions, check:
1. Application logs in `logs/` directory
2. Circuit breaker status at `/api/circuit-breaker/status`
3. Cache stats at `/api/cache/stats`
4. Health check at `/health`

## 📄 License

MIT

---

**Ready to deploy!** Complete backend with production-grade error handling, caching, and real-time streaming. ✨
