# Financial Dashboard — Quick Start Guide (15 minutes)

**Time to Live Dashboard: < 1 hour**

---

## Prerequisites

```bash
# Check versions (should have these)
node --version    # v22+ recommended
npm --version     # v10+
git --version     # Any recent version
```

---

## Step 1: Create Project (2 minutes)

```bash
# Create Vite React project with TypeScript
npm create vite@latest my-dashboard -- --template react-ts

cd my-dashboard

# Install dependencies
npm install
```

---

## Step 2: Install Core Libraries (1 minute)

```bash
# Real-time + State Management
npm install zustand socket.io-client

# HTTP + Caching
npm install axios @tanstack/react-query

# UI + Styling
npm install -D tailwindcss postcss autoprefixer daisyui

# Charts (optional, for later)
npm install recharts

# Tables (optional, for later)
npm install @tanstack/react-table
```

---

## Step 3: Setup Tailwind (1 minute)

```bash
# Initialize Tailwind config
npx tailwindcss init -p
```

**Edit `tailwind.config.js`:**

```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: { extend: {} },
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["dark", "light"],
    base: true,
  },
}
```

**Edit `src/index.css`:**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

---

## Step 4: Create Price Store (2 minutes)

**`src/store/priceStore.ts`:**

```typescript
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/react';

export const usePriceStore = create(
  subscribeWithSelector((set) => ({
    prices: {} as Record<string, number>,
    setPrices: (prices: Record<string, number>) => set({ prices }),
  }))
);

// Hook for individual price (only re-renders when THIS price changes)
export const usePriceFor = (symbol: string) =>
  usePriceStore(
    (state) => state.prices[symbol] ?? 0,
    (a, b) => a === b
  );
```

---

## Step 5: Create Real-Time Hook (3 minutes)

**`src/hooks/useRealtimePrices.ts`:**

```typescript
import { useEffect } from 'react';
import { io } from 'socket.io-client';
import { usePriceStore } from '../store/priceStore';

export const useRealtimePrices = (symbols: string[]) => {
  const setPrices = usePriceStore((s) => s.setPrices);

  useEffect(() => {
    // Connect to backend
    const socket = io(import.meta.env.VITE_API_URL || 'http://localhost:3000', {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    // Subscribe on connect
    socket.on('connect', () => {
      console.log('✅ Connected');
      socket.emit('subscribe', { symbols });
    });

    // Handle price updates
    socket.on('price:update', (data) => {
      setPrices(data);
    });

    // Cleanup
    return () => {
      if (symbols.length > 0) {
        socket.emit('unsubscribe', { symbols });
      }
      socket.disconnect();
    };
  }, [symbols.join(','), setPrices]);
};
```

---

## Step 6: Create Dashboard Component (3 minutes)

**`src/components/Dashboard.tsx`:**

```typescript
import React, { useEffect } from 'react';
import { useRealtimePrices } from '../hooks/useRealtimePrices';
import { usePriceFor, usePriceStore } from '../store/priceStore';

// Individual ticker card (optimized: only re-renders when price changes)
const TickerCard: React.FC<{ symbol: string }> = ({ symbol }) => {
  const price = usePriceFor(symbol);
  
  return (
    <div className="card bg-slate-800 shadow-lg">
      <div className="card-body">
        <h2 className="card-title">{symbol}</h2>
        <p className="text-4xl font-bold text-green-500">
          ${price.toFixed(2)}
        </p>
      </div>
    </div>
  );
};

// Main dashboard
export const Dashboard: React.FC = () => {
  const symbols = ['AAPL', 'TSLA', 'GOOGL', 'MSFT'];
  const prices = usePriceStore((s) => s.prices);

  // Connect to real-time updates
  useRealtimePrices(symbols);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <h1 className="text-4xl font-bold mb-8">📊 Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {symbols.map((symbol) => (
          <TickerCard key={symbol} symbol={symbol} />
        ))}
      </div>

      <div className="mt-8 text-gray-400">
        Connected: {Object.keys(prices).length > 0 ? '✅ Live' : '⏳ Waiting...'}
      </div>
    </div>
  );
};
```

