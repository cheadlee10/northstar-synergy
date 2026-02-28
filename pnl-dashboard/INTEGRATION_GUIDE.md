# WebSocket Integration Guide

This guide explains how to connect the NorthStar P&L Dashboard to your real-time data stream.

## 1. Server Setup

Ensure your backend server is set up to emit WebSocket messages in the format expected by the dashboard.

### Node.js/Express Example with Socket.io

```javascript
// server.js
const express = require('express');
const http = require('http');
const socketIO = require('socket.io');
const cors = require('cors');

const app = express();
const server = http.createServer(app);
const io = socketIO(server, {
  cors: { origin: 'http://localhost:5173' }
});

app.use(cors());

// Emit P&L updates to connected clients
setInterval(() => {
  const pnlData = {
    timestamp: new Date().toISOString(),
    revenue: Math.random() * 150000 + 100000,
    expenses: Math.random() * 60000 + 40000,
    netPnL: 0, // Calculated client-side
    previousRevenue: 118200,
    previousExpenses: 45600,
    previousNetPnL: 72600,
    trendsData: getTrendData(),
    costBreakdown: getCostBreakdown(),
    agentAttribution: getAgentStats(),
  };

  io.emit('pnl-update', pnlData);
}, 1000); // Update every second

server.listen(8000, () => {
  console.log('P&L Server running on port 8000');
});
```

### Python/Flask Example

```python
# app.py
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def on_connect():
    print('Client connected')
    emit('response', {'data': 'Connected to P&L stream'})

def emit_pnl_update():
    pnl_data = {
        'timestamp': datetime.now().isoformat(),
        'revenue': 125450,
        'expenses': 48320,
        'netPnL': 77130,
        'previousRevenue': 118200,
        'previousExpenses': 45600,
        'previousNetPnL': 72600,
        'trendsData': get_trend_data(),
        'costBreakdown': get_cost_breakdown(),
        'agentAttribution': get_agent_stats(),
    }
    socketio.emit('pnl-update', pnl_data)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000)
```

## 2. Dashboard Configuration

### Step 1: Update Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env`:

```
VITE_WS_URL=ws://your-server.com/pnl-stream
VITE_WS_SECURE=true  # Use wss:// in production
VITE_API_URL=https://your-server.com/api
```

### Step 2: Update App.jsx

Modify the WebSocket connection in `App.jsx`:

```jsx
useEffect(() => {
  const wsProtocol = import.meta.env.VITE_WS_SECURE ? 'wss' : 'ws';
  const wsUrl = `${wsProtocol}://${import.meta.env.VITE_WS_URL.replace(/^wss?:\/\//, '')}`;

  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('✅ Connected to P&L stream');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      
      // Update KPI data
      setPnlData({
        revenue: data.revenue,
        expenses: data.expenses,
        netPnL: data.revenue - data.expenses,
        previousRevenue: data.previousRevenue,
        previousExpenses: data.previousExpenses,
        previousNetPnL: data.previousNetPnL,
      });

      // Update trends
      if (data.trendsData) {
        setTrendsData(data.trendsData);
      }

      // Update cost breakdown
      if (data.costBreakdown) {
        setCostBreakdown(data.costBreakdown);
      }

      // Update agent attribution
      if (data.agentAttribution) {
        setAgentAttribution(data.agentAttribution);
      }
    } catch (error) {
      console.error('Error parsing WebSocket data:', error);
    }
  };

  ws.onerror = (error) => {
    console.error('❌ WebSocket error:', error);
  };

  ws.onclose = () => {
    console.log('⚠️ Disconnected from P&L stream');
    // Attempt reconnection after 3 seconds
    setTimeout(() => {
      window.location.reload();
    }, 3000);
  };

  return () => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.close();
    }
  };
}, []);
```

## 3. Data Schema

### Main P&L Data Object

```typescript
interface PnLData {
  timestamp: string;           // ISO 8601 timestamp
  revenue: number;             // Total revenue
  expenses: number;            // Total expenses
  netPnL: number;             // Net profit/loss
  previousRevenue: number;     // Previous period revenue
  previousExpenses: number;    // Previous period expenses
  previousNetPnL: number;      // Previous period net
}
```

### Trends Data

```typescript
interface TrendData {
  date: string;               // YYYY-MM-DD format
  revenue: number;
  expenses: number;
  net: number;
}

type TrendsArray = TrendData[];  // Last 30 days
```

### Cost Breakdown

```typescript
interface CostCategory {
  name: string;               // Category name
  value: number;              // Dollar amount
  percentage: number;         // Percentage of total
}

type CostBreakdown = CostCategory[];
```

### Agent Attribution

```typescript
interface AgentMetrics {
  agent: string;              // "Scalper" | "John" | "Cliff"
  revenue: number;
  expenses: number;
  net: number;
}

