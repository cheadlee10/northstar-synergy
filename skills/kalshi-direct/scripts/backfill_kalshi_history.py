#!/usr/bin/env python3
"""
backfill_kalshi_history.py — Fetch complete Kalshi order history from API
Populates kalshi_orders table with all fills, wins/losses, P&L
"""
import os, sqlite3, json, urllib.request, urllib.error, argparse
from datetime import datetime, timedelta
import sys

# ── Config ────────────────────────────────────────────────────────────────────
KALSHI_API_KEY = os.environ.get('KALSHI_API_KEY', '').strip()
KALSHI_BASE_URL = 'https://api.kalshi.com/trade-api/v2'
DASHBOARD_DB = r"C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db"

def http_request(method, url, headers=None):
    """Make HTTP request to Kalshi API."""
    if not headers:
        headers = {}
    headers['Authorization'] = f'Bearer {KALSHI_API_KEY}'
    headers['Content-Type'] = 'application/json'
    
    try:
        req = urllib.request.Request(url, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode('utf-8'))
            return data, r.status
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read().decode('utf-8'))
        except:
            data = {"error": str(e)}
        return data, e.code
    except Exception as ex:
        return {"error": str(ex)}, 0

def init_kalshi_orders_table(conn):
    """Create kalshi_orders table if not exists."""
    conn.execute("""
    CREATE TABLE IF NOT EXISTS kalshi_orders (
        id TEXT PRIMARY KEY,
        ticker TEXT NOT NULL,
        side TEXT,
        quantity INTEGER,
        price REAL,
        filled_at TEXT,
        status TEXT,
        pnl_cents INTEGER DEFAULT 0,
        notes TEXT
    )
    """)
    conn.commit()

def fetch_all_orders(limit_per_page=100, max_pages=None):
    """Fetch all orders from Kalshi API with pagination."""
    all_orders = []
    page = 1
    
    while True:
        if max_pages and page > max_pages:
            break
        
        print(f"[*] Fetching orders page {page}...")
        url = f'{KALSHI_BASE_URL}/orders?limit={limit_per_page}&offset={(page-1)*limit_per_page}&status=any'
        data, code = http_request('GET', url)
        
        if code != 200:
            print(f"[!] Page {page} failed ({code}): {data}")
            break
        
        orders = data.get('orders', [])
        if not orders:
            print(f"[*] No more orders (page {page})")
            break
        
        all_orders.extend(orders)
        print(f"    Fetched {len(orders)} orders (total: {len(all_orders)})")
        page += 1
    
    return all_orders

def sync_orders_to_db(orders, conn, verbose=False):
    """Store orders in kalshi_orders table."""
    synced = 0
    for order in orders:
        try:
            order_id = order.get('id')
            if not order_id:
                continue
            
            # Check if exists
            cur = conn.execute("SELECT id FROM kalshi_orders WHERE id = ?", (order_id,))
            if cur.fetchone():
                continue
            
            ticker = order.get('ticker', '')
            side = order.get('side', '')  # BUY / SELL
            quantity = order.get('quantity', 0)
            price = order.get('price', 0)
            filled_at = order.get('filled_at', '')
            status = order.get('status', 'unknown')
            pnl = int((order.get('pnl', 0) or 0) * 100)  # Convert to cents
            
            conn.execute("""
                INSERT INTO kalshi_orders 
                (id, ticker, side, quantity, price, filled_at, status, pnl_cents)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_id, ticker, side, quantity, price, filled_at, status, pnl))
            synced += 1
        except Exception as e:
            if verbose:
                print(f"[!] Error storing order {order.get('id')}: {e}")
    
    conn.commit()
    return synced

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=0, help='Fetch last N days')
    parser.add_argument('--full', action='store_true', help='Fetch all available')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    
    if not KALSHI_API_KEY:
        print("[!] ERROR: KALSHI_API_KEY not set")
        print("    Set it: [System.Environment]::SetEnvironmentVariable('KALSHI_API_KEY','key','User')")
        sys.exit(1)
    
    print("[*] Kalshi Order History Backfill")
    print(f"    Time: {datetime.now().isoformat()}")
    print()
    
    # Fetch orders
    if args.full:
        orders = fetch_all_orders(max_pages=None)
    else:
        # For now, fetch last 100 pages (can be tuned)
        orders = fetch_all_orders(max_pages=100)
    
    if not orders:
        print("[!] No orders fetched")
        sys.exit(1)
    
    print()
    
    # Sync to DB
    conn = sqlite3.connect(DASHBOARD_DB)
    init_kalshi_orders_table(conn)
    
    synced = sync_orders_to_db(orders, conn, args.verbose)
    conn.close()
    
    print()
    print(f"[OK] Synced {synced} orders to kalshi_orders table")
    print(f"     Dashboard will display live P&L at: https://chronic-slope-condo-justify.trycloudflare.com")

if __name__ == '__main__':
    main()
