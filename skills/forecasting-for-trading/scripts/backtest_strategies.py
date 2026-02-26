#!/usr/bin/env python3
"""
backtest_strategies.py — Test Kalshi MM & Snipe strategies against forecast scenarios

Tests 3 strategy options against different forecast accuracy levels:
  A. Tighter MM (1-cent spread)
  B. Snipe-only (high confidence)
  C. Hybrid (MM on Days 1-3, Snipe on Days 4+)

And 3 forecast scenarios:
  1. Perfect forecast (ceiling)
  2. Realistic forecast (70-80% accuracy)
  3. Degraded forecast (50-60% accuracy)
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Tuple, List
from scipy.stats import norm

# ──────────────────────────────────────────────────────────────────────────────
# DATA MODEL: Simulated Market State
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class MarketState:
    """Represents Kalshi market at one point in time"""
    day: int  # Days until contract expiry
    true_outcome: float  # Actual outcome (what will happen)
    forecast: float  # Our forecast
    forecast_accuracy: float  # P(|forecast - true| < threshold)
    bid: float  # Current market bid
    ask: float  # Current market ask
    midpoint: float  # (bid + ask) / 2
    volume: int  # Daily volume (contracts)
    
    def spread(self) -> float:
        return self.ask - self.bid
    
    def is_mispriced(self, threshold=0.03) -> Tuple[bool, str, float]:
        """
        Check if market is mispriced given our forecast
        Returns: (is_mispriced, direction, edge)
        """
        # Simple test: if bid is >10% away from forecast, it's mispriced
        fair_value = self.forecast
        bid_error = abs(self.bid - fair_value) / fair_value
        ask_error = abs(self.ask - fair_value) / fair_value
        
        if bid_error > threshold:
            return True, "SELL", bid_error
        elif ask_error > threshold:
            return True, "BUY", ask_error
        else:
            return False, "SKIP", 0

# ──────────────────────────────────────────────────────────────────────────────
# FORECAST SCENARIOS
# ──────────────────────────────────────────────────────────────────────────────

def generate_forecast_scenario(scenario: str, base_accuracy: float = 0.75) -> float:
    """Generate forecast accuracy for a scenario"""
    if scenario == "perfect":
        return 1.00  # 100% accuracy
    elif scenario == "realistic":
        return base_accuracy  # 75-85% typical
    elif scenario == "degraded":
        return base_accuracy - 0.15  # 60-70% degraded
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

def simulate_kalshi_market(
    days_ahead: int,
    forecast_accuracy: float,
    true_bias: float = 0.0,
) -> MarketState:
    """
    Simulate a Kalshi market state at 'days_ahead' from expiry
    
    Parameters:
      days_ahead: Days until contract expiry (1-30)
      forecast_accuracy: P(our forecast is within ±threshold)
      true_bias: Bias in our forecast (e.g., -0.02 = forecast is 2% too low)
    """
    
    # True outcome drawn from distribution
    true_outcome = np.random.beta(5, 5)  # Centered around 50%
    
    # Our forecast (with accuracy and bias)
    if np.random.random() < forecast_accuracy:
        # We're right (within threshold)
        forecast = true_outcome + np.random.normal(0, 0.02)  # ±2% noise
    else:
        # We're wrong (random guess)
        forecast = np.random.uniform(0, 1)
    
    # Apply bias
    forecast = np.clip(forecast + true_bias, 0, 1)
    
    # Market prices based on true outcome (but doesn't know what we know)
    market_forecast = np.random.normal(true_outcome, 0.05)  # Market is noisier
    market_forecast = np.clip(market_forecast, 0, 1)
    
    midpoint = market_forecast
    spread = 0.02 + (0.05 / days_ahead)  # Wider spreads further out
    
    return MarketState(
        day=days_ahead,
        true_outcome=true_outcome,
        forecast=forecast,
        forecast_accuracy=forecast_accuracy,
        bid=max(0, midpoint - spread/2),
        ask=min(1, midpoint + spread/2),
        midpoint=midpoint,
        volume=1000 + np.random.randint(-200, 200),
    )

# ──────────────────────────────────────────────────────────────────────────────
# STRATEGY IMPLEMENTATIONS
# ──────────────────────────────────────────────────────────────────────────────

class Strategy:
    """Base strategy class"""
    
    def __init__(self, name: str):
        self.name = name
        self.trades = []
    
    def should_trade(self, market: MarketState) -> Tuple[bool, str, float]:
        """Determine whether to trade and what action. Override in subclass."""
        raise NotImplementedError
    
    def execute(self, market: MarketState) -> Tuple[float, str]:
        """Execute trade and return (profit, action)"""
        should_trade, action, confidence = self.should_trade(market)
        
        if not should_trade:
            return 0.0, "SKIP"
        
        # Determine trade direction and entry
        if action == "BUY":
            entry_price = market.ask
            exit_price = market.true_outcome
        elif action == "SELL":
            entry_price = market.bid
            exit_price = market.true_outcome
        else:
            return 0.0, "SKIP"
        
        # P&L calculation
        if action == "BUY":
            pnl = exit_price - entry_price
        else:
            pnl = entry_price - exit_price
        
        self.trades.append({
            'day': market.day,
            'action': action,
            'entry': entry_price,
            'exit': exit_price,
            'pnl': pnl,
            'confidence': confidence,
        })
        
        return pnl, action
    
    def summary(self) -> dict:
        """Calculate strategy performance metrics"""
        if not self.trades:
            return {
                'name': self.name,
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'win_rate': 0.0,
                'sharpe': 0.0,
                'max_dd': 0.0,
            }
        
        trades_df = pd.DataFrame(self.trades)
        wins = (trades_df['pnl'] > 0).sum()
        losses = (trades_df['pnl'] < 0).sum()
        total_pnl = trades_df['pnl'].sum()
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if wins > 0 else 0
        avg_loss = abs(trades_df[trades_df['pnl'] < 0]['pnl'].mean()) if losses > 0 else 0
        win_rate = wins / len(trades_df) if len(trades_df) > 0 else 0
        
        # Sharpe ratio
        returns = trades_df['pnl'].values
        sharpe = np.mean(returns) / np.std(returns) if len(returns) > 1 else 0
        
        # Max drawdown
        cumsum = np.cumsum(returns)
        max_dd = np.min(cumsum) if len(cumsum) > 0 else 0
        
        return {
            'name': self.name,
            'trades': len(trades_df),
            'wins': wins,
            'losses': losses,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'win_rate': win_rate,
            'sharpe': sharpe,
            'max_dd': max_dd,
        }

class TightMMStrategy(Strategy):
    """Strategy A: Tight market-making (1-cent spreads)"""
    
    def should_trade(self, market: MarketState) -> Tuple[bool, str, float]:
        """
        Place orders inside the spread (tight MM)
        Win if our forecast is better than market's
        """
        
        # Only trade Days 1-3 (high forecast accuracy)
        if market.day > 3:
            return False, "SKIP", 0
        
        # Check if our forecast is different from market's
        forecast_error = abs(market.forecast - market.midpoint)
        
        # If our forecast is significantly different, place order
        if forecast_error > market.spread() * 0.5:
            if market.forecast > market.midpoint:
                return True, "BUY", forecast_error
            else:
                return True, "SELL", forecast_error
        
        return False, "SKIP", 0

class SnipeOnlyStrategy(Strategy):
    """Strategy B: Only snipe on high-confidence forecasts"""
    
    def should_trade(self, market: MarketState) -> Tuple[bool, str, float]:
        """
        Only trade when we have high forecast confidence
        and market is mispriced
        """
        
        # Need >70% forecast accuracy
        if market.forecast_accuracy < 0.70:
            return False, "SKIP", 0
        
        # Check mispricing
        is_mispriced, direction, edge = market.is_mispriced(threshold=0.05)
        
        if is_mispriced:
            return True, direction, edge
        
        return False, "SKIP", 0

class HybridStrategy(Strategy):
    """Strategy C: Hybrid (MM Days 1-3, Snipe Days 4+)"""
    
    def should_trade(self, market: MarketState) -> Tuple[bool, str, float]:
        """
        Days 1-3: Tight MM
        Days 4+: Snipe only
        """
        
        if market.day <= 3:
            # MM phase
            forecast_error = abs(market.forecast - market.midpoint)
            if forecast_error > market.spread() * 0.5:
                if market.forecast > market.midpoint:
                    return True, "BUY", forecast_error
                else:
                    return True, "SELL", forecast_error
        else:
            # Snipe phase
            if market.forecast_accuracy < 0.65:
                return False, "SKIP", 0
            
            is_mispriced, direction, edge = market.is_mispriced(threshold=0.08)
            if is_mispriced:
                return True, direction, edge
        
        return False, "SKIP", 0

# ──────────────────────────────────────────────────────────────────────────────
# BACKTEST HARNESS
# ──────────────────────────────────────────────────────────────────────────────

def backtest_scenario(
    strategy: Strategy,
    scenario: str,
    num_markets: int = 100,
    lead_times: List[int] = None,
) -> dict:
    """
    Backtest a strategy across multiple simulated markets
    
    Parameters:
      strategy: Strategy to test
      scenario: "perfect", "realistic", or "degraded"
      num_markets: Number of simulated markets
      lead_times: Days ahead to simulate (default 1-30)
    """
    
    if lead_times is None:
        lead_times = list(range(1, 31))
    
    forecast_accuracy = generate_forecast_scenario(scenario)
    
    for _ in range(num_markets):
        # Simulate a market at random lead time
        days = np.random.choice(lead_times)
        market = simulate_kalshi_market(days, forecast_accuracy)
        
        pnl, action = strategy.execute(market)
    
    return strategy.summary()

def print_results(results: List[dict]):
    """Pretty-print backtest results"""
    
    print("\n" + "=" * 100)
    print("KALSHI STRATEGY BACKTEST RESULTS")
    print("=" * 100)
    
    for r in results:
        print(f"\n{r['name']} ({r['trades']} trades)")
        print(f"  Total P&L:    ${r['total_pnl']:>8.2f}")
        print(f"  Win Rate:     {r['win_rate']:>8.1%}")
        print(f"  Wins/Losses:  {r['wins']:>2d} / {r['losses']:>2d}")
        print(f"  Avg Win/Loss: ${r['avg_win']:>6.3f} / ${r['avg_loss']:>6.3f}")
        print(f"  Sharpe Ratio: {r['sharpe']:>8.2f}")
        print(f"  Max Drawdown: ${r['max_dd']:>8.2f}")

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Backtesting Kalshi strategies across forecast scenarios...")
    
    scenarios = ["perfect", "realistic", "degraded"]
    strategies = [
        TightMMStrategy("Strategy A: Tight MM (1-cent)"),
        SnipeOnlyStrategy("Strategy B: Snipe Only"),
        HybridStrategy("Strategy C: Hybrid (MM+Snipe)"),
    ]
    
    for scenario in scenarios:
        print(f"\n\n{'=' * 100}")
        print(f"SCENARIO: {scenario.upper()} FORECAST")
        print(f"{'=' * 100}")
        
        results = []
        for strategy in strategies:
            strategy.trades = []  # Reset
            result = backtest_scenario(strategy, scenario, num_markets=500)
            results.append(result)
        
        print_results(results)
        
        # Recommendation
        best = max(results, key=lambda x: x['total_pnl'])
        print(f"\n→ BEST STRATEGY ({scenario}): {best['name']}")
        print(f"  Total P&L: ${best['total_pnl']:.2f}")
