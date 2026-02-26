# Anthropic Usage Tracking Setup

**Status:** ✅ Ready to deploy  
**First Run:** 2026-02-25 12:30 PM  
**Log Location:** `~/.openclaw/workspace/data/anthropic_usage.jsonl`

---

## Overview

This system tracks **every Anthropic API call** in real-time with zero external dependencies:
- ✅ Capture `input_tokens` + `output_tokens` from response
- ✅ Calculate cost per call using live Anthropic pricing
- ✅ Log per-agent attribution (Cliff, Scalper, John)
- ✅ Per-model breakdown
- ✅ Daily/weekly summaries
- ✅ Audit trail (immutable append-only log)

**Why this works:**
Every Anthropic API response includes a `usage` field with token counts. We intercept at that point (no Admin API key needed, no infrastructure required).

---

## Components

### 1. **anthropic-usage-tracker.js** (Core Logger)
Handles all logging logic:
- Append-only JSON log file
- Pricing calculations
- Query interface (today/weekly/report)
- No external dependencies

```bash
# View today's report
node scripts/anthropic-usage-tracker.js report

# Test log entry
node scripts/anthropic-usage-tracker.js test
```

### 2. **anthropic-interceptor.js** (Request Wrapper)
Integrates with OpenClaw:
- Wraps Anthropic SDK client
- Auto-logs every `messages.create()` call
- Attaches usage metadata to response
- Per-agent tracking

---

## Integration: How to Use in OpenClaw

### Step 1: Modify each agent's initialization

Find where each agent creates the Anthropic client. Wrap it immediately:

```javascript
// Before:
const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// After:
const Anthropic = require('@anthropic-ai/sdk');
const wrapAnthropicClient = require('./scripts/anthropic-interceptor');

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
const wrappedClient = wrapAnthropicClient(client, 'cliff'); // agent name
```

### Step 2: For each agent, repeat with their agent ID

- **Cliff:** `wrapAnthropicClient(client, 'cliff')`
- **Scalper:** `wrapAnthropicClient(client, 'scalper')`
- **John:** `wrapAnthropicClient(client, 'john')`

### Step 3: That's it.

From that point on, every call logs automatically. No code changes needed in message creation logic.

---

## Pricing

Current pricing (Anthropic, Feb 2026):

| Model | Input $/M | Output $/M |
|-------|-----------|-----------|
| claude-opus-4-6 | $15 | $75 |
| claude-sonnet-4-6 | $3 | $15 |
| claude-haiku-4-5 | $0.80 | $4 |

Pricing is stored in `~/.openclaw/workspace/data/anthropic_pricing.json` and auto-updates on first run.

**To update pricing manually:**
Edit `anthropic_pricing.json` and restart any agent.

---

## Reports

### Daily Report
```bash
node scripts/anthropic-usage-tracker.js report
```

Output shows:
- Today's total cost
- Breakdown by agent (Cliff vs Scalper vs John)
- Breakdown by model (Opus vs Sonnet vs Haiku)
- Weekly trend
- Total log entries

### Real-time Log
Log entries are appended to `~/.openclaw/workspace/data/anthropic_usage.jsonl`:

```json
{
  "timestamp": "2026-02-25T12:30:45.123Z",
  "agent_id": "cliff",
  "model": "claude-opus-4-6",
  "input_tokens": 1000,
  "output_tokens": 500,
  "total_tokens": 1500,
  "input_cost": 0.015,
  "output_cost": 0.0375,
  "total_cost": 0.0525,
  "api_request_id": "msg_12345..."
}
```

---

## Cron Job: Hourly Usage Alert

Add this to OpenClaw's cron config (OPTIONAL but recommended):

```json
{
  "name": "hourly-usage-check",
  "schedule": { "kind": "cron", "expr": "0 * * * *" },
  "payload": {
    "kind": "systemEvent",
    "text": "[CRON] Run: node scripts/anthropic-usage-tracker.js report"
  },
  "sessionTarget": "main"
}
```

This will ping you with usage every hour.

---

## Verification

### Step 1: Check log file was created
```bash
ls -la ~/.openclaw/workspace/data/anthropic_usage.jsonl
```

Should show a file with entries (even if small).

### Step 2: Run report
```bash
node scripts/anthropic-usage-tracker.js report
```

Should show today's spend (even if $0 initially).

### Step 3: Make a test call
Any OpenClaw session using the wrapped client should automatically log.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No logs appearing | Check agent is using wrapped client. Verify `[INTERCEPTOR]` line appears on startup. |
| "Cannot find module" | Install: `npm install` (should already be available) |
| Zero cost showing | Pricing file may be wrong. Check `anthropic_pricing.json`. |
| Old logs aren't counted | Log file is write-only. Old entries are in `usage.jsonl` — read them all. |

---

## Implementation Timeline

**Phase 1: Core logger** ✅  
**Phase 2: Interceptor wrapper** ✅  
**Phase 3: Integration into agents** ⏳ (in progress)  
**Phase 4: Cron alerts** ⏳ (optional)  

---

## Data Integrity

### Audit Trail
Every log entry is immutable:
- Timestamp: ISO-8601 (UTC)
- Agent: immutable once written
- Tokens: exact count from Anthropic response
- Cost: calculated using current pricing

### Recovery
If logs are lost:
- Historical data gone (no backup)
- Future logs will capture from that point
- Anthropic's console can provide backup (via Cost page)

**Recommendation:** Weekly snapshot of `anthropic_usage.jsonl` to backup location.

---

## Next Steps

1. **Deploy to agents:** Modify each agent's initialization
2. **Verify:** Run a test query in each agent, check report
3. **Monitor:** Run daily reports manually or via cron
4. **Alert:** Set up cron job for hourly pings if high-spend detected

---

## Questions?

This system is designed for maximum reliability with zero external dependencies.  
All data is yours. No cloud, no APIs, no third-party integrations.

---

**Last updated:** 2026-02-25 12:30 PM  
**By:** Cliff (Token Economy Officer)
