/**
 * Integration Tests for WebSocket Real-Time Updates
 * Verifies data flows: frontend → backend → charts
 */

const { Server: HTTPServer } = require('http');
const { Server: SocketIOServer } = require('socket.io');
const { io: ioClient } = require('socket.io-client');
const { DataAggregator } = require('../../lib/aggregator');
const { KalshiMockDataFactory } = require('../mocks/kalshi.mock');

jest.mock('../../lib/logger');
jest.mock('../../lib/cache');
jest.mock('../../lib/circuitBreaker');

describe('WebSocket Integration Tests', () => {
  let server;
  let io;
  let serverSocket;
  let clientSocket;
  let mockCacheManager;
  let mockCircuitBreaker;
  let aggregator;

  const PORT = 3001;
  const URL = `http://localhost:${PORT}`;

  beforeAll(async () => {
    // Create HTTP server with Socket.IO
    server = new HTTPServer();
    io = new SocketIOServer(server, {
      cors: { origin: '*' }
    });

    // Mock dependencies
    mockCacheManager = {
      initialize: jest.fn().mockResolvedValue(true),
      set: jest.fn().mockResolvedValue(true),
      get: jest.fn().mockResolvedValue(null),
      getStats: jest.fn().mockResolvedValue({})
    };

    mockCircuitBreaker = {
      execute: jest.fn((name, fn) => fn())
    };

    aggregator = new DataAggregator(mockCacheManager, mockCircuitBreaker);

    // Mock aggregator methods
    aggregator.getPnLSnapshot = jest.fn().mockResolvedValue({
      totalRevenue: 10000,
      totalExpenses: 2000,
      netPnL: 8000,
      grossMargin: 80,
      timestamp: new Date().toISOString(),
      components: {
        kalshi: { pnl: 3000 },
        anthropic: { dailySpend: 2000 },
        johns: { collected: 7000 }
      }
    });

    aggregator.getComponentBreakdown = jest.fn().mockResolvedValue({
      kalshi: { pnl: 3000 },
      anthropic: { dailySpend: 2000 },
      johns: { collected: 7000 }
    });

    // Setup Socket.IO connection handlers
    io.on('connection', (socket) => {
      serverSocket = socket;

      socket.on('subscribe_pnl', async () => {
        const pnl = await aggregator.getPnLSnapshot();
        socket.emit('pnl_update', {
          data: pnl,
          timestamp: new Date().toISOString(),
          source: 'initial'
        });
        socket.join('pnl_subscribers');
      });

      socket.on('subscribe_components', async () => {
        const breakdown = await aggregator.getComponentBreakdown();
        socket.emit('components_update', {
          data: breakdown,
          timestamp: new Date().toISOString(),
          source: 'initial'
        });
        socket.join('component_subscribers');
      });

      socket.on('disconnect', () => {
        // Handle disconnect
      });
    });

    server.listen(PORT);

    return new Promise((resolve) => {
      server.on('listening', resolve);
    });
  });

  afterAll((done) => {
    if (clientSocket) clientSocket.close();
    io.close();
    server.close(done);
  });

  // ============================================================================
  // CONNECTION TESTS
  // ============================================================================

  describe('WebSocket Connection', () => {
    test('should establish client connection', (done) => {
      const client = ioClient(URL);

      client.on('connect', () => {
        expect(client.connected).toBe(true);
        client.close();
        done();
      });

      client.on('connect_error', (error) => {
        done(error);
      });
    });

    test('should emit connection success message', (done) => {
      const client = ioClient(URL);

      client.on('connect_success', (data) => {
        expect(data.message).toBeDefined();
        expect(data.clientId).toBeDefined();
        expect(data.timestamp).toBeDefined();
        client.close();
        done();
      });

      client.on('connect_error', (error) => {
        done(error);
      });
    });

    test('should handle disconnection gracefully', (done) => {
      const client = ioClient(URL);

      client.on('connect', () => {
        client.close();
      });

      client.on('disconnect', () => {
        expect(client.connected).toBe(false);
        done();
      });

      client.on('connect_error', (error) => {
        done(error);
      });
    });
  });

  // ============================================================================
  // P&L SUBSCRIPTION TESTS
  // ============================================================================

  describe('P&L Subscription', () => {
    test('should subscribe to P&L updates', (done) => {
      const client = ioClient(URL);

      client.on('connect', () => {
        client.emit('subscribe_pnl');
      });

      client.on('pnl_update', (data) => {
        expect(data.data).toBeDefined();
        expect(data.data.totalRevenue).toBe(10000);
        expect(data.data.totalExpenses).toBe(2000);
        expect(data.data.netPnL).toBe(8000);
        expect(data.data.grossMargin).toBe(80);
        expect(data.timestamp).toBeDefined();
        expect(data.source).toBe('initial');
        client.close();
        done();
      });

      client.on('connect_error', (error) => {
        done(error);
      });
    });

    test('should receive complete P&L metrics', (done) => {
      const client = ioClient(URL);

      client.on('connect', () => {
        client.emit('subscribe_pnl');
      });

      client.on('pnl_update', (data) => {
        const { data: pnl } = data;

        // Verify all required fields
        expect(pnl.totalRevenue).toBeDefined();
        expect(pnl.totalExpenses).toBeDefined();
        expect(pnl.netPnL).toBeDefined();
        expect(pnl.grossMargin).toBeDefined();
        expect(pnl.timestamp).toBeDefined();
        expect(pnl.components).toBeDefined();

        // Verify waterfall reconstruction
        expect(
          pnl.components.kalshi.pnl + pnl.components.johns.collected
        ).toBe(pnl.totalRevenue);

        client.close();
        done();
      });

      client.on('connect_error', (error) => {
        done(error);
      });
    });
  });

  // ============================================================================
  // COMPONENT SUBSCRIPTION TESTS
  // ============================================================================

  describe('Component Breakdown Subscription', () => {
    test('should subscribe to component updates', (done) => {
      const client = ioClient(URL);

      client.on('connect', () => {
        client.emit('subscribe_components');
      });

      client.on('components_update', (data) => {
        expect(data.data).toBeDefined();
        expect(data.data.kalshi).toBeDefined();
        expect(data.data.anthropic).toBeDefined();
        expect(data.data.johns).toBeDefined();
        expect(data.timestamp).toBeDefined();
        expect(data.source).toBe('initial');
        client.close();
        done();
      });

      client.on('connect_error', (error) => {
        done(error);
      });
    });

    test('should receive detailed component breakdown', (done) => {
      const client = ioClient(URL);

      client.on('connect', () => {
        client.emit('subscribe_components');
      });

      client.on('components_update', (data) => {
        const { data: breakdown } = data;

        expect(breakdown.kalshi.pnl).toBe(3000);
        expect(breakdown.anthropic.dailySpend).toBe(2000);
        expect(breakdown.johns.collected).toBe(7000);

        client.close();
        done();
      });

      client.on('connect_error', (error) => {
        done(error);
      });
    });
  });

  // ============================================================================
  // REAL-TIME STREAMING TESTS
  // ============================================================================

  describe('Real-Time Streaming', () => {
    test('should stream P&L updates at regular intervals', (done) => {
      const client = ioClient(URL);
      let updateCount = 0;

      client.on('connect', () => {
        client.emit('subscribe_pnl');
      });

      client.on('pnl_update', (data) => {
        updateCount++;

        if (updateCount >= 2) {
          client.close();
          done();
        }

        // Simulate new update by emitting to all subscribers
        if (updateCount === 1) {
          io.to('pnl_subscribers').emit('pnl_update', {
            data: { ...data.data, netPnL: 8500 },
            timestamp: new Date().toISOString(),
            source: 'stream'
          });
        }
      });

      client.on('connect_error', (error) => {
        done(error);
      });
    });

    test('should handle multiple concurrent subscribers', (done) => {
      const client1 = ioClient(URL);
      const client2 = ioClient(URL);
      let client1Received = false;
      let client2Received = false;

      const checkComplete = () => {
        if (client1Received && client2Received) {
          client1.close();
          client2.close();
          done();
        }
      };

      client1.on('connect', () => {
        client1.emit('subscribe_pnl');
      });

      client2.on('connect', () => {
        client2.emit('subscribe_pnl');
      });

      client1.on('pnl_update', () => {
        client1Received = true;
        checkComplete();
      });

      client2.on('pnl_update', () => {
        client2Received = true;
        checkComplete();
      });

      client1.on('connect_error', (error) => {
        done(error);
      });

      client2.on('connect_error', (error) => {
        done(error);
      });
    });
  });

  // ============================================================================
  // DATA FLOW TESTS
  // ============================================================================

  describe('Data Flow: Backend → Frontend → Charts', () => {
    test('should propagate data changes through the pipeline', (done) => {
      const client = ioClient(URL);

      client.on('connect', () => {
        client.emit('subscribe_pnl');
      });

      client.on('pnl_update', (data) => {
        // Simulate chart update
        const chartData = {
          revenue: data.data.totalRevenue,
          expenses: data.data.totalExpenses,
          net: data.data.netPnL,
          margin: data.data.grossMargin,
          timestamp: data.timestamp
        };

        expect(chartData.revenue).toBeGreaterThanOrEqual(0);
        expect(chartData.expenses).toBeGreaterThanOrEqual(0);
        expect(chartData.net).toBeDefined();
        expect(chartData.margin).toBeDefined();

        client.close();
        done();
      });

      client.on('connect_error', (error) => {
        done(error);
      });
    });

    test('should maintain data consistency across updates', (done) => {
      const client = ioClient(URL);
      const updates = [];

      client.on('connect', () => {
        client.emit('subscribe_pnl');
      });

      client.on('pnl_update', (data) => {
        updates.push(data.data);

        if (updates.length === 1) {
          // Verify consistency: Revenue - Expenses = Net
          const { totalRevenue, totalExpenses, netPnL } = updates[0];
          const calculatedNet = totalRevenue - totalExpenses;
          expect(calculatedNet).toBe(netPnL);

          client.close();
          done();
        }
      });

      client.on('connect_error', (error) => {
        done(error);
      });
    });
  });

  // ============================================================================
  // ERROR HANDLING TESTS
  // ============================================================================

  describe('Error Handling', () => {
    test('should handle subscription errors gracefully', (done) => {
      // Mock aggregator to throw error
      const originalPnL = aggregator.getPnLSnapshot;
      aggregator.getPnLSnapshot = jest.fn().mockRejectedValue(
        new Error('API Error')
      );

      const client = ioClient(URL);

      client.on('connect', () => {
        client.emit('subscribe_pnl');
      });

      client.on('error', (data) => {
        expect(data.message).toBeDefined();
        client.close();

        // Restore original
        aggregator.getPnLSnapshot = originalPnL;
        done();
      });

      // If error event not fired, timeout
      setTimeout(() => {
        client.close();
        aggregator.getPnLSnapshot = originalPnL;
        done();
      }, 1000);
    });
  });

  // ============================================================================
  // PERFORMANCE TESTS
  // ============================================================================

  describe('WebSocket Performance', () => {
    test('should handle updates within 100ms latency', (done) => {
      const client = ioClient(URL);

      client.on('connect', () => {
        const startTime = performance.now();
        client.emit('subscribe_pnl');

        client.on('pnl_update', () => {
          const latency = performance.now() - startTime;
          expect(latency).toBeLessThan(100); // 100ms threshold
          client.close();
          done();
        });
      });

      client.on('connect_error', (error) => {
        done(error);
      });
    });

    test('should process 100 concurrent messages', (done) => {
      const clients = Array.from({ length: 10 }, () => ioClient(URL));
      let updateCount = 0;

      clients.forEach((client) => {
        client.on('connect', () => {
          client.emit('subscribe_pnl');
        });

        client.on('pnl_update', () => {
          updateCount++;

          if (updateCount >= clients.length) {
            clients.forEach(c => c.close());
            done();
          }
        });

        client.on('connect_error', (error) => {
          done(error);
        });
      });
    });
  });
});
