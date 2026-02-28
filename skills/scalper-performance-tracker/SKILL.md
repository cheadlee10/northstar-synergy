# SCALPER PERFORMANCE TRACKER SKILL

**Purpose:** Track Scalper's daily bets from 10 AM email, measure performance over time, identify strengths/weaknesses.

**This is NOT P&L tracking.** This is performance analytics: win rate, accuracy, bet quality, trend analysis.

---

## Data Collection

### Daily Bet Email (10 AM PT)
- **Source:** Scalper sends bets every day at 10 AM
- **Parse:** Bet type, stake, odds, market, thesis
- **Log:** Database with timestamp + metadata

### Bet Categories (from Scalper's current portfolio)
1. **Sports Betting** (NCAAB, MLB, NFL, etc.)
   - Game, team, pick, ML odds, stake
   - Result (PENDING/WIN/LOSS)

2. **Kalshi Trading** (Weather, econ, crypto events)
   - Market name, direction (YES/NO), stake, fill price
   - Result (PENDING/WIN/LOSS)

3. **Crypto Snipes** (V8 engine)
   - Coin, entry price, exit price, stake
   - Result (PENDING/WIN/LOSS)

---

## Performance Metrics (Real-time)

### Daily Metrics
- **Total bets placed today:** N
- **Total stake today:** $X
- **Pending bets:** N (waiting for result)
- **Completed bets:** N
- **Win rate (today):** X%

### By Category
| Category | Bets | Wins | Win Rate | ROI | Avg Stake |
|----------|------|------|----------|-----|-----------|
| Sports | | | | | |
| Kalshi | | | | | |
| Crypto | | | | | |

### Historical Trends
- **Week P&L:** +$X
- **Month P&L:** +$X
- **Week win rate:** X%
- **Best performing category:** X (Y% WR)
- **Worst performing category:** X (Y% WR)
- **Edge accuracy:** X% (how often was thesis correct?)

### Advanced Metrics
- **Sharpe ratio:** (Return / Volatility)
- **Max drawdown:** Worst losing streak
- **Consecutive wins/losses:** Current streak
- **Return on risk:** Average win / Average loss

---

## Database Schema

```sql
CREATE TABLE scalper_bets (
  id INTEGER PRIMARY KEY,
  bet_date TEXT NOT NULL,
  bet_type TEXT NOT NULL,  -- 'sports' | 'kalshi' | 'crypto'
  market TEXT,             -- "NCAAB Duke vs UNC" or "BTC price >50k"
  direction TEXT,          -- "ML Duke" or "YES" or "LONG"
  stake REAL NOT NULL,
  odds_decimal REAL,       -- 1.5 for -200, 2.0 for +100
  entry_price REAL,        -- for crypto
  exit_price REAL,         -- for crypto
  thesis TEXT,             -- Why this bet was placed
  result TEXT,             -- 'PENDING' | 'WIN' | 'LOSS'
  profit_loss REAL,        -- Actual P&L if complete
  edge_val REAL,           -- Edge percentage (from Scalper's analysis)
  confidence TEXT,         -- 'HIGH' | 'MEDIUM' | 'LOW'
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT        -- When result determined
);

CREATE TABLE scalper_performance_daily (
  id INTEGER PRIMARY KEY,
  date TEXT NOT NULL UNIQUE,
  total_bets INTEGER,
  total_stake REAL,
  wins INTEGER,
  losses INTEGER,
  win_rate REAL,           -- wins / (wins + losses)
  daily_pnl REAL,
  pending_bets INTEGER,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## Daily Workflow

### 10 AM PT (Email Arrives)
1. **Parse email** → Extract all bets for the day
2. **Insert into database** → `scalper_bets` table
3. **Log:** Date, count, total stake
4. **Display:** Show bets in dashboard

### End of Day (6 PM PT)
1. **Update results** → Mark bets as WIN/LOSS
2. **Calculate metrics** → Update `scalper_performance_daily`
3. **Alert Cliff** → "Scalper: 5 bets today, 3W-2L, +$XXX"

### Weekly (Monday)
1. **Trend analysis** → Week vs previous week
2. **Category breakdown** → Which category is performing best?
3. **Identify patterns** → When does Scalper do well?

---

## Dashboard Widgets

### Real-time
- **Today's Bets** (count + status)
- **Today's Record** (3W-2L, 60% WR)
- **Today's Stake** ($XXX at risk)
- **Week Record** (18W-12L, 60% WR)
- **Best Category** (Sports: 75% WR)
- **Edge Accuracy** (60% — thesis correct, but market moved)

### Historical Trends
- **Win rate by week** (chart)
- **P&L by category** (bar chart)
- **Bet count by category** (pie chart)
- **Consecutive win/loss streaks** (line chart)
- **Performance vs market conditions** (correlation analysis)

---

## Implementation

### Step 1: Email Parser
- Read Scalper's 10 AM email
- Extract: market, direction, stake, odds
- Insert into database

### Step 2: Result Updater
- At market close, mark bets as WIN/LOSS
- Calculate P&L
- Update daily summary

### Step 3: Dashboard Widgets
- Real-time bet counter
- Performance metrics (win rate, ROI, streak)
- Historical trends + charts

### Step 4: Alerts
- Alert Cliff daily with Scalper's record
- Alert if win rate drops below threshold
- Highlight best/worst performing categories

---

## Success Criteria

✅ Every bet Scalper places is tracked  
✅ Performance measured daily  
✅ Trends visible over time (week, month, year)  
✅ Categories compared (what works best?)  
✅ Edge accuracy measured (was thesis correct?)  
✅ Dashboard updates automatically  
✅ Cliff can see at a glance: Is Scalper good? Improving? Where's he strong?

---

## Next Steps

1. Build email parser for 10 AM bets
2. Create database schema
3. Build dashboard widgets
4. Set up daily result updater
5. Add trend analysis
6. Integrate with main dashboard

---

Created: 2026-02-25  
Owner: Cliff (with Scalper collaboration)  
Priority: CRITICAL (this is how we measure trading performance)
