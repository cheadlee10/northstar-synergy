# DASHBOARD FIX — $1K Hole Root Cause Analysis

**Generated:** 2026-02-24 15:05 PST  
**Status:** CRITICAL — Dashboard does not reflect true company P&L  
**Symptoms:** Showing -$173 net when actual hole is ~$1,000

---

## Current P&L (From Dashboard API)
```
Manual Revenue:              +$89.68
John Jobs Collected:         +$0.00    ← PROBLEM: Should be higher
Kalshi P&L:                  +$0.00    ← PROBLEM: Showing $0, should show actual
Betting P&L:                 +$0.00
                            --------
GROSS REVENUE:               +$89.68

API Costs:                   -$7.47
Expenses (manual):           -$255.33
                            --------
NET P&L:                     -$173.13

EXPECTED HOLE:              ~-$1,000
UNEXPLAINED GAP:             -$827
```

---

## Root Cause #1: KALSHI DATA BROKEN
- Dashboard shows $0.00 P&L across all periods
- Live balance: $0.02 (down from $245 on 2026-02-24)
- Last snapshot: 2026-02-24 23:27:48

**What's happening:**
- Query was "fixed" but still showing $0 P&L
- Either: (a) Kalshi lost $245 in actual trading, or (b) Data pipeline is stale
- Either way, need to verify actual balance from scalper_v8.db

**Fix:**
- [ ] Check Scalper's scalper_v8.db directly for actual Kalshi balance + P&L
- [ ] Re-sync kalshi_snapshots table from primary source
- [ ] Verify analytics.py query is pulling latest snapshot correctly
- [ ] If Kalshi truly lost $245, that's -$245 of the hole (leaving -$582 unaccounted)

---

## Root Cause #2: JOHN'S JOBS NOT TRACKED
- Dashboard shows 0 jobs, $0 invoiced, $0 collected
- John should have revenue from business development

**What's happening:**
- john_jobs.jsonl exists but isn't being synced to dashboard
- auto_populate.py should read from workspace-john/jobs.jsonl
- Either file missing or sync not working

**Fix:**
- [ ] Verify workspace-john/jobs.jsonl exists and has actual job data
- [ ] Check if auto_populate.py is reading it correctly
- [ ] If file is there, ensure john_jobs table is being populated on dashboard sync
- [ ] If John has generated revenue, it should appear here

---

## Root Cause #3: EXPENSES INCOMPLETE
- Showing $255.33 in manual expenses
- Missing operational costs: credits, software, infrastructure, etc.

**What's happening:**
- Expense table is likely being populated manually
- Not capturing all business costs

**Fix:**
- [ ] Audit all actual expenses over past 7 days
- [ ] Add missing categories: cloud hosting, software licenses, third-party APIs
- [ ] Ensure expenses table is complete

---

## Root Cause #4: REVENUE TRACKING IS MANUAL ONLY
- Revenue table shows $89.68 (manual entries)
- Should auto-calculate from: John jobs paid + Kalshi wins + other sources

**Fix:**
- [ ] Build auto-revenue calculation from: john_jobs.collected + kalshi_pnl
- [ ] Stop relying on manual entries
- [ ] Dashboard should be "show me true state" not "show me what I manually logged"

---

## Action Plan

### PHASE 1: DATA AUDIT (15 min)
```bash
# Check what actually exists
1. workspace-scalper/scalper_v8.db — is there Kalshi data?
   - Current balance (actual)
   - P&L history
   - Recent trades

2. workspace-john/jobs.jsonl — does John have jobs?
   - How many jobs?
   - Total revenue?
   - Any collected yet?

3. All expense sources — what costs are real?
   - API costs: $7.47 ✓ (tracked)
   - What else?
```

### PHASE 2: DATA REPAIR (30 min)
1. **Kalshi:** Read scalper_v8.db directly; update kalshi_snapshots with real data
2. **John:** Read jobs.jsonl; sync to john_jobs table
3. **Expenses:** Compile complete list; backfill into expenses table
4. **Revenue:** Delete manual entries; auto-calculate from john_jobs.collected + kalshi_pnl

### PHASE 3: VERIFICATION (10 min)
- Query dashboard API again
- Verify new P&L matches expected -$1,000 hole (or better)
- Check each component is calculating correctly

---

## Quick Diagnosis Script
*Run this to identify what's missing:*

```python
import os, json
from pathlib import Path

# Check Scalper data
scalper_db = Path(r"C:\Users\chead\.openclaw\workspace-scalper\scalper_v8.db")
print(f"Scalper DB exists: {scalper_db.exists()}")

# Check John data
john_jobs = Path(r"C:\Users\chead\.openclaw\workspace-john\jobs.jsonl")
print(f"John jobs.jsonl exists: {john_jobs.exists()}")
if john_jobs.exists():
    with open(john_jobs) as f:
        jobs = [json.loads(line) for line in f if line.strip()]
        print(f"  Jobs: {len(jobs)}")
        total = sum(j.get('invoice_amount', 0) for j in jobs)
        collected = sum(j.get('invoice_amount', 0) for j in jobs if j.get('paid'))
        print(f"  Total invoiced: ${total}")
        print(f"  Collected: ${collected}")
```

---

## Hypothesis
The $1,000 hole likely breaks down as:
- **-$245**: Kalshi losses (balance dropped from startup to near-zero)
- **-$582**: John revenue not captured OR other hidden expenses
- **-$173**: Current dashboard show

**Action:** Find out what John has actually earned (or lost), and we'll find the missing $827.

---

## Next Steps
1. Grant exec permission to run diagnostic script
2. Identify actual data in Scalper/John workspaces
3. Rebuild dashboard from authoritative sources
4. Deploy fixed dashboard that shows real P&L
