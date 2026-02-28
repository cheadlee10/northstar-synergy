/**
 * Unit Tests for P&L Aggregator (Calculation Engine)
 */

const { DataAggregator } = require('../../lib/aggregator');
const { KalshiMockDataFactory } = require('../mocks/kalshi.mock');
const { AnthropicMockDataFactory } = require('../mocks/anthropic.mock');
const { JohnMockDataFactory } = require('../mocks/john.mock');

// Mock dependencies
jest.mock('../../lib/logger');
const logger = require('../../lib/logger');

// Mock cache manager
const mockCacheManager = {
  initialize: jest.fn().mockResolvedValue(true),
  set: jest.fn().mockResolvedValue(true),
  get: jest.fn().mockResolvedValue(null),
  getStats: jest.fn().mockResolvedValue({})
};

// Mock circuit breaker
const mockCircuitBreaker = {
  execute: jest.fn((name, fn) => fn())
};

describe('DataAggregator - P&L Calculation Engine', () => {
  let aggregator;

  beforeEach(() => {
    aggregator = new DataAggregator(mockCacheManager, mockCircuitBreaker);
    jest.clearAllMocks();
  });

  // ============================================================================
  // BASIC INITIALIZATION TESTS
  // ============================================================================

  describe('Initialization', () => {
    test('should initialize aggregator', async () => {
      await aggregator.initialize();
      expect(aggregator).toBeDefined();
      expect(aggregator.pnlHistory).toEqual([]);
    });

    test('should have correct default values', () => {
      expect(aggregator.defaults.kalshi).toEqual({
        balance: 0,
        positions: [],
        pnl: 0
      });
    });
  });

  // ============================================================================
  // P&L METRIC CALCULATION TESTS
  // ============================================================================

  describe('P&L Metric Calculations', () => {
    test('should calculate metrics with positive revenue and expenses', () => {
      const kalshiData = { balance: 50000, positions: 5, pnl: 5000 };
      const anthropicData = { dailySpend: 25.50 };
      const johnsData = { invoiced: 20000, collected: 18000 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      // Revenue = Kalshi PnL + John's collected = 5000 + 18000 = 23000
      expect(metrics.totalRevenue).toBe(23000);
      
      // Expenses = Anthropic daily spend = 25.50
      expect(metrics.totalExpenses).toBe(25.50);
      
      // Net PnL = 23000 - 25.50 = 22974.50
      expect(metrics.netPnL).toBe(22974.50);
    });

    test('should calculate gross margin correctly', () => {
      const kalshiData = { balance: 50000, positions: 5, pnl: 10000 };
      const anthropicData = { dailySpend: 2000 };
      const johnsData = { invoiced: 0, collected: 0 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      // Revenue = 10000, Expenses = 2000
      // Margin = (10000 - 2000) / 10000 * 100 = 80%
      expect(metrics.grossMargin).toBe(80);
    });

    test('should handle zero revenue scenario', () => {
      const kalshiData = { balance: 50000, positions: 0, pnl: 0 };
      const anthropicData = { dailySpend: 100 };
      const johnsData = { invoiced: 0, collected: 0 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      expect(metrics.totalRevenue).toBe(0);
      expect(metrics.totalExpenses).toBe(100);
      expect(metrics.netPnL).toBe(-100);
      expect(metrics.grossMargin).toBe(0);
    });

    test('should handle high expenses scenario', () => {
      const kalshiData = { balance: 10000, positions: 2, pnl: 1000 };
      const anthropicData = { dailySpend: 5000 };
      const johnsData = { invoiced: 0, collected: 0 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      expect(metrics.netPnL).toBe(-4000); // Negative PnL
      expect(metrics.grossMargin).toBeLessThan(0);
    });

    test('should have timestamp in metrics', () => {
      const kalshiData = { balance: 5000, positions: 1, pnl: 500 };
      const anthropicData = { dailySpend: 10 };
      const johnsData = { invoiced: 0, collected: 0 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      expect(metrics.timestamp).toBeDefined();
      expect(metrics.calculatedAt).toBeDefined();
      expect(typeof metrics.timestamp).toBe('string');
    });

    test('should include component breakdown', () => {
      const kalshiData = { balance: 5000, positions: 1, pnl: 500 };
      const anthropicData = { dailySpend: 10 };
      const johnsData = { invoiced: 1000, collected: 800 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      expect(metrics.components).toBeDefined();
      expect(metrics.components.kalshi).toEqual(kalshiData);
      expect(metrics.components.anthropic).toEqual(anthropicData);
      expect(metrics.components.johns).toEqual(johnsData);
    });
  });

  // ============================================================================
  // DAILY TREND CALCULATION TESTS
  // ============================================================================

  describe('Daily Trend Calculation', () => {
    test('should return 0 for single entry', () => {
      aggregator.pnlHistory = [{ netPnL: 1000 }];
      const trend = aggregator.calculateDailyTrend();
      expect(trend).toBe(0);
    });

    test('should calculate positive trend', () => {
      aggregator.pnlHistory = [
        { netPnL: 1000 }, // oldest
        { netPnL: 2000 }  // newest
      ];
      const trend = aggregator.calculateDailyTrend();
      expect(trend).toBe(100); // 100% increase
    });

    test('should calculate negative trend', () => {
      aggregator.pnlHistory = [
        { netPnL: 2000 }, // oldest
        { netPnL: 1000 }  // newest
      ];
      const trend = aggregator.calculateDailyTrend();
      expect(trend).toBe(-50); // 50% decrease
    });

    test('should handle zero previous value', () => {
      aggregator.pnlHistory = [
        { netPnL: 0 },    // oldest
        { netPnL: 1000 }  // newest
      ];
      const trend = aggregator.calculateDailyTrend();
      expect(trend).toBe(100);
    });

    test('should handle multiple history entries', () => {
      aggregator.pnlHistory = [
        { netPnL: 1000 },
        { netPnL: 1500 },
        { netPnL: 1200 },
        { netPnL: 2000 }
      ];
      const trend = aggregator.calculateDailyTrend();
      // Compare last (2000) with first (1000) = 100% increase
      expect(trend).toBe(100);
    });
  });

  // ============================================================================
  // REAL-WORLD SCENARIO TESTS
  // ============================================================================

  describe('Real-World Scenarios', () => {
    test('should calculate P&L for winning trading day', () => {
      const kalshiData = KalshiMockDataFactory.generateWinningScenario();
      const anthropicData = { dailySpend: 5.00 };
      const johnsData = { invoiced: 0, collected: 0 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      expect(metrics.netPnL).toBeGreaterThan(0);
      expect(metrics.grossMargin).toBeGreaterThan(0);
    });

    test('should calculate P&L for losing trading day', () => {
      const kalshiData = KalshiMockDataFactory.generateLosingScenario();
      const anthropicData = { dailySpend: 10.00 };
      const johnsData = { invoiced: 0, collected: 0 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      expect(metrics.netPnL).toBeLessThan(0);
      expect(metrics.grossMargin).toBeLessThan(0);
    });

    test('should calculate P&L with mixed trading outcomes', () => {
      const kalshiData = KalshiMockDataFactory.generateMixedScenario();
      const anthropicData = { dailySpend: 15.00 };
      const johnsData = { invoiced: 30000, collected: 25000 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      expect(metrics.totalRevenue).toBeGreaterThan(0);
      expect(metrics.totalExpenses).toBeGreaterThan(0);
      expect(metrics.netPnL).toBeDefined();
    });

    test('should handle high Anthropic costs', () => {
      const kalshiData = { balance: 50000, positions: 3, pnl: 3000 };
      const anthropicData = AnthropicMockDataFactory.generateHighUsageDay();
      const johnsData = { invoiced: 0, collected: 0 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      // High costs should reduce margin
      expect(metrics.totalExpenses).toBeGreaterThan(metrics.totalRevenue);
    });

    test('should handle strong John\'s revenue', () => {
      const kalshiData = { balance: 10000, positions: 1, pnl: 500 };
      const anthropicData = { dailySpend: 10 };
      const johnsData = JohnMockDataFactory.generateHighCollectionScenario();

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      expect(metrics.totalRevenue).toBeGreaterThan(5000);
      expect(metrics.netPnL).toBeGreaterThan(metrics.totalRevenue - 50);
    });
  });

  // ============================================================================
  // ROUNDING AND PRECISION TESTS
  // ============================================================================

  describe('Currency Precision', () => {
    test('should round currency values to 2 decimals', () => {
      const kalshiData = { balance: 1000.999, positions: 0, pnl: 0.001 };
      const anthropicData = { dailySpend: 0.005 };
      const johnsData = { invoiced: 0, collected: 0 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      // Check all values are properly rounded
      expect(metrics.totalRevenue).toBe(0); // 0.001 rounds to 0
      expect(String(metrics.totalExpenses).split('.')[1].length).toBeLessThanOrEqual(2);
      expect(String(metrics.netPnL).split('.')[1].length).toBeLessThanOrEqual(2);
    });

    test('should prevent floating point arithmetic errors', () => {
      const kalshiData = { balance: 0, positions: 0, pnl: 0.1 };
      const anthropicData = { dailySpend: 0.2 };
      const johnsData = { invoiced: 0, collected: 0 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      // 0.1 - 0.2 should equal -0.1, not -0.09999999999
      expect(metrics.netPnL).toBe(-0.1);
    });
  });

  // ============================================================================
  // WATERFALL DECOMPOSITION TESTS
  // ============================================================================

  describe('Waterfall Decomposition', () => {
    test('should break down revenue sources correctly', () => {
      const kalshiData = { balance: 0, positions: 0, pnl: 5000 };
      const anthropicData = { dailySpend: 0 };
      const johnsData = { invoiced: 0, collected: 10000 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      // Revenue = Kalshi PnL + John's collected
      expect(metrics.totalRevenue).toBe(5000 + 10000);
      expect(metrics.components.kalshi.pnl).toBe(5000);
      expect(metrics.components.johns.collected).toBe(10000);
    });

    test('should break down expense sources correctly', () => {
      const kalshiData = { balance: 0, positions: 0, pnl: 0 };
      const anthropicData = { dailySpend: 500 };
      const johnsData = { invoiced: 0, collected: 0 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      // Expenses = Anthropic daily spend
      expect(metrics.totalExpenses).toBe(500);
      expect(metrics.components.anthropic.dailySpend).toBe(500);
    });

    test('should reconstruct total from waterfall components', () => {
      const kalshiData = { balance: 0, positions: 0, pnl: 3000 };
      const anthropicData = { dailySpend: 150 };
      const johnsData = { invoiced: 0, collected: 7000 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      const reconstructedRevenue = 
        metrics.components.kalshi.pnl + 
        metrics.components.johns.collected;

      const reconstructedExpenses = 
        metrics.components.anthropic.dailySpend;

      const reconstructedNet = reconstructedRevenue - reconstructedExpenses;

      expect(reconstructedRevenue).toBe(metrics.totalRevenue);
      expect(reconstructedExpenses).toBe(metrics.totalExpenses);
      expect(reconstructedNet).toBe(metrics.netPnL);
    });
  });

  // ============================================================================
  // EDGE CASES
  // ============================================================================

  describe('Edge Cases', () => {
    test('should handle all-zero data', () => {
      const kalshiData = { balance: 0, positions: 0, pnl: 0 };
      const anthropicData = { dailySpend: 0 };
      const johnsData = { invoiced: 0, collected: 0 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      expect(metrics.totalRevenue).toBe(0);
      expect(metrics.totalExpenses).toBe(0);
      expect(metrics.netPnL).toBe(0);
      expect(metrics.grossMargin).toBe(0);
    });

    test('should handle missing optional fields', () => {
      const kalshiData = { pnl: 1000 }; // missing balance, positions
      const anthropicData = {}; // missing dailySpend
      const johnsData = {}; // missing everything

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      expect(metrics.totalRevenue).toBe(1000);
      expect(metrics.totalExpenses).toBe(0);
      expect(metrics.netPnL).toBe(1000);
    });

    test('should handle very large numbers', () => {
      const kalshiData = { balance: 0, positions: 0, pnl: 999999999.99 };
      const anthropicData = { dailySpend: 1000000.50 };
      const johnsData = { invoiced: 0, collected: 0 };

      const metrics = aggregator.calculatePnLMetrics(
        kalshiData,
        anthropicData,
        johnsData
      );

      expect(metrics.totalRevenue).toBe(999999999.99);
      expect(metrics.netPnL).toBe(999999999.99 - 1000000.50);
    });
  });
});
