# Weather Forecasting for Kalshi Trading

## GFS Model Fundamentals

**GFS (Global Forecast System)** is NOAA's operational weather model:
- **Grid Resolution**: 0.5° (≈35 km)
- **Forecast Horizon**: 384 hours (16 days)
- **Update Frequency**: 4x daily (00Z, 06Z, 12Z, 18Z UTC)
- **Ensemble**: 21 members (GFS deterministic + 20 ensemble members)

### Accuracy by Lead Time

| Lead Time | TMAX Error | TMIN Error | Probability of Precipitation |
|-----------|-----------|-----------|-----|
| Day 1-2 | ±1.5°F | ±1.5°F | 90%+ skill |
| Day 3-5 | ±2.5°F | ±2.5°F | 80-90% skill |
| Day 6-10 | ±4-6°F | ±4-6°F | 60-80% skill |
| Day 11-16 | ±8-12°F | ±8-12°F | 40-60% skill |

**Key Finding**: Kalshi contracts are typically Days 5-30. Expect forecast errors of 3-10°F.

## Kalshi Weather Markets

### Major Market Types (US-based)

1. **High/Low Temperature** (most common)
   - Will NYC high exceed 75°F on Feb 26?
   - Bid/Ask on prediction: 62-64 cents
   - Accuracy needed: Forecast skill on TMAX

2. **Precipitation**
   - Will Chicago receive >0.10" on Feb 27?
   - Bid/Ask wider (harder to forecast precisely)
   - Accuracy needed: 70%+ on PoP threshold

3. **Wind Speed**
   - Will Denver wind gust >25 mph?
   - Bid/Ask: 35-38 cents (rare event)
   - Accuracy needed: 60%+ on extremes

4. **Dew Point / Humidity**
   - Will Miami dew point exceed 65°F?
   - Less commonly traded
   - Harder to forecast (finer margin of error)

### Location-Specific Forecast Skill

**High Predictability** (±2°F by day 5):
- NYC, CHI, DEN, ATL, BOS, PHX
- Regular geography, good model performance

**Moderate Predictability** (±3-4°F by day 5):
- LAS, MIA, SEA (marine influence, special setup)
- Coastal cities (sea breeze, upwelling)

**Low Predictability** (±5-8°F by day 5):
- Complex terrain: mountains, canyons
- Coastal transitions (LAX, SFO)

## Forecast Error Distribution

Not all errors are equal. Errors follow **normal distribution with seasonal bias**:

```
Winter (Jan-Feb):
- Cold bias: GFS forecasts slightly too cold
- Bias: -2 to -3°F average
- Std Dev: ±2-3°F

Summer (Jun-Aug):
- Warm bias: GFS forecasts slightly too warm
- Bias: +2 to +3°F average
- Std Dev: ±3-4°F (higher variability)

Spring/Fall (Mar-May, Sep-Nov):
- Neutral bias: -1 to +1°F
- Std Dev: ±2-3°F
```

**Implication**: Don't trust GFS point forecasts. Use ensemble members (GFS + perturbed members) for confidence intervals.

## Real-Time Forecast Data

### Open-Meteo (Free)
```
https://api.open-meteo.com/v1/forecast?
  latitude=40.71&longitude=-74.01
  &start_date=2026-02-25&end_date=2026-03-06
  &hourly=temperature_2m,precipitation,wind_speed_10m
  &models=gfs,ecmwf,icon
```

Returns: Ensemble forecasts from 3 models. Useful for confidence bounds.

### NOAA GFS (Official)
```
https://www.ncei.noaa.gov/products/weather-global-data-assimilation-system
Download GRiB2 files → parse with pygrib
```

### NWS Observations (Ground Truth)
```
https://api.weather.gov/points/{lat},{lon}
→ grid point data + hourly observations
```

## Trading Strategy Implications

### High Forecast Skill Opportunities (Days 1-3)
- Tight forecast cones (±1.5°F)
- Wide bid/ask spreads on high-confidence predictions
- Good for MM: tight spreads, reliable prices
- **Action**: Trade only Days 1-3 for MM strategy; avoid longer-dated contracts

