# API COST TRACKING MASTERY SKILL

**Purpose:** Obsessive, real-time tracking of every API dollar spent  
**Standard:** Accuracy to the cent, visible in dashboard, alerts on anomalies  
**Responsibility:** Identify waste, optimize, never lose track of costs  

---

## CURRENT SITUATION (CRISIS MODE)

**OpenRouter:** $1,267/week (unsustainable) — $5,268/month pace  
**Anthropic:** Unknown (need real numbers, not estimates)  
**Target:** Reduce by 50%+ through optimization

---

## API COST SOURCES

### 1. Anthropic (Direct)
- **API:** https://api.anthropic.com
- **Billing:** Token-based (input + output separate)
- **Models:** Opus ($15/$75/M), Sonnet ($3/$15/M), Haiku ($0.80/$4/M)
- **Data source:** API responses include usage
- **Dashboard integration:** CRITICAL

### 2. OpenRouter (Proxy)
- **API:** https://openrouter.ai
- **Issue:** Unknown routing (which models? which costs?)
- **Problem:** $1,267/week with no visibility
- **Solution:** Inject cost tracking at proxy level

### 3. Other APIs
- **Kalshi:** Trading fees (calculate from fills)
- **FRED:** Macro data (free tier, negligible)
- **The Odds API:** Sports data ($50/month)

---

## IMPLEMENTATION: REAL ANTHROPIC COSTS IN DASHBOARD

### Step 1: Extract from API Responses
Every Anthropic API call returns:
```json
{
  "usage": {
    "input_tokens": 1000,
    "output_tokens": 500
  }
}
```

### Step 2: Calculate Cost
```python
# Anthropic pricing (per 1M tokens)
PRICING = {
  "claude-opus-4-6": {"input": 15, "output": 75},
  "claude-sonnet-4-6": {"input": 3, "output": 15},
  "claude-haiku-4-5": {"input": 0.80, "output": 4},
}

input_cost = (input_tokens / 1_000_000) * PRICING[model]["input"]
output_cost = (output_tokens / 1_000_000) * PRICING[model]["output"]
total_cost = input_cost + output_cost
```

### Step 3: Log & Aggregate
Already built: `anthropic-usage-tracker.js` + `anthropic-interceptor.js`
- Logs every call to JSON file
- Syncs to dashboard DB every 12 hours (8 AM & 6 PM)

### Step 4: Dashboard Widget
Create widget showing:
- **Today's spend:** $X.XX
- **This week:** $Y.YY
- **This month:** $Z.ZZ
- **Burn rate:** $X/day
- **Projection:** $YY/month at current pace
- **By model:** Opus vs Sonnet vs Haiku breakdown
- **By agent:** Cliff vs Scalper vs John breakdown
- **Alert:** If daily spend > threshold, flag red

---

## COST OPTIMIZATION STRATEGIES

### Strategy 1: Use Cheaper Models
- **Haiku for simple tasks** (routing, classification): Save 93% vs Opus
- **Sonnet for complex analysis** (variance, trending): Save 80% vs Opus
- **Opus ONLY for critical decisions** (trades, hiring, strategy): Full power

**Expected saving:** 40-50% immediately

### Strategy 2: Prompt Optimization
- **Caching** (Anthropic supports prompt caching): Reuse context, save tokens
- **Shorter prompts** (remove unnecessary context)
- **Structured output** (JSON not prose): Fewer tokens needed

**Expected saving:** 10-20%

### Strategy 3: Batch Processing
- **Collect 10 queries → 1 batch call** (instead of 10 calls)
- **Async processing** (don't wait for immediate response)
- **Off-peak timing** (no pricing difference, but reduces contention)

**Expected saving:** 5-10%

### Strategy 4: Local Models (Escape the API Tax)
- **Ollama with GLM 4.7 Flash** ($0 after initial download)
- **Use local for:** Research, routing, low-stakes decisions
- **Use API for:** Critical financial decisions, Scalper trades, client work

**Expected saving:** 70%+ on routine work

---

## DASHBOARD WIDGETS (Phase 4)

### Real-time Cost Meter
```
TODAY'S API SPEND
$X.XX / $5.00 budget
████████░░ 80% used

By Model:
  Opus: $X.XX (75% of spend)
  Sonnet: $X.XX (20% of spend)
  Haiku: $X.XX (5% of spend)

By Agent:
  Cliff: $X.XX (40%)
  Scalper: $X.XX (35%)
  John: $X.XX (25%)
```

### Weekly/Monthly Burn
```
WEEKLY BURN RATE
This week: $X.XX
Last week: $Y.YY
Trend: 📈 UP / 📉 DOWN

MONTHLY PROJECTION
Current pace: $Z.ZZ/month
Budget: $150/month (goal)
Status: 🔴 OVER BUDGET
```

### Cost By Time
```
HOURLY COST TREND
[Line chart showing $ per hour]
Peak: 2-4 PM (trading hours)
Low: Midnight-6 AM
```

---

## MONITORING & ALERTS

### Daily (Automated)
- [ ] Calculate daily spend
- [ ] Compare to budget ($5/day)
- [ ] Alert if over 80% of daily budget

### Weekly (Automated)
- [ ] Calculate weekly spend
- [ ] Calculate monthly projection
- [ ] Alert if projecting over budget

### Monthly (Manual)
- [ ] Full cost analysis
- [ ] Optimization opportunities identified
- [ ] Strategy adjustments made

---

## COST REDUCTION ROADMAP

**Week 1: Visibility**
- [x] Real Anthropic costs in dashboard
- [ ] OpenRouter cost breakdown (if possible)
- [ ] Identify cost spikes

**Week 2: Optimization**
- [ ] Switch to Haiku for simple tasks
- [ ] Implement prompt caching
- [ ] Batch where possible

**Week 3: Alternatives**
- [ ] Deploy Ollama locally
- [ ] Hybrid: local + API
- [ ] Measure savings

**Week 4: Target**
- [ ] Reduce from $1,267/week to <$300/week
- [ ] Maintain quality (no slowdowns, no errors)
- [ ] Sustainability achieved

---

## SUCCESS CRITERIA

✅ Every API dollar is tracked to the cent  
✅ Real costs (not estimates) in dashboard  
✅ Costs broken down by model, agent, time  
✅ Anomalies trigger alerts (over-spend warning)  
✅ Cost optimization strategies measurable  
✅ Monthly projection visible + actionable  
✅ Anthropic costs < $150/month  
✅ OpenRouter costs eliminated or <$50/month  

---

**This is not a luxury. This is survival. Track obsessively. Optimize relentlessly.**