---

## Step 7: Create Backend (Backend Node.js/Express)

Create `server.ts` in project root:

```typescript
import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';
import cors from 'cors';

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: { origin: 'http://localhost:5173' },
});

app.use(cors());

// Market data
const prices: Record<string, number> = {
  AAPL: 150.25,
  TSLA: 210.55,
  GOOGL: 139.45,
  MSFT: 380.0,
};

// Simulate price updates every 1 second
setInterval(() => {
  const updates: Record<string, number> = {};
  
  for (const [symbol, price] of Object.entries(prices)) {
    // Random walk: ±1%
    const change = (Math.random() - 0.5) * 0.02;
    const newPrice = price * (1 + change);
    updates[symbol] = newPrice;
    prices[symbol] = newPrice;
  }

  // Broadcast to all clients
  io.emit('price:update', updates);
}, 1000);

// Socket.io
io.on('connection', (socket) => {
  console.log(`✅ Client ${socket.id} connected`);

  socket.on('subscribe', ({ symbols }: { symbols: string[] }) => {
    console.log(`  → Subscribed to ${symbols.join(', ')}`);
  });

  socket.on('disconnect', () => {
    console.log(`❌ Client disconnected`);
  });
});

server.listen(3000, () => {
  console.log('🚀 Server on http://localhost:3000');
});
```

Install backend dependencies:
```bash
npm install express cors socket.io
npm install -D typescript ts-node @types/node @types/express
```

---

## Step 8: Environment Variables

Create `.env.local`:

```
VITE_API_URL=http://localhost:3000
```

---

## Step 9: Run Everything

**Terminal 1 (Frontend):**
```bash
npm run dev
# Output: http://localhost:5173
```

**Terminal 2 (Backend):**
```bash
npx ts-node server.ts
# Output: http://localhost:3000
```

**Open browser:** http://localhost:5173

You should see **live updating prices** from the backend! ✨

---

## What's Happening

```
Backend (3000)
    ↓ Socket.io price:update (every 1 sec)
    ↓
Frontend (5173)
    ↓ socket.on('price:update')
    ↓
Zustand store update
    ↓
React re-renders only changed tickers
    ↓
DOM updates < 20ms
    ↓
User sees live prices! ✅
```

---

## Next Steps (Extend Your Dashboard)

### Add P&L Tracking

```typescript
interface Position {
  symbol: string;
  quantity: number;
  entryPrice: number;
}

const positions = [
  { symbol: 'AAPL', quantity: 100, entryPrice: 148 },
  { symbol: 'TSLA', quantity: 50, entryPrice: 215 },
];

function PnLRow({ position }: { position: Position }) {
  const currentPrice = usePriceFor(position.symbol);
  const pnl = (currentPrice - position.entryPrice) * position.quantity;
  
  return (
    <tr>
      <td>{position.symbol}</td>
      <td>{position.quantity}</td>
      <td>${currentPrice.toFixed(2)}</td>
      <td className={pnl >= 0 ? 'text-green-500' : 'text-red-500'}>
        ${pnl.toFixed(2)}
      </td>
    </tr>
  );
}
```

### Add Order Tracking

```typescript
const useOrderStore = create((set) => ({
  orders: [],
  addOrder: (order) => set((state) => ({
    orders: [...state.orders, order]
  })),
}));
```

### Add Charts

```bash
npm install recharts
```

```typescript
import { LineChart, Line, XAxis, YAxis } from 'recharts';

<LineChart width={600} height={300} data={priceHistory}>
  <Line type="monotone" dataKey="AAPL" />
  <XAxis />
  <YAxis />
</LineChart>
```

### Connect to Real Data

Replace the mock price updates with:
- **Alpaca** (stocks): https://alpaca.markets
- **Polygon.io** (stocks/crypto): https://polygon.io
- **Binance** (crypto): https://binance-docs.github.io/apidocs/
- **IB Gateway** (options/futures): Interactive Brokers API

---

## Deployment (Production)

