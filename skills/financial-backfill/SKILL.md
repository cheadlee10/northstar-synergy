---
name: financial-backfill
description: Historical expense and revenue backfill for Northstar Synergy dashboard. Use when populating 10+ days of financial data from all sources (OpenRouter, Anthropic, Kalshi, sports picks, John's business) into the dashboard database. Aggregates costs, P&L, revenue, and expenses from scattered sources into a unified view.
---

# Financial Backfill Skill

Pulls complete financial history from all NorthStar sources and populates the dashboard database with no gaps.

## Sources + Backfill Strategy

| Source | Method | Lookback | Notes |
|--------|--------|----------|-------|
| OpenRouter | Direct API query (`/auth/key`) | Daily aggregate | Credits used; parse response.usage |
| Anthropic | Session log parsing | Parse all .jsonl files | Extract usage from message.usage; cost calculated per model |
| Kalshi | Direct read from scalper_v8.db | Full table dump | All pnl_snapshots; 5000+ rows possible |
| Sports picks | Parse pick_performance_log.jsonl | All entries | Results + P&L calculation |
| John jobs | Parse jobs.jsonl | All entries | Invoices, payments, status |
| John leads | Parse leads.jsonl | All entries | Sales pipeline tracking |

## Scripts

### `backfill_10days.py`
Master backfill script. Pulls data from all sources for the last 10 days (or all available), normalizes, deduplicates, and populates dashboard.db.

**Usage:**
```bash
python scripts/backfill_10days.py --days 10
python scripts/backfill_10days.py --days 10 --verbose
python scripts/backfill_10days.py --full  # All available data
```

**Output:** Console summary + row counts per source.

### `sync_historical_costs.py`
Backfill API costs (OpenRouter + Anthropic) for a date range.

**Usage:**
```bash
python scripts/sync_historical_costs.py --start 2026-02-14 --end 2026-02-24
```

### `sync_historical_kalshi.py`
Backfill Kalshi P&L snapshots from scalper_v8.db (deduplicates on snapshot_ts).

**Usage:**
```bash
python scripts/sync_historical_kalshi.py
```

## Execution (Recommended Order)

1. Run master backfill:
   ```bash
   python C:\Users\chead\.openclaw\workspace\skills\financial-backfill\scripts\backfill_10days.py --days 10 --verbose
   ```

2. Verify dashboard loads at `http://localhost:8765`

3. If dashboard needs restart:
   ```bash
   powershell -ExecutionPolicy Bypass -File C:\Users\chead\.openclaw\workspace\dashboard\deploy.ps1
   ```

## Key Design Notes

- **Deduplication:** Uses unique constraints on (date, provider, model) for API costs; (snapshot_ts) for Kalshi; (pick_date, game, pick) for sports picks
- **Idempotent:** Safe to run multiple times; INSERT OR IGNORE on conflicts
- **Chronological:** All data is aggregated by date for easy charting
- **Cost calculation:** Anthropic pricing hardcoded per model (claude-sonnet-4-x, claude-haiku, claude-opus)
