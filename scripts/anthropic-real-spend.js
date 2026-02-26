#!/usr/bin/env node
/**
 * REAL TOKEN SPEND MONITOR — Hits Anthropic API Directly
 * Pulls actual usage data from: https://api.anthropic.com/v1/organizations/usage_report/messages
 * Requires: ANTHROPIC_ADMIN_API_KEY environment variable
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const ANTHROPIC_API = 'https://api.anthropic.com/v1/organizations/usage_report/messages';
const ADMIN_API_KEY = process.env.ANTHROPIC_ADMIN_API_KEY || process.env.ANTHROPIC_API_KEY;

async function getUsageFromAnthropicAPI(startDate, endDate) {
  return new Promise((resolve, reject) => {
    if (!ADMIN_API_KEY) {
      return reject(new Error('ANTHROPIC_ADMIN_API_KEY or ANTHROPIC_API_KEY environment variable not set'));
    }

    // Build query params
    const params = new URLSearchParams({
      starting_at: startDate || new Date(Date.now() - 86400000).toISOString(), // Last 24h
      ending_at: endDate || new Date().toISOString(),
      group_by: 'model', // Group by model (claude-opus, claude-sonnet, etc)
      bucket_width: '1d', // Daily buckets
    });

    const url = `${ANTHROPIC_API}?${params.toString()}`;

    console.log(`[ANTHROPIC] Fetching usage data...`);
    console.log(`[ANTHROPIC] URL: ${url.split('?')[0]}?...`);

    const options = {
      hostname: 'api.anthropic.com',
      port: 443,
      path: `/v1/organizations/usage_report/messages?${params.toString()}`,
      method: 'GET',
      headers: {
        'anthropic-version': '2023-06-01',
        'x-api-key': ADMIN_API_KEY,
      },
    };

    const req = https.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          if (res.statusCode !== 200) {
            console.log(`[ERROR] Status ${res.statusCode}: ${data}`);
            return reject(new Error(`API returned ${res.statusCode}: ${data}`));
          }

          const parsed = JSON.parse(data);
          resolve(parsed);
        } catch (error) {
          reject(new Error(`Failed to parse response: ${error.message}`));
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

async function parseUsageData(data) {
  console.log(`\n[PARSE] Analyzing usage report...`);

  if (!data.data || !Array.isArray(data.data)) {
    console.log('[WARNING] Unexpected response format');
    return null;
  }

  let totalInputTokens = 0;
  let totalOutputTokens = 0;
  let totalCostUSD = 0;
  let models = {};

  for (const entry of data.data) {
    const inputTokens = entry.input_tokens || 0;
    const outputTokens = entry.output_tokens || 0;
    const cost = entry.cost || 0; // Cost in USD

    totalInputTokens += inputTokens;
    totalOutputTokens += outputTokens;
    totalCostUSD += cost;

    const model = entry.model || 'unknown';
    if (!models[model]) {
      models[model] = { input: 0, output: 0, cost: 0 };
    }
    models[model].input += inputTokens;
    models[model].output += outputTokens;
    models[model].cost += cost;
  }

  return {
    totalInputTokens,
    totalOutputTokens,
    totalTokens: totalInputTokens + totalOutputTokens,
    totalCostUSD: parseFloat(totalCostUSD.toFixed(2)),
    models,
    dataPoints: data.data.length,
  };
}

async function logSpend(summary) {
  const logFile = path.join(
    process.env.USERPROFILE,
    '.openclaw',
    'workspace',
    'memory',
    'ANTHROPIC_REAL_SPEND.md'
  );

  const now = new Date().toISOString();
  const content = `# REAL ANTHROPIC SPEND — Live API Data
**Last Updated:** ${now}
**Budget:** $5.00/day

## Summary

| Metric | Value |
|--------|-------|
| **Total Cost (Today)** | **$${summary.totalCostUSD}** |
| Total Tokens | ${summary.totalTokens.toLocaleString()} |
| Input Tokens | ${summary.totalInputTokens.toLocaleString()} |
| Output Tokens | ${summary.totalOutputTokens.toLocaleString()} |
| Data Points | ${summary.dataPoints} |

## By Model

${Object.entries(summary.models)
  .map(
    ([model, data]) =>
      `| ${model} | $${data.cost.toFixed(2)} | ${data.input.toLocaleString()} in | ${data.output.toLocaleString()} out |`
  )
  .join('\n')}

## Status

${
  summary.totalCostUSD > 5
    ? '🔴 **OVER BUDGET** — Daily spend exceeded $5'
    : summary.totalCostUSD > 4
      ? '🟡 **CAUTION** — Approaching $5 daily limit'
      : '✅ **ON TRACK** — Within budget'
}

---

**Source:** Anthropic Usage and Cost API (real data)
**Verified:** ${now}
`;

  fs.writeFileSync(logFile, content);
  console.log(`\n[LOG] Spend logged to: ${logFile}`);
}

async function main() {
  try {
    console.log('═══════════════════════════════════════════════════════════');
    console.log('ANTHROPIC REAL SPEND MONITOR');
    console.log('═══════════════════════════════════════════════════════════\n');

    // Get today's spend
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const startDate = today.toISOString();
    const endDate = new Date().toISOString();

    console.log(`[QUERY] Date range: ${startDate.split('T')[0]}`);
    console.log(`[QUERY] Admin API Key: ${ADMIN_API_KEY ? '✅ Provided' : '❌ MISSING'}`);

    if (!ADMIN_API_KEY) {
      console.log(
        '\n[ERROR] No admin API key. Set: ANTHROPIC_ADMIN_API_KEY=sk_... or ANTHROPIC_API_KEY=sk_...'
      );
      console.log('[INFO] Usage API requires admin-level API key (not regular API key)');
      return;
    }

    const usage = await getUsageFromAnthropicAPI(startDate, endDate);
    console.log(`[API] Response received (${JSON.stringify(usage).length} bytes)`);

    const summary = await parseUsageData(usage);

    if (!summary) {
      console.log('[ERROR] Failed to parse usage data');
      return;
    }

    // Display results
    console.log(`\n═══════════════════════════════════════════════════════════`);
    console.log('TODAY\'S SPEND (Real Data from Anthropic)');
    console.log(`═══════════════════════════════════════════════════════════`);
    console.log(`\n💵 Total Cost: $${summary.totalCostUSD.toFixed(2)}`);
    console.log(`📊 Total Tokens: ${summary.totalTokens.toLocaleString()}`);
    console.log(`  ├─ Input: ${summary.totalInputTokens.toLocaleString()}`);
    console.log(`  └─ Output: ${summary.totalOutputTokens.toLocaleString()}`);
    console.log(`\n📈 By Model:`);

    for (const [model, data] of Object.entries(summary.models)) {
      console.log(`  ${model}:`);
      console.log(`    Cost: $${data.cost.toFixed(2)}`);
      console.log(`    Tokens: ${(data.input + data.output).toLocaleString()} (${data.input} in, ${data.output} out)`);
    }

    console.log(`\n📋 Status:`);
    if (summary.totalCostUSD > 5) {
      console.log(`  🔴 OVER BUDGET (${((summary.totalCostUSD / 5) * 100).toFixed(0)}% of daily limit)`);
    } else if (summary.totalCostUSD > 4) {
      console.log(`  🟡 CAUTION (${((summary.totalCostUSD / 5) * 100).toFixed(0)}% of daily limit)`);
    } else {
      console.log(`  ✅ ON TRACK (${((summary.totalCostUSD / 5) * 100).toFixed(0)}% of daily limit)`);
    }

    // Log to file
    await logSpend(summary);

    console.log(`\n═══════════════════════════════════════════════════════════`);
  } catch (error) {
    console.error(`\n[FATAL] ${error.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { getUsageFromAnthropicAPI, parseUsageData };
