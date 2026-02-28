# P&L Streaming Backend - API Reference

Complete API documentation for the real-time P&L streaming backend.

## 🔑 Authentication

All API requests (except `/health`) require authentication via API key.

### Methods

**1. Header-based (Recommended)**
```http
GET /api/pnl/current
X-API-Key: your-secret-key
```

**2. Query parameter**
```http
GET /api/pnl/current?apiKey=your-secret-key
```

**3. Socket.io auth**
```javascript
io('http://localhost:3000', {
  auth: { apiKey: 'your-secret-key' }
});
```

## 📡 REST Endpoints

### Health Check
```http
GET /health
```
No authentication required.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-02-25T22:24:00.000Z",
  "uptime": 3600.123,
  "environment": "production",
  "services": {
    "cache": "healthy",
    "aggregator": "running"
  }
}
```

### Get Current P&L
```http
GET /api/pnl/current
X-API-Key: your-secret-key
```

**Response:**
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
      "kalshi": {
        "balance": 10000.00,
        "positions": 3,
        "pnl": 500.00
      },
      "anthropic": {
        "dailySpend": 5.25
      },
      "johns": {
        "invoiced": 2000.00,
        "collected": 1000.00
      }
    },
    "timestamp": "2024-02-25T22:24:00.000Z",
    "calculatedAt": 1708887840000
  },
  "timestamp": "2024-02-25T22:24:00.000Z"
}
```

### Get P&L History
```http
GET /api/pnl/history?limit=100
X-API-Key: your-secret-key
```

**Query Parameters:**
- `limit` (optional): Maximum number of records (default: 100, max: 100)

**Response:**
```json
{
  "success": true,
  "data": {
    "count": 50,
    "data": [
      {
        "totalRevenue": 1500.00,
        "totalExpenses": 125.50,
        "netPnL": 1374.50,
        "timestamp": "2024-02-25T22:24:00.000Z"
      },
      // ... more records
    ]
  },
  "timestamp": "2024-02-25T22:24:05.000Z"
}
```

### Get Component Breakdown
```http
GET /api/pnl/breakdown
X-API-Key: your-secret-key
```

**Response:**
```json
{
  "success": true,
  "data": {
    "kalshi": {
      "balance": 10000.00,
      "positions": 3,
      "pnl": 500.00
    },
    "anthropic": {
      "dailySpend": 5.25
    },
    "johns": {
      "invoiced": 2000.00,
      "collected": 1000.00
    },
    "summary": {
      "totalRevenue": 1500.00,
      "totalExpenses": 125.50,
      "netPnL": 1374.50,
      "grossMargin": 91.63
    },
    "timestamp": "2024-02-25T22:24:00.000Z"
  },
  "timestamp": "2024-02-25T22:24:00.000Z"
}
```

### Get Circuit Breaker Status
```http
GET /api/circuit-breaker/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "timestamp": "2024-02-25T22:24:00.000Z",
    "services": {
      "kalshi": {
        "state": "CLOSED",
        "failureCount": 0,
        "lastFailureTime": null,
        "lastSuccessTime": 1708887840000,
        "nextAttemptTime": null
      },
      "anthropic": {
        "state": "OPEN",
        "failureCount": 5,
        "lastFailureTime": 1708887835000,
        "lastSuccessTime": null,
        "nextAttemptTime": 1708887895000
      }
    },
    "config": {
      "failureThreshold": 5,
      "resetTimeout": 60000
    }
  },
  "timestamp": "2024-02-25T22:24:00.000Z"
}
```

### Get Cache Statistics
```http
GET /api/cache/stats
X-API-Key: your-secret-key
```

**Response:**
```json
{
  "success": true,
  "data": {
    "hits": 1250,
    "misses": 234,
    "sets": 456,
    "deletes": 12,
    "errors": 2,
    "total": 1484,
    "hitRate": "84.25%",
    "processCacheSize": 45,
    "timestamp": "2024-02-25T22:24:00.000Z"
  },
  "timestamp": "2024-02-25T22:24:00.000Z"
}
```

## 🔌 WebSocket (Socket.io) API

### Connection

**JavaScript Client**
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:3000', {
  auth: {
    apiKey: 'your-secret-key'
  },
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5,
  transports: ['websocket', 'polling']
});

