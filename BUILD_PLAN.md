# NORTHSTAR P&L DASHBOARD — COMPREHENSIVE BUILD PLAN

**Philosophy:** Quality > Speed. Built once, built right. Tweaked over months, not overhauled.

**Timeline:** 4-6 weeks of methodical development (not compressed into days)

**Backbone Status:** This IS the company's foundation. Every decision data-driven.

---

## PHASE 1: MASTERY & ARCHITECTURE (Week 1-2)

### 1.1 Web Development Mastery
**Learning from John's skills**
- [ ] Request John's web dev skillset
- [ ] Master: React component architecture (reusable, testable)
- [ ] Master: CSS grid/flexbox for financial dashboards
- [ ] Master: Real-time data visualization (D3/Plotly)
- [ ] Master: State management (Redux or Context API)
- [ ] Master: Performance optimization (sub-300ms queries)
- [ ] Document: Web Dev Mastery skill file

### 1.2 Data Architecture Mastery
**From Stripe/Bloomberg research**
- [ ] Master: Event-driven streaming (Kafka concepts)
- [ ] Master: Time-series database design (PostgreSQL + TimescaleDB)
- [ ] Master: Real-time aggregation patterns
- [ ] Master: Hierarchical drill-down queries
- [ ] Master: Attribution decomposition logic
- [ ] Document: Data Architecture skill file

### 1.3 Financial Dashboard Mastery
**From TradesViz/Bloomberg/Stripe**
- [ ] Master: PnL calendar heatmap design
- [ ] Master: Real-time metric calculation
- [ ] Master: Custom metric definition engines
- [ ] Master: Stress testing + scenario analysis
- [ ] Master: Performance attribution (why did P&L change?)
- [ ] Document: Financial Dashboard Mastery skill file

### 1.4 Database Schema Design
**Methodical design (not rushed)**
- [ ] Document all data sources (Kalshi, John revenue, API costs, etc.)
- [ ] Design normalized schema
- [ ] Design aggregation tables (daily/weekly/monthly summaries)
- [ ] Design time-series tables (Scalper bets, price history)
- [ ] Document: Database Schema Mastery skill file

---

## PHASE 2: FOUNDATION (Week 2-3)

