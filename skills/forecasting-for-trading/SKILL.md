---
name: forecasting-for-trading
description: Deep forecasting knowledge for trading strategy optimization. Use when: (1) Testing trading strategies against forecast accuracy (weather, crypto, econ), (2) Building forecast quality metrics, (3) Analyzing how forecast errors affect P&L, (4) Backtesting strategies with different forecast scenarios, (5) Optimizing trading parameters based on forecast skill. Covers weather (NWS GFS), crypto (technical analysis + RSI), economic (FRED + correlation), and forecast validation.
---

# Forecasting for Trading — Deep Knowledge & Strategy Testing

Trading strategy performance depends critically on forecast quality. This skill provides the frameworks and code to test strategies against realistic forecast scenarios and optimize for actual forecast skill.

## Core Concept: Forecast Skill vs Strategy Skill

- **Forecast Skill** = How well we predict the outcome (weather high, BTC price, CPI number)
- **Strategy Skill** = How well we profit given our forecast

Example: If our weather forecast is 90% accurate but MM orders don't fill, we make $0 profit despite good forecasts.

**Strategy redesign must account for both.**

## Three Forecasting Domains

### 1. Weather Forecasting (Kalshi Weather Markets)

**Data Sources:**
- **GFS Model** (NOAA): Global Forecast System, 384 forecast hours, 0.5° resolution
- **Open-Meteo API**: Free access to GFS, ECMWF, ICON ensemble forecasts
- **NWS.NOAA.GOV**: Official National Weather Service observations

**Key Metrics for Kalshi:**
- High temperature (TMAX)
- Low temperature (TMIN)
- Precipitation probability (PoP) and amount
- Wind speed
- Dew point

**Forecast Quality by Lead Time:**
| Lead | Accuracy | Skill |
|------|----------|-------|
| 1-3 days | 85-95% | High (bias < 2°F) |
| 4-6 days | 75-85% | Medium (bias < 5°F) |
| 7-10 days | 60-75% | Low (bias < 10°F) |
| 10+ days | 50-60% | Very Low (climatology) |

**Kalshi markets are typically 5-30 day contracts** → expect 60-85% accuracy → 15-40% forecast error range.

**Test Strategy Against:** 
- Perfect forecast (ceiling performance)
- Real GFS forecast (realistic)
- Degraded forecast (-5% accuracy) (stress test)

### 2. Cryptocurrency Forecasting (Technical Analysis)

**Data Sources:**
- **CoinGecko API**: Historical OHLCV, free
- **Binance API**: Real-time 15m/1h/4h/1d candles
- **Funding Rates**: BitMEX, Bybit (sentiment)
- **On-Chain Metrics**: Glassnode (whale movement)

**Technical Indicators for Kalshi Crypto Markets:**
- **RSI (14-period)**: Overbought (>70) / Oversold (<30)
- **MACD**: Momentum + trend
- **Bollinger Bands**: Volatility + support/resistance
- **Moving Averages**: 20/50/200 (trend confirmation)
- **Volume Profile**: Liquidity levels

**Forecast Skill Decay:**
- **1-hour forecast**: 55-65% accuracy (better than random)
- **4-hour forecast**: 50-60% accuracy (weak edge)
- **1-day forecast**: 48-55% accuracy (slim edge)
- **5-day forecast**: 50-52% accuracy (near-random)

**Key Learning:** Crypto forecasts lose skill fast. Scalper's snipe strategy (1-4 hour timeframe) has better odds than long-dated bets.

**Test Strategy Against:**
- Actual RSI + MACD signals (realistic)
- Degraded signals (50% accuracy) (conservative)
- Market reversal scenario (forecasts inverted) (stress test)

### 3. Economic Indicator Forecasting (FRED + Correlation)

**Data Sources:**
- **FRED API** (Federal Reserve): 400k+ time series, free
- **Key Series**: CPI, NFP, Unemployment, ISM PMI, Treasury Yields
- **Release Calendar**: CNBC, Trading Economics

**Forecast Accuracy by Indicator:**
| Indicator | Announcement | Post-Announcement Drift | Kalshi Relevance |
|-----------|--------------|------------------------|------------------|
| CPI | Monthly ±0.1% | ±0.5% over 5 days | HIGH (inflation bets) |
| NFP | Monthly ±50k jobs | ±1% over 10 days | HIGH (employment bets) |
| Fed Funds Rate | Quarterly ±0% | ±0.5% over month | HIGH (rate path bets) |
| ISM PMI | Monthly ±1 point | ±2% drift | MEDIUM |

