---
name: dashboard-populator
description: Auto-populates the Northstar Synergy P&L dashboard with live data from all sources. Use when setting up the dashboard on a new machine, diagnosing missing data, or adding a new data source.
---

# Dashboard Auto-Populate

Pulls data from all sources into `northstar.db` with zero manual entry.

## Sources + How They Work

| Source | Method | Schedule |
|--------|--------|----------|
| OpenRouter spend | `GET /api/v1/auth/key` → credits used | Every 15 min |
| Anthropic spend | Parse `~/.openclaw/agents/**/*.jsonl` for `message.usage` | Every 15 min |
| Kalshi P&L | Direct read from `workspace-scalper/scalper_v8.db` | Every 15 min |
| Sports picks | Parse `workspace-scalper/pick_performance_log.jsonl` | Every 15 min |
| John jobs | Parse `workspace-john/jobs.jsonl` | Every 15 min |
| John leads | Parse `workspace-john/leads.jsonl` | Every 15 min |

## Key Files

```
workspace/dashboard/auto_populate.py        ← master sync script
workspace/dashboard/data/northstar.db       ← SQLite database
workspace/dashboard/app.py                  ← FastAPI server (port 8765)
workspace/dashboard/static/index.html       ← Dashboard UI
workspace/dashboard/start_dashboard.ps1     ← Start server + Cloudflare tunnel
```

## Task Scheduler Tasks (zero token cost)

| Task | Schedule | What It Does |
|------|----------|--------------|
| `\OpenClaw\NorthstarAutoPopulate` | Every 15 min | Runs auto_populate.py |
| `\OpenClaw\NorthstarDashboard` | At login | Starts server + Cloudflare tunnel, texts Craig URL |
| `\OpenClaw\GranolaMonitor` | Every 10 min | Checks Granola for new meeting notes |

## Setup on New Machine

```powershell
# 1. Install deps
pip install fastapi uvicorn aiosqlite httpx

# 2. Register Task Scheduler tasks
powershell -ExecutionPolicy Bypass -File workspace\dashboard\register_autopopulate.ps1
powershell -ExecutionPolicy Bypass -File workspace\dashboard\register_granola_task.ps1
powershell -ExecutionPolicy Bypass -File workspace\dashboard\register_dashboard_task.ps1

# 3. Start dashboard
powershell -ExecutionPolicy Bypass -File workspace\dashboard\start_dashboard.ps1
```

## Adding a New Data Source

1. Add a `sync_<source>(conn)` function to `auto_populate.py`
2. Call it in `run_all()`
3. Add the table to `init_db()` if needed
4. Add an endpoint to `app.py` if dashboard needs to show it
5. Update the UI in `static/index.html`

## API Keys (from environment)

```
ANTHROPIC_API_KEY  — Anthropic (Claude) — session log parsing for cost calc
OPENROUTER_API_KEY — OpenRouter — direct API call for credits used
```

OpenRouter key: user-level env var (`[System.Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY','User')`)
Anthropic key: process env `$env:ANTHROPIC_API_KEY`

## Anthropic Cost Calculation

Parsed from `~/.openclaw/agents/**/*.jsonl`:
```json
{"message": {"role": "assistant", "provider": "anthropic", "model": "claude-sonnet-4-6",
  "usage": {"input": 12500, "output": 850, "cacheRead": 48000, "cacheWrite": 0}}}
```

Pricing (per million tokens):
- claude-sonnet-4-x: $3.00 in / $15.00 out / $0.30 cache_read / $3.75 cache_write
- claude-haiku: $0.25 in / $1.25 out / $0.03 cache_read / $0.30 cache_write
- claude-opus: $15.00 in / $75.00 out / $1.50 cache_read / $18.75 cache_write

## Troubleshooting

**Dashboard shows $0 API costs**: Run `python auto_populate.py` manually — check output.
**OpenRouter sync fails 401**: Check `OPENROUTER_API_KEY` in user env (not process env).
**Kalshi shows no data**: Confirm `workspace-scalper/scalper_v8.db` exists and is not locked by Scalper engine.
**Server not starting**: Check port 8765 not in use — `netstat -ano | findstr 8765`
**Tunnel URL changed**: Run `start_dashboard.ps1` again — it auto-texts Craig the new URL.
