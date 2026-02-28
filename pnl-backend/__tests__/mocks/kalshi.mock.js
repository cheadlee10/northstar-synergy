/**
 * Kalshi Mock Data Factory
 * Generates realistic mock data for Kalshi trading platform
 */

const { v4: uuidv4 } = require('uuid');

class KalshiMockDataFactory {
  /**
   * Generate a random Kalshi user balance
   * Range: $1,000 - $100,000
   */
  static generateBalance(min = 1000, max = 100000) {
    return parseFloat((Math.random() * (max - min) + min).toFixed(2));
  }

  /**
   * Generate a realistic position
   */
  static generatePosition(overrides = {}) {
    const id = uuidv4();
    const quantity = Math.floor(Math.random() * 100) + 1;
    const avgPrice = parseFloat((Math.random() * 0.5 + 0.25).toFixed(4)); // $0.25-$0.75
    const currentPrice = parseFloat((Math.random() * 0.6 + 0.2).toFixed(4));
    
    return {
      id,
      symbol: `MARKET-${Math.floor(Math.random() * 1000)}`,
      quantity,
      averagePrice: avgPrice,
      currentPrice: currentPrice,
      pnl_cents: Math.round((currentPrice - avgPrice) * quantity * 100),
      status: 'open',
      createdAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000),
      ...overrides
    };
  }

  /**
   * Generate multiple positions
   */
  static generatePositions(count = 5, overrides = {}) {
    return Array.from({ length: count }, () => 
      this.generatePosition(overrides)
    );
  }

  /**
   * Generate a trade
   */
  static generateTrade(overrides = {}) {
    return {
      id: uuidv4(),
      symbol: `MARKET-${Math.floor(Math.random() * 1000)}`,
      side: Math.random() > 0.5 ? 'buy' : 'sell',
      quantity: Math.floor(Math.random() * 50) + 1,
      price: parseFloat((Math.random() * 0.5 + 0.25).toFixed(4)),
      timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000),
      status: 'filled',
      ...overrides
    };
  }

  /**
   * Generate multiple trades
   */
  static generateTrades(count = 10, overrides = {}) {
    return Array.from({ length: count }, () => 
      this.generateTrade(overrides)
    );
  }

  /**
   * Generate complete Kalshi API response
   */
  static generateKalshiSnapshot(overrides = {}) {
    const positions = this.generatePositions(Math.floor(Math.random() * 5) + 1);
    const pnl = positions.reduce((sum, pos) => sum + (pos.pnl_cents || 0), 0) / 100;
    
    return {
      balance: this.generateBalance(),
      balance_cents: Math.round(this.generateBalance() * 100),
      positions: positions,
      totalPnl: pnl,
      currency: 'USD',
      timestamp: new Date().toISOString(),
      ...overrides
    };
  }

  /**
   * Generate Kalshi API user endpoint response
   */
  static generateUserResponse(overrides = {}) {
    const balance = this.generateBalance();
    return {
      user_id: uuidv4(),
      username: 'trader_' + Math.floor(Math.random() * 10000),
      email: `trader${Math.floor(Math.random() * 1000)}@example.com`,
      balance_cents: Math.round(balance * 100),
      balance: balance,
      createdAt: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000),
      ...overrides
    };
  }

  /**
   * Generate Kalshi API positions endpoint response
   */
  static generatePositionsResponse(count = 5, overrides = {}) {
    return {
      positions: this.generatePositions(count),
      count: count,
      ...overrides
    };
  }

  /**
   * Generate scenario: Winning trades
   */
  static generateWinningScenario(positionCount = 3) {
    const positions = Array.from({ length: positionCount }, () => {
      const avgPrice = 0.30;
      const currentPrice = 0.75; // Big winner
      const quantity = Math.floor(Math.random() * 100) + 50;
      return this.generatePosition({
        averagePrice: avgPrice,
        currentPrice: currentPrice,
        pnl_cents: Math.round((currentPrice - avgPrice) * quantity * 100),
        quantity
      });
    });

    const pnl = positions.reduce((sum, pos) => sum + (pos.pnl_cents || 0), 0) / 100;
    return {
      balance: 50000,
      balance_cents: 5000000,
      positions,
      totalPnl: pnl,
      scenario: 'winning'
    };
  }

  /**
   * Generate scenario: Losing trades
   */
  static generateLosingScenario(positionCount = 3) {
    const positions = Array.from({ length: positionCount }, () => {
      const avgPrice = 0.70;
      const currentPrice = 0.15; // Big loser
      const quantity = Math.floor(Math.random() * 100) + 50;
      return this.generatePosition({
        averagePrice: avgPrice,
        currentPrice: currentPrice,
        pnl_cents: Math.round((currentPrice - avgPrice) * quantity * 100),
        quantity
      });
    });

    const pnl = positions.reduce((sum, pos) => sum + (pos.pnl_cents || 0), 0) / 100;
    return {
      balance: 10000,
      balance_cents: 1000000,
      positions,
      totalPnl: pnl,
      scenario: 'losing'
    };
  }

  /**
   * Generate scenario: Mixed outcomes
   */
  static generateMixedScenario(winCount = 2, loseCount = 2) {
    const winners = Array.from({ length: winCount }, () => 
      this.generatePosition({
        averagePrice: 0.30,
        currentPrice: 0.75,
        pnl_cents: Math.round(0.45 * 100 * 100)
      })
    );

    const losers = Array.from({ length: loseCount }, () => 
      this.generatePosition({
        averagePrice: 0.70,
        currentPrice: 0.15,
        pnl_cents: Math.round(-0.55 * 100 * 100)
      })
    );

    const positions = [...winners, ...losers];
    const pnl = positions.reduce((sum, pos) => sum + (pos.pnl_cents || 0), 0) / 100;

    return {
      balance: 35000,
      balance_cents: 3500000,
      positions,
      totalPnl: pnl,
      scenario: 'mixed'
    };
  }
}

module.exports = { KalshiMockDataFactory };