### 2.1 Database Schema Implementation
- [ ] Create `scalper_bets` table (daily bet tracking)
- [ ] Create `scalper_performance_daily` (daily summary)
- [ ] Create `company_revenue` table (John's jobs + all sources)
- [ ] Create `company_expenses` table (API costs, infrastructure, etc.)
- [ ] Create `kalshi_snapshots` (historical trade data)
- [ ] Create aggregation views (daily/weekly/monthly rollups)
- [ ] Create indexes for sub-300ms query performance

### 2.2 Data Ingestion Pipelines
**Build systematically**
- [ ] Scalper 10 AM email parser (daily bets)
- [ ] Kalshi API connector (live balance + historical trades)
- [ ] OpenRouter cost ingestion (API usage logs)
- [ ] Anthropic cost sync (from existing cron)
- [ ] John's revenue tracker (job completions)
- [ ] Document: Data Ingestion Mastery skill file

### 2.3 Real-time Aggregation Engine
**Stripe-style streaming**
- [ ] Design state machine for bet lifecycle (PLACED → PENDING → WIN/LOSS)
- [ ] Build daily summary rollup (runs at market close)
- [ ] Build weekly summary rollup
- [ ] Build monthly summary rollup
- [ ] Implement <300ms query latency
- [ ] Document: Real-time Aggregation skill file

---

## PHASE 3: CORE DASHBOARD (Week 3-4)

### 3.1 Scalper Performance Dashboard
**TradesViz-inspired**
- [ ] Build 365-day heatmap widget
- [ ] Color coding: green (win) → yellow (neutral) → red (loss)
- [ ] Intensity: magnitude of P&L
- [ ] Drill-down: Click day → see all bets
- [ ] Category filter: Show sports/kalshi/crypto separately
- [ ] Win rate % displayed
- [ ] Streak tracking (consecutive wins/losses)

### 3.2 Company P&L Dashboard
**Master view of everything**
- [ ] Total revenue (all sources, real-time)
- [ ] Total expenses (API costs, infrastructure, etc.)
- [ ] Net profit (revenue - expenses)
- [ ] Revenue breakdown (Scalper P&L, John jobs, other)
- [ ] Expense breakdown (Anthropic, OpenRouter, infrastructure)
- [ ] Waterfall chart (how we got from A to B)

### 3.3 Attribution Breakdown
**Bloomberg-inspired**
- [ ] Scalper: Profit by category (sports/kalshi/crypto)
- [ ] Scalper: Profit by time period (week/month)
- [ ] Scalper: Edge accuracy (thesis correct vs. actual result)
- [ ] Company: Revenue contribution by agent
- [ ] Company: Cost attribution by system

### 3.4 Real-time Widgets
- [ ] Today's Scalper record (3W-2L, +$XXX)
- [ ] Week's record
- [ ] Month's record
- [ ] Best performing category (live)
- [ ] API costs YTD
- [ ] Company P&L YTD

---

## PHASE 4: ADVANCED FEATURES (Week 4-5)

### 4.1 Trend Analysis
- [ ] Week-over-week performance trends
- [ ] Month-over-month trends
- [ ] Seasonal analysis (which months are strongest?)
- [ ] Category performance evolution
- [ ] Alert system (win rate dropping, spending spiking)

### 4.2 Scenario Analysis
- [ ] "What if Scalper maintains this win rate for a year?"
- [ ] "What if API costs increase 20%?"
- [ ] Stress testing: Portfolio at extreme market conditions

### 4.3 Custom Metrics Engine
- [ ] Users (Craig) can define custom metrics
- [ ] Historical backfill (recalculate metrics for past data)
- [ ] Real-time update (new data flows through custom metric)

### 4.4 Mobile Optimization
- [ ] Responsive heatmaps
- [ ] Touch-friendly drill-down
- [ ] Mobile performance (<1s load time)

---

## PHASE 5: INTEGRATION & REFINEMENT (Week 5-6)

### 5.1 Data Backfill
- [ ] Kalshi: All historical trades (6+ months)
- [ ] John: All completed jobs (revenue)
- [ ] API costs: 6+ months historical
- [ ] Validate data accuracy against sources

### 5.2 Quality Assurance
- [ ] Data validation (do totals match source systems?)
- [ ] Query performance testing (<300ms latency)
- [ ] UI/UX testing (mobile + desktop)
- [ ] Accuracy spot-checks (sample P&L calculations)

### 5.3 Optimization & Polish
- [ ] Optimize slow queries
- [ ] Improve visualizations (colors, labels, clarity)
- [ ] Add help text / tooltips
- [ ] Document data dictionary

### 5.4 Launch & Monitoring
- [ ] Deploy to production
- [ ] Monitor data freshness (daily checks)
- [ ] Monitor performance (query latency)
- [ ] Gather Craig's feedback

---

## ONGOING (After Launch)

### Weekly Tweaks (not overhauls)
- Color adjustments
- Label clarity
- New alerting thresholds
- Widget reordering

### Monthly Improvements
- New feature add (e.g., stress testing)
- Category restructuring
- Metric refinements

### Quarterly Overhauls
- Only if major business change (e.g., new revenue stream)
- NOT architectural, just new data sources

---

## SKILLS TO MASTER & DOCUMENT

Each skill gets its own SKILL.md file:

1. ✅ Scalper Performance Tracker (done)
2. Web Development Mastery (learn from John)
3. Data Architecture Mastery (from research)
4. Financial Dashboard Mastery (from research)
5. Database Schema Mastery (this build)
6. Real-time Aggregation (this build)
7. Data Visualization Mastery (D3/Plotly)
8. Time-series Analysis (trend detection)
9. Attribution Decomposition (financial analysis)
10. Custom Metrics Engine (advanced)

---

## SUCCESS CRITERIA (Not Speed)

✅ Every dollar is tracked and accounted for  
✅ Every bet Scalper places is recorded  
✅ Performance metrics update in real-time  
✅ Data is 99.9% accurate (spot-checked monthly)  
✅ Queries respond in <300ms  
✅ Dashboard looks like Stripe/Bloomberg quality  
✅ Craig can see the business at a glance  
✅ Trends are visible (week-over-week, month-over-month)  
✅ We can measure what's working (Scalper's edge, John's pricing, API efficiency)  
✅ Built once, tweaked forever — no major overhauls needed  

---

## TEAM

- **Cliff:** Architecture, database, data pipelines, mastery skills
- **Sub-agent:** Research, visualization optimization, advanced analytics
- **John:** Web dev patterns and guidance (when available)
- **Craig:** Requirements, direction, final approval

---

**Rome wasn't built in a day. NorthStar's financial backbone won't be either.**

**Starting Phase 1 now.**

---

Created: 2026-02-25  
Status: ACTIVE  
Timeline: 4-6 weeks (methodical, quality-first)
