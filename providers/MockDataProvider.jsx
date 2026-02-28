/**
 * Mock Data Provider
 * Simulates WebSocket P&L updates for development and testing
 * Generates realistic trending data without backend connection
 */

import { useEffect, useRef, useCallback } from 'react';
import { usePnLStore } from '../hooks/usePnL';
import { generateMockPnL, aggregatePnL } from '../utils/dataTransform';

const DEFAULT_UPDATE_INTERVAL = 5000; // 5 seconds

/**
 * MockDataProvider Hook
 * Simulates server-sent P&L updates with realistic trends
 *
 * @param {Object} options - Configuration
 * @returns {Object} Control functions
 */
export const useMockDataProvider = (options = {}) => {
  const {
    updateInterval = DEFAULT_UPDATE_INTERVAL,
    volatility = 0.1,
    baseRevenue = 50000,
    baseExpenses = 30000,
    trending = 'neutral', // 'up', 'down', 'neutral'
    autoStart = true,
  } = options;

  const store = usePnLStore();
  const timerRef = useRef(null);
  const stateRef = useRef({
    revenue: baseRevenue,
    expenses: baseExpenses,
    updateCount: 0,
  });

  /**
   * Generate next mock data point
   */
  const generateNextUpdate = useCallback(() => {
    const state = stateRef.current;
    const now = new Date().toISOString();

    // Apply trending
    let revenueMultiplier = 1;
    let expensesMultiplier = 1;

    switch (trending) {
      case 'up':
        revenueMultiplier = 1 + (Math.random() * volatility * 0.5 + volatility * 0.25);
        expensesMultiplier = 1 + (Math.random() * volatility * 0.3);
        break;
      case 'down':
        revenueMultiplier = 1 - (Math.random() * volatility * 0.5 + volatility * 0.25);
        expensesMultiplier = 1 + (Math.random() * volatility * 0.3);
        break;
      default: // neutral
        revenueMultiplier = 1 + (Math.random() - 0.5) * volatility;
        expensesMultiplier = 1 + (Math.random() - 0.5) * volatility;
    }

    state.revenue = Math.max(1000, state.revenue * revenueMultiplier);
    state.expenses = Math.max(100, state.expenses * expensesMultiplier);
    state.updateCount += 1;

    const net = state.revenue - state.expenses;
    const marginPercent = net > 0 ? (net / state.revenue) * 100 : 0;

    return {
      revenue: state.revenue,
      expenses: state.expenses,
      net,
      margin_percent: marginPercent,
      updated_at: now,
    };
  }, [volatility, trending]);

  /**
   * Push update to store
   */
  const pushUpdate = useCallback(() => {
    const update = generateNextUpdate();
    store.setPnL(update);
    store.addTrendPoint(update);
    store.setDataSource('mock');
  }, [generateNextUpdate, store]);

  /**
   * Start auto-updating
   */
  const start = useCallback(() => {
    if (timerRef.current) return; // Already running

    store.setLoading(false);
    store.clearError();

    // Immediately send first update
    pushUpdate();

    // Schedule recurring updates
    timerRef.current = setInterval(() => {
      pushUpdate();
    }, updateInterval);
  }, [pushUpdate, store, updateInterval]);

  /**
   * Stop auto-updating
   */
  const stop = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  /**
   * Send single update
   */
  const update = useCallback(() => {
    pushUpdate();
  }, [pushUpdate]);

  /**
   * Reset to initial state
   */
  const reset = useCallback(() => {
    stop();
    stateRef.current = {
      revenue: baseRevenue,
      expenses: baseExpenses,
      updateCount: 0,
    };
    store.reset();
  }, [stop, baseRevenue, baseExpenses, store]);

  /**
   * Change trending direction
   */
  const setTrending = useCallback(
    (newTrending) => {
      // Note: can't directly reassign trending parameter, so this is for documentation
      console.warn(
        '[MockDataProvider] To change trending, create new hook with options={...options, trending}'
      );
    },
    []
  );

  /**
   * Initialize on mount
   */
  useEffect(() => {
    if (autoStart) {
      start();
    }

    return () => {
      stop();
    };
  }, [autoStart, start, stop]);

  return {
    start,
    stop,
    update,
    reset,
    setTrending,
    updateCount: stateRef.current.updateCount,
  };
};

/**
 * MockDataProvider Component
 * Wraps children with mock data generation
 * Useful for Storybook stories or isolated testing
 */
export const MockDataProvider = ({
  children,
  options = {},
  showStatus = false,
}) => {
  const { updateCount, start, stop } = useMockDataProvider(options);
  const { dataSource } = usePnLStore((state) => ({
    dataSource: state.dataSource,
  }));

  return (
    <>
      {showStatus && (
        <div
          style={{
            padding: '8px 12px',
            backgroundColor: '#e8f4f8',
            borderBottom: '1px solid #b3d9e8',
            fontSize: '12px',
            color: '#006080',
            fontFamily: 'monospace',
          }}
        >
          📊 Mock Data Provider | Updates: {updateCount} | Source: {dataSource}
          <button
            onClick={stop}
            style={{
              marginLeft: '16px',
              padding: '4px 8px',
              fontSize: '11px',
              cursor: 'pointer',
            }}
          >
            Stop
          </button>
          <button
            onClick={start}
            style={{
              marginLeft: '4px',
              padding: '4px 8px',
              fontSize: '11px',
              cursor: 'pointer',
            }}
          >
            Start
          </button>
        </div>
      )}
      {children}
    </>
  );
};

/**
 * Batch data generator for testing
 * Returns pre-generated mock data without WebSocket
 */
export const generateMockBatch = (count = 30, options = {}) => {
  const {
    baseRevenue = 50000,
    baseExpenses = 30000,
    volatility = 0.1,
  } = options;

  return generateMockPnL({
    baseRevenue,
    baseExpenses,
    trendPoints: count,
    volatility,
  });
};

/**
 * Hook for testing snapshots
 * Returns pre-generated trends without state management
 */
export const useMockSnapshot = (count = 30) => {
  const data = useRef(generateMockBatch(count)).current;
  return data;
};

/**
 * Stress test data generator
 * Creates sharp changes for testing error handling and edge cases
 */
export const generateStressTestData = (count = 30) => {
  const trends = [];
  const now = new Date();
  let revenue = 50000;
  let expenses = 30000;

  for (let i = count - 1; i >= 0; i--) {
    // Create sudden spikes and drops
    const random = Math.random();
    if (random > 0.9) {
      revenue *= 1.3; // 10% chance of 30% spike
    } else if (random < 0.05) {
      revenue *= 0.7; // 5% chance of 30% drop
    } else {
      revenue *= 0.95 + Math.random() * 0.1; // Normal variation
    }

    if (Math.random() > 0.85) {
      expenses *= 1.2;
    } else if (Math.random() < 0.05) {
      expenses *= 0.8;
    } else {
      expenses *= 0.95 + Math.random() * 0.1;
    }

    revenue = Math.max(1000, revenue);
    expenses = Math.max(100, expenses);

    const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000); // Hours back

    trends.push({
      revenue,
      expenses,
      net: revenue - expenses,
      timestamp: timestamp.toISOString(),
    });
  }

  const latestTrend = trends[trends.length - 1];

  return {
    current: {
      revenue: latestTrend.revenue,
      expenses: latestTrend.expenses,
      net: latestTrend.net,
      margin_percent:
        latestTrend.revenue > 0
          ? ((latestTrend.net / latestTrend.revenue) * 100)
          : 0,
      updated_at: latestTrend.timestamp,
    },
    trends,
  };
};
