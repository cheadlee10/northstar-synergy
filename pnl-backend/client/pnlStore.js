/**
 * Zustand store for P&L data management
 * Integrates with Socket.io for real-time updates
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { io } from 'socket.io-client';

// Socket.io configuration
const SOCKET_SERVER = process.env.REACT_APP_SOCKET_SERVER || 'http://localhost:3000';
const API_KEY = process.env.REACT_APP_API_KEY || 'default-key';

/**
 * Zustand store for P&L state management
 */
export const usePnLStore = create(
  devtools(
    persist(
      (set, get) => ({
        // State
        socket: null,
        connected: false,
        pnl: {
          totalRevenue: 0,
          totalExpenses: 0,
          netPnL: 0,
          grossMargin: 0,
          dailyTrend: 0,
          components: {
            kalshi: { balance: 0, positions: 0, pnl: 0 },
            anthropic: { dailySpend: 0 },
            johns: { invoiced: 0, collected: 0 }
          },
          timestamp: null,
          calculatedAt: null
        },
        components: {
          kalshi: { balance: 0, positions: 0, pnl: 0 },
          anthropic: { dailySpend: 0 },
          johns: { invoiced: 0, collected: 0 }
        },
        history: [],
        error: null,
        loading: false,
        lastUpdate: null,

        // Actions
        /**
         * Initialize socket connection
         */
        initSocket: async () => {
          try {
            set({ loading: true });

            const socket = io(SOCKET_SERVER, {
              auth: { apiKey: API_KEY },
              reconnection: true,
              reconnectionDelay: 1000,
              reconnectionDelayMax: 5000,
              reconnectionAttempts: 5,
              transports: ['websocket', 'polling'] // WebSocket primary, polling fallback
            });

            // Connection success
            socket.on('connect_success', (data) => {
              console.log('✅ Connected to P&L server', data);
              set({ connected: true, error: null });
              
              // Subscribe to P&L updates
              socket.emit('subscribe_pnl');
              socket.emit('subscribe_components');
            });

            // P&L updates
            socket.on('pnl_update', (data) => {
              set((state) => ({
                pnl: data.data,
                lastUpdate: data.timestamp,
                history: [...state.history.slice(-99), data.data] // Keep last 100
              }));
            });

            // Component updates
            socket.on('components_update', (data) => {
              set({
                components: data.data,
                lastUpdate: data.timestamp
              });
            });

            // Error handling
            socket.on('error', (error) => {
              console.error('Socket error:', error);
              set({ error: error.message });
            });

            socket.on('stream_error', (error) => {
              console.error('Stream error:', error);
              set({ error: error.message });
            });

            // Disconnection
            socket.on('disconnect', () => {
              console.warn('⚠️ Disconnected from P&L server');
              set({ connected: false });
            });

            set({ socket, loading: false });
          } catch (error) {
            console.error('Failed to initialize socket:', error);
            set({ error: error.message, loading: false });
          }
        },

        /**
         * Fetch current P&L snapshot
         */
        fetchCurrentPnL: async () => {
          try {
            set({ loading: true });

            const response = await fetch(`${SOCKET_SERVER}/api/pnl/current`, {
              headers: { 'x-api-key': API_KEY }
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            set({
              pnl: result.data,
              lastUpdate: result.timestamp,
              error: null,
              loading: false
            });

            return result.data;
          } catch (error) {
            console.error('Failed to fetch P&L:', error);
            set({ error: error.message, loading: false });
            throw error;
          }
        },

        /**
         * Fetch P&L history
         */
        fetchHistory: async (limit = 100) => {
          try {
            const response = await fetch(
              `${SOCKET_SERVER}/api/pnl/history?limit=${limit}`,
              { headers: { 'x-api-key': API_KEY } }
            );

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            set({ history: result.data.data });

            return result.data;
          } catch (error) {
            console.error('Failed to fetch history:', error);
            set({ error: error.message });
            throw error;
          }
        },

        /**
         * Fetch component breakdown
         */
        fetchComponentBreakdown: async () => {
          try {
            const response = await fetch(
              `${SOCKET_SERVER}/api/pnl/breakdown`,
              { headers: { 'x-api-key': API_KEY } }
            );

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const result = await response.json();
            set({ components: result.data });

            return result.data;
          } catch (error) {
            console.error('Failed to fetch breakdown:', error);
            set({ error: error.message });
            throw error;
          }
        },

        /**
         * Disconnect socket
         */
        disconnect: () => {
          const { socket } = get();
          if (socket) {
            socket.disconnect();
            set({ socket: null, connected: false });
          }
        },

        /**
         * Clear error
         */
        clearError: () => set({ error: null }),

        /**
         * Clear history
         */
        clearHistory: () => set({ history: [] })
      }),
      {
        name: 'pnl-store',
        partialize: (state) => ({
          pnl: state.pnl,
          history: state.history,
          components: state.components
        })
      }
    )
  )
);

/**
 * Hook to initialize socket on component mount
 */
export function usePnLSocket() {
  const { initSocket, disconnect } = usePnLStore();

  return { initSocket, disconnect };
}

/**
 * Hook to fetch P&L data
 */
export function useFetchPnL() {
  const { fetchCurrentPnL, fetchHistory, fetchComponentBreakdown } = usePnLStore();

  return { fetchCurrentPnL, fetchHistory, fetchComponentBreakdown };
}

/**
 * Selector hooks
 */
export const usePnLMetrics = () => usePnLStore((state) => state.pnl);
export const usePnLComponents = () => usePnLStore((state) => state.components);
export const usePnLHistory = () => usePnLStore((state) => state.history);
export const usePnLConnection = () => usePnLStore((state) => ({ 
  connected: state.connected, 
  loading: state.loading,
  error: state.error 
}));
export const useLastUpdate = () => usePnLStore((state) => state.lastUpdate);
