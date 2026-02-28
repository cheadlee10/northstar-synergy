const { DataAggregator } = require('../lib/aggregator');
const { CacheManager } = require('../lib/cache');
const { CircuitBreaker } = require('../lib/circuitBreaker');

describe('DataAggregator', () => {
  let aggregator;
  let cacheManager;
  let circuitBreaker;

  beforeEach(() => {
    cacheManager = new CacheManager();
    circuitBreaker = new CircuitBreaker();
    aggregator = new DataAggregator(cacheManager, circuitBreaker);
  });

  afterEach(() => {
    circuitBreaker.destroy();
  });

  describe('calculatePnLMetrics', () => {
    test('should correctly calculate P&L metrics', () => {
      const kalshi = { balance: 10000, positions: 3, pnl: 500 };
      const anthropic = { dailySpend: 50 };
      const johns = { invoiced: 2000, collected: 1000 };

      const metrics = aggregator.calculatePnLMetrics(kalshi, anthropic, johns);

      expect(metrics.totalRevenue).toBe(1500); // 500 + 1000
      expect(metrics.totalExpenses).toBe(50);
      expect(metrics.netPnL).toBe(1450);
      expect(metrics.grossMargin).toBeCloseTo(96.67, 1);
    });

    test('should handle zero revenue', () => {
      const kalshi = { balance: 10000, positions: 0, pnl: 0 };
      const anthropic = { dailySpend: 50 };
      const johns = { invoiced: 0, collected: 0 };

      const metrics = aggregator.calculatePnLMetrics(kalshi, anthropic, johns);

      expect(metrics.totalRevenue).toBe(0);
      expect(metrics.grossMargin).toBe(0);
    });

    test('should include component breakdown', () => {
      const kalshi = { balance: 10000, positions: 3, pnl: 500 };
      const anthropic = { dailySpend: 50 };
      const johns = { invoiced: 2000, collected: 1000 };

      const metrics = aggregator.calculatePnLMetrics(kalshi, anthropic, johns);

      expect(metrics.components.kalshi).toEqual(kalshi);
      expect(metrics.components.anthropic).toEqual(anthropic);
      expect(metrics.components.johns).toEqual(johns);
    });
  });

  describe('calculateDailyTrend', () => {
    test('should calculate trend from history', () => {
      aggregator.pnlHistory = [
        { netPnL: 1000 },
        { netPnL: 1100 }
      ];

      const trend = aggregator.calculateDailyTrend();
      expect(trend).toBe(10); // 10% increase
    });

    test('should return 0 if less than 2 entries', () => {
      aggregator.pnlHistory = [{ netPnL: 1000 }];

      const trend = aggregator.calculateDailyTrend();
      expect(trend).toBe(0);
    });
  });

  describe('getDefaultSnapshot', () => {
    test('should return default values', () => {
      const snapshot = aggregator.getDefaultSnapshot();

      expect(snapshot.totalRevenue).toBe(0);
      expect(snapshot.totalExpenses).toBe(0);
      expect(snapshot.netPnL).toBe(0);
      expect(snapshot.grossMargin).toBe(0);
      expect(snapshot.components).toBeDefined();
    });
  });
});
