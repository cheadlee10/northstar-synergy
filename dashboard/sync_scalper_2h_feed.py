"""
Ingest Scalper 2-hour feed artifacts (JSON + text summary) into Northstar dashboard DB.

Sources (default):
- JSON snapshot:      C:/Users/chead/.openclaw/workspace-scalper/dashboard/dashboard_data.json
- JSON history (jsonl): C:/Users/chead/.openclaw/workspace-scalper/dashboard/feed_history.jsonl
- Summary text:       C:/Users/chead/.openclaw/workspace-scalper/dashboard/last_cliff_feed.txt

Features:
- schema bootstrap (feed snapshots, holdings, summary, reconciliation alerts)
- idempotent upsert on feed_ts_utc
- reconciliation against kalshi_snapshots (nearest timestamp within a time window)
- discrepancy alert generation
- validation queries for quick audit
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

DASHBOARD_DB = r"C:/Users/chead/.openclaw/workspace/dashboard/data/northstar.db"
FEED_JSON = r"C:/Users/chead/.openclaw/workspace-scalper/dashboard/dashboard_data.json"
FEED_HISTORY_JSONL = r"C:/Users/chead/.openclaw/workspace-scalper/dashboard/feed_history.jsonl"
FEED_SUMMARY = r"C:/Users/chead/.openclaw/workspace-scalper/dashboard/last_cliff_feed.txt"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS scalper_feed_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_ts_utc TEXT NOT NULL,
    feed_ts_pt TEXT,
    total_value_usd REAL,
    cash_usd REAL,
    positions_usd REAL,
    open_positions INTEGER,
    pending_settlements INTEGER,
    realized_pnl_d REAL,
    unrealized_pnl_d REAL,
    recent_gain_usd REAL,
    recent_gain_pct REAL,
    payload_json TEXT NOT NULL,
    source_file TEXT,
    ingested_at TEXT DEFAULT (datetime('now')),
    UNIQUE(feed_ts_utc)
);

CREATE TABLE IF NOT EXISTS scalper_feed_holdings (
    snapshot_id INTEGER NOT NULL,
    rank_no INTEGER NOT NULL,
    ticker TEXT,
    side TEXT,
    contract_count REAL,
    value_usd REAL,
    unrealized_pnl REAL,
    PRIMARY KEY (snapshot_id, rank_no),
    FOREIGN KEY (snapshot_id) REFERENCES scalper_feed_snapshots(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scalper_feed_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_ts_utc TEXT,
    summary_text TEXT NOT NULL,
    parsed_total_value_usd REAL,
    parsed_cash_usd REAL,
    parsed_positions_usd REAL,
    parsed_open_positions INTEGER,
    parsed_pending_settlements INTEGER,
    parsed_realized_pnl_d REAL,
    parsed_unrealized_pnl_d REAL,
    parsed_recent_gain_usd REAL,
    parsed_recent_gain_pct REAL,
    source_file TEXT,
    ingested_at TEXT DEFAULT (datetime('now')),
    UNIQUE(feed_ts_utc, summary_text)
);

CREATE TABLE IF NOT EXISTS scalper_feed_reconciliation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_snapshot_id INTEGER NOT NULL,
    kalshi_snapshot_id INTEGER,
    kalshi_snapshot_ts TEXT,
    seconds_apart INTEGER,
    delta_cash_usd REAL,
    delta_open_positions INTEGER,
    delta_realized_pnl_d REAL,
    delta_total_value_vs_balance_usd REAL,
    status TEXT NOT NULL,
    alert_message TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(feed_snapshot_id),
    FOREIGN KEY (feed_snapshot_id) REFERENCES scalper_feed_snapshots(id) ON DELETE CASCADE,
    FOREIGN KEY (kalshi_snapshot_id) REFERENCES kalshi_snapshots(id)
);

CREATE INDEX IF NOT EXISTS idx_scalper_feed_snapshots_ts ON scalper_feed_snapshots(feed_ts_utc);
CREATE INDEX IF NOT EXISTS idx_scalper_feed_recon_status ON scalper_feed_reconciliation(status);
"""

