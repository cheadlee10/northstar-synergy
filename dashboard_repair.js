#!/usr/bin/env node
/**
 * Dashboard Repair Script
 * Identifies missing data, rebuilds P&L from authoritative sources
 */
const path = require('path');
const fs = require('fs');
const sqlite3 = require('sqlite3').verbose();

const DASHBOARD_DB = r'C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db';
const SCALPER_DB = r'C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db';
const JOHN_JOBS = r'C:\Users\chead\.openclaw\workspace-john\jobs.jsonl';

console.log('=' .repeat(80));
console.log('DASHBOARD REPAIR — P&L RECONCILIATION');
console.log('=' .repeat(80));

let findings = {
  kalshi: {},
  john: {},
  dashboard: {},
  gap: 0,
  recommendations: []
};

// 1. CHECK JOHN'S ACTUAL JOBS
console.log('\n[1] JOHN\'S BUSINESS AUDIT');
if (fs.existsSync(JOHN_JOBS)) {
  try {
    const lines = fs.readFileSync(JOHN_JOBS, 'utf-8').trim().split('\n');
    const jobs = lines.filter(l => l.trim()).map(l => JSON.parse(l));
    
    const invoiced = jobs.reduce((sum, j) => sum + (j.invoice_amount || 0), 0);
    const collected = jobs.filter(j => j.paid).reduce((sum, j) => sum + (j.invoice_amount || 0), 0);
    
    console.log(`    Jobs file: EXISTS (${jobs.length} jobs)`);
    console.log(`    Total invoiced: $${invoiced.toFixed(2)}`);
    console.log(`    Collected: $${collected.toFixed(2)}`);
    console.log(`    Unpaid: $${(invoiced - collected).toFixed(2)}`);
    
    findings.john = {
      exists: true,
      total_jobs: jobs.length,
      invoiced,
      collected,
      unpaid: invoiced - collected
    };
    
    if (collected > 0 && collected > 100) {
      findings.recommendations.push(`John has $${collected.toFixed(2)} collected but dashboard shows $0 — SYNC BROKEN`);
      findings.gap += collected; // This is missing revenue
    }
  } catch (e) {
    console.log(`    ERROR reading jobs: ${e.message}`);
  }
} else {
  console.log(`    Jobs file: MISSING (${JOHN_JOBS})`);
}

// 2. CHECK SCALPER'S KALSHI DATA
console.log('\n[2] SCALPER\'S KALSHI AUDIT');
if (fs.existsSync(SCALPER_DB)) {
  try {
    const db = new sqlite3.Database(SCALPER_DB);
    db.all(`
      SELECT 
        MAX(balance_cents) last_balance,
        SUM(daily_pnl_cents) total_pnl,
        COUNT(*) snapshots,
        MAX(timestamp) last_ts
      FROM kalshi_snapshots
    `, [], (err, rows) => {
      if (err) {
        console.log(`    ERROR: ${err.message}`);
      } else if (rows && rows[0]) {
        const row = rows[0];
        const balance = (row.last_balance || 0) / 100;
        const pnl = (row.total_pnl || 0) / 100;
        const snaps = row.snapshots || 0;
        
        console.log(`    Scalper DB: EXISTS`);
        console.log(`    Current balance: $${balance.toFixed(2)}`);
        console.log(`    Total P&L: $${pnl.toFixed(2)}`);
        console.log(`    Snapshots: ${snaps}`);
        console.log(`    Last update: ${row.last_ts}`);
        
        findings.kalshi = {
          exists: true,
          balance,
          pnl,
          snapshots: snaps
        };
      }
      db.close();
      finish();
    });
  } catch (e) {
    console.log(`    ERROR: ${e.message}`);
    finish();
  }
} else {
  console.log(`    Scalper DB: MISSING (${SCALPER_DB})`);
  finish();
}

function finish() {
  // 3. COMPARE TO DASHBOARD
  console.log('\n[3] DASHBOARD CURRENT STATE');
  console.log(`    Revenue (manual): $89.68`);
  console.log(`    API Costs: -$7.47`);
  console.log(`    Expenses: -$255.33`);
  console.log(`    NET: -$173.13`);
  
  // 4. CALCULATE REAL P&L
  console.log('\n[4] REAL P&L CALCULATION');
  const real_revenue = (findings.john.collected || 0) + (findings.kalshi.pnl || 0) + 89.68;
  const real_expenses = 255.33 + 7.47;
  const real_net = real_revenue - real_expenses;
  
  console.log(`    Revenue (John): $${(findings.john.collected || 0).toFixed(2)}`);
  console.log(`    Revenue (manual): $89.68`);
  console.log(`    Revenue (Kalshi): $${(findings.kalshi.pnl || 0).toFixed(2)}`);
  console.log(`    TOTAL REVENUE: $${real_revenue.toFixed(2)}`);
  console.log(`    Expenses: -$${real_expenses.toFixed(2)}`);
  console.log(`    REAL NET P&L: ${real_net < 0 ? '-' : ''}$${Math.abs(real_net).toFixed(2)}`);
  
  // 5. RECOMMENDATIONS
  console.log('\n[5] ISSUES & FIXES');
  if (findings.john.invoiced > 0 && findings.john.collected === 0) {
    console.log(`    ❌ John has $${findings.john.invoiced.toFixed(2)} invoiced but dashboard doesn't see any collections`);
    console.log(`       FIX: Sync john_jobs.jsonl to dashboard john_jobs table`);
  }
  if (findings.kalshi.balance < 50) {
    console.log(`    ⚠️  Kalshi balance is LOW: $${findings.kalshi.balance.toFixed(2)}`);
    console.log(`       STATUS: Account is at risk`);
  }
  if (findings.kalshi.pnl < 0) {
    console.log(`    ❌ Kalshi P&L is NEGATIVE: -$${Math.abs(findings.kalshi.pnl).toFixed(2)} loss`);
    console.log(`       This is the main reason for the hole`);
  }
  
  console.log('\n' + '=' .repeat(80));
  console.log('FINDINGS JSON:');
  console.log(JSON.stringify(findings, null, 2));
}
