# Forecast Monitoring — 3x Daily Setup (Low Token Cost)
**Purpose:** Keep forecast accuracy fresh. Run at 8 AM, 12 PM, 5 PM PT.  
**Cost:** ~$0.0045/day ($0.15/month) — negligible  
**Integration:** Feeds live accuracy to V8, triggers kill switches  

---

## What This Does

Every run (3x daily):
1. **Measure forecast accuracy** from recent trades
2. **Check kill switch conditions** (halt if accuracy drops)
3. **Update V8 config** (enable/disable strategies based on accuracy)
4. **Log all metrics** for daily review

**Example Output:**
```
[1] Measuring Forecast Accuracy...
  RSI Accuracy: 58.2%
  MACD Accuracy: 54.7%
  Combined (RSI+MACD): 66.3%
  Weather (GFS): 76.8%

[2] Kill Switch Logic...
  ✓ CONTINUE: Trading conditions OK

[3] Strategy Recommendation...
  ✓ Crypto snipes ENABLED (RSI+MACD 66.3%)
  ✓ Weather MM ENABLED (Days 1-3, accuracy 76.8%)
```

---

## Setup Instructions

### Option 1: Windows Task Scheduler (Recommended)

**Create 3 scheduled tasks:**

#### Task 1: 8 AM PT
```powershell
# Run as Administrator
$action = New-ScheduledTaskAction `
  -Execute "C:\Users\chead\AppData\Local\Programs\Python\Python312\python.exe" `
  -Argument "C:\Users\chead\.openclaw\workspace\skills\forecasting-for-trading\scripts\forecast_monitor_3x_daily.py"

$trigger = New-ScheduledTaskTrigger `
  -At 08:00:00 `
  -RepeatInterval (New-TimeSpan -Hours 24)

Register-ScheduledTask `
  -TaskName "ForecastMonitor_8AM" `
  -Action $action `
  -Trigger $trigger `
  -RunLevel Highest
```

#### Task 2: 12 PM PT
```powershell
$trigger = New-ScheduledTaskTrigger `
  -At 12:00:00 `
  -RepeatInterval (New-TimeSpan -Hours 24)

Register-ScheduledTask `
  -TaskName "ForecastMonitor_12PM" `
  -Action $action `
  -Trigger $trigger `
  -RunLevel Highest
```

#### Task 3: 5 PM PT
```powershell
$trigger = New-ScheduledTaskTrigger `
  -At 17:00:00 `
  -RepeatInterval (New-TimeSpan -Hours 24)

Register-ScheduledTask `
  -TaskName "ForecastMonitor_5PM" `
  -Action $action `
  -Trigger $trigger `
  -RunLevel Highest
```

### Option 2: OpenClaw Cron (Alternative)

```json
{
  "name": "ForecastMonitor_3xDaily",
  "schedule": {
    "kind": "cron",
    "expr": "0 8,12,17 * * *",
    "tz": "America/Los_Angeles"
  },
  "payload": {
    "kind": "systemEvent",
    "text": "Run forecast monitor: python C:\\Users\\chead\\.openclaw\\workspace\\skills\\forecasting-for-trading\\scripts\\forecast_monitor_3x_daily.py"
  },
  "sessionTarget": "main"
}
```

### Option 3: Manual Testing (Before Automation)

```bash
# Test run (outputs to console)
python C:\Users\chead\.openclaw\workspace\skills\forecasting-for-trading\scripts\forecast_monitor_3x_daily.py

# Check results
type C:\Users\chead\.openclaw\workspace-scalper\forecast_accuracy.jsonl | tail -1
```

---

## How V8 Uses This Data

### 1. Kill Switch Integration

V8 checks this file every minute:
```
C:\Users\chead\.openclaw\workspace-scalper\halt_trading.flag
```

If file exists, content tells V8 why to halt:
```
# File exists = halt trading
# Content example:
Combined accuracy 48.3% < 50%

# File deleted = resume trading
```

### 2. Strategy Selection

V8 reads forecast accuracy and adjusts:

```python
# In V8 config decision logic:

if combined_accuracy > 0.65:
    # Crypto snipes only (tight filters)
    ENABLE_CRYPTO_SNIPES = true
    RSI_THRESHOLD = 30
    MACD_ALIGNMENT_REQUIRED = true
    
elif combined_accuracy > 0.55:
    # Loosen filters, fewer trades
    RSI_THRESHOLD = 25  # More positions
    MACD_ALIGNMENT_REQUIRED = false  # Single indicator OK
    
else:
    # Halt trading
    HALT_TRADING = true
```

### 3. Position Sizing

Adjust Kelly fraction based on accuracy:

```python
# Kelly criterion adjusts dynamically

if combined_accuracy > 0.70:
    KELLY_FRACTION = 0.25  # Aggressive (2.5% per trade)
elif combined_accuracy > 0.60:
    KELLY_FRACTION = 0.10  # Conservative (1% per trade)
else:
    KELLY_FRACTION = 0.05  # Very conservative (0.5% per trade)
```

---

## Daily Review Process

### Morning (8 AM run)
```
1. Check forecast_accuracy.jsonl latest entry
2. Note: RSI, MACD, Combined accuracy
3. Decision: Trade all strategies, or crypto snipes only?
4. Example: "RSI 58%, MACD 54%, Combined 66% → snipes enabled"
```