VALIDATION_QUERIES = {
    "feed_counts": """
        SELECT date(feed_ts_utc) AS d, COUNT(*) AS snapshots, MIN(feed_ts_utc) AS first_ts, MAX(feed_ts_utc) AS last_ts
        FROM scalper_feed_snapshots
        GROUP BY date(feed_ts_utc)
        ORDER BY d DESC
        LIMIT 14;
    """,
    "latest_reconciliation": """
        SELECT s.feed_ts_utc, r.status, r.seconds_apart, r.delta_cash_usd, r.delta_open_positions,
               r.delta_realized_pnl_d, r.delta_total_value_vs_balance_usd, r.alert_message
        FROM scalper_feed_reconciliation r
        JOIN scalper_feed_snapshots s ON s.id = r.feed_snapshot_id
        ORDER BY s.feed_ts_utc DESC
        LIMIT 25;
    """,
    "active_discrepancies": """
        SELECT s.feed_ts_utc, r.status, r.alert_message
        FROM scalper_feed_reconciliation r
        JOIN scalper_feed_snapshots s ON s.id = r.feed_snapshot_id
        WHERE r.status IN ('WARN', 'CRITICAL', 'NO_MATCH')
        ORDER BY s.feed_ts_utc DESC
        LIMIT 50;
    """,
    "summary_json_mismatch": """
        SELECT s.feed_ts_utc,
               ROUND(s.total_value_usd - sm.parsed_total_value_usd, 2) AS total_value_diff,
               ROUND(s.cash_usd - sm.parsed_cash_usd, 2) AS cash_diff,
               ROUND(s.positions_usd - sm.parsed_positions_usd, 2) AS positions_diff
        FROM scalper_feed_snapshots s
        JOIN scalper_feed_summaries sm ON sm.feed_ts_utc = s.feed_ts_utc
        WHERE ABS(COALESCE(s.total_value_usd,0) - COALESCE(sm.parsed_total_value_usd,0)) > 0.01
           OR ABS(COALESCE(s.cash_usd,0) - COALESCE(sm.parsed_cash_usd,0)) > 0.01
           OR ABS(COALESCE(s.positions_usd,0) - COALESCE(sm.parsed_positions_usd,0)) > 0.01
        ORDER BY s.feed_ts_utc DESC;
    """,
}


@dataclass
class Thresholds:
    max_seconds_apart: int = 600
    warn_cash_delta: float = 5.0
    critical_cash_delta: float = 25.0
    warn_position_delta: int = 1
    critical_position_delta: int = 3
    warn_realized_delta: float = 10.0
    critical_realized_delta: float = 50.0


