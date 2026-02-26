"""
SYNC_ANTHROPIC_USAGE.py
Reads Anthropic usage log and syncs to NorthStar dashboard database

Runs twice daily:
- 8 AM PT (6 AM UTC)
- 6 PM PT (2 AM UTC next day)
"""

import json
import os
import sys
from datetime import datetime, date
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

import aiosqlite
from database import get_db, DB_PATH

ANTHROPIC_LOG = r"C:\Users\chead\.openclaw\workspace\data\anthropic_usage.jsonl"

async def read_anthropic_logs():
    """Read and parse Anthropic usage.jsonl"""
    if not os.path.exists(ANTHROPIC_LOG):
        print(f"[SYNC] Log file not found: {ANTHROPIC_LOG}")
        return []

    logs = []
    try:
        with open(ANTHROPIC_LOG, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    logs.append(entry)
                except json.JSONDecodeError as e:
                    print(f"[SYNC] JSON parse error: {e}")
                    continue
    except Exception as e:
        print(f"[SYNC] Error reading log: {e}")
        return []

    print(f"[SYNC] Read {len(logs)} entries from anthropic_usage.jsonl")
    return logs


async def sync_to_dashboard():
    """Sync Anthropic logs to dashboard database"""
    logs = await read_anthropic_logs()
    if not logs:
        print("[SYNC] No logs to sync")
        return {"entries_read": 0, "entries_synced": 0, "error": None}

    db = await get_db()
    synced_count = 0
    skipped_count = 0

    try:
        for entry in logs:
            # Parse entry
            timestamp = entry.get('timestamp')
            agent_id = entry.get('agent_id', 'unknown')
            model = entry.get('model', 'unknown')
            input_tokens = entry.get('input_tokens', 0)
            output_tokens = entry.get('output_tokens', 0)
            total_cost = entry.get('total_cost', 0)

            # Extract date from timestamp
            usage_date = timestamp.split('T')[0] if timestamp else str(date.today())

            # Check if already synced (avoid duplicates)
            cur = await db.execute(
                "SELECT id FROM api_usage WHERE provider=? AND usage_date=? AND model=? AND tokens_in=? AND tokens_out=?",
                ("anthropic", usage_date, model, input_tokens, output_tokens)
            )
            existing = await cur.fetchone()

            if existing:
                skipped_count += 1
                continue

            # Insert into dashboard
            await db.execute(
                """INSERT INTO api_usage (usage_date, provider, model, tokens_in, tokens_out, cost_usd, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (usage_date, "anthropic", model, input_tokens, output_tokens, total_cost, f"agent:{agent_id}")
            )
            synced_count += 1

        await db.commit()
        print(f"[SYNC] Synced {synced_count} entries, skipped {skipped_count} duplicates")
        return {
            "entries_read": len(logs),
            "entries_synced": synced_count,
            "entries_skipped": skipped_count,
            "error": None
        }

    except Exception as e:
        print(f"[SYNC] Database error: {e}")
        await db.rollback()
        return {
            "entries_read": len(logs),
            "entries_synced": synced_count,
            "error": str(e)
        }
    finally:
        await db.close()


async def get_usage_summary(days: int = 1):
    """Get usage summary for last N days"""
    db = await get_db()
    try:
        # Total spend
        cur = await db.execute(
            """SELECT 
                SUM(tokens_in + tokens_out) as total_tokens,
                SUM(cost_usd) as total_cost,
                COUNT(*) as request_count
            FROM api_usage 
            WHERE provider='anthropic' AND usage_date >= date('now', '-' || ? || ' days')""",
            (days,)
        )
        total = await cur.fetchone()

        # By model
        cur = await db.execute(
            """SELECT 
                model,
                SUM(tokens_in + tokens_out) as total_tokens,
                SUM(cost_usd) as total_cost,
                COUNT(*) as request_count
            FROM api_usage 
            WHERE provider='anthropic' AND usage_date >= date('now', '-' || ? || ' days')
            GROUP BY model
            ORDER BY total_cost DESC""",
            (days,)
        )
        by_model = await cur.fetchall()

        # By agent (from notes field)
        cur = await db.execute(
            """SELECT 
                SUBSTR(notes, 7) as agent_id,
                SUM(tokens_in + tokens_out) as total_tokens,
                SUM(cost_usd) as total_cost,
                COUNT(*) as request_count
            FROM api_usage 
            WHERE provider='anthropic' AND usage_date >= date('now', '-' || ? || ' days') AND notes LIKE 'agent:%'
            GROUP BY agent_id
            ORDER BY total_cost DESC""",
            (days,)
        )
        by_agent = await cur.fetchall()

        return {
            "period_days": days,
            "total": dict(total) if total else {},
            "by_model": [dict(r) for r in by_model],
            "by_agent": [dict(r) for r in by_agent],
        }

    finally:
        await db.close()


if __name__ == "__main__":
    import asyncio

    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"

    if cmd == "sync":
        result = asyncio.run(sync_to_dashboard())
        print(f"\nResult: {json.dumps(result, indent=2)}")

    elif cmd == "summary":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        summary = asyncio.run(get_usage_summary(days))
        print(f"\nSummary (last {days} days):")
        print(json.dumps(summary, indent=2))

    else:
        print("Usage: python sync_anthropic_usage.py [sync|summary] [days]")
