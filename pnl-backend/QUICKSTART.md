# Quick Start Guide

Get the P&L streaming backend running in 5 minutes.

## 🚀 30-Second Setup

### 1. Install Dependencies
```bash
cd pnl-backend
npm install
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Server
```bash
npm start
```

Server runs on `http://localhost:3000`

## ✅ Verify It's Working

### Check Health
```bash
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "development"
}
```

### Get P&L Snapshot
```bash
curl -H "X-API-Key: default-key-change-me" \
  http://localhost:3000/api/pnl/current
```

## 🔌 Connect Frontend

### React Component
```javascript
import { usePnLSocket, usePnLMetrics } from './client/pnlStore';

export default function Dashboard() {
  const { initSocket } = usePnLSocket();
  const metrics = usePnLMetrics();

  useEffect(() => {
    initSocket();
  }, [initSocket]);

  return <div>Net P&L: ${metrics.netPnL}</div>;
}
```

### Vanilla JavaScript
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:3000', {
  auth: { apiKey: 'default-key-change-me' }
});

socket.emit('subscribe_pnl');

socket.on('pnl_update', (data) => {
  console.log('Updated P&L:', data.data);
});
```

## 🔑 Environment Variables Needed

**Minimum (for testing):**
```bash
PORT=3000
NODE_ENV=development
API_KEY=your-secret-key
```

**For production, also add:**
```bash
KALSHI_API_KEY=your-kalshi-key
ANTHROPIC_API_KEY=your-anthropic-key
JOHNS_REVENUE_URL=http://localhost:5000/api/revenue
REDIS_URL=redis://localhost:6379
```

## 📦 Development Mode

Auto-reload on file changes:
```bash
npm run dev
```

## 🐳 Docker Quick Start

```bash
docker-compose up -d
```

Services:
- Backend: `http://localhost:3000`
- Redis: `localhost:6379`

## 📝 Common Tasks

### Check Server Health
```bash
curl http://localhost:3000/health
```

### View Current P&L
```bash
curl -H "X-API-Key: your-key" http://localhost:3000/api/pnl/current
```

### View Cache Stats
```bash
curl -H "X-API-Key: your-key" http://localhost:3000/api/cache/stats
```

### View Circuit Breaker Status
```bash
curl http://localhost:3000/api/circuit-breaker/status
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Use different port
PORT=3001 npm start
```

### "Cannot find module" errors
```bash
# Reinstall dependencies
rm -rf node_modules
npm install
```

### API Key errors
```bash
# Check your .env file has API_KEY set
# And pass it to requests:
curl -H "X-API-Key: your-actual-key" http://localhost:3000/api/pnl/current
```

### WebSocket Connection Failed
- Check browser console for specific error
- Verify API key is correct
- Ensure server is running on correct port

## 📚 Next Steps

1. **Read API docs**: See `API.md` for all endpoints
2. **Configure integrations**: Add Kalshi, Anthropic, John's API keys
3. **Deploy**: See `DEPLOYMENT.md` for production setup
4. **Monitor**: Check logs in `logs/` directory

## 🆘 Need Help?

Check these first:
- `logs/combined.log` - All server logs
- `logs/error.log` - Error logs only
- `/health` endpoint - Server health
- `/api/circuit-breaker/status` - Service status

---

**Ready to build!** 🎉

For detailed information, see:
- [README.md](README.md) - Full documentation
- [API.md](API.md) - Complete API reference
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production setup
