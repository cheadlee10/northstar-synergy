---
name: kalshi-connection-monitor
description: Monitor and troubleshoot Kalshi API connectivity, diagnose network issues, and verify V8 engine health.
---

# Kalshi Connection Monitor & Troubleshooter

Real-time diagnostics for Kalshi API connectivity and V8 engine health.

## Quick Diagnostics

### Check if Kalshi API is reachable

```bash
python scripts/test_kalshi_production.py
```

Returns: ✓ REACHABLE or ✗ UNREACHABLE with root cause

### Monitor V8 Engine

```bash
python scripts/monitor_v8_health.py
```

Returns: logs, running status, last sync time, position count

### Full Network Audit

```bash
python scripts/diagnose_connections.py
```

Checks:
- DNS resolution (api.elections.kalshi.com)
- TCP connectivity (port 443)
- TLS handshake
- HTTP endpoint responsiveness
- API authentication (with credentials)

## Key Findings

**CRITICAL:** Kalshi uses **elections.kalshi.com**, NOT kalshi.com:

| Endpoint Type | Development | Production |
|---------------|-----------|-----------|
| HTTP REST | https://demo-api.kalshi.co/trade-api/v2 | https://api.elections.kalshi.com/trade-api/v2 |
| WebSocket | wss://demo-api.kalshi.co/trade-api/ws/v2 | wss://api.elections.kalshi.com/trade-api/ws/v2 |
| Auth | Bearer token | RSA-PSS signature |

**Scalper V8 is configured for production** (KALSHI_ENV=production in .env):
- Base URL: https://api.elections.kalshi.com/trade-api/v2
- Auth: RSA-PSS signature with KALSHI_API_KEY_ID + KALSHI_PRIVATE_KEY

## Troubleshooting Flowchart

```
Is V8 engine running?
├─ NO → Start it: Run launch_v8.ps1 from workspace-scalper
└─ YES → Check logs: tail workspace-scalper/logs/scalper_v8.log
         ├─ "Connection refused" → Network/firewall issue (run diagnose_connections.py)
         ├─ "401 Unauthorized" → Bad API key (verify KALSHI_API_KEY_ID + private key)
         ├─ "SSL certificate error" → TLS handshake failed (check system certs)
         └─ "Cannot read orders" → Check if positions are live in Kalshi account
```

## Integration with Dashboard

V8 syncs positions to `scalper_v8.db`:
- `pnl_snapshots` — P&L history (5+ snapshots/min)
- `orders` — All placed orders (7,700+)
- `fills` — Executed trades (currently 0)
- `positions` — Open positions (currently empty in DB, but $733 live per Craig)

Dashboard reads from scalper_v8.db every 15 minutes.

**To sync live positions from V8:**
1. Run `python scripts/fetch_v8_positions.py` — reads positions from local DB
2. Or use `kalshi_api.py` with RSA-PSS auth — pulls live from Kalshi API

## Common Errors & Fixes

### "getaddrinfo failed [Errno 11001]"
DNS cannot resolve the domain.
- Check: `nslookup api.elections.kalshi.com`
- Fix: Verify ISP DNS is working (test with 8.8.8.8)

### "Connection refused"
Firewall blocking port 443 to Kalshi.
- Check: `ping -n 1 api.elections.kalshi.com`
- Fix: Allow outbound HTTPS in Windows Firewall

### "401 Unauthorized"
API authentication failed.
- Check: `echo $env:KALSHI_API_KEY_ID` (should be UUID)
- Fix: Verify private key file exists and is readable

### "Certificate verification failed"
System certificate store issue.
- Check: `python -c "import ssl; print(ssl.create_default_context().check_hostname)"`
- Fix: Update Windows certificate store or disable cert verification (dev only)

## Scripts

- `test_kalshi_production.py` — Single endpoint connectivity test
- `diagnose_connections.py` — Full network + API audit
- `monitor_v8_health.py` — V8 process health + position tracking
- `fetch_v8_positions.py` — Extract positions from scalper_v8.db

## See Also

- kalshi-direct — Direct API integration (Bearer token for manual testing)
- V8 Engine — Main Scalper trading process (launch_v8.ps1)
