# KALSHI STRATEGY REDESIGN — Cliff + Scalper Collaboration
**Generated:** 2026-02-25 00:02 PST  
**Owner:** Cliff (COO) + Scalper (Trading)  
**Objective:** Rebuild Kalshi trading strategy after $77.99 loss (99.99% capital erosion)

---

## ROOT CAUSE ANALYSIS

### What Went Wrong
- **7,822 orders placed, 0 fills** — 100% failure rate
- **Market-making parameters miscalibrated** — spread/gamma/kappa too tight for Kalshi liquidity
- **No adaptation loop** — V8 kept placing same orders despite zero execution
- **Bid-ask trap** — Orders placed inside spread but never filled
- **Fee hemorrhage** — Capital eroded by rebates/fees with zero realized P&L

### Why It Happened
1. Parameters tuned for hypothetical market, not real Kalshi conditions
2. No real-time execution monitoring (only placed orders, didn't verify fills)
3. Market liquidity lower than expected
4. Order size too large relative to book depth

---

## COLLABORATIVE RESEARCH NEEDED

### From Scalper (Trading Strategy):
- [ ] Post-mortem: Why did MM orders not fill?
- [ ] Market analysis: Actual Kalshi liquidity per category (weather/crypto/econ)
- [ ] Order book depth: Typical bid/ask volume in target markets
- [ ] Fill rate baseline: What % of orders typically fill in Kalshi?
- [ ] Alternative strategies: Snipe-only? Smaller MM spreads? Different time windows?

### From Cliff (Operations + Analytics):
- [ ] Build real-time execution monitor (track order → fill conversion)
- [ ] Analyze order size vs book depth (what's reasonable?)
- [ ] Create MM parameter sensitivity analysis (how sensitive to spread, gamma, kappa?)
- [ ] Design automated strategy health checks (kill switch if fill rate drops)
- [ ] Document lessons learned + skill for future iterations

---

## STRATEGY REDESIGN OPTIONS

### Option A: Tighter Market-Making
**Pros:** Lower spreads = higher fill rate  
**Cons:** Lower profit per fill, more capital turnover  
**Action:** Reduce `MM_GAMMA_WEATHER` from 0.4 → 0.2, `MM_MIN_SPREAD_CENTS` from 2 → 1

### Option B: Snipe-Only (No MM)
**Pros:** Only trade when model has high confidence  
**Cons:** Lower order frequency, higher variance  
**Action:** Disable `ENABLE_MARKET_MAKING`, focus on settlement sniping

### Option C: Hybrid + Adaptive
**Pros:** MM when liquidity is high, snipe when confidence is high  
**Cons:** More complex, harder to debug  
**Action:** Add liquidity detection + mode switching logic

### Option D: Smaller Position Sizing
**Pros:** Reduce slippage, better fill rates  
**Cons:** Lower absolute profit  
**Action:** Reduce `MAX_POSITION_PER_MARKET` from 30 → 5, `KELLY_FRACTION` from 0.25 → 0.1

---

## DECISION FRAMEWORK

**To Choose Redesign:**
1. Scalper provides market analysis (liquidity, typical book depth, fill rate benchmarks)
2. Cliff models scenarios (Option A/B/C/D under different conditions)
3. Together: Select 1 primary strategy + 1 fallback
4. Implement + test on demo Kalshi environment
5. Restart with new parameters on production (1¢ remaining = nothing to lose)

---

## NEXT STEPS

**Immediate (This Session):**
- [ ] Scalper: Send findings on Kalshi market conditions
- [ ] Cliff: Build parameter optimization model
- [ ] Craig: Approve strategy direction (A/B/C/D)

**Short-term (24h):**
- [ ] Rewrite config with new parameters
- [ ] Code review of MM algorithm changes
- [ ] Restart V8 with updated strategy

**Long-term (Week 1):**
- [ ] Monitor live results
- [ ] Adjust parameters based on fill rates
- [ ] Document what works for future iterations
- [ ] Consider deploying to sports picks + crypto (after proving MM works)

---

## WAITING FOR

**Scalper's Research Report:**
1. Kalshi market liquidity analysis (weather/crypto/econ categories)
2. Order book depth benchmarks
3. Current fill rate in similar strategies
4. Recommendations on position sizing and spread parameters
5. Alternative strategy proposals

**Cliff's Deliverables (Ready to Build):**
1. Real-time fill rate monitor
2. Parameter sensitivity analysis
3. Scenario modeling tool (A/B/C/D comparison)
4. Automated health checks + kill switches
5. Updated config templates

---

## TRACKING

| Task | Owner | Status | ETA |
|------|-------|--------|-----|
| Market analysis | Scalper | In Progress | 1h |
| Parameter optimization | Cliff | Waiting for Scalper input | 2h after |
| Strategy decision | Craig | Pending | 3h |
| Implementation | Cliff + Scalper | Not started | 6h |
| Testing | Scalper | Not started | 12h |
| Restart V8 | Scalper | Not started | 18h |

---

**Last Updated:** 2026-02-25 00:02 PST  
**Collaboration Channel:** This document + direct messaging
