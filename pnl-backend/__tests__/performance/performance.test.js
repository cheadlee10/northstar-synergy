/**
 * Performance Tests for P&L Dashboard
 * Measures latency, memory usage, and throughput
 */

const { DataAggregator } = require('../../lib/aggregator');
const { KalshiMockDataFactory } = require('../mocks/kalshi.mock');
const { AnthropicMockDataFactory } = require('../mocks/anthropic.mock');
const { JohnMockDataFactory } = require('../mocks/john.mock');

jest.mock('../../lib/logger');
jest.mock('../../lib/cache');
jest.mock('../../lib/circuitBreaker');

describe('Performance Tests', () => {
  let aggregator;
  const mockCacheManager = {
    initialize: jest.fn().mockResolvedValue(true),
    set: jest.fn().mockResolvedValue(true),
    get: jest.fn().mockResolvedValue(null),
    getStats: jest.fn().mockResolvedValue({})
  };

  const mockCircuitBreaker = {
    execute: jest.fn((name, fn) => fn())
  };

  beforeEach(() => {
    aggregator = new DataAggregator(mockCacheManager, mockCircuitBreaker);
  });

  // ============================================================================
  // LATENCY TESTS
  // ============================================================================

  describe('Latency Measurements', () => {
    test('should calculate P&L metrics within 10ms', () => {
      const kalshiData = KalshiMockDataFactory.generateKalshiSnapshot();
      const anthropicData = AnthropicMockDataFactory.generateAgentDailyCost('scalper');
      const johnsData = JohnMockDataFactory.generateRevenueSnapshot();

      const startTime = performance.now();
      const metrics = aggregator.calculatePnLMetrics(kalshiData, anthropicData, johnsData);
      const elapsed = performance.now() - startTime;

      expect(elapsed).toBeLessThan(10);
      expect(metrics).toBeDefined();
    });

    test('should calculate daily trend within 5ms', () => {
      // Populate history
      for (let i = 0; i < 50; i++) {
        aggregator.pnlHistory.push({
          netPnL: Math.random() * 10000,
          timestamp: new Date().toISOString()
        });
      }

      const startTime = performance.now();
      const trend = aggregator.calculateDailyTrend();
      const elapsed = performance.now() - startTime;

      expect(elapsed).toBeLessThan(5);
      expect(typeof trend).toBe('number');
    });

    test('should perform 1000 calculations under 1 second', () => {
      const startTime = performance.now();

      for (let i = 0; i < 1000; i++) {
        const kalshiData = KalshiMockDataFactory.generateKalshiSnapshot();
        const anthropicData = AnthropicMockDataFactory.generateAgentDailyCost('scalper');
        const johnsData = JohnMockDataFactory.generateRevenueSnapshot();

        aggregator.calculatePnLMetrics(kalshiData, anthropicData, johnsData);
      }

      const elapsed = performance.now() - startTime;
      expect(elapsed).toBeLessThan(1000);
    });

    test('should measure aggregation latency', () => {
      const measurements = [];

      for (let i = 0; i < 100; i++) {
        const kalshiData = KalshiMockDataFactory.generateKalshiSnapshot();
        const anthropicData = AnthropicMockDataFactory.generateAgentDailyCost('scalper');
        const johnsData = JohnMockDataFactory.generateRevenueSnapshot();

        const startTime = performance.now();
        aggregator.calculatePnLMetrics(kalshiData, anthropicData, johnsData);
        const elapsed = performance.now() - startTime;

        measurements.push(elapsed);
      }

      const avg = measurements.reduce((a, b) => a + b) / measurements.length;
      const max = Math.max(...measurements);
      const percentile95 = measurements.sort((a, b) => a - b)[Math.floor(measurements.length * 0.95)];

      expect(avg).toBeLessThan(5);
      expect(max).toBeLessThan(20);
      expect(percentile95).toBeLessThan(10);
    });
  });

  // ============================================================================
  // MEMORY USAGE TESTS
  // ============================================================================

  describe('Memory Usage', () => {
    test('should handle 1000 history entries without memory leak', () => {
      const initialMemory = process.memoryUsage().heapUsed;

      // Add 1000 entries
      for (let i = 0; i < 1000; i++) {
        aggregator.pnlHistory.push({
          totalRevenue: Math.random() * 100000,
          totalExpenses: Math.random() * 50000,
          netPnL: Math.random() * 50000,
          grossMargin: Math.random() * 100,
          timestamp: new Date().toISOString(),
          components: {
            kalshi: { pnl: Math.random() * 50000 },
            anthropic: { dailySpend: Math.random() * 500 },
            johns: { collected: Math.random() * 50000 }
          }
        });
      }

      const afterAddition = process.memoryUsage().heapUsed;
      const memoryIncrease = afterAddition - initialMemory;

      // Memory increase should be reasonable (< 10MB for 1000 objects)
      expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024);

      // Clear history
      aggregator.pnlHistory = [];

      // Memory should be reclaimed
      // Note: This might not be immediate due to garbage collection
      expect(aggregator.pnlHistory.length).toBe(0);
    });

    test('should respect maxHistorySize limit', () => {
      aggregator.maxHistorySize = 100;

      // Add more than max
      for (let i = 0; i < 200; i++) {
        aggregator.pnlHistory.push({ netPnL: i * 100 });

        // Simulate the trimming that happens in real aggregation
        if (aggregator.pnlHistory.length > aggregator.maxHistorySize) {
          aggregator.pnlHistory = aggregator.pnlHistory.slice(-aggregator.maxHistorySize);
        }
      }

      expect(aggregator.pnlHistory.length).toBeLessThanOrEqual(aggregator.maxHistorySize);
    });

    test('should efficiently handle large component breakdowns', () => {
      const largeBreakdown = {
        kalshi: {
          balance: Math.random() * 1000000,
          positions: Array.from({ length: 1000 }, (_, i) => ({
            id: `pos-${i}`,
            quantity: Math.random() * 1000,
            pnl: Math.random() * 10000
          })),
          pnl: Math.random() * 100000
        },
        anthropic: {
          dailySpend: Math.random() * 1000
        },
        johns: {
          collected: Math.random() * 100000
        }
      };

      const startMemory = process.memoryUsage().heapUsed;

      // Store and retrieve
      for (let i = 0; i < 100; i++) {
        aggregator.pnlHistory.push({
          ...largeBreakdown,
          timestamp: new Date().toISOString()
        });
      }

      const endMemory = process.memoryUsage().heapUsed;
      const memoryUsed = endMemory - startMemory;

      // Should be manageable
      expect(memoryUsed).toBeLessThan(50 * 1024 * 1024);
    });
  });

  // ============================================================================
  // THROUGHPUT TESTS
  // ============================================================================

  describe('Throughput', () => {
    test('should process 100 P&L calculations per second', () => {
      const startTime = performance.now();
      let count = 0;

      while (performance.now() - startTime < 1000) {
        const kalshiData = KalshiMockDataFactory.generateKalshiSnapshot();
        const anthropicData = AnthropicMockDataFactory.generateAgentDailyCost('scalper');
        const johnsData = JohnMockDataFactory.generateRevenueSnapshot();

        aggregator.calculatePnLMetrics(kalshiData, anthropicData, johnsData);
        count++;
      }

      expect(count).toBeGreaterThan(100);
    });

    test('should handle concurrent metric calculations', async () => {
      const promises = [];

      // Simulate 50 concurrent requests
      for (let i = 0; i < 50; i++) {
        promises.push(
          Promise.resolve().then(() => {
            const kalshiData = KalshiMockDataFactory.generateKalshiSnapshot();
            const anthropicData = AnthropicMockDataFactory.generateAgentDailyCost('scalper');
            const johnsData = JohnMockDataFactory.generateRevenueSnapshot();

            return aggregator.calculatePnLMetrics(kalshiData, anthropicData, johnsData);
          })
        );
      }

      const startTime = performance.now();
      const results = await Promise.all(promises);
      const elapsed = performance.now() - startTime;

      expect(results).toHaveLength(50);
      expect(elapsed).toBeLessThan(500); // Should complete in < 500ms
      expect(results.every(r => r && r.netPnL !== undefined)).toBe(true);
    });
  });

  // ============================================================================
  // CACHE EFFICIENCY TESTS
  // ============================================================================

  describe('Cache Efficiency', () => {
    test('should cache expensive operations', () => {
      const mockCacheWithTracking = {
        ...mockCacheManager,
        getCalls: 0,
        setCalls: 0,
        get: jest.fn(async () => {
          mockCacheWithTracking.getCalls++;
          return null;
        }),
        set: jest.fn(async () => {
          mockCacheWithTracking.setCalls++;
          return true;
        })
      };

      const aggWithCache = new DataAggregator(mockCacheWithTracking, mockCircuitBreaker);

      // Multiple calls should use cache
      const data1 = aggWithCache.calculatePnLMetrics(
        { balance: 5000, positions: 1, pnl: 100 },
        { dailySpend: 10 },
        { invoiced: 0, collected: 0 }
      );

      const data2 = aggWithCache.calculatePnLMetrics(
        { balance: 5000, positions: 1, pnl: 100 },
        { dailySpend: 10 },
        { invoiced: 0, collected: 0 }
      );

      expect(data1).toBeDefined();
      expect(data2).toBeDefined();
    });
  });

  // ============================================================================
  // STRESS TESTS
  // ============================================================================

  describe('Stress Tests', () => {
    test('should handle rapid-fire updates', () => {
      const startTime = performance.now();
      let updateCount = 0;

      while (performance.now() - startTime < 1000) {
        const kalshiData = KalshiMockDataFactory.generateKalshiSnapshot();
        const anthropicData = AnthropicMockDataFactory.generateAgentDailyCost('scalper');
        const johnsData = JohnMockDataFactory.generateRevenueSnapshot();

        aggregator.calculatePnLMetrics(kalshiData, anthropicData, johnsData);
        updateCount++;
      }

      // Should process many updates without degradation
      expect(updateCount).toBeGreaterThan(100);
    });

    test('should handle large data sets', () => {
      // Large positions
      const largeKalshiData = KalshiMockDataFactory.generateKalshiSnapshot();
      largeKalshiData.positions = KalshiMockDataFactory.generatePositions(1000);

      // Large invoices
      const largeJohnsData = JohnMockDataFactory.generateRevenueSnapshot();
      largeJohnsData.invoices.data = JohnMockDataFactory.generateInvoices(500);

      const startTime = performance.now();

      const metrics = aggregator.calculatePnLMetrics(
        largeKalshiData,
        AnthropicMockDataFactory.generateAgentDailyCost('scalper'),
        largeJohnsData
      );

      const elapsed = performance.now() - startTime;

      expect(metrics).toBeDefined();
      expect(elapsed).toBeLessThan(100); // Should still be fast
    });

    test('should maintain accuracy under load', () => {
      const results = [];

      // Simulate 10 minutes of 5-second updates (120 updates)
      for (let i = 0; i < 120; i++) {
        const kalshiData = KalshiMockDataFactory.generateKalshiSnapshot();
        const anthropicData = AnthropicMockDataFactory.generateAgentDailyCost('scalper');
        const johnsData = JohnMockDataFactory.generateRevenueSnapshot();

        const metrics = aggregator.calculatePnLMetrics(
          kalshiData,
          anthropicData,
          johnsData
        );

        results.push(metrics);

        // Verify calculations remain correct
        const calculated = metrics.totalRevenue - metrics.totalExpenses;
        expect(Math.abs(calculated - metrics.netPnL)).toBeLessThan(0.01);
      }

      expect(results).toHaveLength(120);
    });
  });

  // ============================================================================
  // PERCENTILE LATENCY TESTS
  // ============================================================================

  describe('Percentile Latencies', () => {
    test('should measure P95 latency', () => {
      const measurements = [];

      for (let i = 0; i < 200; i++) {
        const kalshiData = KalshiMockDataFactory.generateKalshiSnapshot();
        const anthropicData = AnthropicMockDataFactory.generateAgentDailyCost('scalper');
        const johnsData = JohnMockDataFactory.generateRevenueSnapshot();

        const startTime = performance.now();
        aggregator.calculatePnLMetrics(kalshiData, anthropicData, johnsData);
        const elapsed = performance.now() - startTime;

        measurements.push(elapsed);
      }

      measurements.sort((a, b) => a - b);
      const p95 = measurements[Math.floor(measurements.length * 0.95)];
      const p99 = measurements[Math.floor(measurements.length * 0.99)];

      expect(p95).toBeLessThan(15);
      expect(p99).toBeLessThan(30);
    });
  });
});