def _to_utc_iso(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = text.strip()
    fmts = [
        "%Y-%m-%d %H:%M:%S UTC",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    for f in fmts:
        try:
            dt = datetime.strptime(text, f)
            if f.endswith("UTC") or f.endswith("Z"):
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return None


def parse_summary_text(summary: str) -> Dict[str, Optional[float]]:
    def grab(pattern: str, cast=float):
        m = re.search(pattern, summary, flags=re.IGNORECASE | re.MULTILINE)
        if not m:
            return None
        raw = m.group(1).replace(",", "").strip()
        try:
            return cast(raw)
        except Exception:
            return None

    ts = None
    m_ts = re.search(r"KALSHI FEED UPDATE\s*[-—]\s*(.+)$", summary, flags=re.IGNORECASE | re.MULTILINE)
    if m_ts:
        ts = m_ts.group(1).strip().replace(" PT", "")

    return {
        "feed_ts_utc": _to_utc_iso((datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.now().astimezone().tzinfo).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")) if ts else None),
        "parsed_total_value_usd": grab(r"Total Value:\s*\$([\-0-9.,]+)"),
        "parsed_cash_usd": grab(r"Cash:\s*\$([\-0-9.,]+)"),
        "parsed_positions_usd": grab(r"Positions:\s*\$([\-0-9.,]+)"),
        "parsed_open_positions": grab(r"Open:\s*([0-9]+)\s*positions", int),
        "parsed_pending_settlements": grab(r"Pending:\s*([0-9]+)", int),
        "parsed_realized_pnl_d": grab(r"Realized:\s*\$([\-0-9.,]+)"),
        "parsed_unrealized_pnl_d": grab(r"Unrealized:\s*\$([\-0-9.,]+)"),
        "parsed_recent_gain_usd": grab(r"Recent Gain:\s*\$([\-0-9.,]+)"),
        "parsed_recent_gain_pct": grab(r"Recent Gain:[^\(]*\(([\-0-9.,]+)%\)"),
    }


def load_json_records(json_path: str, jsonl_path: str) -> List[Tuple[dict, str]]:
    recs: List[Tuple[dict, str]] = []
    if os.path.exists(jsonl_path):
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    recs.append((json.loads(line), jsonl_path))
                except json.JSONDecodeError:
                    continue
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                obj = json.load(f)
                if isinstance(obj, list):
                    recs.extend((x, json_path) for x in obj if isinstance(x, dict))
                elif isinstance(obj, dict):
                    recs.append((obj, json_path))
        except Exception:
            pass
    seen = set()
    out: List[Tuple[dict, str]] = []
    for rec, src in recs:
        ts = _to_utc_iso(rec.get("timestamp_utc"))
        if not ts or ts in seen:
            continue
        seen.add(ts)
        out.append((rec, src))
    return sorted(out, key=lambda t: _to_utc_iso(t[0].get("timestamp_utc")) or "")


def upsert_feed_snapshot(conn: sqlite3.Connection, rec: dict, src: str) -> Optional[int]:
    ts_utc = _to_utc_iso(rec.get("timestamp_utc"))
    if not ts_utc:
        return None
    ts_pt = rec.get("timestamp_pt")

    conn.execute(
        """
        INSERT INTO scalper_feed_snapshots
          (feed_ts_utc, feed_ts_pt, total_value_usd, cash_usd, positions_usd, open_positions,
           pending_settlements, realized_pnl_d, unrealized_pnl_d, recent_gain_usd, recent_gain_pct,
           payload_json, source_file)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(feed_ts_utc) DO UPDATE SET
           feed_ts_pt=excluded.feed_ts_pt,
           total_value_usd=excluded.total_value_usd,
           cash_usd=excluded.cash_usd,
           positions_usd=excluded.positions_usd,
           open_positions=excluded.open_positions,
           pending_settlements=excluded.pending_settlements,
           realized_pnl_d=excluded.realized_pnl_d,
           unrealized_pnl_d=excluded.unrealized_pnl_d,
           recent_gain_usd=excluded.recent_gain_usd,
           recent_gain_pct=excluded.recent_gain_pct,
           payload_json=excluded.payload_json,
           source_file=excluded.source_file,
           ingested_at=datetime('now')
        """,
        (
            ts_utc,
            ts_pt,
            rec.get("total_value_usd"),
            rec.get("cash_usd"),
            rec.get("positions_usd"),
            rec.get("open_positions"),
            rec.get("pending_settlements"),
            rec.get("realized_pnl_d"),
            rec.get("unrealized_pnl_d"),
            rec.get("recent_gain_usd"),
            rec.get("recent_gain_pct"),
            json.dumps(rec, ensure_ascii=False),
            src,
        ),
    )
    row = conn.execute("SELECT id FROM scalper_feed_snapshots WHERE feed_ts_utc=?", (ts_utc,)).fetchone()
    if not row:
        return None
    snapshot_id = int(row[0])

    conn.execute("DELETE FROM scalper_feed_holdings WHERE snapshot_id=?", (snapshot_id,))
    holdings = rec.get("top_holdings") or []
    for i, h in enumerate(holdings, start=1):
        conn.execute(
            """
            INSERT INTO scalper_feed_holdings
              (snapshot_id, rank_no, ticker, side, contract_count, value_usd, unrealized_pnl)
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                snapshot_id,
                i,
                h.get("ticker"),
                h.get("side"),
                h.get("count"),
                h.get("value_usd"),
                h.get("unrealized_pnl"),
            ),
        )
    return snapshot_id


def ingest_summary(conn: sqlite3.Connection, summary_path: str) -> int:
    if not os.path.exists(summary_path):
        return 0
    text = open(summary_path, "r", encoding="utf-8", errors="ignore").read().strip()
    if not text:
        return 0
    p = parse_summary_text(text)
    conn.execute(
        """
        INSERT OR IGNORE INTO scalper_feed_summaries
          (feed_ts_utc, summary_text, parsed_total_value_usd, parsed_cash_usd, parsed_positions_usd,
           parsed_open_positions, parsed_pending_settlements, parsed_realized_pnl_d,
           parsed_unrealized_pnl_d, parsed_recent_gain_usd, parsed_recent_gain_pct, source_file)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            p.get("feed_ts_utc"),
            text,
            p.get("parsed_total_value_usd"),
            p.get("parsed_cash_usd"),
            p.get("parsed_positions_usd"),
            p.get("parsed_open_positions"),
            p.get("parsed_pending_settlements"),
            p.get("parsed_realized_pnl_d"),
            p.get("parsed_unrealized_pnl_d"),
            p.get("parsed_recent_gain_usd"),
            p.get("parsed_recent_gain_pct"),
            summary_path,
        ),
    )
    return conn.execute("SELECT changes()").fetchone()[0]


def reconcile_snapshot(conn: sqlite3.Connection, snapshot_id: int, thresholds: Thresholds):
    feed = conn.execute(
        """
        SELECT id, feed_ts_utc, cash_usd, open_positions, realized_pnl_d, total_value_usd
        FROM scalper_feed_snapshots
        WHERE id=?
        """,
        (snapshot_id,),
    ).fetchone()
    if not feed:
        return

    nearest = conn.execute(
        """
        SELECT id, snapshot_ts, balance_cents, open_positions, daily_pnl_cents,
               ABS(strftime('%s', snapshot_ts) - strftime('%s', ?)) AS sec_apart
        FROM kalshi_snapshots
        ORDER BY sec_apart ASC
        LIMIT 1
        """,
        (feed[1],),
    ).fetchone()

    if not nearest or nearest[5] is None or int(nearest[5]) > thresholds.max_seconds_apart:
        conn.execute(
            """
            INSERT INTO scalper_feed_reconciliation
              (feed_snapshot_id, status, alert_message)
            VALUES (?, 'NO_MATCH', ?)
            ON CONFLICT(feed_snapshot_id) DO UPDATE SET
              kalshi_snapshot_id=NULL, kalshi_snapshot_ts=NULL, seconds_apart=NULL,
              delta_cash_usd=NULL, delta_open_positions=NULL, delta_realized_pnl_d=NULL,
              delta_total_value_vs_balance_usd=NULL,
              status='NO_MATCH', alert_message=excluded.alert_message, created_at=datetime('now')
            """,
            (snapshot_id, f"No kalshi_snapshots row within {thresholds.max_seconds_apart}s"),
        )
        return

    kalshi_id, kalshi_ts, balance_cents, open_pos, daily_pnl_cents, sec_apart = nearest
    delta_cash = round((feed[2] or 0) - ((balance_cents or 0) / 100.0), 2)
    delta_positions = int((feed[3] or 0) - (open_pos or 0))
    delta_realized = round((feed[4] or 0) - ((daily_pnl_cents or 0) / 100.0), 2)
    delta_total_vs_balance = round((feed[5] or 0) - ((balance_cents or 0) / 100.0), 2)

    status = "OK"
    messages: List[str] = []

    if abs(delta_cash) >= thresholds.critical_cash_delta:
        status = "CRITICAL"
        messages.append(f"cash delta ${delta_cash}")
    elif abs(delta_cash) >= thresholds.warn_cash_delta and status == "OK":
        status = "WARN"
        messages.append(f"cash delta ${delta_cash}")

    if abs(delta_positions) >= thresholds.critical_position_delta:
        status = "CRITICAL"
        messages.append(f"open positions delta {delta_positions}")
    elif abs(delta_positions) >= thresholds.warn_position_delta and status == "OK":
        status = "WARN"
        messages.append(f"open positions delta {delta_positions}")

    if abs(delta_realized) >= thresholds.critical_realized_delta:
        status = "CRITICAL"
        messages.append(f"realized P&L delta ${delta_realized}")
    elif abs(delta_realized) >= thresholds.warn_realized_delta and status == "OK":
        status = "WARN"
        messages.append(f"realized P&L delta ${delta_realized}")

    alert = "; ".join(messages) if messages else None

    conn.execute(
        """
        INSERT INTO scalper_feed_reconciliation
          (feed_snapshot_id, kalshi_snapshot_id, kalshi_snapshot_ts, seconds_apart,
           delta_cash_usd, delta_open_positions, delta_realized_pnl_d, delta_total_value_vs_balance_usd,
           status, alert_message)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(feed_snapshot_id) DO UPDATE SET
           kalshi_snapshot_id=excluded.kalshi_snapshot_id,
           kalshi_snapshot_ts=excluded.kalshi_snapshot_ts,
           seconds_apart=excluded.seconds_apart,
           delta_cash_usd=excluded.delta_cash_usd,
           delta_open_positions=excluded.delta_open_positions,
           delta_realized_pnl_d=excluded.delta_realized_pnl_d,
           delta_total_value_vs_balance_usd=excluded.delta_total_value_vs_balance_usd,
           status=excluded.status,
           alert_message=excluded.alert_message,
           created_at=datetime('now')
        """,
        (
            snapshot_id,
            kalshi_id,
            kalshi_ts,
            int(sec_apart),
            delta_cash,
            delta_positions,
            delta_realized,
            delta_total_vs_balance,
            status,
            alert,
        ),
    )


def run_ingestion(db_path: str, json_path: str, jsonl_path: str, summary_path: str, thresholds: Thresholds) -> Dict[str, int]:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_SQL)

    recs = load_json_records(json_path, jsonl_path)
    upserted = 0
    reconciled = 0
    for rec, src in recs:
        snapshot_id = upsert_feed_snapshot(conn, rec, src)
        if snapshot_id:
            upserted += 1
            reconcile_snapshot(conn, snapshot_id, thresholds)
            reconciled += 1

    summaries = ingest_summary(conn, summary_path)
    conn.commit()

    return {
        "records_seen": len(recs),
        "snapshots_upserted": upserted,
        "reconciled": reconciled,
        "summary_rows_inserted": summaries,
    }


def run_validation(db_path: str):
    conn = sqlite3.connect(db_path)
    print("\n== Validation Queries ==")
    for name, sql in VALIDATION_QUERIES.items():
        print(f"\n-- {name} --")
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        print(" | ".join(cols))
        for row in rows:
            print(" | ".join(str(x) if x is not None else "NULL" for x in row))
        if not rows:
            print("(no rows)")


def parse_args():
    p = argparse.ArgumentParser(description="Ingest Scalper 2-hour feed into Northstar DB")
    p.add_argument("--db", default=DASHBOARD_DB)
    p.add_argument("--json", default=FEED_JSON)
    p.add_argument("--jsonl", default=FEED_HISTORY_JSONL)
    p.add_argument("--summary", default=FEED_SUMMARY)
    p.add_argument("--max-seconds-apart", type=int, default=600)
    p.add_argument("--warn-cash-delta", type=float, default=5.0)
    p.add_argument("--critical-cash-delta", type=float, default=25.0)
    p.add_argument("--warn-position-delta", type=int, default=1)
    p.add_argument("--critical-position-delta", type=int, default=3)
    p.add_argument("--warn-realized-delta", type=float, default=10.0)
    p.add_argument("--critical-realized-delta", type=float, default=50.0)
    p.add_argument("--validate", action="store_true")
    return p.parse_args()


def main():
    a = parse_args()
    thresholds = Thresholds(
        max_seconds_apart=a.max_seconds_apart,
        warn_cash_delta=a.warn_cash_delta,
        critical_cash_delta=a.critical_cash_delta,
        warn_position_delta=a.warn_position_delta,
        critical_position_delta=a.critical_position_delta,
        warn_realized_delta=a.warn_realized_delta,
        critical_realized_delta=a.critical_realized_delta,
    )
    stats = run_ingestion(a.db, a.json, a.jsonl, a.summary, thresholds)
    print(json.dumps(stats, indent=2))
    if a.validate:
        run_validation(a.db)


if __name__ == "__main__":
    main()
