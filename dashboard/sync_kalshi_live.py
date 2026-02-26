#!/usr/bin/env python3
"""
sync_kalshi_live.py — Direct Kalshi API integration (RSA-PSS auth)
Uses Scalper's proven auth pattern. Pulls live data every call.
"""
import os, json, sqlite3, asyncio, time, base64
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

try:
    import aiohttp
except ImportError:
    aiohttp = None

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════
KALSHI_API_KEY_ID = os.environ.get('KALSHI_API_KEY_ID', '4fa680d5-be76-4d85-9c1b-5fd2d42c9612')
KALSHI_PRIVATE_KEY_PATH = os.environ.get('KALSHI_PRIVATE_KEY_PATH', r"C:\Users\chead\.openclaw\workspace\kalshi_private_key.pem")
KALSHI_ENV = os.environ.get('KALSHI_ENV', 'production')

if KALSHI_ENV == "production":
    KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"
else:
    KALSHI_BASE = "https://demo-api.kalshi.co/trade-api/v2"

DASHBOARD_DB = r"C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db"

# ══════════════════════════════════════════════════════════════════════════════
# RSA-PSS AUTH (from Scalper's KalshiAuth class)
# ══════════════════════════════════════════════════════════════════════════════
def get_rsa_signature_headers(method: str, path: str) -> dict:
    """Generate RSA-PSS signed headers matching Scalper's kalshi_api.py pattern"""
    try:
        # Load private key from file
        if not os.path.exists(KALSHI_PRIVATE_KEY_PATH):
            raise FileNotFoundError(f"Private key not found: {KALSHI_PRIVATE_KEY_PATH}")
        
        with open(KALSHI_PRIVATE_KEY_PATH, 'rb') as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        
        # Build message: ts + METHOD + /trade-api/v2{path}
        ts = str(int(time.time() * 1000))
        signature_path = f"/trade-api/v2{path}"  # CRITICAL: this is the path to sign
        message = f"{ts}{method.upper()}{signature_path}"
        
        # Sign with RSA-PSS (SHA256)
        sig = private_key.sign(
            message.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        
        return {
            "KALSHI-ACCESS-KEY": KALSHI_API_KEY_ID,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode("utf-8"),
            "KALSHI-ACCESS-TIMESTAMP": ts,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Cache-Control": "no-cache",
        }
    except Exception as e:
        raise RuntimeError(f"[Kalshi Auth] Failed to generate signature: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# ASYNC HTTP CLIENT (using aiohttp if available, fallback to sync)
# ══════════════════════════════════════════════════════════════════════════════
async def http_get_async(url: str, method: str = "GET") -> tuple:
    """Make async HTTP GET request with RSA-PSS auth"""
    if not aiohttp:
        raise RuntimeError("aiohttp not installed; cannot make async requests")
    
    path = url.replace(KALSHI_BASE, "")
    headers = get_rsa_signature_headers(method, path)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                return data, resp.status
        except Exception as e:
            return {"error": str(e)}, 0

def sync_kalshi_live(verbose=False) -> dict:
    """Fetch live Kalshi data and update dashboard DB"""
    if verbose:
        print("[Kalshi API] Starting sync...")
    
    try:
        # Use asyncio to run async code from sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Fetch portfolio (balance, positions, orders)
        portfolio, status = loop.run_until_complete(http_get_async(f"{KALSHI_BASE}/portfolio", "GET"))
        
        if status != 200:
            if verbose:
                print(f"[Kalshi API] Portfolio fetch failed: {status}")
            return {"status": "error", "reason": f"Portfolio fetch failed: {status}", "data": portfolio}
        
        # Extract data
        balance_cents = int(portfolio.get("balance_cents", 0))
        positions = portfolio.get("market_positions", [])
        open_positions = len([p for p in positions if p.get("quantity", 0) != 0])
        
        # Count wins/losses from current positions
        win_count = 0
        loss_count = 0
        total_pnl_cents = 0
        for pos in positions:
            pnl = int(pos.get("pnl_cents", 0))
            total_pnl_cents += pnl
            if pnl > 0:
                win_count += 1
            elif pnl < 0:
                loss_count += 1
        
        if verbose:
            print(f"  Balance: ${balance_cents/100:.2f}")
            print(f"  Open positions: {open_positions}")
            print(f"  Total P&L: ${total_pnl_cents/100:.2f}")
            print(f"  Wins: {win_count}, Losses: {loss_count}")
        
        # Insert snapshot into dashboard DB
        conn = sqlite3.connect(DASHBOARD_DB)
        c = conn.cursor()
        
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        snap_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        try:
            c.execute("""
                INSERT INTO kalshi_snapshots (
                    snapshot_ts, snap_date, balance_cents, total_pnl_cents,
                    open_positions, total_fills, win_count, loss_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ts, snap_date, balance_cents, total_pnl_cents,
                  open_positions, 0, win_count, loss_count))
            conn.commit()
            
            if verbose:
                print(f"[Kalshi API] Snapshot saved: {ts}")
            
            return {
                "status": "ok",
                "timestamp": ts,
                "balance_usd": round(balance_cents / 100, 2),
                "pnl_usd": round(total_pnl_cents / 100, 2),
                "positions": open_positions,
                "wins": win_count,
                "losses": loss_count
            }
        except Exception as e:
            return {"status": "error", "reason": f"DB insert failed: {str(e)}"}
        finally:
            conn.close()
            loop.close()
    
    except Exception as e:
        return {"status": "error", "reason": str(e)}

if __name__ == "__main__":
    import sys
    verbose = "--verbose" in sys.argv
    result = sync_kalshi_live(verbose=verbose)
    print(json.dumps(result, indent=2))
