#!/usr/bin/env python3
"""
kalshi_auth.py — Kalshi OAuth authentication
Generates JWT tokens for Kalshi API access using key ID + private key
"""
import jwt
import time
import json
from pathlib import Path

KALSHI_KEY_ID = "4fa680d5-be76-4d85-9c1b-5fd2d42c9612"
PRIVATE_KEY_PATH = Path(r"C:\Users\chead\.openclaw\workspace\kalshi_private_key.pem")

def load_private_key():
    """Load private key from file."""
    return PRIVATE_KEY_PATH.read_text()

def generate_jwt_token(key_id=KALSHI_KEY_ID, private_key_path=PRIVATE_KEY_PATH):
    """Generate JWT token for Kalshi API authentication."""
    private_key = private_key_path.read_text()
    
    payload = {
        "sub": key_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,  # 1 hour expiry
    }
    
    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token

def get_auth_header():
    """Get Authorization header for Kalshi API requests."""
    token = generate_jwt_token()
    return {"Authorization": f"Bearer {token}"}