### Frontend to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy (automatic)
vercel
```

### Backend to Railway.app

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway up
```

Both services handle real-time WebSocket connections perfectly.

---

## Performance Tips

1. **Memoize components** that render many times:
   ```typescript
   const TickerCard = React.memo(({ symbol }) => { ... });
   ```

2. **Use `subscribeWithSelector`** to avoid unnecessary renders:
   ```typescript
   const price = usePriceStore(
     (state) => state.prices[symbol],
     (a, b) => a === b  // Only re-render if price changed
   );
   ```

3. **Debounce expensive operations**:
   ```typescript
   import { debounce } from 'lodash-es';
   const handleSearch = debounce((query) => { ... }, 300);
   ```

4. **Code split large features**:
   ```typescript
   const Analytics = React.lazy(() => import('./Analytics'));
   ```

5. **Optimize Socket.io messages**:
   - Only send changed prices, not all prices
   - Use binary messages for very high frequency

---

## Troubleshooting

### "Cannot GET /socket.io/"

**Problem:** Backend not running.  
**Solution:** Make sure `server.ts` is running on port 3000.

```bash
npx ts-node server.ts
```

### Prices not updating

**Problem:** Socket connection failed.  
**Solution:** Check browser console (F12) for errors.

- Is backend running?
- Is `VITE_API_URL` correct?
- Are CORS headers set?

### Hot reload not working

**Problem:** Vite HMR disabled.  
**Solution:** Restart dev server.

```bash
# Kill existing process
# Then:
npm run dev
```

### Build fails

**Problem:** TypeScript errors.  
**Solution:**
```bash
npm run build
# Shows exact errors
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Client (React)                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Dashboard.tsx                                     │  │
│  │ ├─ useRealtimePrices()                           │  │
│  │ └─ usePriceFor('AAPL') → Re-render on change    │  │
│  └───────────────────────────────────────────────────┘  │
│                         ↕ Socket.io (ws)                │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Zustand Store (priceStore)                        │  │
│  │ └─ prices: { AAPL: 150.25, TSLA: 210.55, ... }   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↕ Socket.io (wss)
┌─────────────────────────────────────────────────────────┐
│                 Server (Node.js/Express)                │
│  ┌───────────────────────────────────────────────────┐  │
│  │ server.ts                                         │  │
│  │ ├─ setInterval: generate random prices           │  │
│  │ ├─ io.emit('price:update', prices)              │  │
│  │ └─ socket.on('subscribe', ...)                   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Useful Commands

```bash
# Dev
npm run dev          # Start Vite dev server (http://localhost:5173)
npx ts-node server   # Start backend (http://localhost:3000)

# Build
npm run build        # Production bundle (dist/)
npm run preview      # Preview production build

# Lint/Format
npm run lint         # ESLint (if configured)

# Deploy
vercel               # Deploy frontend
railway up           # Deploy backend
```

---

## File Structure (After Setup)

```
my-dashboard/
├── src/
│   ├── components/
│   │   └── Dashboard.tsx
│   ├── hooks/
│   │   └── useRealtimePrices.ts
│   ├── store/
│   │   └── priceStore.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── server.ts
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
├── package.json
└── .env.local
```

---

## Estimated Timeline

| Step | Time | Task |
|------|------|------|
| 1-2 | 5 min | Create project, install deps |
| 3-4 | 5 min | Setup Tailwind, create store |
| 5-6 | 10 min | Create real-time hook, component |
| 7 | 10 min | Create backend server |
| 8-9 | 5 min | Environment + run |
| **Total** | **~35 minutes** | **Working dashboard** ✅ |

---

## Need Help?

- **React Docs:** https://react.dev
- **Vite Docs:** https://vitejs.dev
- **Zustand Issues:** https://github.com/pmndrs/zustand
- **Socket.io Help:** https://socket.io/docs/

---

**Ready to go? Run this:**

```bash
npm create vite@latest my-dashboard -- --template react-ts && cd my-dashboard && npm install zustand socket.io-client && npm run dev
```

You're live in < 2 minutes! 🚀

