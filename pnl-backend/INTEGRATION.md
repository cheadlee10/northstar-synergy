# Integration Guide

How to integrate the P&L backend with external services.

## 🔗 John's Revenue Backend (Python/Flask)

### 1. Flask Backend Setup

Your Flask backend should expose an endpoint returning revenue data:

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/revenue', methods=['GET'])
def get_revenue():
    return jsonify({
        'invoiced': 5000.00,      # Total invoiced amount
        'collected': 3500.00      # Total collected/paid amount
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### 2. Configure Node Backend

Set the revenue URL in `.env`:

```bash
JOHNS_REVENUE_URL=http://localhost:5000/api/revenue
```

Or for remote deployment:
```bash
JOHNS_REVENUE_URL=https://john-backend.example.com/api/revenue
```

### 3. Verify Integration

Check if the backend can reach the revenue API:

```bash
# In Node backend logs, look for:
# "Johns revenue from cache" - working
# "Johns revenue API call failed" - not reaching

# Or check directly
curl http://localhost:5000/api/revenue
```

### Docker Compose Integration

If running with docker-compose:

```yaml
john-backend:
  build: ../workspace-john
  container_name: john-backend
  ports:
    - "5000:5000"
  networks:
    - pnl-network

pnl-backend:
  # ... other config
  environment:
    - JOHNS_REVENUE_URL=http://john-backend:5000/api/revenue
  depends_on:
    - john-backend
```

## 📊 Kalshi API Integration

### 1. Get API Credentials

1. Visit [Kalshi.com](https://kalshi.com)
2. Go to Settings → API Keys
3. Create new API key
4. Copy key to `.env`

### 2. Configure Kalshi

```bash
KALSHI_API_URL=https://api.kalshi.com/v1
KALSHI_API_KEY=your-kalshi-api-key-here
```

### 3. Kalshi Data Endpoints

The backend fetches:
- **Balance**: `GET /users/self`
- **Positions**: `GET /users/self/positions`

The aggregator calculates:
- Total balance
- Number of open positions
- Total P&L from positions

### 4. Verify Kalshi Connection

Check logs for:
```
Kalshi data from cache
```

Or monitor via API:
```bash
curl -H "X-API-Key: your-key" \
  http://localhost:3000/api/pnl/breakdown | jq '.data.kalshi'
```

## 🤖 Anthropic API Integration

### 1. Get API Credentials

1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Go to Settings → API Keys
3. Create new key
4. Add to `.env`

### 2. Configure Anthropic

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Anthropic Cost Tracking

Currently implemented as:
- Mock daily spend ($5.25)
- Can be connected to actual Anthropic billing API when available

### 4. To Use Real Anthropic Costs

When Anthropic releases billing API:

```javascript
// In lib/aggregator.js, update fetchAnthropicCostsFromApi()
async fetchAnthropicCostsFromApi() {
  const response = await axios.get(
    'https://api.anthropic.com/v1/billing/usage',
    {
      headers: {
        'Authorization': `Bearer ${this.config.anthropicApiKey}`
      }
    }
  );
  
  // Parse response and extract daily spend
  return {
    dailySpend: response.data.daily_spend
  };
}
```

## 🔄 Redis Integration

### Local Development

For simple local testing, Redis is optional (uses in-memory cache).

To use Redis:

1. **Install Redis**
   - macOS: `brew install redis`
   - Ubuntu: `sudo apt install redis-server`
   - Windows: Use Docker

2. **Start Redis**
   ```bash
   redis-server
   ```

3. **Configure in .env**
   ```bash
   REDIS_URL=redis://localhost:6379
   ```

### Docker with Redis

```bash
docker-compose up -d
```

This starts both Node backend and Redis.

### Verify Redis Connection

```bash
# Check Redis logs
docker-compose logs redis

# Or connect to Redis CLI
redis-cli
> PING
PONG
```

## 🔌 Multi-Instance Deployment

For multiple backend instances, configure shared Redis:

### Architecture
```
Load Balancer
    ↓
Instance 1 ─┐
Instance 2 ─┼─ Shared Redis
Instance 3 ─┘
```

### Configuration

All instances use same Redis URL:

```bash
# .env for all instances
REDIS_URL=redis://redis-server.example.com:6379
```

### Notes
- Circuit breaker state is per-instance (not shared)
- Cache is shared across instances
- WebSocket connections are per-instance

## 🔐 API Authentication

### Securing Your APIs

**For John's Revenue API:**
```python
from flask import Flask, request, jsonify

@app.route('/api/revenue', methods=['GET'])
def get_revenue():
    token = request.headers.get('Authorization', '')
    if token != f'Bearer {SECRET_TOKEN}':
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({
        'invoiced': 5000.00,
        'collected': 3500.00
    })
```

**Configure in Node backend:**
```bash
JOHNS_REVENUE_TOKEN=your-secret-token
```

**Update aggregator:**
```javascript
// In lib/aggregator.js
async callJohnsRevenueApi() {
  const token = process.env.JOHNS_REVENUE_TOKEN;
  const response = await axios.get(
    this.config.johnsRevenueUrl,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      timeout: 5000
    }
  );
  // ...
}
```

## 📈 Monitoring Integrations

### Health Check All Integrations

```bash
curl http://localhost:3000/api/circuit-breaker/status
```

Look for:
```json
{
  "services": {
    "kalshi": { "state": "CLOSED" },    // ✅ Working
    "anthropic": { "state": "CLOSED" },  // ✅ Working
    "johns_revenue": { "state": "CLOSED" } // ✅ Working
  }
}
```

### Troubleshooting Failed Integrations

If any service is in "OPEN" state:

1. **Check API credentials**
   ```bash
   # Verify keys are set
   echo $KALSHI_API_KEY
   echo $ANTHROPIC_API_KEY
   ```

2. **Check API endpoints**
   ```bash
   # Test Kalshi
   curl -H "Authorization: Bearer $KALSHI_API_KEY" \
     https://api.kalshi.com/v1/users/self
   
   # Test John's revenue
   curl http://localhost:5000/api/revenue
   ```

3. **Check logs**
   ```bash
   tail -f logs/error.log
   ```

4. **Reset circuit breaker**
   ```bash
   # Via API (if available)
   curl -X POST http://localhost:3000/api/circuit-breaker/reset/kalshi
   ```

## 🌐 Cross-Origin (CORS) Integration

For frontend running on different domain:

### Configuration

```bash
CORS_ORIGIN=https://yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

### Browser Console Errors

If you see CORS errors:

1. Check `CORS_ORIGIN` in `.env`
2. Verify frontend URL matches CORS_ORIGIN
3. For development, set `CORS_ORIGIN=*` (not production!)

## 🚀 Example: Complete Setup

### .env Configuration
```bash
# Server
PORT=3000
NODE_ENV=production
API_KEY=super-secret-key

# Kalshi
KALSHI_API_URL=https://api.kalshi.com/v1
KALSHI_API_KEY=kalshi-secret-key

# Anthropic
ANTHROPIC_API_KEY=anthropic-secret-key

# John's Backend
JOHNS_REVENUE_URL=https://john-backend.example.com/api/revenue
JOHNS_REVENUE_TOKEN=johns-secret-token

# Cache
REDIS_URL=redis://redis.example.com:6379

# CORS
CORS_ORIGIN=https://app.example.com
```

### Startup Checklist
- [ ] API keys set in `.env`
- [ ] Redis running (or disabled if not needed)
- [ ] John's backend running
- [ ] Kalshi API accessible
- [ ] CORS origin configured
- [ ] Health check returns healthy
- [ ] Circuit breaker shows all services CLOSED

### Monitoring
```bash
# Watch logs
docker logs -f pnl-backend

# Check status
curl http://localhost:3000/health
curl http://localhost:3000/api/circuit-breaker/status
```

## 📞 Integration Support

If you encounter issues:

1. **Check logs**: `logs/error.log`
2. **Verify credentials**: Each API key format
3. **Test endpoints directly**: Use curl or Postman
4. **Check circuit breaker**: `/api/circuit-breaker/status`
5. **Review docs**: API.md and README.md

---

**All integrations configured and ready!** 🎉
