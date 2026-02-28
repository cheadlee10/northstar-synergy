# Configuration Reference

Complete guide to all configuration options.

## 🔧 Environment Variables

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 3000 | Server port |
| `NODE_ENV` | development | Environment (development/production) |
| `LOG_LEVEL` | info | Logging level (debug/info/warn/error) |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | default-key-change-me | API authentication key |
| `CORS_ORIGIN` | * | CORS origin (single domain) |
| `ALLOWED_ORIGINS` | * | Comma-separated allowed origins |

### External API Keys

| Variable | Required | Description |
|----------|----------|-------------|
| `KALSHI_API_URL` | No | Kalshi API base URL |
| `KALSHI_API_KEY` | No | Kalshi API authentication key |
| `ANTHROPIC_API_KEY` | No | Anthropic API key |
| `JOHNS_REVENUE_URL` | No | John's revenue endpoint URL |
| `JOHNS_REVENUE_TOKEN` | No | John's revenue API token |

### Cache Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | redis://localhost:6379 | Redis connection URL |
| `CACHE_TTL` | 300000 | Cache TTL in milliseconds (5 minutes) |
| `DB_PATH` | ./data/cache.db | SQLite database path |

### Circuit Breaker

| Variable | Default | Description |
|----------|---------|-------------|
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | 5 | Failures before opening |
| `CIRCUIT_BREAKER_RESET_TIMEOUT` | 60000 | Reset timeout in milliseconds |

## 📝 Example Configurations

### Development Setup

```bash
PORT=3000
NODE_ENV=development
LOG_LEVEL=debug
API_KEY=dev-key-123

# Optional APIs (can use mock data)
KALSHI_API_KEY=
ANTHROPIC_API_KEY=
JOHNS_REVENUE_URL=http://localhost:5000/api/revenue

# Cache - use process cache only
CACHE_TTL=60000

# No Redis needed locally
```

### Production Setup

```bash
PORT=3000
NODE_ENV=production
LOG_LEVEL=warn
API_KEY=<strong-secret-key-min-32-chars>

# All API credentials required
KALSHI_API_URL=https://api.kalshi.com/v1
KALSHI_API_KEY=<your-kalshi-key>
ANTHROPIC_API_KEY=<your-anthropic-key>
JOHNS_REVENUE_URL=https://john-backend.example.com/api/revenue
JOHNS_REVENUE_TOKEN=<johns-secret-token>

# CORS restricted
CORS_ORIGIN=https://yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Redis for distributed caching
REDIS_URL=redis://user:pass@redis.example.com:6379

# Longer cache TTL in production
CACHE_TTL=600000

# Stricter circuit breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
CIRCUIT_BREAKER_RESET_TIMEOUT=30000
```

### Docker Setup

```bash
# For docker-compose, set in docker-compose.yml:
environment:
  - NODE_ENV=production
  - PORT=3000
  - API_KEY=${API_KEY}
  - REDIS_URL=redis://redis:6379
  - KALSHI_API_KEY=${KALSHI_API_KEY}
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
  - JOHNS_REVENUE_URL=http://john-backend:5000/api/revenue
```

## 🔒 API Key Format Guide

