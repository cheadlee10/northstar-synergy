# Anthropic Usage Sync — Cron Configuration

**Sync to NorthStar Dashboard:**
- 8 AM PT (15:00 UTC)
- 6 PM PT (02:00 UTC next day)

Add these two cron jobs to OpenClaw's cron configuration:

---

## Cron Job #1: 8 AM PT Sync

```json
{
  "name": "sync-anthropic-usage-morning",
  "schedule": {
    "kind": "cron",
    "expr": "0 8 * * *",
    "tz": "America/Los_Angeles"
  },
  "payload": {
    "kind": "systemEvent",
    "text": "CRON: Syncing Anthropic usage to NorthStar dashboard (8 AM sync). Run: python dashboard/sync_anthropic_usage.py sync"
  },
  "sessionTarget": "main",
  "enabled": true
}
```

## Cron Job #2: 6 PM PT Sync

```json
{
  "name": "sync-anthropic-usage-evening",
  "schedule": {
    "kind": "cron",
    "expr": "0 18 * * *",
    "tz": "America/Los_Angeles"
  },
  "payload": {
    "kind": "systemEvent",
    "text": "CRON: Syncing Anthropic usage to NorthStar dashboard (6 PM sync). Run: python dashboard/sync_anthropic_usage.py sync"
  },
  "sessionTarget": "main",
  "enabled": true
}
```

---

## To Deploy

1. Copy both JSON objects above
2. Paste into OpenClaw's cron configuration (via API or CLI)
3. Verify jobs show as enabled in cron list

## Manual Test

Run anytime to test:
```bash
python dashboard/sync_anthropic_usage.py sync
```

Output will show how many entries were synced.

---

## Dashboard API Endpoints

Once sync is running, these endpoints will be available:

### Get Anthropic usage (last N days)
```
GET /api/usage/anthropic?days=1
```

Returns:
- Total tokens + cost
- Breakdown by model
- Breakdown by agent (Cliff, Scalper, John)
- Daily breakdown

### Get all API usage summary
```
GET /api/usage/summary?days=7
```

Returns:
- All providers (Anthropic, OpenRouter, etc.)
- Grand total for period

### Manual sync trigger
```
POST /api/usage/sync-anthropic
```

Triggers sync immediately (no schedule needed).

---

## UI Integration

Dashboard static files (`dashboard/static/`) should display:
- Real-time Anthropic spend widget
- Daily spend trend
- Per-agent breakdown (Cliff, Scalper, John)
- Per-model breakdown (Opus, Sonnet, Haiku)

Update the dashboard frontend HTML to call `/api/usage/anthropic?days=1` and render.

---

**Status:** Ready to deploy  
**Test date:** 2026-02-25  
**By:** Cliff
