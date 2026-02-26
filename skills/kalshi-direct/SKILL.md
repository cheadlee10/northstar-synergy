---
name: kalshi-direct
description: Direct integration with Kalshi API for live trading account data. Use to fetch account balance, positions, order history, and P&L directly from Kalshi (bypassing local database). Required for real-time dashboard population of Kalshi trading metrics with no intermediaries.
---

# Kalshi Direct API Integration

Fetches live Kalshi account data and populates dashboard with real trading history and P&L.

## API Endpoints

| Endpoint | Purpose | Data |
|----------|---------|------|
| `GET /portfolio` | Account summary | balance, open positions, total orders |
| `GET /orders` | Order history | all fills, cancellations, pending orders |
| `GET /portfolio/pnl` | P&L breakdown | by category (weather, crypto, econ, market making) |
| `GET /portfolio/positions` | Open positions | current contracts held |

## Authentication

Kalshi uses **bearer token** authentication:
```
Authorization: Bearer <KALSHI_API_KEY>
```

API key is stored securely as environment variable: `KALSHI_API_KEY`

## Scripts

### `sync_kalshi_live.py`
Fetches live Kalshi account data and syncs to dashboard database.

**Usage:**
```bash
python scripts/sync_kalshi_live.py
python scripts/sync_kalshi_live.py --verbose
```

**Output:** Stores snapshots in `kalshi_snapshots` table with real P&L.

### `backfill_kalshi_history.py`
Fetches complete order history from Kalshi API and populates `kalshi_orders` table.

**Usage:**
```bash
python scripts/backfill_kalshi_history.py --days 30
python scripts/backfill_kalshi_history.py --full  # All available
```

## Setup

1. **Get Kalshi API key** from Kalshi website (account settings > API)
2. **Set environment variable:**
   ```powershell
   [System.Environment]::SetEnvironmentVariable('KALSHI_API_KEY','your-key-here','User')
   ```
3. **Run sync:**
   ```bash
   python scripts/sync_kalshi_live.py
   ```

## Database Schema

New table: `kalshi_orders`
```sql
CREATE TABLE kalshi_orders (
    id TEXT PRIMARY KEY,
    ticker TEXT,
    side TEXT,  -- BUY / SELL
    quantity INTEGER,
    price REAL,
    filled_at TEXT,
    status TEXT,
    pnl_cents INTEGER
);
```

## Live Position Tracking

Use `kalshi_api.py` to fetch live positions directly from Kalshi:

```python
from kalshi_api import KalshiAPI

api = KalshiAPI(api_key="your-key-here")
positions = api.get_open_positions_summary()
# Returns: [
#   {
#     "ticker": "KXHIGHNY-26FEB24-T35",
#     "quantity": 10,
#     "side": "yes",
#     "avg_price": 15.32,
#     "unrealized_pnl": 234.50,
#     "realized_pnl": 0
#   }
# ]
```

## Integration with Dashboard

Auto-populate runs every 15 min and calls `sync_kalshi_live()` to refresh Kalshi data in `kalshi_snapshots` with live P&L.

When API is unavailable, sync_kalshi_live.py uses local database as fallback source.
