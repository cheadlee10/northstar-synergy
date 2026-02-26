"""
Initialize dashboard database with Anthropic usage data from JSON log.
Runs on app startup to ensure fresh data on Railway's ephemeral storage.
"""

import json
import os
import aiosqlite
from pathlib import Path
from database import DB_PATH

async def init_anthropic_data():
    """Load Anthropic usage from JSON log and populate database"""
    
    # Path to JSON log (local or deployed)
    log_paths = [
        "/data/anthropic_usage.jsonl",
        "/app/data/anthropic_usage.jsonl",
        "/tmp/anthropic_usage.jsonl",
        "data/anthropic_usage.jsonl",
        os.path.expanduser("~/.openclaw/workspace/data/anthropic_usage.jsonl"),
    ]
    
    log_file = None
    for path in log_paths:
        if os.path.exists(path):
            log_file = path
            print(f"[INIT] Found Anthropic usage log: {path}")
            break
    
    if not log_file:
        print("[INIT] No Anthropic usage log found. Skipping data init.")
        return
    
    # Read JSON lines
    entries = []
    try:
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        print(f"[INIT] Loaded {len(entries)} usage entries from log")
    except Exception as e:
        print(f"[INIT] Error reading usage log: {e}")
        return
    
    if not entries:
        print("[INIT] No entries to load")
        return
    
    # Insert into database
    db = await aiosqlite.connect(DB_PATH)
    try:
        # Check if data already exists for today
        today = entries[-1]["timestamp"].split("T")[0] if entries else None
        if today:
            cur = await db.execute(
                "SELECT COUNT(*) FROM api_usage WHERE provider='anthropic' AND usage_date=?",
                (today,)
            )
            (count,) = await cur.fetchone()
            if count > 0:
                print(f"[INIT] Data already exists for {today}. Skipping insert.")
                await db.close()
                return
        
        # Insert entries
        for entry in entries:
            usage_date = entry.get("timestamp", "").split("T")[0]
            provider = "anthropic"
            model = entry.get("model", "unknown")
            tokens_in = entry.get("input_tokens", 0)
            tokens_out = entry.get("output_tokens", 0)
            cost = entry.get("total_cost", 0)
            notes = f"agent:{entry.get('agent_id', 'unknown')}"
            
            try:
                await db.execute(
                    """INSERT INTO api_usage (usage_date, provider, model, tokens_in, tokens_out, cost_usd, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (usage_date, provider, model, tokens_in, tokens_out, cost, notes)
                )
            except Exception as e:
                # Likely duplicate key; skip
                pass
        
        await db.commit()
        print(f"[INIT] Inserted {len(entries)} usage entries into database")
    
    except Exception as e:
        print(f"[INIT] Error inserting data: {e}")
    
    finally:
        await db.close()

async def ensure_tables():
    """Ensure all required tables exist"""
    db = await aiosqlite.connect(DB_PATH)
    try:
        # Create tables if missing
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usage_date TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                tokens_in INTEGER,
                tokens_out INTEGER,
                cost_usd REAL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(usage_date, provider, model, tokens_in, tokens_out)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS kalshi_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                market TEXT,
                direction TEXT,
                stake REAL,
                fill_price REAL,
                exit_price REAL,
                profit_loss REAL,
                status TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS company_revenue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                source TEXT,
                amount REAL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()
        print("[INIT] Tables ensured")
    except Exception as e:
        print(f"[INIT] Error creating tables: {e}")
    finally:
        await db.close()
