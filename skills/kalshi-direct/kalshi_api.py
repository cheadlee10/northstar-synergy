#!/usr/bin/env python3
"""
kalshi_api.py — Direct Kalshi REST API integration
Fetches live account data, positions, orders, and P&L
"""
import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Any, List

class KalshiAPI:
    """Direct Kalshi API client using bearer token auth"""
    
    BASE_URL = "https://api.kalshi.com/v2"
    
    def __init__(self, api_key: str = None):
        """Initialize with API key (bearer token from Kalshi)"""
        self.api_key = api_key or os.environ.get('KALSHI_API_KEY', '')
        if not self.api_key:
            raise ValueError("KALSHI_API_KEY not set in environment")
    
    def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make HTTP request to Kalshi API"""
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            if data:
                req = urllib.request.Request(
                    url, 
                    data=json.dumps(data).encode('utf-8'),
                    headers=headers,
                    method=method
                )
            else:
                req = urllib.request.Request(url, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode('utf-8'))
        
        except urllib.error.HTTPError as e:
            try:
                return {"error": json.loads(e.read()), "status": e.code}
            except:
                return {"error": str(e), "status": e.code}
        except Exception as e:
            return {"error": str(e), "status": 0}
    
    def get_portfolio(self) -> Dict[str, Any]:
        """Get account portfolio summary"""
        return self._request("GET", "/portfolio")
    
    def get_positions(self) -> Dict[str, Any]:
        """Get all open positions"""
        return self._request("GET", "/portfolio/positions")
    
    def get_orders(self, limit: int = 100) -> Dict[str, Any]:
        """Get order history"""
        return self._request("GET", f"/orders?limit={limit}")
    
    def get_pnl(self) -> Dict[str, Any]:
        """Get P&L breakdown by category"""
        return self._request("GET", "/portfolio/pnl")
    
    def get_balance(self) -> float:
        """Get current account balance in USD"""
        portfolio = self.get_portfolio()
        if "error" in portfolio:
            raise Exception(f"Failed to get balance: {portfolio['error']}")
        return (portfolio.get("balance_cents", 0) or 0) / 100
    
    def get_open_positions_summary(self) -> List[Dict]:
        """Get summary of all open positions"""
        positions_response = self.get_positions()
        
        if "error" in positions_response:
            raise Exception(f"Failed to get positions: {positions_response['error']}")
        
        positions = positions_response.get("positions", [])
        result = []
        
        for pos in positions:
            if pos.get("quantity", 0) != 0:
                result.append({
                    "ticker": pos.get("ticker"),
                    "quantity": pos.get("quantity"),
                    "side": pos.get("side"),
                    "avg_price": (pos.get("avg_price_cents", 0) or 0) / 100,
                    "unrealized_pnl": (pos.get("unrealized_pnl_cents", 0) or 0) / 100,
                    "realized_pnl": (pos.get("realized_pnl_cents", 0) or 0) / 100,
                })
        
        return result
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get complete account summary"""
        portfolio = self.get_portfolio()
        pnl = self.get_pnl()
        positions = self.get_open_positions_summary()
        
        return {
            "balance_usd": (portfolio.get("balance_cents", 0) or 0) / 100,
            "open_positions": len(positions),
            "total_orders": portfolio.get("total_orders", 0),
            "total_fills": portfolio.get("total_fills", 0),
            "win_count": portfolio.get("win_count", 0),
            "loss_count": portfolio.get("loss_count", 0),
            "unrealized_pnl": sum(p["unrealized_pnl"] for p in positions),
            "total_pnl": (pnl.get("total_pnl_cents", 0) or 0) / 100,
            "positions": positions,
        }

if __name__ == "__main__":
    # Test
    try:
        api = KalshiAPI()
        summary = api.get_account_summary()
        print(json.dumps(summary, indent=2))
    except Exception as e:
        print(f"Error: {e}")
