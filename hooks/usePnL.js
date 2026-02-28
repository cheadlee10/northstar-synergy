/**
 * P&L Store (Zustand)
 * Global state management for P&L data with selective subscriptions
 * Persists to localStorage automatically
 */

import { useEffect } from 'react';
import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { useSocket } from './socket';
import { normalizeTimestamp, formatCurrency } from '../utils/dataTransform';

// Storage key for localStorage
const STORAGE_KEY = 'pnl-store';

/**
 * Zustand Store for P&L Data
 * Features:
 * - Persistent storage to localStorage
 * - DevTools integration (dev only)
 * - Selector-based subscriptions (only re-render on relevant changes)
 */
export const usePnLStore = create(
  devtools(
    persist(
      subscribeWithSelector((set, get) => ({
        // Core P&L data
        revenue: 0,
        expenses: 0,
        net: 0,
        marginPercent: 0,

        // Trends (historical data)
        trends: {
          revenue: [],
          expenses: [],
          net: [],
          dates: [],
        },

        // Metadata
        lastUpdated: null,
        dataSource: 'mock', // 'live' or 'mock'
        isLoading: true,
        error: null,

        // Actions
        setPnL: (pnlData) =>
          set((state) => {
            const { revenue, expenses, margin_percent, updated_at } = pnlData;
            const net = revenue - expenses;

            return {
              revenue,
              expenses,
              net,
              marginPercent: margin_percent ?? 0,
              lastUpdated: normalizeTimestamp(updated_at),
              isLoading: false,
              error: null,
            };
          }),

        addTrendPoint: (trendData) =>
          set((state) => {
            const { revenue, expenses, net, timestamp } = trendData;
            const newDate = normalizeTimestamp(timestamp);

            // Keep only last 100 data points
            const maxPoints = 100;
            const trimStart = state.trends.dates.length >= maxPoints ? 1 : 0;

            return {
              trends: {
                revenue: [...state.trends.revenue.slice(trimStart), revenue],
                expenses: [...state.trends.expenses.slice(trimStart), expenses],
                net: [...state.trends.net.slice(trimStart), net],
                dates: [...state.trends.dates.slice(trimStart), newDate],
              },
            };
          }),

        updateTrends: (trendsData) =>
          set(() => ({
            trends: {
              revenue: trendsData.revenue || [],
              expenses: trendsData.expenses || [],
              net: trendsData.net || [],
              dates: (trendsData.dates || []).map(normalizeTimestamp),
            },
          })),

        setError: (error) =>
          set({
            error,
            isLoading: false,
            dataSource: 'error',
          }),

        setLoading: (isLoading) =>
          set({ isLoading }),

        setDataSource: (source) =>
          set({ dataSource: source }),

        clearError: () =>
          set({ error: null }),

        // Reset to initial state
        reset: () =>
          set({
            revenue: 0,
            expenses: 0,
            net: 0,
            marginPercent: 0,
            trends: { revenue: [], expenses: [], net: [], dates: [] },
            lastUpdated: null,
            dataSource: 'mock',
            isLoading: true,
            error: null,
          }),
      })),
      {
        name: STORAGE_KEY,
        // Persist only essential data, not loading states
        partialize: (state) => ({
          revenue: state.revenue,
          expenses: state.expenses,
          net: state.net,
          marginPercent: state.marginPercent,
          trends: state.trends,
          lastUpdated: state.lastUpdated,
        }),
      }
    ),
    { name: 'PnL Store' }
  )
);

/**
 * Selector: Get all P&L data
 */
export const selectPnL = (state) => ({
  revenue: state.revenue,
  expenses: state.expenses,
  net: state.net,
  marginPercent: state.marginPercent,
  lastUpdated: state.lastUpdated,
});

/**
 * Selector: Get trends data
 */
export const selectTrends = (state) => state.trends;

/**
 * Selector: Get status (loading, error, source)
 */
