# Northstar Telemetry Bridge — OpenAPI Draft

Overview: Production-grade data bridge for telemetry/trade events from Scalper into Cliff's dashboard. Dual-output to local CSV and to dashboard API endpoints.

1) Telemetry/Trade Bridge
- Python data bridge writing to JSON API at http://localhost:8765/api/bets/sync-scalper (idempotent POST, retry/backoff, logging)
- Endpoints: POST /api/bets/sync-scalper
- Model: TelemetryEvent { id, timestamp, source, eventType, payload }

2) Local P&L Writer
- CSV: timestamp,ticker,direction,qty,price,pnl,status
- Output path: C:\Users\chead\.openclaw\dashboard\pnl.log.csv (append)

3) Dual Output
- POST /api/bets/sync-scalper with TelemetryEvent payloads
- POST /api/bets with Bet payloads

4) OpenAPI Spec (draft)
- Paths: /api/bets, /api/bets/sync-scalper
- Components: TelemetryEvent, BetPayload, PnLSnapshot
- Security: Bearer token header OPENCLAW_API_TOKEN
- Rate limits: 100 req/min

5) Readme & Deployment Plan
- README with quick start, containerization (Docker), cron/logs, and health checks

6) Sample Payloads
- TelemetryEvent sample
- BetPayload sample
- PnLSnapshot sample

7) Deliverables
- All in /workspace/bridge and /workspace/skills/dashboard-history-bridge
- unit tests, sample datasets, and a Git-friendly structure