### Kalshi API Key
- Format: Alphanumeric string
- Location: [kalshi.com](https://kalshi.com) → Settings → API Keys
- Example: `abc123def456ghi789`

### Anthropic API Key
- Format: `sk-ant-...` (Claude API key)
- Location: [console.anthropic.com](https://console.anthropic.com) → Settings
- Example: `sk-ant-v0-abc123def456...`

### Redis URL
- Format: `redis://[user:password@]host:port[/db]`
- Local: `redis://localhost:6379`
- Remote: `redis://user:pass@redis.example.com:6379`
- With password: `redis://:password@redis.example.com:6379`

## 📊 Performance Tuning

### For High-Throughput

```bash
# Increase cache size and TTL
CACHE_TTL=600000              # 10 minutes
DB_PATH=/fast-ssd/cache.db    # Use SSD if available

# Use Redis
REDIS_URL=redis://redis-cluster:6379

# Adjust circuit breaker for production
CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
CIRCUIT_BREAKER_RESET_TIMEOUT=30000
```

### For High-Availability

```bash
# Distributed Redis cluster
REDIS_URL=redis://cluster.example.com:6379

# Load balancer with sticky sessions
# (configure at load balancer level)

# Use process cache as L1
# SQLite as L2
# Redis as L3

# Circuit breaker keeps trying
CIRCUIT_BREAKER_RESET_TIMEOUT=10000  # Faster recovery
```

### For Memory-Constrained

```bash
# Reduce cache sizes
DB_PATH=/small-disk/cache.db

# Disable SQLite if needed
# Disable Redis if not scaling

# Use process cache only
CACHE_TTL=120000  # 2 minutes

# Smaller cache size (in code)
# See CacheManager maxProcessCacheSize option
```

## 🔍 Logging Configuration

### Log Levels

In order of verbosity:
1. **error** - Only errors
2. **warn** - Warnings and errors
3. **info** - Normal operation (default)
4. **debug** - Detailed debugging

### Set Log Level

```bash
LOG_LEVEL=debug npm start
```

### Log Files

- **combined.log** - All events (stdout + file)
- **error.log** - Errors only

Location: `logs/` directory

## 🌍 Network Configuration

### CORS for Single Domain

```bash
CORS_ORIGIN=https://app.example.com
```

### CORS for Multiple Domains

```bash
CORS_ORIGIN=https://app.example.com
ALLOWED_ORIGINS=https://app.example.com,https://api.example.com,http://localhost:3000
```

### CORS for Development

```bash
# Allow all (development only!)
CORS_ORIGIN=*
ALLOWED_ORIGINS=*
```

## 🔐 Security Configuration

### Strong API Key

Generate with:
```bash
# Linux/Mac
openssl rand -base64 32

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### Redis Authentication

```bash
# With password
REDIS_URL=redis://:your-password@redis.example.com:6379

# With user and password
REDIS_URL=redis://user:password@redis.example.com:6379
```

### HTTPS in Production

Configure at load balancer/reverse proxy level:
- AWS ALB with ACM certificate
- Nginx reverse proxy
- Cloudflare (free HTTPS)

## 📈 Circuit Breaker Tuning

### For Unstable Networks

```bash
# Allow more failures before opening
CIRCUIT_BREAKER_FAILURE_THRESHOLD=10

# Longer reset timeout
CIRCUIT_BREAKER_RESET_TIMEOUT=120000  # 2 minutes
```

### For Stable Networks

```bash
# Open quickly on failures
CIRCUIT_BREAKER_FAILURE_THRESHOLD=2

# Retry sooner
CIRCUIT_BREAKER_RESET_TIMEOUT=10000  # 10 seconds
```

### For Debugging

```bash
# Monitor circuit breaker
curl http://localhost:3000/api/circuit-breaker/status

# Check cache stats
curl -H "X-API-Key: your-key" \
  http://localhost:3000/api/cache/stats
```

## 🧪 Testing Configuration

### Unit Tests

```bash
npm test
```

### Integration Tests

```bash
# Start services
docker-compose up -d

# Run full integration test
npm run test:integration
```

### Load Testing

```bash
# Example: 100 requests/second for 60 seconds
artillery quick --count 100 --num 60 http://localhost:3000/api/pnl/current
```

## 📋 Configuration Checklist

### Development
- [ ] Copy `.env.example` to `.env`
- [ ] Set `NODE_ENV=development`
- [ ] Set API key for local testing
- [ ] Run `npm install`
- [ ] Start with `npm run dev`

### Staging
- [ ] Set `NODE_ENV=staging`
- [ ] Set all API keys
- [ ] Configure Redis
- [ ] Set realistic `CACHE_TTL`
- [ ] Configure `CORS_ORIGIN`
- [ ] Run health checks
- [ ] Monitor logs

### Production
- [ ] Set `NODE_ENV=production`
- [ ] Set strong `API_KEY` (32+ chars)
- [ ] Set all API keys and tokens
- [ ] Configure Redis with auth
- [ ] Set HTTPS at load balancer
- [ ] Configure `ALLOWED_ORIGINS`
- [ ] Set `LOG_LEVEL=warn`
- [ ] Configure log rotation
- [ ] Set up monitoring/alerting
- [ ] Test failover scenarios
- [ ] Backup configuration

## 🔗 Integration Configuration

### John's Flask Backend

```bash
JOHNS_REVENUE_URL=http://localhost:5000/api/revenue
JOHNS_REVENUE_TOKEN=your-secret-token
```

Return format expected:
```json
{
  "invoiced": 5000.00,
  "collected": 3500.00
}
```

### Kalshi Integration

```bash
KALSHI_API_URL=https://api.kalshi.com/v1
KALSHI_API_KEY=your-kalshi-key
```

### Anthropic Integration

```bash
ANTHROPIC_API_KEY=sk-ant-your-key
```

## 🆘 Troubleshooting Configuration

### "Cannot read property 'xxx' of undefined"
- Missing required environment variable
- Check `.env` file has correct variable names

### "ECONNREFUSED" for Redis
- Redis not running
- Wrong Redis URL
- Firewall blocking connection

### "401 Unauthorized" for Kalshi
- Invalid API key
- Key doesn't have required permissions

### High Memory Usage
- Increase `CACHE_TTL` to reduce refresh rate
- Reduce `maxProcessCacheSize` in code
- Use Redis instead of SQLite for scaling

### Slow Response Times
- Check cache hit rate: `/api/cache/stats`
- Monitor circuit breaker: `/api/circuit-breaker/status`
- Check external API response times

---

**Configuration complete!** Refer to this guide for any setup questions. 📋
