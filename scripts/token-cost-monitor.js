#!/usr/bin/env node
/**
 * TOKEN COST MONITOR — Real-Time Daily Spend Tracking
 * Alerts when daily burn exceeds $5 or hourly trajectory hits limits
 * Runs hourly via Task Scheduler
 */

const fs = require('fs');
const path = require('path');

const DAILY_BUDGET = 5.00;
const HOURLY_BUDGET = DAILY_BUDGET / 24; // $0.208/hour
const TOKEN_LOG = path.join(process.env.USERPROFILE, '.openclaw', 'workspace', 'memory', 'token_costs.jsonl');
const ALERT_LOG = path.join(process.env.USERPROFILE, '.openclaw', 'workspace', 'memory', 'token_alerts.md');

/**
 * Parse token usage from session logs
 * Expected format: each line = JSON with timestamp, cost, source
 */
async function getTokenCosts() {
  if (!fs.existsSync(TOKEN_LOG)) {
    return { hourly: 0, daily: 0, agents: {} };
  }

  const now = new Date();
  const today = now.toISOString().split('T')[0];
  const currentHour = now.getHours();
  
  const lines = fs.readFileSync(TOKEN_LOG, 'utf-8').trim().split('\n').filter(l => l);
  let hourlySpend = 0;
  let dailySpend = 0;
  let agents = {};

  lines.forEach(line => {
    try {
      const entry = JSON.parse(line);
      if (!entry.timestamp || !entry.cost) return;

      const entryDate = entry.timestamp.split('T')[0];
      const entryHour = new Date(entry.timestamp).getHours();

      // Count daily spend
      if (entryDate === today) {
        dailySpend += entry.cost;
        
        // Count hourly spend (only current hour)
        if (entryHour === currentHour) {
          hourlySpend += entry.cost;
        }
      }

      // Track by agent
      const agent = entry.agent || 'unknown';
      agents[agent] = (agents[agent] || 0) + entry.cost;
    } catch (e) {
      // Skip malformed lines
    }
  });

  return { hourly: hourlySpend, daily: dailySpend, agents };
}

/**
 * Calculate hourly trajectory
 * If we're on pace to exceed daily budget by hour X, alert
 */
function calculateTrajectory(hourlySpend, currentHour, dailySpend) {
  const hoursRemaining = 24 - currentHour;
  const projectedDaily = dailySpend + (hourlySpend * hoursRemaining);
  const percentOfBudget = (dailySpend / DAILY_BUDGET) * 100;
  
  return {
    projectedDaily,
    percentOfBudget,
    hoursRemaining,
    onTrack: projectedDaily <= DAILY_BUDGET,
  };
}

/**
 * Log alerts if thresholds exceeded
 */
function logAlert(type, message, data) {
  const timestamp = new Date().toISOString();
  const alert = `\n[${timestamp}] 🔴 ${type}\n${message}\n${JSON.stringify(data, null, 2)}`;
  
  let existing = '';
  if (fs.existsSync(ALERT_LOG)) {
    existing = fs.readFileSync(ALERT_LOG, 'utf-8');
  }
  
  fs.writeFileSync(ALERT_LOG, existing + alert);
  
  // Also log to observations for Cliff's heartbeat
  const obsLog = path.join(process.env.USERPROFILE, '.openclaw', 'workspace', 'memory', 'observations.md');
  const obsEntry = `\n[${new Date().toLocaleTimeString()}] 🔴 TOKEN ALERT: ${type}\nDetails: ${message}`;
  
  if (fs.existsSync(obsLog)) {
    const obs = fs.readFileSync(obsLog, 'utf-8');
    fs.writeFileSync(obsLog, obs + obsEntry);
  }
  
  return timestamp;
}

/**
 * Write daily status to memory
 */
