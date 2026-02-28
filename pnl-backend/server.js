#!/usr/bin/env node

const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const bodyParser = require('body-parser');
const logger = require('./lib/logger');
const { CacheManager } = require('./lib/cache');
const { CircuitBreaker } = require('./lib/circuitBreaker');
const { DataAggregator } = require('./lib/aggregator');
const { normalizeTimestamp } = require('./lib/utils');

// Environment config
require('dotenv').config();
const PORT = process.env.PORT || 3000;
const NODE_ENV = process.env.NODE_ENV || 'development';

// Initialize Express app
const app = express();
const server = http.createServer(app);

// Socket.io with fallback support
const io = socketIo(server, {
  cors: {
    origin: process.env.CORS_ORIGIN || '*',
    methods: ['GET', 'POST']
  },
  transports: ['websocket', 'polling'], // WebSocket primary, polling (SSE-like) fallback
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: 5
});

// Middleware
app.use(helmet());
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Request logging middleware
app.use((req, res, next) => {
  const startTime = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    logger.info(`${req.method} ${req.path} - ${res.statusCode} (${duration}ms)`);
  });
  next();
});

// Initialize services
let cacheManager;
let dataAggregator;
let circuitBreaker;
let pnlStreamInterval;

// ============================================================================
// SERVICE INITIALIZATION
// ============================================================================

async function initializeServices() {
  try {
    // Initialize cache manager (4-tier)
    cacheManager = new CacheManager();
    await cacheManager.initialize();
    logger.info('Cache manager initialized');

    // Initialize circuit breaker for external APIs
    circuitBreaker = new CircuitBreaker({
      failureThreshold: 5,
      resetTimeout: 60000, // 60 seconds
      monitoringInterval: 5000
    });

    // Initialize data aggregator
    dataAggregator = new DataAggregator(cacheManager, circuitBreaker);
    await dataAggregator.initialize();
    logger.info('Data aggregator initialized');

    return true;
  } catch (error) {
    logger.error('Service initialization failed', { error: error.message, stack: error.stack });
    throw error;
  }
}

// ============================================================================
// REST ENDPOINTS
// ============================================================================

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    const health = {
      status: 'healthy',
      timestamp: normalizeTimestamp(new Date()),
      uptime: process.uptime(),
      environment: NODE_ENV,
      services: {
        cache: cacheManager.getHealth ? await cacheManager.getHealth() : 'unknown',
        aggregator: 'running'
      }
    };

    res.status(200).json(health);
  } catch (error) {
    logger.error('Health check failed', { error: error.message });
    res.status(503).json({
      status: 'unhealthy',
      error: error.message,
      timestamp: normalizeTimestamp(new Date())
    });
  }
});

// Get current P&L snapshot
app.get('/api/pnl/current', async (req, res) => {
  try {
    const pnl = await dataAggregator.getPnLSnapshot();
    res.status(200).json({
      success: true,
      data: pnl,
      timestamp: normalizeTimestamp(new Date())
    });
  } catch (error) {
    logger.error('Failed to get P&L snapshot', { error: error.message });
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: normalizeTimestamp(new Date())
    });
  }
});

// Get P&L history
app.get('/api/pnl/history', async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 100;
    const history = await dataAggregator.getPnLHistory(limit);
    res.status(200).json({
      success: true,
      data: history,
      timestamp: normalizeTimestamp(new Date())
    });
  } catch (error) {
    logger.error('Failed to get P&L history', { error: error.message });
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: normalizeTimestamp(new Date())
    });
  }
});

// Get detailed component breakdown
app.get('/api/pnl/breakdown', async (req, res) => {
  try {
    const breakdown = await dataAggregator.getComponentBreakdown();
    res.status(200).json({
      success: true,
      data: breakdown,
      timestamp: normalizeTimestamp(new Date())
    });
  } catch (error) {
    logger.error('Failed to get breakdown', { error: error.message });
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: normalizeTimestamp(new Date())
    });
  }
});