type AgentAttribution = AgentMetrics[];
```

## 4. Real-time Update Examples

### Streaming Market Data (Every Second)

```json
{
  "timestamp": "2026-02-25T22:24:00Z",
  "revenue": 125450,
  "expenses": 48320,
  "netPnL": 77130,
  "previousRevenue": 125200,
  "previousExpenses": 48100,
  "previousNetPnL": 77100,
  "trendsData": [
    {"date": "2026-02-25", "revenue": 125450, "expenses": 48320, "net": 77130}
  ],
  "costBreakdown": [
    {"name": "Trading Fees", "value": 18500, "percentage": 38.3},
    {"name": "Infrastructure", "value": 12800, "percentage": 26.5},
    {"name": "Personnel", "value": 11200, "percentage": 23.2},
    {"name": "Other", "value": 5820, "percentage": 12.0}
  ],
  "agentAttribution": [
    {"agent": "Scalper", "revenue": 75000, "expenses": 28500, "net": 46500},
    {"agent": "John", "revenue": 32000, "expenses": 12800, "net": 19200},
    {"agent": "Cliff", "revenue": 18450, "expenses": 7020, "net": 11430}
  ]
}
```

### Periodic Daily Update (Once per Day)

Include historical trends data:

```json
{
  "timestamp": "2026-02-25T00:00:00Z",
  "revenue": 125450,
  "expenses": 48320,
  "netPnL": 77130,
  "previousRevenue": 125000,
  "previousExpenses": 48100,
  "previousNetPnL": 76900,
  "trendsData": [
    // Last 30 days of data
    {"date": "2026-01-27", "revenue": 108000, "expenses": 42000, "net": 66000},
    ...
    {"date": "2026-02-25", "revenue": 125450, "expenses": 48320, "net": 77130}
  ],
  "costBreakdown": [...],
  "agentAttribution": [...]
}
```

## 5. Error Handling

### Reconnection Logic

```jsx
const [connectionStatus, setConnectionStatus] = useState('connecting');
const [reconnectAttempts, setReconnectAttempts] = useState(0);

useEffect(() => {
  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnectionStatus('connected');
        setReconnectAttempts(0);
      };

      ws.onerror = (error) => {
        setConnectionStatus('error');
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        setConnectionStatus('disconnected');
        
        // Exponential backoff for reconnection
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
        setTimeout(connectWebSocket, delay);
        setReconnectAttempts(prev => prev + 1);
      };

      // Handle messages...
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionStatus('error');
    }
  };

  connectWebSocket();
}, []);
```

### Loading States

Add a connection indicator to the dashboard header:

```jsx
<div className="flex items-center gap-2">
  <div
    className={`w-2 h-2 rounded-full ${
      connectionStatus === 'connected'
        ? 'bg-emerald-500 animate-pulse'
        : 'bg-red-500'
    }`}
  />
  <span className="text-xs text-gray-400">
    {connectionStatus === 'connected' ? 'Live' : 'Offline'}
  </span>
</div>
```

## 6. Performance Tuning

### Throttle High-Frequency Updates

```javascript
let lastUpdate = Date.now();
const UPDATE_THROTTLE = 1000; // 1 second

ws.onmessage = (event) => {
  const now = Date.now();
  if (now - lastUpdate < UPDATE_THROTTLE) {
    return; // Skip this update
  }
  lastUpdate = now;

  const data = JSON.parse(event.data);
  // Process update...
};
```

### Batch Updates

```javascript
const pendingUpdates = [];

ws.onmessage = (event) => {
  pendingUpdates.push(JSON.parse(event.data));
};

setInterval(() => {
  if (pendingUpdates.length > 0) {
    const latestUpdate = pendingUpdates[pendingUpdates.length - 1];
    // Process latest update
    updateDashboard(latestUpdate);
    pendingUpdates.length = 0;
  }
}, 1000);
```

## 7. Testing

### Mock WebSocket Server for Development

```javascript
// test-server.js
const WebSocket = require('ws');

const wss = new WebSocket.Server({ port: 8000 });

wss.on('connection', (ws) => {
  console.log('Client connected');

  // Send mock data every second
  const interval = setInterval(() => {
    const data = {
      timestamp: new Date().toISOString(),
      revenue: Math.random() * 150000 + 100000,
      expenses: Math.random() * 60000 + 40000,
      netPnL: 0,
      previousRevenue: 118200,
      previousExpenses: 45600,
      previousNetPnL: 72600,
      trendsData: generateTrendData(),
      costBreakdown: generateCostBreakdown(),
      agentAttribution: generateAgentStats(),
    };
    ws.send(JSON.stringify(data));
  }, 1000);

  ws.on('close', () => {
    clearInterval(interval);
    console.log('Client disconnected');
  });
});

console.log('Test WebSocket server running on ws://localhost:8000');
```

Run with: `node test-server.js`

## 8. Deployment

### Docker Setup

```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 5173

CMD ["npm", "run", "preview"]
```

### Environment Variables in Production

Set these in your deployment platform:

```bash
VITE_WS_URL=wss://api.production.com/pnl-stream
VITE_WS_SECURE=true
VITE_API_URL=https://api.production.com
```

## Troubleshooting

### WebSocket Connection Refused

- Check server is running on correct port
- Verify firewall allows WebSocket connections
- Use `wss://` for HTTPS deployments

### Data Not Updating

- Check browser DevTools → Network → WS tab
- Verify message format matches schema
- Check browser console for parsing errors

### High Latency

- Reduce update frequency on server
- Implement throttling in dashboard
- Check network bandwidth

---

For more details, see the main [README.md](./README.md)
