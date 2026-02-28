const axios = require('axios');
const logger = require('./logger');
const { 
  normalizeTimestamp, 
  calculateGrossMargin, 
  roundCurrency,
  createCacheKey,
  getCurrentTimestampMs
} = require('./utils');

/**
 * Data Aggregator - Combines P&L data from three sources:
 * 1. Kalshi (trading balance, positions, P&L)
 * 2. Anthropic API (daily spend/costs)
 * 3. John's Revenue (invoiced, collected)
 */
class DataAggregator {
  constructor(cacheManager, circuitBreaker) {
    this.cacheManager = cacheManager;
    this.circuitBreaker = circuitBreaker;

    this.config = {
      kalshiBaseUrl: process.env.KALSHI_API_URL || 'https://api.kalshi.com/v1',
      kalshiApiKey: process.env.KALSHI_API_KEY || '',
      anthropicApiKey: process.env.ANTHROPIC_API_KEY || '',
      johnsRevenueUrl: process.env.JOHNS_REVENUE_URL || 'http://localhost:5000/api/revenue',
      cacheTtl: 60000 // 60 seconds
    };

    this.pnlHistory = []; // Keep last 100 snapshots
    this.maxHistorySize = 100;

    // Default values for fallback
    this.defaults = {
      kalshi: { balance: 0, positions: [], pnl: 0 },
      anthropic: { dailySpend: 0 },
      johnsRevenue: { invoiced: 0, collected: 0 }
    };
  }

  /**
   * Initialize aggregator
   */
  async initialize() {
    logger.info('Data aggregator initialized');
  }

  /**
   * Get current P&L snapshot
   */
  async getPnLSnapshot() {
    try {
      const startTime = getCurrentTimestampMs();

      // Fetch data from all sources in parallel
      const [kalshiData, anthropicData, johnsData] = await Promise.all([
        this.fetchKalshiData(),
        this.fetchAnthropicCosts(),
        this.fetchJohnsRevenue()
      ]);

      // Calculate aggregated metrics
      const metrics = this.calculatePnLMetrics(kalshiData, anthropicData, johnsData);

      // Store in history
      this.pnlHistory.push({
        ...metrics,
        timestamp: normalizeTimestamp(new Date())
      });

      // Keep only last N entries
      if (this.pnlHistory.length > this.maxHistorySize) {
        this.pnlHistory = this.pnlHistory.slice(-this.maxHistorySize);
      }

      // Cache the snapshot
      await this.cacheManager.set(
        createCacheKey('pnl', 'current'),
        metrics,
        this.config.cacheTtl
      );

      const duration = getCurrentTimestampMs() - startTime;
      logger.info(`P&L snapshot generated (${duration}ms)`, {
        revenue: metrics.totalRevenue,
        expenses: metrics.totalExpenses,
        netPnl: metrics.netPnL
      });

      return metrics;

    } catch (error) {
      logger.error('Failed to generate P&L snapshot', { error: error.message });
      
      // Try to get from cache
      const cached = await this.cacheManager.get(createCacheKey('pnl', 'current'));
      if (cached) {
        logger.info('Using cached P&L snapshot');
        return cached;
      }

      // Return fallback
      return this.getDefaultSnapshot();
    }
  }

  /**
   * Fetch data from Kalshi API
   */
  async fetchKalshiData() {
    const cacheKey = createCacheKey('kalshi', 'data');
    
    return this.circuitBreaker.execute(
      'kalshi',
      async () => {
        // Try cache first
        const cached = await this.cacheManager.get(cacheKey);
        if (cached) {
          logger.debug('Kalshi data from cache');
          return cached;
        }

        // Fetch from API
        const data = await this.callKalshiApi();
        
        // Cache it
        await this.cacheManager.set(cacheKey, data, this.config.cacheTtl);
        
        return data;
      },
      this.defaults.kalshi
    );
  }

