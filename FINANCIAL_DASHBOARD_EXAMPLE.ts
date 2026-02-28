/**
 * FINANCIAL DASHBOARD - Complete Working Example
 * Copy-paste ready code for React + Vite + Zustand + Socket.io
 * 
 * Files to create:
 * 1. src/store/priceStore.ts (this file)
 * 2. src/hooks/useRealtimePrices.ts
 * 3. src/hooks/usePortfolio.ts
 * 4. src/components/PnLDashboard.tsx
 * 5. server/index.ts (backend)
 */

// ============================================================================
// FILE 1: src/store/priceStore.ts
// ============================================================================

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/react';

export interface Price {
  symbol: string;
  value: number;
  change: number; // Percentage change
  changeAmount: number;
  timestamp: number;
  bid: number;
  ask: number;
}

interface PriceState {
  // Store structure: { 'AAPL': Price, 'TSLA': Price, ... }
  prices: Record<string, Price>;
  lastUpdate: number;
  isConnected: boolean;
  
  // Actions
  updatePrice: (symbol: string, price: Price) => void;
  updatePrices: (updates: Record<string, Price>) => void;
  setConnectionStatus: (connected: boolean) => void;
  clear: () => void;
}

export const usePriceStore = create<PriceState>()(
  subscribeWithSelector((set) => ({
    prices: {},
    lastUpdate: 0,
    isConnected: false,

    updatePrice: (symbol: string, price: Price) =>
      set((state) => ({
        prices: { ...state.prices, [symbol]: price },
        lastUpdate: Date.now(),
      })),

    updatePrices: (updates: Record<string, Price>) =>
      set((state) => ({
        prices: { ...state.prices, ...updates },
        lastUpdate: Date.now(),
      })),

    setConnectionStatus: (connected: boolean) =>
      set({ isConnected: connected }),

    clear: () =>
      set({ prices: {}, lastUpdate: 0 }),
  }))
);

// Selector hook: only re-render when *this specific* price changes
export const usePriceFor = (symbol: string) =>
  usePriceStore(
    (state) => state.prices[symbol]?.value ?? 0,
    (a, b) => a === b // Shallow equality: only re-render if price value changed
  );

// Selector hook: get full price object (including bid/ask)
export const useFullPriceFor = (symbol: string) =>
  usePriceStore(
    (state) => state.prices[symbol],
    (a, b) => a?.timestamp === b?.timestamp // Re-render only if updated
  );

// Subscribe to connection status
export const useConnectionStatus = () =>
  usePriceStore((state) => state.isConnected);

// ============================================================================
// FILE 2: src/hooks/useRealtimePrices.ts
// ============================================================================

import { useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { usePriceStore } from '../store/priceStore';

interface UseRealtimePricesOptions {
  symbols: string[];
  url?: string;
  onError?: (error: Error) => void;
}

export const useRealtimePrices = (options: UseRealtimePricesOptions) => {
  const { symbols, url = 'http://localhost:3000', onError } = options;
  const socketRef = useRef<Socket | null>(null);
  const updatePrices = usePriceStore((s) => s.updatePrices);
  const setConnectionStatus = usePriceStore((s) => s.setConnectionStatus);

  useEffect(() => {
    // Initialize socket connection with reconnection options
    const socket = io(url, {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 10,
      transports: ['websocket', 'polling'], // Fallback to polling if WS unavailable
    });

    socketRef.current = socket;

    // On connection
    socket.on('connect', () => {
      console.log('✅ Connected to price feed');
      setConnectionStatus(true);

      // Subscribe to these symbols
      socket.emit('subscribe', { symbols });
    });

    // Handle incoming price updates
    socket.on('price:update', (data: Record<string, any>) => {
      try {
        updatePrices(data);
      } catch (error) {
        console.error('Error updating prices:', error);
        onError?.(error as Error);
      }
    });

    // Reconnection event
    socket.on('reconnect', () => {
      console.log('🔄 Reconnected to price feed');
      setConnectionStatus(true);
      socket.emit('subscribe', { symbols });
    });

    // Connection error
    socket.on('connect_error', (error) => {
      console.error('❌ Connection error:', error);
      setConnectionStatus(false);
      onError?.(error);
    });

    // Disconnect
    socket.on('disconnect', (reason) => {
      console.log('Disconnected:', reason);
      setConnectionStatus(false);
    });

    // Cleanup function
    return () => {
      if (symbols.length > 0) {
        socket.emit('unsubscribe', { symbols });
      }
      socket.disconnect();
    };
  }, [symbols.join(','), url, updatePrices, setConnectionStatus, onError]); // Re-run if symbols change
};

// ============================================================================
// FILE 3: src/store/portfolioStore.ts
// ============================================================================

import { create } from 'zustand';

export interface Position {
  id: string;
  symbol: string;
  quantity: number;
  entryPrice: number;
  currentPrice: number; // Updated via price feed
  costBasis: number; // entryPrice * quantity
}

interface PortfolioState {
  positions: Position[];
  cash: number;
  leverage: number; // 1 = no leverage, 2 = 2x margin

  // Actions
  addPosition: (position: Position) => void;
  updatePosition: (id: string, currentPrice: number) => void;
  removePosition: (id: string) => void;
  setCash: (amount: number) => void;
  setLeverage: (leverage: number) => void;
}

export const usePortfolioStore = create<PortfolioState>((set) => ({
  positions: [],
  cash: 100000,
  leverage: 1,

  addPosition: (position) =>
    set((state) => ({
      positions: [...state.positions, position],
    })),

  updatePosition: (id, currentPrice) =>
    set((state) => ({
      positions: state.positions.map((p) =>
        p.id === id ? { ...p, currentPrice } : p
      ),
    })),

  removePosition: (id) =>
    set((state) => ({
      positions: state.positions.filter((p) => p.id !== id),
    })),

  setCash: (amount) => set({ cash: amount }),
  setLeverage: (leverage) => set({ leverage }),
}));

// Computed selectors
export const usePortfolioMetrics = () => {
  const positions = usePortfolioStore((s) => s.positions);
  const cash = usePortfolioStore((s) => s.cash);

  const totalMarketValue = positions.reduce(
    (sum, p) => sum + p.currentPrice * p.quantity,
    0
  );

  const totalCostBasis = positions.reduce((sum, p) => sum + p.costBasis, 0);

  const realizedPnL = 0; // Track separately in app
  const unrealizedPnL = totalMarketValue - totalCostBasis;
  const totalPnL = realizedPnL + unrealizedPnL;

  const totalEquity = cash + totalMarketValue;
  const totalReturn = ((totalPnL / totalCostBasis) * 100).toFixed(2);

  return {
    totalMarketValue,
    totalCostBasis,
    unrealizedPnL,
    totalPnL,
    totalEquity,
    totalReturn: parseFloat(totalReturn),
    cash,
  };
};

// ============================================================================
// FILE 4: src/components/PnLDashboard.tsx
// ============================================================================

import React from 'react';
import { useRealtimePrices } from '../hooks/useRealtimePrices';
import { usePriceFor, useConnectionStatus } from '../store/priceStore';
import { usePortfolioStore, usePortfolioMetrics } from '../store/portfolioStore';

// Header: Connection status + Account overview
export const DashboardHeader: React.FC = () => {
  const isConnected = useConnectionStatus();
  const metrics = usePortfolioMetrics();

  return (
    <div className="bg-slate-900 p-6 rounded-lg shadow-lg mb-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-3xl font-bold">Trading Dashboard</h1>
        <div className={`badge ${isConnected ? 'badge-success' : 'badge-error'}`}>
          {isConnected ? '🟢 Live' : '🔴 Offline'}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Equity"
          value={`$${metrics.totalEquity.toFixed(2)}`}
          change={metrics.totalReturn}
        />
        <StatCard
          label="Total P&L"
          value={`$${metrics.totalPnL.toFixed(2)}`}
          change={parseFloat(metrics.totalReturn)}
          color={metrics.totalPnL >= 0 ? 'text-green-500' : 'text-red-500'}
        />
        <StatCard
          label="Position Value"
          value={`$${metrics.totalMarketValue.toFixed(2)}`}
        />
        <StatCard
          label="Cash"
          value={`$${metrics.cash.toFixed(2)}`}
        />
      </div>
    </div>
  );
};

// Stat card component
const StatCard: React.FC<{
  label: string;
  value: string;
  change?: number;
  color?: string;
}> = ({ label, value, change, color = '' }) => (
  <div className="stat bg-slate-800">
    <div className="stat-title text-sm text-gray-400">{label}</div>
    <div className={`stat-value text-2xl font-bold ${color}`}>{value}</div>
    {change !== undefined && (
      <div className={`stat-desc ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
        {change >= 0 ? '+' : ''}{change.toFixed(2)}%
      </div>
    )}
  </div>
);

// Position row with live price updates
const PositionRow: React.FC<{ positionId: string; symbol: string }> = ({
  positionId,
  symbol,
}) => {
  const positions = usePortfolioStore((s) => s.positions);
  const position = positions.find((p) => p.id === positionId);
  const currentPrice = usePriceFor(symbol); // Optimized: only re-render when this price changes

  if (!position) return null;

  const pnl = (currentPrice - position.entryPrice) * position.quantity;
  const pnlPct = ((currentPrice / position.entryPrice - 1) * 100).toFixed(2);
  const isProfitable = pnl >= 0;

  return (
    <tr className="hover:bg-slate-700 transition">
      <td className="font-semibold">{symbol}</td>
      <td>{position.quantity}</td>
      <td>${position.entryPrice.toFixed(2)}</td>
      <td className="font-bold">${currentPrice?.toFixed(2) || '—'}</td>
      <td>${(currentPrice * position.quantity).toFixed(2)}</td>
      <td className={`font-bold ${isProfitable ? 'text-green-500' : 'text-red-500'}`}>
        ${pnl.toFixed(2)} ({pnlPct}%)
      </td>
    </tr>
  );
};

// Main dashboard
export const PnLDashboard: React.FC = () => {
  const positions = usePortfolioStore((s) => s.positions);
  const symbols = positions.map((p) => p.symbol);

  // Connect to real-time prices
  useRealtimePrices({ symbols });

  if (symbols.length === 0) {
    return (
      <div className="min-h-screen bg-slate-950 text-white p-8">
        <DashboardHeader />
        <div className="alert alert-info">
          <span>No positions loaded. Add positions to begin tracking.</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <DashboardHeader />

      {/* Positions Table */}
      <div className="overflow-x-auto bg-slate-900 rounded-lg shadow-lg">
        <table className="table w-full text-sm">
          <thead className="bg-slate-800">
            <tr>
              <th>Symbol</th>
              <th>Qty</th>
              <th>Entry</th>
              <th>Current</th>
              <th>Position Value</th>
              <th>P&L</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((position) => (
              <PositionRow
                key={position.id}
                positionId={position.id}
                symbol={position.symbol}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ============================================================================
// FILE 5: server/index.ts (Backend - Node.js + Express + Socket.io)
// ============================================================================

/*
npm install express cors socket.io

Run with:
npx ts-node server/index.ts
*/

import express from 'express';
import { createServer } from 'http';
import { Server, Socket } from 'socket.io';
import cors from 'cors';

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: ['http://localhost:5173', 'http://localhost:3000'],
    methods: ['GET', 'POST'],
  },
});

app.use(cors());
app.use(express.json());

// Track client subscriptions
const clientSubscriptions = new Map<string, Set<string>>();

// Simulated market data
const marketData = new Map([
  ['AAPL', { symbol: 'AAPL', value: 150.25, change: 1.2 }],
  ['TSLA', { symbol: 'TSLA', value: 210.55, change: -0.8 }],
  ['GOOGL', { symbol: 'GOOGL', value: 139.45, change: 0.5 }],
  ['MSFT', { symbol: 'MSFT', value: 380.0, change: 2.1 }],
]);

// Simulate price updates every 1 second
const simulatePrices = () => {
  const updates: Record<string, any> = {};

  for (const [symbol, data] of marketData) {
    // Random walk
    const changePercent = (Math.random() - 0.5) * 0.02; // ±1%
    const newPrice = data.value * (1 + changePercent);

    updates[symbol] = {
      symbol,
      value: newPrice,
      change: ((newPrice / data.value - 1) * 100).toFixed(2),
      changeAmount: (newPrice - data.value).toFixed(2),
      timestamp: Date.now(),
      bid: newPrice - 0.01,
      ask: newPrice + 0.01,
    };

    marketData.set(symbol, { ...data, value: newPrice });
  }

  // Broadcast to all clients
  io.emit('price:update', updates);
};

// Start price simulation
setInterval(simulatePrices, 1000);

// Socket.io connection handling
io.on('connection', (socket: Socket) => {
  console.log(`✅ Client connected: ${socket.id}`);
  clientSubscriptions.set(socket.id, new Set());

  // Client subscribes to symbols
  socket.on('subscribe', ({ symbols }: { symbols: string[] }) => {
    const subs = clientSubscriptions.get(socket.id) || new Set();
    symbols.forEach((s) => subs.add(s));
    clientSubscriptions.set(socket.id, subs);
    console.log(`  ${socket.id} subscribed to: ${symbols.join(', ')}`);
  });

  // Client unsubscribes
  socket.on('unsubscribe', ({ symbols }: { symbols: string[] }) => {
    const subs = clientSubscriptions.get(socket.id) || new Set();
    symbols.forEach((s) => subs.delete(s));
    console.log(`  ${socket.id} unsubscribed from: ${symbols.join(', ')}`);
  });

  // Cleanup on disconnect
  socket.on('disconnect', () => {
    clientSubscriptions.delete(socket.id);
    console.log(`❌ Client disconnected: ${socket.id}`);
  });
});

// REST endpoints
app.get('/health', (req, res) => {
  res.json({ status: 'ok', connectedClients: io.engine.clientsCount });
});

app.get('/prices', (req, res) => {
  const prices: Record<string, any> = {};
  for (const [symbol, data] of marketData) {
    prices[symbol] = data;
  }
  res.json(prices);
});

// Start server
server.listen(3000, () => {
  console.log('🚀 Server running on http://localhost:3000');
  console.log('📊 Dashboard: http://localhost:5173');
});

// ============================================================================
// FILE 6: src/main.tsx (React entry point)
// ============================================================================

/*
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
*/

// ============================================================================
// FILE 7: src/App.tsx (Main component)
// ============================================================================

/*
import { useEffect } from 'react'
import { usePortfolioStore } from './store/portfolioStore'
import { PnLDashboard } from './components/PnLDashboard'

function App() {
  // Load sample portfolio
  useEffect(() => {
    const portfolio = usePortfolioStore();
    
    portfolio.addPosition({
      id: '1',
      symbol: 'AAPL',
      quantity: 100,
      entryPrice: 148.0,
      currentPrice: 150.25,
      costBasis: 14800,
    });
    
    portfolio.addPosition({
      id: '2',
      symbol: 'TSLA',
      quantity: 50,
      entryPrice: 215.0,
      currentPrice: 210.55,
      costBasis: 10750,
    });
  }, []);

  return <PnLDashboard />
}

export default App
*/

export {};