export const selectStatus = (state) => ({
  isLoading: state.isLoading,
  error: state.error,
  dataSource: state.dataSource,
  lastUpdated: state.lastUpdated,
});

/**
 * Selector: Get financial summary with formatted values
 */
export const selectSummary = (state) => ({
  revenue: formatCurrency(state.revenue),
  expenses: formatCurrency(state.expenses),
  net: formatCurrency(state.net),
  marginPercent: state.marginPercent ? `${state.marginPercent.toFixed(2)}%` : '0%',
});

/**
 * usePnL Hook
 * Combines Socket.io updates with Zustand store
 * Handles connection, data transformation, and state persistence
 *
 * @param {Object} options - Configuration
 * @param {string} options.source - 'live' for backend, 'mock' for development
 * @param {Function} options.onError - Custom error handler
 * @returns {Object} P&L data, status, and controls
 */
export const usePnL = (options = {}) => {
  const { source = 'live', onError = null } = options;

  // Subscribe to store with selective updates
  const pnlData = usePnLStore(selectPnL);
  const trends = usePnLStore(selectTrends);
  const status = usePnLStore(selectStatus);
  const actions = usePnLStore((state) => ({
    setPnL: state.setPnL,
    addTrendPoint: state.addTrendPoint,
    updateTrends: state.updateTrends,
    setError: state.setError,
    setLoading: state.setLoading,
    clearError: state.clearError,
    reset: state.reset,
  }));

  // Setup socket connection
  const { subscribe, isConnected } = useSocket(
    () => {
      actions.setDataSource('live');
      actions.clearError();
    },
    () => {
      actions.setError('WebSocket disconnected');
    }
  );

  // Subscribe to P&L updates
  useEffect(() => {
    if (source === 'mock') {
      actions.setDataSource('mock');
      actions.setLoading(false);
      return;
    }

    if (!isConnected) return;

    // Subscribe to main P&L updates
    const unsubscribePnL = subscribe('pnl:update', (data) => {
      try {
        actions.setPnL(data);
      } catch (error) {
        console.error('[usePnL] Error processing P&L update:', error);
        actions.setError(error.message);
        onError?.(error);
      }
    });

    // Subscribe to trends updates
    const unsubscribeTrends = subscribe('pnl:trends', (data) => {
      try {
        actions.updateTrends(data);
      } catch (error) {
        console.error('[usePnL] Error processing trends:', error);
        onError?.(error);
      }
    });

    // Request initial data
    subscribe('pnl:initial', (data) => {
      actions.setPnL(data);
      actions.setLoading(false);
    });

    return () => {
      unsubscribePnL();
      unsubscribeTrends();
    };
  }, [isConnected, source, subscribe, actions, onError]);

  return {
    // Data
    pnl: pnlData,
    trends,
    
    // Status
    isConnected,
    isLoading: status.isLoading,
    error: status.error,
    dataSource: status.dataSource,
    lastUpdated: status.lastUpdated,

    // Actions
    refresh: () => {
      if (isConnected) {
        actions.setLoading(true);
      }
    },
    reset: actions.reset,
    clearError: actions.clearError,
  };
};

/**
 * Hook for selective P&L subscription (revenue only)
 */
export const useRevenueOnly = () =>
  usePnLStore((state) => ({
    revenue: state.revenue,
    lastUpdated: state.lastUpdated,
  }));

/**
 * Hook for selective P&L subscription (expenses only)
 */
export const useExpensesOnly = () =>
  usePnLStore((state) => ({
    expenses: state.expenses,
    lastUpdated: state.lastUpdated,
  }));

/**
 * Hook for selective P&L subscription (net profit only)
 */
export const useNetProfitOnly = () =>
  usePnLStore((state) => ({
    net: state.net,
    marginPercent: state.marginPercent,
    lastUpdated: state.lastUpdated,
  }));

/**
 * Hook for selective P&L subscription (trends only)
 */
export const useTrendsOnly = () =>
  usePnLStore((state) => ({
    trends: state.trends,
    lastUpdated: state.lastUpdated,
  }));
