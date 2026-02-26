/**
 * ANTHROPIC USAGE TRACKER (File-based)
 * Intercepts Anthropic API responses and logs token usage + costs
 * 
 * No external dependencies. Uses JSON + file system for maximum reliability.
 * 
 * Features:
 * - Real-time token tracking (no delays)
 * - Per-agent attribution (Cliff, Scalper, John)
 * - Cost calculation by model
 * - JSON persistence (immutable append-only log)
 * - Query interface for reports
 * - Audit trail (all data timestamped)
 */

const fs = require('fs');
const path = require('path');

const LOG_DIR = path.join(process.env.HOME || process.env.USERPROFILE, '.openclaw', 'workspace', 'data');
const USAGE_LOG_FILE = path.join(LOG_DIR, 'anthropic_usage.jsonl');
const PRICING_FILE = path.join(LOG_DIR, 'anthropic_pricing.json');

// Ensure data directory exists
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

// Model pricing (cost per million tokens)
const DEFAULT_PRICING = {
  'claude-opus-4-6': { input: 15, output: 75, context: 200000 },
  'claude-sonnet-4-6': { input: 3, output: 15, context: 200000 },
  'claude-haiku-4-5': { input: 0.80, output: 4, context: 200000 },
  'claude-3.5-sonnet': { input: 3, output: 15, context: 200000 },
  'claude-3-opus': { input: 15, output: 75, context: 200000 },
};

class AnthropicUsageTracker {
  constructor() {
    this.pricingCache = null;
  }

  /**
   * Initialize and load pricing
   */
  init() {
    this.loadPricing();
    console.log(`[TRACKER] Initialized | Logs: ${USAGE_LOG_FILE}`);
  }

  /**
   * Load or create pricing file
   */
  loadPricing() {
    try {
      if (fs.existsSync(PRICING_FILE)) {
        this.pricingCache = JSON.parse(fs.readFileSync(PRICING_FILE, 'utf-8'));
      } else {
        this.pricingCache = { ...DEFAULT_PRICING };
        this.savePricing();
      }
    } catch (err) {
      console.warn('[TRACKER] Pricing load failed, using defaults:', err.message);
      this.pricingCache = { ...DEFAULT_PRICING };
    }
  }

  /**
   * Save pricing to file
   */
  savePricing() {
    try {
      fs.writeFileSync(PRICING_FILE, JSON.stringify(this.pricingCache, null, 2));
    } catch (err) {
      console.error('[TRACKER] Failed to save pricing:', err);
    }
  }

  /**
   * Log a single API call (append-only, no overwrites)
   */
  logUsage({
    agentId = 'unknown',
    model = 'unknown',
    inputTokens = 0,
    outputTokens = 0,
    apiRequestId = null,
  }) {
    // Get pricing for this model
    const pricing = this.pricingCache[model] || { input: 0, output: 0 };

    // Calculate costs (input/output per token, then scale to actual usage)
    const inputCost = (inputTokens / 1_000_000) * pricing.input;
    const outputCost = (outputTokens / 1_000_000) * pricing.output;
    const totalCost = inputCost + outputCost;
    const totalTokens = inputTokens + outputTokens;

    const logEntry = {
      timestamp: new Date().toISOString(),
      agent_id: agentId,
      model: model,
      input_tokens: inputTokens,
      output_tokens: outputTokens,
      total_tokens: totalTokens,
      input_cost: parseFloat(inputCost.toFixed(6)),
      output_cost: parseFloat(outputCost.toFixed(6)),
      total_cost: parseFloat(totalCost.toFixed(6)),
      api_request_id: apiRequestId,
    };

    // Append to log file (atomic write)
    try {
      fs.appendFileSync(USAGE_LOG_FILE, JSON.stringify(logEntry) + '\n');
      console.log(`[TRACKER] Logged: ${agentId} | ${model} | ${totalTokens} tokens | $${totalCost.toFixed(4)}`);
      return logEntry;
    } catch (err) {
      console.error('[TRACKER] Failed to log usage:', err);
      throw err;
    }
  }

