# DATA ARCHITECTURE MASTERY SKILL

**Based on:** Stripe (Flink + Pinot), Bloomberg, TradesViz research  
**Purpose:** Real-time financial analytics at scale  
**Standard:** <300ms query latency, 99.9% accuracy  

---

## ARCHITECTURE COMPONENTS

### 1. Event Streaming (Stripe Pattern)
**Concept:** Don't wait for batch processing. Stream events in real-time.

**Implementation Options:**
- **Apache Kafka** (enterprise-grade, exactly-once semantics)
- **Postgres LISTEN/NOTIFY** (simpler, built-in)
- **Event table** (simplest: append-only log)

**For NorthStar:**
```
Event Stream:
  - Scalper places bet (10 AM email) → INSERT into scalper_bets
  - Market closes (4 PM) → UPDATE bet result (WIN/LOSS)
  - API call happens → INSERT into api_usage
  - Job completed → INSERT into company_revenue
  
All events → Aggregation pipeline
```

**Key Insight:** State is incremental, not recalculated from scratch.

### 2. State Management (Stripe's Flink Pattern)
**Concept:** Maintain "running ledger" of aggregates.

**Without Streaming:**
```sql
SELECT SUM(profit_loss) FROM scalper_bets WHERE date = '2026-02-25'
-- Have to scan ALL bets every time (slow)
```

**With State:**
```
State: "Feb 25 total profit = +$400"
New bet arrives → State updates to "+$425"
Query runs against state (instant)
```

**Implementation:**
```python
# Pseudo-code
daily_state = {
  "2026-02-25": {
    "total_bets": 5,
    "total_stake": $1000,
    "wins": 3,
    "losses": 2,
    "profit_loss": +$400,
    "by_category": {
      "sports": {...},
      "kalshi": {...},
      "crypto": {...}
    }
  }
}

# When new bet arrives:
daily_state["2026-02-25"]["total_bets"] += 1
daily_state["2026-02-25"]["profit_loss"] += bet_result
# Instant. No re-aggregation.
```

### 3. Time-Series Database Design
**Tools:**
- **TimescaleDB** (Postgres extension, time-optimized)
- **InfluxDB** (purpose-built, expensive)
- **Plain Postgres** with indexes (sufficient for NorthStar's scale)

**Schema Principles:**
- Immutable events (events, not updates)
- Aggregation tables (daily/weekly/monthly summaries)
- Indexed by time (critical for range queries)

**For NorthStar:**
```sql
-- Events (immutable)
CREATE TABLE scalper_bets (
  id SERIAL PRIMARY KEY,
  placed_at TIMESTAMP NOT NULL,
  market_closes_at TIMESTAMP,
  market TEXT,
  stake DECIMAL,
  result TEXT,  -- 'WIN' | 'LOSS' | 'PENDING'
  profit_loss DECIMAL,
  INDEX on placed_at
);

-- Aggregates (daily)
CREATE TABLE scalper_daily_summary (
  date DATE PRIMARY KEY,
  total_bets INT,
  wins INT,
  losses INT,
  profit_loss DECIMAL,
  by_category JSONB,  -- {sports: {...}, kalshi: {...}, ...}
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 4. Query Patterns for <300ms Latency

**FAST (use these):**
```sql
-- Query on aggregation table (daily summary)
SELECT * FROM scalper_daily_summary WHERE date >= '2026-02-20'
-- 10ms response

-- Query with index
SELECT SUM(profit_loss) FROM scalper_bets 
WHERE placed_at >= '2026-02-20' AND placed_at < '2026-02-21'
-- 50ms response (index speeds this up)
```

**SLOW (avoid):**
```sql
-- Full table scan, no aggregation
SELECT * FROM scalper_bets WHERE EXTRACT(YEAR FROM placed_at) = 2026
-- 5000ms response

-- Complex calculation in query
SELECT 
  placed_at,
  (SELECT AVG(stake) FROM scalper_bets) as avg_stake  -- Correlated subquery
FROM scalper_bets
-- 2000ms response
```

**Optimization Rule:** Aggregates at write-time, queries at read-time.

### 5. Hierarchical Drill-Down Queries
**Pattern:** Query at multiple levels (month → week → day → trade)

```sql
-- Level 1: Monthly
SELECT 
  DATE_TRUNC('month', placed_at) as month,
  SUM(profit_loss) as profit
FROM scalper_bets
GROUP BY month;

-- Level 2: Weekly (drill-down)
SELECT 
  DATE_TRUNC('week', placed_at) as week,
  SUM(profit_loss) as profit
FROM scalper_bets
WHERE DATE_TRUNC('month', placed_at) = '2026-02-01'
GROUP BY week;

-- Level 3: Daily (drill-down further)
SELECT 
  DATE(placed_at) as day,
  SUM(profit_loss) as profit
FROM scalper_bets
WHERE DATE_TRUNC('week', placed_at) = '2026-02-18'
GROUP BY day;

-- Level 4: Individual trade (final drill-down)
SELECT * FROM scalper_bets
WHERE DATE(placed_at) = '2026-02-25'
ORDER BY placed_at;
```

**UI Implementation:** Click month → shows weeks. Click week → shows days. Click day → shows trades.

### 6. Attribution Decomposition

**Example:** "Scalper made +$400 today. Why?"

```sql
SELECT 
  category,
  COUNT(*) as num_bets,
  SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
  SUM(profit_loss) as profit_loss
FROM scalper_bets
WHERE DATE(placed_at) = '2026-02-25'
GROUP BY category;

-- Result:
-- sports: 2 bets, 2 wins, +$300
-- kalshi: 2 bets, 1 win, +$100
-- crypto: 1 bet, 0 wins, $0
-- Total: +$400
```

**UI:** Show stacked bar chart by category.

---

## IMPLEMENTATION ROADMAP

**Week 1:**
- [ ] Design normalized schema (no redundancy)
- [ ] Create aggregation strategy (daily/weekly/monthly)
- [ ] Index critical columns for sub-300ms latency
- [ ] Document schema in data dictionary

**Week 2:**
- [ ] Build data ingestion pipelines
- [ ] Setup aggregation jobs (daily summaries)
- [ ] Performance testing (query optimization)
- [ ] Validate data accuracy

**Week 3:**
- [ ] Build drill-down query layer
- [ ] Implement attribution decomposition
- [ ] Add caching layer (if needed)
- [ ] Monitor query performance

---

## DATA SOURCES FOR NORTSTAR

**From Scalper:**
- Daily bets (10 AM email parser)
- Trade results (market close)
- Historical Kalshi trades (API)

**From John:**
- Job completions (revenue tracking)
- Job pipeline (pending revenue)

**From Operations:**
- API costs (Anthropic, OpenRouter)
- Infrastructure costs
- Other expenses

**From Dashboard:**
- P&L calculations
- Performance metrics

---

## SUCCESS CRITERIA

✅ Query latency <300ms for all dashboards  
✅ Data accuracy 99.9% (spot-check monthly)  
✅ Aggregation happens automatically (no manual recalculation)  
✅ New data sources add without schema changes  
✅ Drill-down queries work smoothly (month → day → trade)  
✅ Attribution breakdowns are accurate and fast  

---

**Start Phase 1: Schema design. Quality over speed.**
