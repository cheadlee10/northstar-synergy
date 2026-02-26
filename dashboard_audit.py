#!/usr/bin/env python3
"""Dashboard audit — identify missing data sources for $1K hole"""
import sqlite3, json
from pathlib import Path
from datetime import datetime, date

DB = r"C:\Users\chead\.openclaw\workspace\dashboard\data\northstar.db"

def audit():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("=" * 80)
    print("NORTHSTAR SYNERGY — FINANCIAL DATA AUDIT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # API USAGE
    print("\n[1] API USAGE COSTS")
    c.execute("SELECT provider, SUM(cost_usd) total, COUNT(*) records FROM api_usage GROUP BY provider")
    for row in c.fetchall():
        print(f"    {row['provider']}: ${row['total']:.2f} ({row['records']} records)")
    c.execute("SELECT SUM(cost_usd) FROM api_usage")
    api_total = c.fetchone()[0] or 0
    print(f"    TOTAL API COSTS: ${api_total:.2f}")
    
    # KALSHI
    print("\n[2] KALSHI P&L (Latest Snapshot)")
    c.execute("SELECT * FROM kalshi_snapshots ORDER BY snapshot_ts DESC LIMIT 1")
    ks = c.fetchone()
    if ks:
        bal = (ks['balance_cents'] or 0) / 100
        pnl = (ks['total_pnl_cents'] or 0) / 100
        print(f"    Last Update: {ks['snapshot_ts']}")
        print(f"    Balance: ${bal:.2f}")
        print(f"    Total P&L: ${pnl:.2f}")
        print(f"    Open Positions: {ks['open_positions']}")
        print(f"    Fills: {ks['total_fills']} (Wins: {ks['win_count']}, Losses: {ks['loss_count']})")
        # Category breakdown
        print(f"    Weather P&L: ${(ks['weather_pnl_cents'] or 0)/100:.2f}")
        print(f"    Crypto P&L: ${(ks['crypto_pnl_cents'] or 0)/100:.2f}")
        print(f"    Econ P&L: ${(ks['econ_pnl_cents'] or 0)/100:.2f}")
    else:
        print("    NO DATA")
    
    # SPORTS PICKS
    print("\n[3] SPORTS PICKS")
    c.execute("""
        SELECT COUNT(*) total, 
               SUM(CASE WHEN result='WIN' THEN 1 ELSE 0 END) wins,
               SUM(CASE WHEN result='LOSS' THEN 1 ELSE 0 END) losses,
               SUM(CASE WHEN result='PENDING' THEN 1 ELSE 0 END) pending,
               SUM(profit_loss) pl, SUM(stake) staked
        FROM sports_picks
    """)
    sp = c.fetchone()
    print(f"    Total: {sp[0]} (Wins: {sp[1]}, Losses: {sp[2]}, Pending: {sp[3]})")
    print(f"    P&L: ${(sp[4] or 0):.2f}")
    print(f"    Total Staked: ${(sp[5] or 0):.2f}")
    
    # JOHN'S JOBS
    print("\n[4] JOHN'S BUSINESS")
    c.execute("""
        SELECT COUNT(*) total, SUM(invoice_amount) invoiced,
               SUM(CASE WHEN paid=1 THEN invoice_amount ELSE 0 END) collected,
               COUNT(CASE WHEN paid=1 THEN 1 END) paid_jobs
        FROM john_jobs
    """)
    jj = c.fetchone()
    print(f"    Jobs: {jj[0]} (Paid: {jj[3]})")
    print(f"    Total Invoiced: ${(jj[1] or 0):.2f}")
    print(f"    Collected: ${(jj[2] or 0):.2f}")
    
    # REVENUE
    print("\n[5] MANUAL REVENUE ENTRIES")
    c.execute("SELECT segment, COUNT(*) count, SUM(amount) total FROM revenue GROUP BY segment")
    has_rev = False
    for row in c.fetchall():
        print(f"    {row[0]}: ${row[2]:.2f} ({row[1]} entries)")
        has_rev = True
    c.execute("SELECT SUM(amount) FROM revenue")
    rev_total = c.fetchone()[0] or 0
    if not has_rev:
        print(f"    EMPTY")
    print(f"    TOTAL REVENUE: ${rev_total:.2f}")
    
    # EXPENSES
    print("\n[6] MANUAL EXPENSE ENTRIES")
    c.execute("SELECT category, COUNT(*) count, SUM(amount) total FROM expenses GROUP BY category")
    has_exp = False
    for row in c.fetchall():
        print(f"    {row[0]}: ${row[2]:.2f} ({row[1]} entries)")
        has_exp = True
    c.execute("SELECT SUM(amount) FROM expenses")
    exp_total = c.fetchone()[0] or 0
    if not has_exp:
        print(f"    EMPTY")
    print(f"    TOTAL EXPENSES: ${exp_total:.2f}")
    
    # BETS
    print("\n[7] MANUAL BET ENTRIES")
    c.execute("""
        SELECT COUNT(*) total,
               SUM(CASE WHEN result='WIN' THEN 1 ELSE 0 END) wins,
               SUM(CASE WHEN result='LOSS' THEN 1 ELSE 0 END) losses,
               SUM(profit_loss) pl, SUM(stake) staked
        FROM bets
    """)
    b = c.fetchone()
    print(f"    Total: {b[0]} (Wins: {b[1]}, Losses: {b[2]})")
    print(f"    P&L: ${(b[3] or 0):.2f}")
    print(f"    Staked: ${(b[4] or 0):.2f}")
    
    # CALC NET P&L
    print("\n" + "=" * 80)
    print("NET P&L CALCULATION")
    print("=" * 80)
    
    # Get latest Kalshi PnL
    c.execute("SELECT total_pnl_cents FROM kalshi_snapshots ORDER BY snapshot_ts DESC LIMIT 1")
    kalshi_pnl = ((c.fetchone() or [0])[0] or 0) / 100
    
    net = (rev_total + (jj[2] or 0) + kalshi_pnl + (b[3] or 0)) - (exp_total + api_total)
    
    print(f"Revenue (manual):       +${rev_total:.2f}")
    print(f"John (collected):       +${(jj[2] or 0):.2f}")
    print(f"Kalshi P&L:             +${kalshi_pnl:.2f}")
    print(f"Bets P&L:               +${(b[3] or 0):.2f}")
    print(f"                        --------")
    total_in = rev_total + (jj[2] or 0) + kalshi_pnl + (b[3] or 0)
    print(f"GROSS REVENUE:          +${total_in:.2f}")
    print()
    print(f"API Costs:              -${api_total:.2f}")
    print(f"Expenses (manual):      -${exp_total:.2f}")
    print(f"                        --------")
    print(f"NET P&L:                ${net:.2f}")
    print()
    if net < -500:
        print(f"⚠️  CRITICAL: ${abs(net):.2f} in the hole")
    
    # DIAGNOSTICS
    print("\n" + "=" * 80)
    print("DIAGNOSTICS")
    print("=" * 80)
    if rev_total == 0:
        print("❌ Revenue table is EMPTY — no manual entries")
    if exp_total == 0:
        print("❌ Expenses table is EMPTY — no manual entries")
    if kalshi_pnl == 0:
        print("⚠️  Kalshi P&L is $0 — check scalper_v8.db sync")
    if (jj[2] or 0) == 0:
        print("⚠️  John jobs collected is $0 — check john_jobs syncing")
    if api_total < 1:
        print("⚠️  API costs low (${:.2f}) — check API syncing".format(api_total))
    
    conn.close()
    return net

if __name__ == "__main__":
    try:
        net = audit()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