**Correlation Analysis:** 
Kalshi weather markets correlate with economic activity:
- Cold snaps → heating demand → energy prices → CPI inflation expectations
- Drought seasons → agricultural prices → food CPI → Fed policy

Example: If FRED shows CPI trending up, expect Kalshi "Will inflation be >X%" markets to shift accordingly.

**Test Strategy Against:**
- Baseline FRED correlations (realistic)
- Broken correlations (-50% correlation) (market shock scenario)
- Perfect economic foresight (ceiling)

---

## Framework: Forecast Accuracy → Strategy Performance

### Step 1: Measure Forecast Skill

For each domain, calculate:

```
Accuracy = (Correct Predictions) / (Total Predictions)
Bias = (Predicted Value) - (Actual Value)  
RMSE = sqrt(mean((Predicted - Actual)²))
```

Example Weather:
- GFS forecast: "High will be 72°F"
- Actual: 74°F
- Error: +2°F (bias)
- Skill: Within 3°F threshold = ✓ Accurate

### Step 2: Stress-Test Strategy

Run simulations:
1. **Perfect forecast scenario**: What's the ceiling P&L if we knew the outcome?
2. **Realistic forecast scenario**: What's expected P&L with 70-80% accuracy?
3. **Degraded forecast scenario**: What's P&L if accuracy drops to 50%?
4. **Reversed forecast scenario**: What if forecasts are backwards?

### Step 3: Identify Forecast-Dependent Parameters

Which strategy parameters break under poor forecasts?

Example MM Strategy:
- **Spread**: Tight spreads assume prices don't move far → breaks with bad crypto forecast
- **Position Size**: Kelly fraction assumes edge → breaks with degraded forecast accuracy
- **Order Placement**: If forecasts are wrong 30% of time, place orders further from midpoint

### Step 4: Optimize for Realistic Forecast Skill

Don't optimize for perfect forecasts. Optimize for **realistic forecast skill** you can actually achieve.

Example:
- Bad strategy: Assume 95% weather forecast accuracy → tight spreads → break when accuracy is 75%
- Good strategy: Assume 70% weather forecast accuracy → wider spreads → survive degradation

---

## Integration: Forecast-Aware Strategy Testing

### Scripts to Build

1. **forecast_accuracy_validator.py**
   - Loads actual NOAA/FRED data
   - Calculates realized forecast skill
   - Outputs: accuracy, bias, RMSE per forecast type

2. **strategy_backtest_with_forecasts.py**
   - Runs strategy with different forecast accuracy scenarios
   - Outputs: P&L under perfect/realistic/degraded forecasts
   - Identifies which parameters are forecast-sensitive

3. **forecast_scenario_generator.py**
   - Generates synthetic forecast errors
   - Creates test scenarios: +5% accuracy, -10% accuracy, reversed, etc.
   - Stress-tests strategy robustness

### References to Load

- `references/weather_forecasting.md` — GFS model details, accuracy by lead time
- `references/crypto_technical.md` — RSI/MACD/BB indicators + forecast skill
- `references/econ_correlations.md` — FRED data + correlation matrix
- `references/backtest_framework.md` — Methodology for strategy testing against forecasts

---

## Immediate Action for Kalshi Redesign

**For Scalper's V8 Reboot:**

1. **Measure current forecast skill** (GFS weather accuracy last 7 days)
2. **Test MM parameters** against realistic weather forecast errors (±3-5°F)
3. **Check crypto RSI signals** — how often are they right? (50-60% expected)
4. **Design strategy for realistic skill**, not optimistic skill
5. **Add forecast monitoring** — alert if forecast accuracy drops below threshold

**Example Redesigned Config:**
```
# Old (broken): Assumes perfect forecasts
MM_GAMMA_WEATHER=0.4  # Tight spreads
MM_MIN_SPREAD_CENTS=2

# New (realistic): Accounts for 20-30% forecast error
MM_GAMMA_WEATHER=0.2  # Wider spreads to survive forecast misses
MM_MIN_SPREAD_CENTS=5  # Buffer for price moves
KELLY_FRACTION=0.1   # Conservative sizing for forecast uncertainty
```

---

## See Also

- `kalshi-connection-monitor` — Real-time position tracking
- `kalshi-direct` — Live API integration
- `STRATEGY_REDESIGN_BRIEF.md` — Full collaboration plan with parameters A/B/C/D
