---
name: agent-credential-retrieval
description: Retrieve credentials and secrets from other NorthStar agents securely. Use when you need to fetch API keys, database credentials, or other sensitive data from Scalper, John, or other team members without storing them locally. Handles inter-agent communication, validation, and secure storage.
---

# Agent Credential Retrieval

Securely retrieve credentials from other agents without direct credential storage.

## Sources

| Agent | Credential | Use Case |
|-------|-----------|----------|
| Scalper | KALSHI_API_KEY | Direct Kalshi API integration |
| Scalper | OPENROUTER_API_KEY | Optional backup API costs |
| John | Client credentials | Business integrations |

## Scripts

### `get_scalper_credentials.py`
Request Kalshi API key from Scalper agent via inter-agent messaging.

**Usage:**
```bash
python scripts/get_scalper_credentials.py --credential KALSHI_API_KEY
python scripts/get_scalper_credentials.py --credential KALSHI_API_KEY --set-env
```

**Output:** 
- Prints credential (masked for safety)
- Optionally sets Windows environment variable for immediate use

### `retrieve_and_activate.py`
One-shot: fetch Kalshi key from Scalper and activate dashboard sync.

**Usage:**
```bash
python scripts/retrieve_and_activate.py
```

## Workflow

1. **Request**: Send message to Scalper asking for KALSHI_API_KEY
2. **Verify**: Check response format and validate key structure
3. **Activate**: Set environment variable and restart dashboard sync
4. **Confirm**: Dashboard reports live Kalshi data in next sync cycle

## Security Notes

- Keys are never logged to disk or memory files
- Keys transmitted only via OpenClaw's encrypted sessions
- Keys set to Windows user environment (not process/global)
- Each retrieval request is logged (masked) to observations.md
