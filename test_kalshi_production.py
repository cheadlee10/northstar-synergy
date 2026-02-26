#!/usr/bin/env python3
"""
test_kalshi_production.py — Test Kalshi production endpoint (what Scalper uses)
"""
import socket
import urllib.request
import urllib.error
import ssl
import json

print("=" * 80)
print("KALSHI PRODUCTION API TEST (api.elections.kalshi.com)")
print("=" * 80)

# 1. DNS Resolution
print("\n[1] DNS RESOLUTION")
try:
    ip = socket.gethostbyname('api.elections.kalshi.com')
    print(f"  ✓ api.elections.kalshi.com resolves to: {ip}")
except socket.gaierror as e:
    print(f"  ✗ DNS FAILED: {e}")
    exit(1)

# 2. Network connectivity test
print("\n[2] TCP CONNECTION (port 443)")
try:
    sock = socket.create_connection(("api.elections.kalshi.com", 443), timeout=5)
    sock.close()
    print(f"  ✓ TCP connection successful")
except Exception as e:
    print(f"  ✗ TCP connection failed: {e}")
    exit(1)

# 3. HTTPS handshake
print("\n[3] HTTPS/TLS HANDSHAKE")
try:
    context = ssl.create_default_context()
    with socket.create_connection(("api.elections.kalshi.com", 443), timeout=5) as sock:
        with context.wrap_socket(sock, server_hostname="api.elections.kalshi.com") as ssock:
            print(f"  ✓ SSL/TLS handshake successful")
except Exception as e:
    print(f"  ✗ SSL/TLS failed: {e}")
    exit(1)

# 4. HTTP GET to /trade-api/v2 (Scalper's endpoint)
print("\n[4] HTTP GET /trade-api/v2 (no auth)")
try:
    url = 'https://api.elections.kalshi.com/trade-api/v2/markets'
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as response:
        print(f"  ✓ HTTP {response.status}")
        try:
            data = json.loads(response.read())
            print(f"    Endpoint is operational, returned {len(data.get('markets', []))} markets")
        except:
            print(f"    Response received (not JSON)")
except urllib.error.HTTPError as e:
    print(f"  ~ HTTP {e.code} (expected for unauthenticated requests)")
except urllib.error.URLError as e:
    print(f"  ✗ URL error: {e}")
    exit(1)
except Exception as e:
    print(f"  ✗ Request failed: {e}")
    exit(1)

print("\n" + "=" * 80)
print("STATUS: ✓ PRODUCTION ENDPOINT IS REACHABLE")
print("=" * 80)
print("""
Scalper's V8 engine is configured to use:
  Base URL: https://api.elections.kalshi.com/trade-api/v2
  Auth: RSA-PSS signature (KALSHI_API_KEY_ID + KALSHI_PRIVATE_KEY)
  
This endpoint is REACHABLE from your network.

If Scalper V8 is still having connection issues:
1. Check that Scalper process is running (launch_v8.ps1)
2. Verify KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY_PATH in .env are set
3. Check logs in workspace-scalper/logs/scalper_v8.log
4. Restart V8 engine: Stop-Process and re-run launch_v8.ps1
""")
