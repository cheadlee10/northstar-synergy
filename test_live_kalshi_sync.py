#!/usr/bin/env python3
import os
import sys
import json

# Load Scalper .env
env_file = r"C:\Users\chead\.openclaw\workspace-scalper\.env"
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip()

# Add dashboard to path
sys.path.insert(0, r'C:\Users\chead\.openclaw\workspace\dashboard')

from sync_kalshi_live import sync_kalshi_live

print("Testing live Kalshi API sync...")
print(f"API Key ID: {os.environ.get('KALSHI_API_KEY_ID', 'NOT SET')[:8]}...")

result = sync_kalshi_live(verbose=True)
print("\nResult:")
print(json.dumps(result, indent=2))