### Afternoon (12 PM run)
```
1. Check if forecast accuracy has changed from morning
2. Alert if:
   - Accuracy dropped >5% (indicates model degradation)
   - Kill switch was triggered (investigate why)
3. Adjust position sizing if needed
```

### Evening (5 PM run)
```
1. Final accuracy check before overnight
2. Review day's win rate vs forecast accuracy
3. Log any correlation issues for Cliff's review
4. Decide: Continue current strategy tomorrow, or pause?
```

---

## Troubleshooting

### Task doesn't run
```powershell
# Check Task Scheduler
Get-ScheduledTask -TaskName "ForecastMonitor_8AM"

# Check logs
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" | Where-Object {$_.Message -like "*ForecastMonitor*"}

# Run manually to debug
python C:\Users\chead\.openclaw\workspace\skills\forecasting-for-trading\scripts\forecast_monitor_3x_daily.py
```

### forecast_accuracy.jsonl not updating
```
1. Check file permissions (write access)
2. Check Python can import required modules (numpy, sqlite3, requests)
3. Check if trades.jsonl exists at expected path
4. Run manual test: python forecast_monitor_3x_daily.py
```

### Halt flag triggers too often
```
1. Check combined_accuracy threshold (currently 50%)
2. Increase to 55% if accuracy is naturally 50-55%
3. Add grace period: don't halt until 3 runs in a row show low accuracy
4. Review RSI/MACD calculation (ensure using recent data only)
```

---

## Cost Analysis

### Token Usage Per Run
```
Operations:
  1. Read trades.jsonl (local, $0)
  2. Calculate accuracy (local, $0)
  3. Read/write DB (local, $0)
  4. Write to forecast_accuracy.jsonl (local, $0)

Total per run: ~0 API tokens (all local operations)
3x daily: ~0 tokens/day

Weather API (optional):
  - Open-Meteo: Free (0 tokens)
  - GFS queries: Cached, ~$0.0015/day if using paid API
  - 3x daily: ~$0.004/day max

Total: ~$0.004/day = $0.12/month (negligible)
```

---

## Integration Checklist

- [ ] Create forecast_monitor_3x_daily.py (done)
- [ ] Set up 3x daily Task Scheduler jobs (see above)
- [ ] Test manual run: `python forecast_monitor_3x_daily.py`
- [ ] Verify forecast_accuracy.jsonl is created
- [ ] Update V8 to read halt_trading.flag
- [ ] Test kill switch: manually create flag, V8 halts?
- [ ] Review first day's accuracy metrics
- [ ] Integrate into Cliff's daily monitoring dashboard

---

## Files

```
Scripts:
  - forecast_monitor_3x_daily.py (12.5K, main runner)
  - Location: workspace/skills/forecasting-for-trading/scripts/

Output:
  - forecast_accuracy.jsonl (line-delimited JSON with timestamp + metrics)
  - Location: workspace-scalper/forecast_accuracy.jsonl
  - Example line: {"rsi": 0.58, "macd": 0.547, "crypto_rsi_macd": 0.663, ...}

Kill Switch Flag:
  - halt_trading.flag (created when kill switch triggers)
  - Location: workspace-scalper/halt_trading.flag
  - V8 reads this file every minute and halts if exists

V8 Integration:
  - Update main.py to check halt_trading.flag on every trade loop
  - Update position sizing based on forecast_accuracy.jsonl latest entry
```

---

## Next: Integration with V8

Once monitoring is set up, Scalper needs to:

1. **Read halt_trading.flag** before each order placement
   ```python
   if Path(r'workspace-scalper\halt_trading.flag').exists():
       # Halt all trading, log reason, alert Cliff
       self.log.warning(f"Kill switch triggered: {flag_content}")
       return  # Skip this trading cycle
   ```

2. **Adjust position sizing** from latest forecast accuracy
   ```python
   with open(r'workspace-scalper\forecast_accuracy.jsonl') as f:
       latest_line = f.readlines()[-1]
       latest_accuracy = json.loads(latest_line)
   
   combined_acc = latest_accuracy['crypto_rsi_macd']
   if combined_acc < 0.55:
       self.kelly_fraction = 0.05  # Very conservative
   elif combined_acc < 0.65:
       self.kelly_fraction = 0.10  # Conservative
   else:
       self.kelly_fraction = 0.25  # Baseline
   ```

3. **Log accuracy with each trade** for Cliff's review
   ```python
   trade = {
       'timestamp': datetime.utcnow().isoformat(),
       'symbol': 'BTC',
       'rsi_value': rsi,
       'rsi_correct': (rsi_signal and price_moved_predicted_way),
       'macd_value': macd,
       'macd_correct': (macd_signal and price_moved_predicted_way),
       'result': 'WIN' if profit > 0 else 'LOSS',
   }
   # Write to trades.jsonl for next monitor run to read
   ```

---

## Summary

**Setup: 5 minutes** (create 3 Task Scheduler jobs)  
**Cost: ~$0.004/day** (negligible, all local operations)  
**Benefit: Real-time forecast accuracy + kill switches working**

Every 4 hours, forecast accuracy is measured and V8 adjusts accordingly.
If accuracy drops, V8 halts automatically.
If accuracy is high, V8 increases position sizing.

This is how the strategy becomes adaptive and survivable under real-world conditions.
