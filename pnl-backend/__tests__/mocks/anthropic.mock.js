/**
 * Anthropic API Costs Mock Data Factory
 * Generates realistic mock data for Anthropic API usage/costs
 */

const { v4: uuidv4 } = require('uuid');

class AnthropicMockDataFactory {
  /**
   * Generate a single API call cost
   * Claude models range from ~$0.00001 to $0.01 per token
   */
  static generateApiCallCost() {
    const inputTokens = Math.floor(Math.random() * 2000) + 100;
    const outputTokens = Math.floor(Math.random() * 1000) + 50;
    
    // Claude 3 pricing (example)
    const inputCost = (inputTokens / 1000) * 0.003; // $0.003 per 1K input tokens
    const outputCost = (outputTokens / 1000) * 0.015; // $0.015 per 1K output tokens
    
    return {
      inputTokens,
      outputTokens,
      inputCost: parseFloat(inputCost.toFixed(6)),
      outputCost: parseFloat(outputCost.toFixed(6)),
      totalCost: parseFloat((inputCost + outputCost).toFixed(6))
    };
  }

  /**
   * Generate daily usage for a specific agent
   * Range: $0.50 - $50.00 per day
   */
  static generateAgentDailyCost(agent = 'scalper', baseMultiplier = 1) {
    // Different agents have different usage patterns
    const multipliers = {
      scalper: 10, // Heavy trading analysis
      john: 3,     // Medium business development
      cliff: 2,    // Light analysis
      other: 1     // Default
    };

    const multiplier = multipliers[agent] || 1;
    const base = Math.random() * 50 * multiplier;
    const dailySpend = Math.max(0.50, base);

    return {
      agent,
      dailySpend: parseFloat(dailySpend.toFixed(2)),
      apiCallCount: Math.floor(Math.random() * 500) + 50,
      tokenCount: Math.floor(Math.random() * 1000000) + 100000,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Generate monthly usage summary
   */
  static generateMonthlySummary(agents = ['scalper', 'john', 'cliff']) {
    const summary = {
      month: new Date().toISOString().slice(0, 7), // YYYY-MM
      agents: {},
      totalSpend: 0,
      totalApiCalls: 0,
      totalTokens: 0,
      averageDailySpend: 0
    };

    // Generate data for 30 days
    const dailyData = {};
    
    for (let day = 1; day <= 30; day++) {
      dailyData[day] = {};
      
      agents.forEach(agent => {
        const cost = this.generateAgentDailyCost(agent);
        dailyData[day][agent] = cost;
        
        // Accumulate totals
        if (!summary.agents[agent]) {
          summary.agents[agent] = {
            totalSpend: 0,
            totalCalls: 0,
            avgDailySpend: 0
          };
        }
        
        summary.agents[agent].totalSpend += cost.dailySpend;
        summary.agents[agent].totalCalls += cost.apiCallCount;
        summary.totalSpend += cost.dailySpend;
        summary.totalApiCalls += cost.apiCallCount;
        summary.totalTokens += cost.tokenCount;
      });
    }

    // Calculate averages
    summary.averageDailySpend = parseFloat((summary.totalSpend / 30).toFixed(2));
    Object.keys(summary.agents).forEach(agent => {
      summary.agents[agent].avgDailySpend = parseFloat(
        (summary.agents[agent].totalSpend / 30).toFixed(2)
      );
    });

    summary.dailyData = dailyData;
    return summary;
  }

  /**
   * Generate cost breakdown by model
   */
  static generateModelBreakdown() {
    const models = [
      { name: 'claude-3-opus', percentage: 0.10 },      // Most expensive
      { name: 'claude-3-sonnet', percentage: 0.40 },    // Medium
      { name: 'claude-3-haiku', percentage: 0.50 }      // Cheapest
    ];

    const totalCost = Math.random() * 100 + 50;
    const breakdown = {
      totalCost: parseFloat(totalCost.toFixed(2)),
      models: {}
    };

    models.forEach(model => {
      const modelCost = totalCost * model.percentage;
      breakdown.models[model.name] = {
        cost: parseFloat(modelCost.toFixed(2)),
        percentage: model.percentage * 100,
        calls: Math.floor(Math.random() * 1000) + 100
      };
    });

    return breakdown;
  }

  /**
   * Generate real-time cost stream (simulated)
   */
  static generateCostStream(duration = 60) {
    const stream = [];
    const startTime = Date.now();

    for (let i = 0; i < duration; i++) {
      stream.push({
        timestamp: new Date(startTime + i * 1000).toISOString(),
        cost: parseFloat((Math.random() * 0.5).toFixed(4)),
        apiCalls: Math.floor(Math.random() * 10),
        tokens: Math.floor(Math.random() * 5000)
      });
    }

    return stream;
  }

  /**
   * Scenario: Low usage day
   */
  static generateLowUsageDay() {
    return {
      date: new Date().toISOString().split('T')[0],
      agents: {
        scalper: { dailySpend: 0.50, apiCalls: 10, tokens: 20000 },
        john: { dailySpend: 0.25, apiCalls: 5, tokens: 10000 },
        cliff: { dailySpend: 0.10, apiCalls: 2, tokens: 5000 }
      },
      totalSpend: 0.85,
      scenario: 'low_usage'
    };
  }

  /**
   * Scenario: High usage day
   */
  static generateHighUsageDay() {
    return {
      date: new Date().toISOString().split('T')[0],
      agents: {
        scalper: { dailySpend: 150.00, apiCalls: 3000, tokens: 5000000 },
        john: { dailySpend: 45.00, apiCalls: 900, tokens: 1500000 },
        cliff: { dailySpend: 25.00, apiCalls: 500, tokens: 800000 }
      },
      totalSpend: 220.00,
      scenario: 'high_usage'
    };
  }

  /**
   * Generate API usage by cost category
   */
  static generateCostByCategory() {
    const categories = {
      'trading-analysis': { percentage: 0.45, spend: 0 },
      'business-development': { percentage: 0.30, spend: 0 },
      'operations': { percentage: 0.15, spend: 0 },
      'research': { percentage: 0.10, spend: 0 }
    };

    const totalSpend = Math.random() * 100 + 25;

    Object.keys(categories).forEach(cat => {
      categories[cat].spend = parseFloat(
        (totalSpend * categories[cat].percentage).toFixed(2)
      );
    });

    return {
      period: 'daily',
      totalSpend: parseFloat(totalSpend.toFixed(2)),
      categories
    };
  }
}

module.exports = { AnthropicMockDataFactory };