async function updateTokenMemory(costs, trajectory) {
  const memoryFile = path.join(process.env.USERPROFILE, '.openclaw', 'workspace', 'memory', 'DAILY_TOKEN_STATUS.md');
  const today = new Date().toISOString().split('T')[0];
  const now = new Date();
  
  const status = `# Daily Token Cost Status — ${today}

**Current Time:** ${now.toLocaleTimeString()}  
**Budget:** $${DAILY_BUDGET.toFixed(2)}/day

## Spending

| Metric | Value | Status |
|--------|-------|--------|
| Hourly spend (this hour) | $${costs.hourly.toFixed(3)} | ${costs.hourly > HOURLY_BUDGET * 1.5 ? '🔴 HIGH' : '🟢 OK'} |
| Daily spend (so far) | $${costs.daily.toFixed(2)} | ${trajectory.percentOfBudget > 100 ? '🔴 OVER' : trajectory.percentOfBudget > 80 ? '🟡 CAUTION' : '🟢 OK'} |
| Projected end of day | $${trajectory.projectedDaily.toFixed(2)} | ${trajectory.onTrack ? '✅ On track' : '❌ WILL EXCEED'} |
| % of daily budget | ${trajectory.percentOfBudget.toFixed(1)}% | — |

## By Agent

${Object.entries(costs.agents)
  .map(([agent, spend]) => `- **${agent}**: $${spend.toFixed(2)}`)
  .join('\n')}

## Alert Status

${trajectory.percentOfBudget > 100 ? '🔴 **OVER BUDGET** — Daily spend exceeded $5. Review agent activity.' : ''}
${trajectory.projectedDaily > DAILY_BUDGET ? '🟡 **CAUTION** — On pace to exceed daily budget by EOD.' : ''}
${costs.hourly > HOURLY_BUDGET * 2 ? '🟡 **HIGH HOURLY** — Spending above expected hourly rate.' : ''}
${trajectory.percentOfBudget <= 80 && costs.hourly <= HOURLY_BUDGET * 1.5 ? '✅ **HEALTHY** — Within budget parameters.' : ''}

---

*Last updated: ${now.toISOString()}*
`;

  fs.writeFileSync(memoryFile, status);
}

/**
 * MAIN: Check costs and alert if necessary
 */
async function main() {
  const costs = await getTokenCosts();
  const currentHour = new Date().getHours();
  const trajectory = calculateTrajectory(costs.hourly, currentHour, costs.daily);

  // Update memory with current status
  await updateTokenMemory(costs, trajectory);

  // ALERT TRIGGERS
  
  // 1. Daily budget exceeded
  if (costs.daily > DAILY_BUDGET) {
    logAlert(
      'DAILY_BUDGET_EXCEEDED',
      `Daily spend ($${costs.daily.toFixed(2)}) exceeds budget ($${DAILY_BUDGET.toFixed(2)})`,
      { daily: costs.daily, budget: DAILY_BUDGET, excess: costs.daily - DAILY_BUDGET }
    );
  }

  // 2. Projected to exceed by end of day
  if (trajectory.projectedDaily > DAILY_BUDGET * 1.1 && trajectory.percentOfBudget > 60) {
    logAlert(
      'PROJECTED_BUDGET_EXCEED',
      `On pace to exceed daily budget. Projected: $${trajectory.projectedDaily.toFixed(2)}`,
      {
        projected: trajectory.projectedDaily,
        budget: DAILY_BUDGET,
        percentSpent: trajectory.percentOfBudget,
        hoursRemaining: trajectory.hoursRemaining,
      }
    );
  }

  // 3. Hourly spike (2x normal rate)
  if (costs.hourly > HOURLY_BUDGET * 2) {
    logAlert(
      'HOURLY_SPIKE',
      `Hourly spend ($${costs.hourly.toFixed(3)}) is 2x expected rate ($${HOURLY_BUDGET.toFixed(3)})`,
      {
        hourlySpend: costs.hourly,
        expectedHourly: HOURLY_BUDGET,
        agents: costs.agents,
      }
    );
  }

  // 4. Single agent exceeding allocation
  const avgPerAgent = costs.daily / Object.keys(costs.agents).length;
  Object.entries(costs.agents).forEach(([agent, spend]) => {
    if (spend > avgPerAgent * 1.5) {
      logAlert(
        `AGENT_OVERSPEND_${agent.toUpperCase()}`,
        `Agent "${agent}" spending above expected rate`,
        {
          agent,
          spend,
          expectedAvg: avgPerAgent,
          excess: spend - avgPerAgent,
        }
      );
    }
  });

  // Console output (for Task Scheduler logs)
  console.log(`[${new Date().toISOString()}] TOKEN MONITOR`);
  console.log(`Daily: $${costs.daily.toFixed(2)}/$${DAILY_BUDGET} | Projected: $${trajectory.projectedDaily.toFixed(2)} | ${trajectory.percentOfBudget.toFixed(1)}%`);
  console.log(`Status: ${trajectory.onTrack ? 'ON TRACK' : 'CAUTION'}`);
}

main().catch(err => {
  console.error('TOKEN MONITOR ERROR:', err.message);
  process.exit(1);
});
