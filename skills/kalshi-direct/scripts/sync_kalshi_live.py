#!/usr/bin/env python3
"""
sync_kalshi_live.py — Fetch live Kalshi account data directly from API
Syncs balance, positions, orders, and P&L to dashboard database
"""
import os, sqlite3, json, urllib.request, urllib.error
from datetime import datetime
import sys

# ── Config ────────────────────────────────────────────────────────────────────
KALSHI_API_KEY = os.environ.get('KALSHI_API_KEY', '').strip()
KALSHI_BASE_URL = 'https://api.kalshi.com/trade-api/v2'
DASHBOARD_DB = r"C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db"

def http_request(method, url, headers=None, body=None):
    """Make HTTP request to Kalshi API."""
    if not headers:
        headers = {}
    if not KALSHI_API_KEY:
        return None, 401
    
    headers['Authorization'] = f'Bearer {KALSHI_API_KEY}'
    headers['Content-Type'] = 'application/json'
    
    try:
        req = urllib.request.Request(url, headers=headers, method=method)
        if body:
            req.data = json.dumps(body).encode('utf-8')
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

def fetch_portfolio():
    """Get account summary: balance, open positions, etc."""
    print("[*] Fetching portfolio...")
    data, code = http_request('GET', f'{KALSHI_BASE_URL}/portfolio')
    if code != 200:
        print(f"[!] Portfolio API {code}: {data}")
        return None
    print(f"    OK: balance=${data.get('balance', 0)/100:.2f}")
    return data

def fetch_pnl():
    """Get P&L breakdown by category."""
    print("[*] Fetching P&L...")
    data, code = http_request('GET', f'{KALSHI_BASE_URL}/portfolio/pnl')
    if code != 200:
        print(f"[!] P&L API {code}: {data}")
        return None
    print(f"    OK: categories={len(data.get('categories', []))}")
    return data

def fetch_orders(limit=1000):
    """Get order history."""
    print(f"[*] Fetching order history (limit={limit})...")
    data, code = http_request('GET', f'{KALSHI_BASE_URL}/orders?limit={limit}&status=any')
    if code != 200:
        print(f"[!] Orders API {code}: {data}")
        return None
    orders = data.get('orders', [])
    print(f"    OK: {len(orders)} orders")
    return orders

def fetch_positions():
    """Get currently open positions."""
    print("[*] Fetching positions...")
    data, code = http_request('GET', f'{KALSHI_BASE_URL}/portfolio/positions')
    if code != 200:
        print(f"[!] Positions API {code}: {data}")
        return None
    positions = data.get('positions', [])
    print(f"    OK: {len(positions)} open positions")
    return positions

def sync_to_dashboard(portfolio, pnl, orders, positions, verbose=False):
    """Store Kalshi data in dashboard database."""
    conn = sqlite3.connect(DASHBOARD_DB)
    now = datetime.now().isoformat()
    synced = 0
    
    try:
        # Create snapshot entry
        if portfolio:
            balance_cents = int((portfolio.get('balance') or 0) * 100)
            
            # Calculate totals from P&L if available
            total_pnl_cents = 0
            weather_pnl = 0
            crypto_pnl = 0
            econ_pnl = 0
            mm_pnl = 0
            
            if pnl:
                for cat in pnl.get('categories', []):
                    pnl_val = int((cat.get('pnl', 0) or 0) * 100)
                    cat_name = cat.get('name', '').lower()
                    if 'weather' in cat_name:
                        weather_pnl = pnl_val
                    elif 'crypto' in cat_name or 'cryptocurrency' in cat_name:
                        crypto_pnl = pnl_val
                    elif 'econ' in cat_name:
                        econ_pnl = pnl_val
                    elif 'market' in cat_name or 'mm' in cat_name:
                        mm_pnl = pnl_val
                    total_pnl_cents += pnl_val
            
            # Insert snapshot
            conn.execute("""
                INSERT OR REPLACE INTO kalshi_snapshots 
                (snapshot_ts, snap_date, balance_cents, total_pnl_cents,
                 weather_pnl_cents, crypto_pnl_cents, econ_pnl_cents, mm_pnl_cents,
                 open_positions, total_orders)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, now[:10], balance_cents, total_pnl_cents,
                  weather_pnl, crypto_pnl, econ_pnl, mm_pnl,
                  len(positions) if positions else 0,
                  len(orders) if orders else 0))
            synced += 1
            if verbose:
                print(f"    [+] Snapshot: ${balance_cents/100:.2f} balance, ${total_pnl_cents/100:.2f} P&L")
        
        conn.commit()
    except Exception as e:
        print(f"[!] Database error: {e}")
    finally:
        conn.close()
    
    return synced

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    
    if not KALSHI_API_KEY:
        print("[!] ERROR: KALSHI_API_KEY not set")
        print("    Set it: [System.Environment]::SetEnvironmentVariable('KALSHI_API_KEY','key','User')")
        sys.exit(1)
    
    print("[*] Kalshi Direct Sync")
    print(f"    Time: {datetime.now().isoformat()}")
    print()
    
    # Fetch all data
    portfolio = fetch_portfolio()
    pnl = fetch_pnl()
    orders = fetch_orders()
    positions = fetch_positions()
    
    print()
    
    # Sync to dashboard
    synced = sync_to_dashboard(portfolio, pnl, orders, positions, args.verbose)
    
    print()
    print(f"[OK] Synced {synced} snapshot(s) to {DASHBOARD_DB}")
    print("     Dashboard will refresh at: https://chronic-slope-condo-justify.trycloudflare.com")

if __name__ == '__main__':
    main()
