#!/usr/bin/env python3
"""
diagnose_kalshi_connection.py — Diagnose Kalshi API connectivity issues
"""
import socket
import urllib.request
import urllib.error
import ssl
import json

print("=" * 80)
print("KALSHI CONNECTION DIAGNOSTICS")
print("=" * 80)

# 1. DNS Resolution
print("\n[1] DNS RESOLUTION")
try:
    ip = socket.gethostbyname('api.kalshi.com')
    print(f"  ✓ api.kalshi.com resolves to: {ip}")
except socket.gaierror as e:
    print(f"  ✗ DNS FAILED: {e}")

# 2. Network connectivity test
print("\n[2] NETWORK CONNECTIVITY")
try:
    socket.create_connection(("api.kalshi.com", 443), timeout=5)
    print(f"  ✓ TCP connection to api.kalshi.com:443: SUCCESS")
except Exception as e:
    print(f"  ✗ TCP connection failed: {e}")

# 3. HTTPS handshake
print("\n[3] HTTPS CERTIFICATE")
try:
    context = ssl.create_default_context()
    with socket.create_connection(("api.kalshi.com", 443), timeout=5) as sock:
        with context.wrap_socket(sock, server_hostname="api.kalshi.com") as ssock:
            print(f"  ✓ SSL handshake successful")
            cert = ssock.getpeercert()
            if cert:
                print(f"    Subject: {cert.get('subject')}")
except Exception as e:
    print(f"  ✗ SSL handshake failed: {e}")

# 4. HTTP GET (no auth)
print("\n[4] HTTP GET (unauthenticated)")
try:
    req = urllib.request.Request('https://api.kalshi.com/v2/markets', timeout=10)
    response = urllib.request.urlopen(req)
    print(f"  ✓ GET /v2/markets: {response.status}")
except urllib.error.HTTPError as e:
    print(f"  ✓ Endpoint reachable (HTTP {e.code})")
except Exception as e:
    print(f"  ✗ Request failed: {e}")

# 5. Test with Bearer token
print("\n[5] HTTP GET (with Bearer auth)")
api_key = None
try:
    with open(r'C:\Users\chead\.openclaw\workspace-scalper\.env') as f:
        for line in f:
            if 'KALSHI_API_KEY=' in line:
                api_key = line.split('=', 1)[1].strip()
                break
except:
    pass

if api_key:
    try:
        req = urllib.request.Request(
            'https://api.kalshi.com/v2/portfolio',
            headers={'Authorization': f'Bearer {api_key}'}
        )
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read())
        print(f"  ✓ GET /v2/portfolio: SUCCESS")
        print(f"    Response keys: {list(data.keys())}")
    except urllib.error.HTTPError as e:
        try:
            error_data = json.loads(e.read())
            print(f"  ~ HTTP {e.code}: {error_data}")
        except:
            print(f"  ✗ HTTP {e.code}")
    except Exception as e:
        print(f"  ✗ Request failed: {e}")
else:
    print(f"  ? API key not found in .env")

# 6. Proxy check
print("\n[6] PROXY CONFIGURATION")
import urllib.request
proxies = urllib.request.getproxies()
if proxies:
    print(f"  ! Proxies detected: {proxies}")
else:
    print(f"  ✓ No proxy configured")

# 7. Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
If DNS resolution fails: Network or firewall is blocking kalshi.com
If TCP fails: Firewall is blocking port 443
If SSL fails: Certificate issue or MITM
If HTTP fails: Kalshi API is down or wrong endpoint
If Bearer fails: Check API key or Kalshi authentication

Recommended fixes:
1. Check Windows Firewall (allow https://api.kalshi.com)
2. Check antivirus/security software
3. Check internet connection (test with ping google.com)
4. Verify API key is correct
5. Check if Kalshi API is operational (https://status.kalshi.com)
""")