socket.on('connect_success', (data) => {
  console.log('Connected!', data);
});
```

### Events

#### Connection Success
```javascript
socket.on('connect_success', (data) => {
  console.log(data);
  // {
  //   message: "Connected to P&L streaming server",
  //   clientId: "abc123",
  //   timestamp: "2024-02-25T22:24:00.000Z",
  //   transport: "websocket"
  // }
});
```

#### Subscribe to P&L Updates
```javascript
// Subscribe
socket.emit('subscribe_pnl');

// Receive updates (every 5 seconds)
socket.on('pnl_update', (data) => {
  console.log(data);
  // {
  //   data: { totalRevenue, totalExpenses, netPnL, ... },
  //   timestamp: "2024-02-25T22:24:00.000Z",
  //   source: "stream"
  // }
});
```

#### Subscribe to Component Updates
```javascript
// Subscribe
socket.emit('subscribe_components');

// Receive updates
socket.on('components_update', (data) => {
  console.log(data);
  // {
  //   data: { kalshi: {...}, anthropic: {...}, johns: {...} },
  //   timestamp: "2024-02-25T22:24:00.000Z",
  //   source: "stream"
  // }
});
```

#### Error Events
```javascript
// Socket connection error
socket.on('error', (error) => {
  console.error('Socket error:', error.message);
});

// Stream update error
socket.on('stream_error', (error) => {
  console.error('Stream error:', error);
});
```

#### Disconnection
```javascript
socket.on('disconnect', (reason) => {
  console.log('Disconnected:', reason);
  // Automatic reconnection will attempt if configured
});
```

## 💾 Data Models

### P&L Metrics Object

```typescript
{
  totalRevenue: number;        // Total revenue from all sources
  totalExpenses: number;       // Total expenses (API costs, etc.)
  netPnL: number;              // Net profit/loss (revenue - expenses)
  grossMargin: number;         // Gross margin percentage (0-100)
  dailyTrend: number;          // Daily % change from start of day
  
  components: {
    kalshi: {
      balance: number;         // Current account balance
      positions: number;       // Number of open positions
      pnl: number;            // Realized P&L
    },
    anthropic: {
      dailySpend: number;      // Daily API spend
    },
    johns: {
      invoiced: number;        // Total invoiced amount
      collected: number;       // Total collected/paid amount
    }
  },
  
  timestamp: string;           // ISO 8601 UTC timestamp
  calculatedAt: number;        // Unix milliseconds
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "id": "abc123",
    "message": "Error description",
    "stack": "... (only in development)"
  },
  "timestamp": "2024-02-25T22:24:00.000Z"
}
```

## 🔄 Rate Limiting

Rate limiting is applied per IP address:

- **Default**: 100 requests per minute
- **HTTP Status**: 429 (Too Many Requests)
- **Response Header**: `Retry-After` (seconds)

**Response when rate limited:**
```json
{
  "success": false,
  "error": {
    "message": "Too many requests",
    "retryAfter": 45
  },
  "timestamp": "2024-02-25T22:24:00.000Z"
}
```

## 🔐 Security Headers

Responses include security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
```

## ✅ Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request |
| 401 | Missing/invalid API key |
| 403 | Forbidden |
| 429 | Rate limited |
| 500 | Server error |
| 503 | Service unavailable |

## 📝 Examples

### cURL
```bash
# Get current P&L
curl -H "X-API-Key: your-secret-key" \
  http://localhost:3000/api/pnl/current

# Get history
curl -H "X-API-Key: your-secret-key" \
  "http://localhost:3000/api/pnl/history?limit=50"

# Check health
curl http://localhost:3000/health
```

### JavaScript (Fetch)
```javascript
// Get current P&L
const response = await fetch('http://localhost:3000/api/pnl/current', {
  headers: { 'X-API-Key': 'your-secret-key' }
});
const data = await response.json();
console.log(data);
```

### Python
```python
import requests

headers = {'X-API-Key': 'your-secret-key'}

# Get current P&L
response = requests.get(
  'http://localhost:3000/api/pnl/current',
  headers=headers
)
data = response.json()
print(data)
```

### React with Zustand Hook
```javascript
import { usePnLMetrics, useFetchPnL } from './pnlStore';

function MyComponent() {
  const metrics = usePnLMetrics();
  const { fetchCurrentPnL } = useFetchPnL();

  useEffect(() => {
    fetchCurrentPnL();
  }, [fetchCurrentPnL]);

  return <div>P&L: ${metrics.netPnL}</div>;
}
```

---

**For detailed examples and implementation guides, see the main README.md**
