# Deployment Guide

Complete guide for deploying the P&L streaming backend to production.

## 🐳 Docker Deployment

### Build and Run Locally

```bash
# Build Docker image
docker build -t pnl-backend:latest .

# Run container
docker run -p 3000:3000 \
  -e NODE_ENV=production \
  -e API_KEY=your-secret-key \
  -e KALSHI_API_KEY=your-key \
  -e ANTHROPIC_API_KEY=your-key \
  pnl-backend:latest
```

### Docker Compose (Development)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f pnl-backend

# Stop services
docker-compose down
```

## ☁️ Cloud Deployment

### AWS ECS

1. **Create ECR Repository**
```bash
aws ecr create-repository --repository-name pnl-backend
```

2. **Build and Push Image**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_URL
docker build -t pnl-backend:latest .
docker tag pnl-backend:latest YOUR_ECR_URL/pnl-backend:latest
docker push YOUR_ECR_URL/pnl-backend:latest
```

3. **Create ECS Task Definition**
```json
{
  "family": "pnl-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "pnl-backend",
      "image": "YOUR_ECR_URL/pnl-backend:latest",
      "portMappings": [
        {
          "containerPort": 3000,
          "hostPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "API_KEY",
          "valueFrom": "arn:aws:secretsmanager:...:secret:pnl-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/pnl-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Heroku

1. **Create Heroku App**
```bash
heroku create pnl-streaming-backend
```

2. **Set Environment Variables**
```bash
heroku config:set NODE_ENV=production
heroku config:set API_KEY=your-secret-key
heroku config:set KALSHI_API_KEY=your-key
heroku config:set ANTHROPIC_API_KEY=your-key
heroku config:set REDIS_URL=$(heroku addons:create heroku-redis)
```

3. **Deploy**
```bash
git push heroku main
```

### Google Cloud Run

1. **Build and Push**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/pnl-backend
```

2. **Deploy**
```bash
gcloud run deploy pnl-backend \
  --image gcr.io/PROJECT_ID/pnl-backend \
  --platform managed \
  --region us-central1 \
  --set-env-vars NODE_ENV=production,API_KEY=your-key
```

## 🔒 Security Checklist

- [ ] Change `API_KEY` from default
- [ ] Set `NODE_ENV=production`
- [ ] Use HTTPS for all connections
- [ ] Restrict `CORS_ORIGIN` to your domain
- [ ] Store secrets in environment variables (not .env)
- [ ] Enable rate limiting in production
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerts
- [ ] Use Redis with authentication
- [ ] Backup SQLite database regularly

## 📊 Production Configuration

### Environment Variables

```bash
# Server
NODE_ENV=production
PORT=3000
LOG_LEVEL=warn

# Security
API_KEY=<strong-secret-key>
CORS_ORIGIN=https://yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com

# APIs
KALSHI_API_KEY=<your-key>
ANTHROPIC_API_KEY=<your-key>
JOHNS_REVENUE_URL=https://john-backend.example.com/api/revenue

# Cache
REDIS_URL=redis://user:pass@redis.example.com:6379
CACHE_TTL=300000

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RESET_TIMEOUT=60000
```

## 🔄 Continuous Deployment

### GitHub Actions Example

```yaml
name: Deploy P&L Backend

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build and Push Docker Image
        run: |
          docker build -t pnl-backend:${{ github.sha }} .
          docker push your-registry/pnl-backend:${{ github.sha }}
      
      - name: Deploy to Production
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
        run: |
          ssh -i $DEPLOY_KEY user@server << 'EOF'
            docker pull your-registry/pnl-backend:${{ github.sha }}
            docker stop pnl-backend || true
            docker run -d \
              --name pnl-backend \
              -p 3000:3000 \
              -e NODE_ENV=production \
              -e API_KEY=${{ secrets.API_KEY }} \
              your-registry/pnl-backend:${{ github.sha }}
          EOF
```

## 📈 Monitoring

### Health Checks

The server includes built-in health checks:

```bash
curl http://localhost:3000/health
```

Configure your load balancer to hit this endpoint every 30 seconds.

### Key Metrics to Monitor

- Response time (p50, p95, p99)
- Error rate
- Circuit breaker state
- Cache hit rate
- WebSocket connections
- Redis connection status
- Database size

### Suggested Monitoring Tools

- **CloudWatch** (AWS)
- **Stackdriver** (Google Cloud)
- **New Relic**
- **Datadog**
- **Prometheus + Grafana**

## 🔧 Scaling Considerations

### Horizontal Scaling

With multiple backend instances:

1. **Use Redis** for shared cache (required)
2. **Use load balancer** (ALB, NLB)
3. **Configure sticky sessions** if needed
4. **Monitor circuit breaker** state across instances

### Vertical Scaling

For single-instance deployments:

- Increase `maxProcessCacheSize` for more in-memory caching
- Use Redis for better performance
- Monitor CPU and memory usage

## 🛠️ Maintenance

### Database Cleanup

```bash
# Clear expired cache entries (run weekly)
PRAGMA journal_mode=WAL;
DELETE FROM cache WHERE expiry < strftime('%s', 'now') * 1000;
VACUUM;
```

### Log Rotation

Configure log rotation (logrotate on Linux):

```
/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 nobody nobody
}
```

### Backup

```bash
# Backup SQLite database
cp data/cache.db data/cache.db.backup
gzip data/cache.db.backup

# Upload to S3
aws s3 cp data/cache.db.backup.gz s3://backups/
```

## 🚨 Incident Response

### Circuit Breaker Open

If external APIs fail:

1. Check API status pages
2. Verify network connectivity
3. Check API credentials
4. Review application logs
5. Circuit breaker will auto-recover after reset timeout

### High Memory Usage

1. Check process cache size
2. Monitor Redis memory
3. Check SQLite database size
4. Clear old cache entries

### WebSocket Connection Issues

1. Check firewall rules
2. Verify CORS configuration
3. Check browser console for errors
4. Verify API key is correct

## 📞 Support & Troubleshooting

- **Logs**: Check `logs/combined.log` and `logs/error.log`
- **Health**: GET `/health`
- **Status**: GET `/api/circuit-breaker/status`
- **Cache**: GET `/api/cache/stats`

---

**Deployment complete!** Your P&L backend is ready for production. 🚀