### Medium Skill (Days 4-7)
- Widening forecast cones (±2.5-4°F)
- Good for snipes: wait for market mispricing of forecast uncertainty
- Bad for tight MM: orders won't fill (wide bid/ask spread)
- **Action**: Place wider MM spreads; focus on snipe strategy

### Low Skill (Days 8+)
- Very wide forecast cones (±6-12°F)
- Market prices should reflect this uncertainty
- If they don't → mispricing opportunity
- **Action**: Avoid unless market is underpricing uncertainty

### Seasonal Adjustments

**Winter (Jan-Mar)**:
- Forecast skill slightly lower (variability in cold systems)
- Use +5% bias correction (GFS runs cold)
- Expected error: ±3-5°F

**Summer (Jun-Aug)**:
- Forecast skill slightly lower (convective uncertainty)
- Use -5% bias correction (GFS runs warm)
- Expected error: ±4-6°F

**Spring/Fall (Mar-May, Sep-Nov)**:
- Forecast skill highest (balanced, predictable transitions)
- No bias correction needed
- Expected error: ±2-3°F

## Code: Load & Validate Weather Forecast

```python
import requests
import pandas as pd

def get_gfs_forecast(lat: float, lon: float, days: int = 10) -> pd.DataFrame:
    """Fetch GFS forecast from Open-Meteo"""
    url = f"https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": pd.Timestamp.today().strftime("%Y-%m-%d"),
        "end_date": (pd.Timestamp.today() + pd.Timedelta(days=days)).strftime("%Y-%m-%d"),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "models": "gfs,ecmwf,icon",
        "timezone": "America/New_York",
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    # Parse ensemble
    forecasts = []
    for model in ["gfs", "ecmwf", "icon"]:
        if model in data:
            df = pd.DataFrame({
                "date": pd.to_datetime(data[model]["daily"]["time"]),
                "tmax": data[model]["daily"]["temperature_2m_max"],
                "tmin": data[model]["daily"]["temperature_2m_min"],
                "precip": data[model]["daily"]["precipitation_sum"],
            })
            df["model"] = model
            forecasts.append(df)
    
    return pd.concat(forecasts, ignore_index=True)

def calculate_forecast_confidence(forecast_df: pd.DataFrame) -> dict:
    """Get ensemble spread as confidence bounds"""
    return {
        "tmax_mean": forecast_df["tmax"].mean(),
        "tmax_min": forecast_df["tmax"].min(),
        "tmax_max": forecast_df["tmax"].max(),
        "tmax_std": forecast_df["tmax"].std(),
        "ensemble_spread": forecast_df["tmax"].max() - forecast_df["tmax"].min(),
    }
```

## Strategy Parameter Tuning for Weather Forecast Skill

**Days 1-3 (High Skill: 90%+)**:
- Use tight MM spreads: 1-2 cents
- Aggressive position sizing
- Example: MM_GAMMA_WEATHER = 0.4, MM_MIN_SPREAD_CENTS = 1

**Days 4-7 (Medium Skill: 70-80%)**:
- Use medium MM spreads: 3-5 cents
- Conservative position sizing
- Example: MM_GAMMA_WEATHER = 0.2, MM_MIN_SPREAD_CENTS = 3

**Days 8+ (Low Skill: 50-60%)**:
- Use wide MM spreads: 8-15 cents OR disable MM
- Snipe-only strategy
- Example: ENABLE_MARKET_MAKING = false, focus on high-confidence snipes

## Monitoring Forecast Accuracy

Track GFS accuracy in real-time:

```python
def monitor_forecast_skill():
    """Daily accuracy check: GFS forecast vs realized"""
    yesterday = pd.Timestamp.today() - pd.Timedelta(days=1)
    
    # Get yesterday's 5-day forecast (made 5 days ago)
    past_forecast = load_forecast_from_archive(yesterday - pd.Timedelta(days=5))
    
    # Get actual observed high/low
    actual = get_nws_observations(yesterday)
    
    # Calculate error
    error = abs(past_forecast["tmax"] - actual["tmax"])
    
    # Alert if error > 5°F (outside expected ±3-4°F range)
    if error > 5:
        print(f"WARNING: Forecast error {error}°F (greater than expected)")
        # Consider adjusting strategy parameters
```