  /**
   * Read all log entries
   */
  readAllLogs() {
    try {
      if (!fs.existsSync(USAGE_LOG_FILE)) {
        return [];
      }

      const content = fs.readFileSync(USAGE_LOG_FILE, 'utf-8');
      return content
        .split('\n')
        .filter((line) => line.trim())
        .map((line) => JSON.parse(line));
    } catch (err) {
      console.error('[TRACKER] Failed to read logs:', err);
      return [];
    }
  }

  /**
   * Get spend for a specific date
   */
  getSpendByDate(dateStr) {
    const logs = this.readAllLogs();
    const filtered = logs.filter(
      (log) => log.timestamp.startsWith(dateStr)
    );

    const totals = {
      date: dateStr,
      total_tokens: 0,
      total_cost: 0,
      request_count: 0,
      by_agent: {},
      by_model: {},
    };

    filtered.forEach((log) => {
      totals.total_tokens += log.total_tokens;
      totals.total_cost += log.total_cost;
      totals.request_count += 1;

      // By agent
      if (!totals.by_agent[log.agent_id]) {
        totals.by_agent[log.agent_id] = { tokens: 0, cost: 0, requests: 0 };
      }
      totals.by_agent[log.agent_id].tokens += log.total_tokens;
      totals.by_agent[log.agent_id].cost += log.total_cost;
      totals.by_agent[log.agent_id].requests += 1;

      // By model
      if (!totals.by_model[log.model]) {
        totals.by_model[log.model] = { tokens: 0, cost: 0, requests: 0 };
      }
      totals.by_model[log.model].tokens += log.total_tokens;
      totals.by_model[log.model].cost += log.total_cost;
      totals.by_model[log.model].requests += 1;
    });

    return totals;
  }

  /**
   * Get today's spend
   */
  getTodaySpend() {
    const today = new Date().toISOString().split('T')[0];
    return this.getSpendByDate(today);
  }

  /**
   * Get weekly spend (last 7 days)
   */
  getWeeklySpend() {
    const logs = this.readAllLogs();
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    const filtered = logs.filter((log) => log.timestamp.substring(0, 10) >= sevenDaysAgo);

    let total_tokens = 0;
    let total_cost = 0;

    filtered.forEach((log) => {
      total_tokens += log.total_tokens;
      total_cost += log.total_cost;
    });

    return {
      period: 'Last 7 days',
      total_tokens,
      total_cost: parseFloat(total_cost.toFixed(2)),
      request_count: filtered.length,
    };
  }

  /**
   * Get full report
   */
  getReport() {
    const today = this.getTodaySpend();
    const weekly = this.getWeeklySpend();

    return {
      today,
      weekly,
      log_file: USAGE_LOG_FILE,
      total_entries: this.readAllLogs().length,
    };
  }
}

// CLI interface
if (require.main === module) {
  const tracker = new AnthropicUsageTracker();
  tracker.init();

  const cmd = process.argv[2];

  if (cmd === 'report') {
    const report = tracker.getReport();
    console.log('\n=== USAGE REPORT ===');
    console.log('TODAY:', JSON.stringify(report.today, null, 2));
    console.log('\nWEEKLY:', JSON.stringify(report.weekly, null, 2));
    console.log('\nLog file:', report.log_file);
  } else if (cmd === 'test') {
    // Test logging
    console.log('Testing tracker...');
    tracker.logUsage({
      agentId: 'cliff',
      model: 'claude-opus-4-6',
      inputTokens: 1000,
      outputTokens: 500,
      apiRequestId: 'test-001',
    });
    console.log('✓ Test log successful');
    console.log('\nReport after test log:');
    const report = tracker.getReport();
    console.log(JSON.stringify(report.today, null, 2));
  } else {
    console.log('Usage: node anthropic-usage-tracker.js [report|test]');
  }
}

module.exports = AnthropicUsageTracker;
