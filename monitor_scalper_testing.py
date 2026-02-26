#!/usr/bin/env python3
"""
monitor_scalper_testing.py — Real-time monitoring of Scalper's V8 testing
Watches TEST_RESULTS.jsonl for updates and provides live guidance.
Run this in a separate terminal while Scalper tests.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import time

TEST_RESULTS = r'C:\Users\chead\.openclaw\workspace-scalper\TEST_RESULTS.jsonl'
TRADES = r'C:\Users\chead\.openclaw\workspace-scalper\trades.jsonl'
FORECAST_ACCURACY = r'C:\Users\chead\.openclaw\workspace-scalper\forecast_accuracy.jsonl'

def read_latest_entry(file_path: str) -> dict:
    """Read the latest JSON entry from a JSONL file."""
    try:
        if not Path(file_path).exists():
            return {}
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
            if lines:
                return json.loads(lines[-1])
    except:
        pass
    return {}

def analyze_trades() -> dict:
    """Analyze recent trades for accuracy."""
    try:
        if not Path(TRADES).exists():
            return {'trades': 0, 'wins': 0, 'accuracy': 0}
        
        with open(TRADES) as f:
            trades = [json.loads(line) for line in f if line.strip()]
        
        if not trades:
            return {'trades': 0, 'wins': 0, 'accuracy': 0}
        
        # Only analyze last 10 trades
        recent = trades[-10:]
        wins = sum(1 for t in recent if t.get('result') == 'WIN')
        accuracy = wins / len(recent) if recent else 0
        
        return {
            'trades': len(recent),
            'wins': wins,
            'accuracy': accuracy,
            'pnl': sum(t.get('pnl', 0) for t in recent)
        }
    except:
        return {'trades': 0, 'wins': 0, 'accuracy': 0}

def get_guidance(status: str, accuracy: float, trades: int, wins: int) -> str:
    """Generate real-time guidance based on test status."""
    
    guidance = []
    
    if status == 'testing':
        if accuracy >= 0.65:
            guidance.append("✅ ACCURACY GOOD (65%+) — Continue to Phase 5 (live trading)")
        elif accuracy >= 0.55:
            guidance.append("⚠️  ACCURACY MEDIUM (55-65%) — Trade conservatively (1% position size)")
        else:
            guidance.append("❌ ACCURACY LOW (<55%) — Halt trading, check RSI/MACD calculations")
    
    elif status == 'kill_switch_test':
        guidance.append("🔴 KILL SWITCH TEST — Did V8 skip trades? Check halt_trading.flag was read.")
    
    elif status == 'accuracy_feedback_test':
        guidance.append("🔄 FEEDBACK LOOP TEST — Check if forecast_accuracy.jsonl updated with new trade data")
    
    elif status == 'live_trading':
        if wins / max(1, trades) >= 0.65:
            guidance.append(f"✅ LIVE TRADING GOOD (Win Rate {wins}/{trades} = {wins/max(1,trades):.0%})")
        else:
            guidance.append(f"⚠️  WIN RATE LOW ({wins}/{trades} = {wins/max(1,trades):.0%}) — Check filter parameters")
    
    return " | ".join(guidance)

def print_status(test_results: dict, trades_analysis: dict, forecast_acc: dict):
    """Print formatted status for real-time monitoring."""
    
    print("\n" + "=" * 100)
    print(f"SCALPER TESTING — {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 100)
    
    # Test Results
    if test_results:
        print(f"\n[TEST RESULTS]")
        print(f"  Status: {test_results.get('status', 'unknown')}")
        print(f"  Trades executed: {test_results.get('trades', 0)}")
        print(f"  Wins: {test_results.get('wins', 0)}")
        print(f"  Accuracy: {test_results.get('accuracy', 0):.1%}")
        print(f"  Notes: {test_results.get('notes', '')}")
    
    # Trades Analysis
    if trades_analysis and trades_analysis['trades'] > 0:
        print(f"\n[TRADE ANALYSIS]")
        print(f"  Recent trades: {trades_analysis['trades']}")
        print(f"  Wins: {trades_analysis['wins']}")
        print(f"  Win rate: {trades_analysis['accuracy']:.1%}")
        print(f"  Total P&L: +{trades_analysis['pnl']:.2f} cents")
    
    # Forecast Accuracy
    if forecast_acc:
        print(f"\n[FORECAST ACCURACY]")
        print(f"  RSI: {forecast_acc.get('rsi', 0):.1%}")
        print(f"  MACD: {forecast_acc.get('macd', 0):.1%}")
        print(f"  Combined: {forecast_acc.get('crypto_rsi_macd', 0):.1%}")
    
    # Guidance
    acc = test_results.get('accuracy', 0) or (trades_analysis.get('accuracy', 0) if trades_analysis else 0)
    guidance = get_guidance(
        test_results.get('status', ''),
        acc,
        test_results.get('trades', 0),
        test_results.get('wins', 0)
    )
    print(f"\n[GUIDANCE]")
    print(f"  {guidance}")
    
    print("\n" + "=" * 100)

def monitor_live(check_interval: int = 5):
    """Monitor test results in real-time."""
    
    print("Starting live monitoring of Scalper's testing...")
    print(f"Checking {TEST_RESULTS} every {check_interval} seconds")
    print("Press Ctrl+C to stop")
    
    last_timestamp = None
    
    try:
        while True:
            test_results = read_latest_entry(TEST_RESULTS)
            
            # Only print if there's new data
            if test_results and test_results.get('timestamp') != last_timestamp:
                last_timestamp = test_results.get('timestamp')
                
                trades_analysis = analyze_trades()
                forecast_acc = read_latest_entry(FORECAST_ACCURACY)
                
                print_status(test_results, trades_analysis, forecast_acc)
            
            time.sleep(check_interval)
    
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

if __name__ == "__main__":
    monitor_live(check_interval=5)