// Get circuit breaker status
app.get('/api/circuit-breaker/status', (req, res) => {
  try {
    const status = circuitBreaker.getStatus();
    res.status(200).json({
      success: true,
      data: status,
      timestamp: normalizeTimestamp(new Date())
    });
  } catch (error) {
    logger.error('Failed to get circuit breaker status', { error: error.message });
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Cache stats
app.get('/api/cache/stats', async (req, res) => {
  try {
    const stats = await cacheManager.getStats();
    res.status(200).json({
      success: true,
      data: stats,
      timestamp: normalizeTimestamp(new Date())
    });
  } catch (error) {
    logger.error('Failed to get cache stats', { error: error.message });
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// ============================================================================
// SOCKET.IO HANDLERS
// ============================================================================

io.on('connection', (socket) => {
  logger.info(`Client connected: ${socket.id}`);

  // Send initial data on connect
  socket.emit('connect_success', {
    message: 'Connected to P&L streaming server',
    clientId: socket.id,
    timestamp: normalizeTimestamp(new Date()),
    transport: socket.handshake.headers['upgrade'] || 'polling'
  });

  // Handle P&L subscription
  socket.on('subscribe_pnl', async () => {
    try {
      const pnl = await dataAggregator.getPnLSnapshot();
      socket.emit('pnl_update', {
        data: pnl,
        timestamp: normalizeTimestamp(new Date()),
        source: 'initial'
      });
      socket.join('pnl_subscribers');
      logger.info(`Client ${socket.id} subscribed to P&L updates`);
    } catch (error) {
      logger.error(`Subscription error for ${socket.id}`, { error: error.message });
      socket.emit('error', {
        message: 'Failed to subscribe to P&L updates',
        error: error.message
      });
    }
  });

  // Handle component subscription (detailed breakdown)
  socket.on('subscribe_components', async () => {
    try {
      const breakdown = await dataAggregator.getComponentBreakdown();
      socket.emit('components_update', {
        data: breakdown,
        timestamp: normalizeTimestamp(new Date()),
        source: 'initial'
      });
      socket.join('component_subscribers');
      logger.info(`Client ${socket.id} subscribed to component updates`);
    } catch (error) {
      logger.error(`Component subscription error for ${socket.id}`, { error: error.message });
      socket.emit('error', {
        message: 'Failed to subscribe to component updates',
        error: error.message
      });
    }
  });

  // Handle disconnect
  socket.on('disconnect', () => {
    logger.info(`Client disconnected: ${socket.id}`);
  });

  // Handle errors
  socket.on('error', (error) => {
    logger.error(`Socket error for ${socket.id}`, { error });
  });
});

// ============================================================================
// REAL-TIME P&L STREAMING
// ============================================================================

async function startPnLStream() {
  pnlStreamInterval = setInterval(async () => {
    try {
      // Get updated P&L metrics
      const pnl = await dataAggregator.getPnLSnapshot();
      
      // Emit to all subscribers
      io.to('pnl_subscribers').emit('pnl_update', {
        data: pnl,
        timestamp: normalizeTimestamp(new Date()),
        source: 'stream'
      });

      // Also emit component breakdown for component subscribers
      const breakdown = await dataAggregator.getComponentBreakdown();
      io.to('component_subscribers').emit('components_update', {
        data: breakdown,
        timestamp: normalizeTimestamp(new Date()),
        source: 'stream'
      });

    } catch (error) {
      logger.error('P&L stream error', { error: error.message });
      io.emit('stream_error', {
        message: 'Error updating P&L metrics',
        timestamp: normalizeTimestamp(new Date())
      });
    }
  }, 5000); // 5-second interval per requirements

  logger.info('P&L streaming started (5-second interval)');
}

// ============================================================================
// GRACEFUL SHUTDOWN
// ============================================================================

async function gracefulShutdown() {
  logger.info('Graceful shutdown initiated');

  // Stop P&L stream
  if (pnlStreamInterval) {
    clearInterval(pnlStreamInterval);
    logger.info('P&L stream stopped');
  }

  // Disconnect all clients
  io.disconnectSockets();

  // Close database connections
  if (cacheManager && cacheManager.disconnect) {
    await cacheManager.disconnect();
    logger.info('Cache connections closed');
  }

  // Close server
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });

  // Force exit after 30 seconds
  setTimeout(() => {
    logger.warn('Forced exit after 30s timeout');
    process.exit(1);
  }, 30000);
}

process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);

// ============================================================================
// SERVER START
// ============================================================================

async function start() {
  try {
    // Initialize all services
    await initializeServices();

    // Start real-time P&L streaming
    await startPnLStream();

    // Start HTTP server
    server.listen(PORT, () => {
      logger.info(`✅ P&L Streaming Server started on port ${PORT}`);
      logger.info(`   Environment: ${NODE_ENV}`);
      logger.info(`   WebSocket: ws://localhost:${PORT}`);
      logger.info(`   Health check: http://localhost:${PORT}/health`);
    });

  } catch (error) {
    logger.error('Failed to start server', { error: error.message, stack: error.stack });
    process.exit(1);
  }
}

start();

module.exports = { app, server, io };
