#!/usr/bin/env python3
"""
get_scalper_credentials.py — Request credentials from Scalper agent
Uses inter-agent messaging to securely fetch API keys
"""
import argparse
import sys
import json
from pathlib import Path

# For demonstration, this script shows the workflow
# In production, this would be called by the main Cliff agent

def request_from_scalper(credential_name):
    """
    Send request to Scalper for credential via inter-agent messaging.
    In actual execution, this runs through OpenClaw's sessions_send.
    
    This script documents the workflow; actual execution happens
    when Cliff calls sessions_send to Scalper's session.
    """
    message = f"""Scalper, I need your {credential_name} to activate direct Kalshi dashboard integration.

Craig wants the dashboard to pull live P&L directly from Kalshi API instead of from scalper_v8.db (which isn't logging P&L currently).

Please respond with the key so I can:
1. Set it in Windows environment variables
2. Activate live Kalshi sync in the dashboard (every 15 min)
3. Display real P&L on https://chronic-slope-condo-justify.trycloudflare.com

Format your response as:
CREDENTIAL:{credential_name}:{{YOUR_KEY_HERE}}

Thanks."""
    
    return message

def main():
    parser = argparse.ArgumentParser(description='Request credentials from Scalper')
    parser.add_argument('--credential', default='KALSHI_API_KEY', help='Credential name to request')
    parser.add_argument('--set-env', action='store_true', help='Set environment variable (requires response first)')
    args = parser.parse_args()
    
    message = request_from_scalper(args.credential)
    print("[*] Message to send to Scalper:")
    print()
    print(message)
    print()
    print("[*] This should be sent via: sessions_send(sessionKey='agent:scalper:main', message=...)")
    print("[*] Scalper will respond with the credential in the format: CREDENTIAL:KALSHI_API_KEY:{{key}}")

if __name__ == '__main__':
    main()
