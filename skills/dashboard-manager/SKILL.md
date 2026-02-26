# DASHBOARD MANAGER SKILL
**Role:** Cliff (Token Economy Officer)  
**Responsibility:** NorthStar Synergy P&L Dashboard — Data Integrity & Operations  
**Critical:** Craig accesses this from his phone daily. Downtime = crisis.

---

## PRIME DIRECTIVE

The NorthStar Synergy dashboard lives at **a permanent, public URL** (never changes).
Craig views it daily from his phone.
**YOU are responsible for:**
1. Data accuracy (syncs happen on schedule)
2. System health (checks twice daily: 10 AM + 4 PM PT)
3. Data correctness (if wrong, research → fix → verify)
4. Uptime monitoring (alert Craig if down)

---

## DAILY RESPONSIBILITIES

### Morning Check (10 AM PT)
```
1. Verify dashboard is accessible: curl https://[DASHBOARD_URL]/api/summary
2. Check Anthropic sync completed: verify data from last 12h
3. Check Kalshi data: last update timestamp vs now (should be <15 min)
4. Verify all 3 agents' activity: Cliff + Scalper + John
5. If any data is stale (>30 min old): ALERT Craig immediately
```

### Evening Check (4 PM PT)
```
1. Repeat all morning checks
2. Verify 6 PM Anthropic sync completed
3. Check P&L totals match expected (no data corruption)
4. Verify widget renders correctly on mobile (test via Chrome DevTools)
5. Log to memory/dashboard_health.md
```

### Data Verification (If Stale or Wrong)

**If Anthropic usage shows $0 all day:**
```
1. RESEARCH: Check anthropic_usage.jsonl exists and has entries
2. IMPLEMENT: Manually run sync_anthropic_usage.py
3. EXECUTE: Verify data appears on dashboard
4. LOG: What was wrong + what fixed it
```

**If Kalshi balance hasn't updated in >30 min:**
```
1. RESEARCH: Check if Kalshi API is responding
2. CONTACT: Alert Scalper if engine is down
3. IMPLEMENT: Restart sync if needed
4. EXECUTE: Verify balance updates
```

**If dashboard is down (HTTP 500 or 502):**
```
1. Check if dashboard process is running
2. Check error logs
3. Restart if needed
4. ALERT Craig immediately with ETA to fix
```

---

## DEPLOYMENT & ACCESS

### Current Status
- **Local:** `http://localhost:8765` (for dev only)
- **Production:** [DEPLOY THIS] to permanent URL

### Deployment Target
- **Service:** Cloudflare Pages / Vercel / Railway (TBD with Craig)
- **URL:** `https://northstar.cliff.ai` (example — confirm with Craig)
- **SSL:** Automatic (Cloudflare/Vercel)
- **Auto-backup:** Daily snapshot to GitHub

### Access from Phone
- Craig opens permanent URL in Safari/Chrome
- Mobile-responsive (already built into dashboard)
- Works on 4G/WiFi anywhere

---

## MONITORING CHECKLIST

### Twice Daily (10 AM + 4 PM PT)

| Check | Expected | Action if Wrong |
|-------|----------|-----------------|
| Dashboard accessible | HTTP 200 | Restart, alert Craig |
| Anthropic sync | Data <12h old | Run sync manually |
| Kalshi balance | Updated <15m ago | Check API, restart Scalper |
| P&L totals | Match expectations | Audit database |
| Mobile rendering | Works in DevTools | Check CSS, fix responsive |
| Login (if auth added) | Works | Reset credentials |

---

## FILES & LOCATIONS

| File | Purpose |
|------|---------|
| `dashboard/app.py` | Main FastAPI server |
| `dashboard/data/northstar.db` | SQLite database (source of truth) |
| `dashboard/static/` | HTML/CSS/JS frontend |
| `dashboard/sync_anthropic_usage.py` | Anthropic data sync |
| `dashboard/sync_kalshi_live.py` | Kalshi balance sync |
| `memory/dashboard_health.md` | Daily health log |

---

## ESCALATION PROTOCOL

### Data is stale (>30 min old)
```
1. Check sync cron job (did it run?)
2. Check API endpoint manually
3. Run sync manually
4. Verify data appears
5. Log what happened
6. If still broken: ALERT Craig + provide ETA
```

### Dashboard is down
```
1. Check process status
2. Check logs for errors
3. Attempt restart
4. If that fails: ALERT Craig immediately (this is critical)
5. Provide timeline: "Down for 5 min, ETA 10 min to fix"
```

### Data is corrupted (wrong numbers)
```
1. STOP — don't let wrong data sit on dashboard
2. RESEARCH: Where did corruption come from?
3. AUDIT: Last good backup timestamp
4. RESTORE: Revert database if needed
5. IMPLEMENT: Fix root cause
6. VERIFY: Correct data now showing
7. REPORT: Tell Craig what happened + fix
```

---

## RSI LOG (Self-Improvement)

Track all improvements in `memory/rsi_log.md`:
```
[DATE] GAP: Dashboard wasn't mobile-responsive
       ACTION: Added CSS media queries
       RESULT: Works on phone now
       VERDICT: KEEP
```

---

## MONTHLY TASKS

1. **Database backup** — Copy `northstar.db` to GitHub
2. **URL uptime report** — Check pingdom/uptime logs
3. **Mobile testing** — Test on actual phone (not just DevTools)
4. **Performance audit** — Check load times, optimize if slow
5. **Security review** — Check for auth vulnerabilities

---

## SUCCESS CRITERIA

✅ Dashboard is always accessible from Craig's phone  
✅ Data is never >30 min stale  
✅ Numbers are always correct  
✅ If something breaks, Craig knows within 15 min  
✅ Root cause is found and fixed within 1 hour  

---

**This is critical infrastructure. Treat it like nuclear power plant operations.**

---

Created: 2026-02-25  
By: Cliff (Chief Operating Officer)
