---
name: dashboard-deployment
description: Deploy P&L dashboards to production (Railway, Vercel, AWS). Use when going live with financial dashboards, setting up CI/CD pipelines, containerizing applications, configuring monitoring, or scaling to production. Includes Docker, GitHub Actions, Railway deployment, performance tuning, and disaster recovery.
---

# Dashboard Deployment Skill

Production deployment patterns for financial dashboards with zero-downtime updates, monitoring, and automated recovery.

## Docker Setup

### Dockerfile (Node.js Backend)
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
EXPOSE 3001

CMD ["node", "server.js"]
```

### docker-compose.yml (Full Stack)
```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:3001

  backend:
    build: ./backend
    ports:
      - "3001:3001"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/pnl
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=pnl
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## Railway Deployment

### Frontend (React) to Vercel
```bash
# 1. Push to GitHub
git push origin main

# 2. Link Vercel project
vercel --prod

# 3. Set environment variables
vercel env add REACT_APP_API_URL https://backend.railway.app
```

### Backend (Node) to Railway
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Add environment variables
railway variables set DATABASE_URL=postgresql://...
railway variables set REDIS_URL=redis://...

# 5. Deploy
railway up
```

### Database (PostgreSQL) on Railway
```bash
# 1. Add PostgreSQL plugin via Railway dashboard
# 2. Get connection string from Railway
# 3. Set as DATABASE_URL

# 4. Run migrations
npx prisma migrate deploy --environment .env.production
```

## GitHub Actions CI/CD

### .github/workflows/deploy.yml
```yaml
name: Deploy P&L Dashboard

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - run: npm ci
      - run: npm test
      - run: npm run lint
      - run: npm run build

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm ci
      - run: npm run build
      
      - name: Deploy to Railway
        uses: devcontainers/cli@v0.31.0
        env:
          RAILWAY_API_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: |
          railway up --environment production
```

## Environment Configuration

### .env.example
```
# Backend
NODE_ENV=production
PORT=3001
DATABASE_URL=postgresql://user:pass@host:5432/pnl
REDIS_URL=redis://host:6379

# Frontend
REACT_APP_API_URL=https://api.example.com
REACT_APP_ENV=production

# APIs
KALSHI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
```

### Production Secrets (Railway)
```bash
railway variables set NODE_ENV production
railway variables set DATABASE_URL $YOUR_DB_URL
railway variables set REDIS_URL $YOUR_REDIS_URL
railway variables set KALSHI_API_KEY $YOUR_KEY
```

## Database Migrations

### Prisma Schema
```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model PnLSnapshot {
  id        Int     @id @default(autoincrement())
  timestamp DateTime @default(now())
  revenue   Float
  expenses  Float
  netPL     Float
  margin    Float
}
```

### Run Migrations
```bash
# Local development
npx prisma migrate dev --name init

# Production
npx prisma migrate deploy --environment .env.production

# Rollback (if needed)
npx prisma migrate resolve --rolled-back init
```

## Health Checks & Monitoring

### Health Check Endpoint
```javascript
app.get('/health', (req, res) => {
  const health = {
    status: 'OK',
    timestamp: new Date(),
    uptime: process.uptime(),
    checks: {
      database: checkDatabase(),
      redis: checkRedis(),
      apiGateways: checkAPIs()
    }
  };
  res.status(200).json(health);
});
```

### Prometheus Metrics
```javascript
const prometheus = require('prom-client');

const httpRequestDuration = new prometheus.Histogram({
  name: 'http_request_duration_ms',
  help: 'Duration of HTTP requests in ms',
  buckets: [0.1, 5, 15, 50, 100, 500]
});

app.get('/metrics', (req, res) => {
  res.set('Content-Type', prometheus.register.contentType);
  res.end(prometheus.register.metrics());
});
```

### Grafana Dashboard
```json
{
  "panels": [
    {
      "title": "P&L Trend",
      "targets": [
        {
          "expr": "pnl_net_pl_usd"
        }
      ]
    },
    {
      "title": "API Latency",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, http_request_duration_ms)"
        }
      ]
    }
  ]
}
```

## Performance Tuning

### CDN Configuration (Cloudflare)
```
1. Cache static assets (JS, CSS, images)
2. Enable Brotli compression
3. Set cache headers: max-age=31536000 (1 year)
4. Enable HTTP/2 Server Push
```

### Database Optimization
```sql
CREATE INDEX idx_pnl_snapshot_timestamp ON PnLSnapshot(timestamp DESC);
CREATE INDEX idx_pnl_snapshot_agent ON PnLSnapshot(agent_id);

-- Analyze performance
EXPLAIN ANALYZE SELECT * FROM PnLSnapshot WHERE timestamp > NOW() - INTERVAL '1 day';
```

### Redis Caching
```javascript
// Cache expensive queries
app.get('/api/pnl/historical', async (req, res) => {
  const cacheKey = `pnl:historical:${req.query.days}`;
  
  const cached = await redis.get(cacheKey);
  if (cached) return res.json(JSON.parse(cached));

  const data = await db.query(...);
  await redis.setex(cacheKey, 3600, JSON.stringify(data));  // 1 hour TTL
  
  res.json(data);
});
```

## Disaster Recovery

### Database Backup
```bash
# Automated daily backups (Railway handles this)
# Manual backup:
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore:
psql $DATABASE_URL < backup_20260225.sql
```

### Rollback Procedure
```bash
# 1. Identify last stable commit
git log --oneline | head -10

# 2. Rollback deployment
railway rollback <previous-deployment-id>

# 3. Verify health
curl https://api.example.com/health
```

## Zero-Downtime Deployment

### Blue-Green Deployment (Railway)
```bash
# 1. Deploy to staging environment
railway up --environment staging

# 2. Run smoke tests
npm run smoke-tests

# 3. Switch traffic (via Railway dashboard)
# Point production domain to new instance

# 4. Keep old instance running for 5 minutes (fallback)
```

## Monitoring & Alerting

### Sentry Error Tracking
```javascript
const Sentry = require("@sentry/node");

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV
});

app.use(Sentry.Handlers.errorHandler());
```

### Alert Rules
```
- Error rate > 1% → Slack notification
- Response time > 1s (p95) → Page
- CPU usage > 80% → Scale up
- Database connection pool > 90% → Alert
```

## Cost Optimization

| Component | Service | Cost | Notes |
|-----------|---------|------|-------|
| Frontend | Vercel | $20/mo | Free tier included |
| Backend | Railway | $5-50/mo | Pay-as-you-go |
| Database | Railway PG | $0-20/mo | Free tier available |
| Cache | Railway Redis | $0-10/mo | Free tier available |
| **Total** | | **$25-100/mo** | Production-grade |

## Deployment Checklist

- [ ] Docker images built and tested locally
- [ ] Environment variables configured (no hardcoded secrets)
- [ ] Database migrations tested on staging
- [ ] Health checks passing (database, Redis, APIs)
- [ ] Monitoring configured (Prometheus, Grafana, Sentry)
- [ ] Load testing completed (100+ concurrent users)
- [ ] SSL certificate configured (auto via Railway)
- [ ] Backups scheduled (automated + manual tested)
- [ ] Rollback procedure documented and tested
- [ ] On-call rotation established
- [ ] Incident response plan in place
