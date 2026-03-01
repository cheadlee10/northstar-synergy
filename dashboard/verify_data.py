#!/usr/bin/env python3
"""
Verify all dashboard data is present and correct
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'northstar.db')

def verify_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("DASHBOARD DATA VERIFICATION REPORT")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Kalshi trades
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status='Settled' THEN 1 ELSE 0 END) FROM kalshi_trades")
    total, settled = cursor.fetchone()
    cursor.execute("SELECT SUM(CASE WHEN pnl_realized IS NOT NULL THEN pnl_realized ELSE 0 END) FROM kalshi_trades WHERE status='Settled'")
    kalshi_pnl = cursor.fetchone()[0] or 0
    print(f"📊 KALSHI TRADING")
    print(f"   Total trades: {total}")
    print(f"   Settled: {settled}")
    print(f"   P&L: ${kalshi_pnl:,.2f}")
    print()
    
    # Sports picks
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN result='WIN' THEN 1 ELSE 0 END), SUM(CASE WHEN result='LOSS' THEN 1 ELSE 0 END), SUM(profit_loss) FROM sports_picks")
    total_picks, wins, losses, sports_pnl = cursor.fetchone()
    print(f"🏀 SPORTS PICKS")
    print(f"   Total picks: {total_picks}")
    print(f"   Wins: {wins or 0} | Losses: {losses or 0}")
    print(f"   P&L: ${sports_pnl or 0:,.2f}")
    print()
    
    # John's business
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END), SUM(CASE WHEN paid=1 THEN invoice_amount ELSE 0 END) FROM john_jobs")
    total_jobs, completed, john_revenue = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM john_leads")
    total_leads = cursor.fetchone()[0]
    print(f"💼 JOHN'S BUSINESS")
    print(f"   Jobs: {total_jobs} (completed: {completed or 0})")
    print(f"   Leads: {total_leads}")
    print(f"   Revenue: ${john_revenue or 0:,.2f}")
    print()
    
    # Expenses
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM expenses")
    exp_count, expenses = cursor.fetchone()
    cursor.execute("SELECT SUM(cost_usd) FROM api_usage")
    api_cost = cursor.fetchone()[0] or 0
    print(f"💰 EXPENSES")
    print(f"   Entries: {exp_count}")
    print(f"   Total: ${expenses or 0:,.2f}")
    print(f"   API costs: ${api_cost:,.2f}")
    print()
    
    # TOTALS
    total_revenue = (john_revenue or 0) + (sports_pnl or 0) + kalshi_pnl
    total_expenses = (expenses or 0) + api_cost
    net_profit = total_revenue - total_expenses
    
    print("=" * 60)
    print("COMPANY TOTALS")
    print("=" * 60)
    print(f"   Total Revenue:  ${total_revenue:>12,.2f}")
    print(f"   Total Expenses: ${total_expenses:>12,.2f}")
    print(f"   NET PROFIT:     ${net_profit:>12,.2f}")
    print("=" * 60)
    
    # Check for zeroes
    issues = []
    if total == 0:
        issues.append("❌ No Kalshi trades")
    if total_picks == 0:
        issues.append("❌ No sports picks")
    if total_jobs == 0:
        issues.append("❌ No John jobs")
    
    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ ALL DATA PRESENT - NO ZEROES")
    
    conn.close()
    
    return {
        "kalshi_trades": total,
        "sports_picks": total_picks,
        "john_jobs": total_jobs,
        "john_leads": total_leads,
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "has_zeroes": len(issues) > 0
    }

if __name__ == "__main__":
    result = verify_data()
    
    # Save report
    report_path = os.path.join(os.path.dirname(__file__), 'data', 'verification_report.json')
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nReport saved to: {report_path}")
