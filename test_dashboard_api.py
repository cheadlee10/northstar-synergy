import requests
import json

try:
    response = requests.get('http://localhost:8765/api/kalshi/summary', timeout=5)
    print(f'Status: {response.status_code}')
    data = response.json()
    
    print('\n=== LIVE ACCOUNT ===')
    print(f'Balance: ${data.get("live_balance", 0):.2f}')
    print(f'Open Positions: {data.get("live_open_positions", 0)}')
    
    print('\n=== PERIOD P&L ===')
    if 'periods' in data:
        for period, metrics in data['periods'].items():
            print(f'  {period}: ${metrics.get("pnl_usd", 0):.2f} ({metrics.get("fills", 0)} fills)')
    
except Exception as e:
    print(f'Error: {e}')