  /**
   * Call Kalshi API endpoints
   */
  async callKalshiApi() {
    try {
      // Get account balance
      const balanceResponse = await axios.get(`${this.config.kalshiBaseUrl}/users/self`, {
        headers: {
          'Authorization': `Bearer ${this.config.kalshiApiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 5000
      });

      const balance = balanceResponse.data.balance_cents / 100 || 0;

      // Get positions
      const positionsResponse = await axios.get(`${this.config.kalshiBaseUrl}/users/self/positions`, {
        headers: {
          'Authorization': `Bearer ${this.config.kalshiApiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 5000
      });

      const positions = positionsResponse.data.positions || [];

      // Calculate P&L from positions
      const pnl = positions.reduce((total, pos) => {
        return total + (pos.pnl_cents || 0) / 100;
      }, 0);

      return {
        balance: roundCurrency(balance),
        positions: positions.length,
        pnl: roundCurrency(pnl),
        timestamp: normalizeTimestamp(new Date())
      };

    } catch (error) {
      logger.error('Kalshi API call failed', { error: error.message });
      throw error;
    }
  }

  /**
   * Fetch Anthropic API costs
   */
  async fetchAnthropicCosts() {
    const cacheKey = createCacheKey('anthropic', 'costs');

    return this.circuitBreaker.execute(
      'anthropic',
      async () => {
        // Try cache first
        const cached = await this.cacheManager.get(cacheKey);
        if (cached) {
          logger.debug('Anthropic costs from cache');
          return cached;
        }

        // Mock API call - replace with actual Anthropic API if available
        const data = await this.fetchAnthropicCostsFromApi();

        // Cache it
        await this.cacheManager.set(cacheKey, data, this.config.cacheTtl);

        return data;
      },
      this.defaults.anthropic
    );
  }

  /**
   * Call Anthropic API for usage/costs
   */
  async fetchAnthropicCostsFromApi() {
    try {
      // This would call Anthropic's API - for now, we'll use a mock
      // In production, integrate with actual Anthropic dashboard or billing API
      
      // Example: You could scrape from https://console.anthropic.com or use their API
      // For now, return mock data
      const dailySpend = 5.25; // Example: $5.25/day
      
      return {
        dailySpend: roundCurrency(dailySpend),
        timestamp: normalizeTimestamp(new Date())
      };

    } catch (error) {
      logger.error('Anthropic API call failed', { error: error.message });
      throw error;
    }
  }

  /**
   * Fetch John's revenue data
   */
  async fetchJohnsRevenue() {
    const cacheKey = createCacheKey('johns', 'revenue');

    return this.circuitBreaker.execute(
      'johns_revenue',
      async () => {
        // Try cache first
        const cached = await this.cacheManager.get(cacheKey);
        if (cached) {
          logger.debug('Johns revenue from cache');
          return cached;
        }

        // Fetch from John's backend
        const data = await this.callJohnsRevenueApi();

        // Cache it
        await this.cacheManager.set(cacheKey, data, this.config.cacheTtl);

        return data;
      },
      this.defaults.johnsRevenue
    );
  }

  /**
   * Call John's revenue backend API
   */
  async callJohnsRevenueApi() {
    try {
      const response = await axios.get(this.config.johnsRevenueUrl, {
        timeout: 5000
      });

      const data = response.data || {};

      return {
        invoiced: roundCurrency(data.invoiced || 0),
        collected: roundCurrency(data.collected || 0),
        timestamp: normalizeTimestamp(new Date())
      };

    } catch (error) {
      logger.error('Johns revenue API call failed', { error: error.message });
      throw error;
    }
  }

  /**
   * Calculate aggregated P&L metrics
   */
  calculatePnLMetrics(kalshiData, anthropicData, johnsData) {
    // Revenue sources
    const kalshiPnl = kalshiData.pnl || 0;
    const johnsCollected = johnsData.collected || 0;
    const totalRevenue = roundCurrency(kalshiPnl + johnsCollected);

    // Expense sources
    const anthropicCosts = anthropicData.dailySpend || 0;
    const totalExpenses = roundCurrency(anthropicCosts);

    // Net P&L
    const netPnL = roundCurrency(totalRevenue - totalExpenses);

    // Gross margin
    const grossMargin = calculateGrossMargin(totalRevenue, totalExpenses);

    // Daily trend (compare with yesterday's snapshot if available)
    const dailyTrend = this.calculateDailyTrend();

    return {
      // Summary metrics
      totalRevenue,
      totalExpenses,
      netPnL,
      grossMargin,
      dailyTrend,
      
      // Component breakdown
      components: {
        kalshi: {
          balance: kalshiData.balance || 0,
          positions: kalshiData.positions || 0,
          pnl: kalshiData.pnl || 0
        },
        anthropic: {
          dailySpend: anthropicData.dailySpend || 0
        },
        johns: {
          invoiced: johnsData.invoiced || 0,
          collected: johnsData.collected || 0
        }
      },
      
      // Metadata
      timestamp: normalizeTimestamp(new Date()),
      calculatedAt: getCurrentTimestampMs()
    };
  }

  /**
   * Calculate daily trend (% change from last recorded day)
   */
  calculateDailyTrend() {
    if (this.pnlHistory.length < 2) return 0;

    const current = this.pnlHistory[this.pnlHistory.length - 1];
    const previous = this.pnlHistory[0]; // Oldest in history

    if (previous.netPnL === 0) {
      return current.netPnL > 0 ? 100 : 0;
    }

    const trend = ((current.netPnL - previous.netPnL) / Math.abs(previous.netPnL)) * 100;
    return roundCurrency(trend);
  }

  /**
   * Get P&L history
   */
  async getPnLHistory(limit = 100) {
    const history = this.pnlHistory.slice(-limit);
    return {
      count: history.length,
      data: history,
      timestamp: normalizeTimestamp(new Date())
    };
  }

  /**
   * Get component breakdown
   */
  async getComponentBreakdown() {
    try {
      const currentPnL = await this.getPnLSnapshot();
      
      return {
        kalshi: currentPnL.components.kalshi,
        anthropic: currentPnL.components.anthropic,
        johns: currentPnL.components.johns,
        summary: {
          totalRevenue: currentPnL.totalRevenue,
          totalExpenses: currentPnL.totalExpenses,
          netPnL: currentPnL.netPnL,
          grossMargin: currentPnL.grossMargin
        },
        timestamp: normalizeTimestamp(new Date())
      };

    } catch (error) {
      logger.error('Failed to get component breakdown', { error: error.message });
      return {
        kalshi: this.defaults.kalshi,
        anthropic: this.defaults.anthropic,
        johns: this.defaults.johnsRevenue,
        summary: this.getDefaultSnapshot(),
        timestamp: normalizeTimestamp(new Date())
      };
    }
  }

  /**
   * Get default snapshot (fallback)
   */
  getDefaultSnapshot() {
    return {
      totalRevenue: 0,
      totalExpenses: 0,
      netPnL: 0,
      grossMargin: 0,
      dailyTrend: 0,
      components: {
        kalshi: { ...this.defaults.kalshi },
        anthropic: { ...this.defaults.anthropic },
        johns: { ...this.defaults.johnsRevenue }
      },
      timestamp: normalizeTimestamp(new Date()),
      calculatedAt: getCurrentTimestampMs()
    };
  }
}

module.exports = { DataAggregator };
