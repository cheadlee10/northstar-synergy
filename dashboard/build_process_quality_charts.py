import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DB_PATH = Path(r"C:/Users/chead/.openclaw/workspace/dashboard/data/northstar.db")
OUT_DIR = Path(r"C:/Users/chead/.openclaw/workspace/chart_output/process_quality")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def implied_prob_american(odds: float) -> float:
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return abs(odds) / (abs(odds) + 100.0)


def profit_per_1_staked(odds: float) -> float:
    if odds > 0:
        return odds / 100.0
    return 100.0 / abs(odds)


conn = sqlite3.connect(DB_PATH)
q = """
SELECT id, pick_date, sport, game, pick, ml, open_ml, edge_val, model_prob, result, stake, profit_loss
FROM sports_picks
WHERE result IN ('WIN','LOSS')
ORDER BY pick_date, id
"""
df = pd.read_sql_query(q, conn)
conn.close()

if df.empty:
    raise SystemExit("No settled sports picks found.")

# Type cleanup
for c in ["ml", "open_ml", "edge_val", "model_prob", "stake", "profit_loss"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df = df.dropna(subset=["ml", "model_prob", "stake", "profit_loss"]).copy()
df["pick_date"] = pd.to_datetime(df["pick_date"])
df["win_flag"] = (df["result"] == "WIN").astype(int)

# EV and realization
# EV_i = stake_i * (p_model_i * win_profit_per_$1_i - (1 - p_model_i))
df["win_profit_per_1"] = df["ml"].apply(profit_per_1_staked)
df["ev"] = df["stake"] * (df["model_prob"] * df["win_profit_per_1"] - (1.0 - df["model_prob"]))
df["cum_ev"] = df["ev"].cumsum()
df["cum_actual"] = df["profit_loss"].cumsum()
df["luck_component"] = df["profit_loss"] - df["ev"]
df["cum_luck"] = df["luck_component"].cumsum()

# CLV proxy from open line -> bet line
# proxy_clv_bp = (implied_prob(open_ml) - implied_prob(bet_ml)) * 10,000
# positive = bet line implies lower probability than open line (better price for bettor)
df["open_ip"] = df["open_ml"].apply(implied_prob_american)
df["bet_ip"] = df["ml"].apply(implied_prob_american)
df["clv_proxy_bp"] = (df["open_ip"] - df["bet_ip"]) * 10000

# Slippage proxy
# theo_pl_i = stake_i * win_profit_per_1 if WIN else -stake_i
# slippage_i = actual_pl_i - theo_pl_i
df["theoretical_pl"] = np.where(df["win_flag"] == 1, df["stake"] * df["win_profit_per_1"], -df["stake"])
df["slippage"] = df["profit_loss"] - df["theoretical_pl"]
df["cum_slippage"] = df["slippage"].cumsum()

# ---- Chart 1: Edge realization vs EV ----
plt.style.use("seaborn-v0_8-darkgrid")
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df["pick_date"], df["cum_ev"], label="Cumulative Expected Value (process)", linewidth=2.5)
ax.plot(df["pick_date"], df["cum_actual"], label="Cumulative Realized P&L (process + luck)", linewidth=2.5)
ax.fill_between(df["pick_date"], df["cum_ev"], df["cum_actual"], alpha=0.18, label="Luck gap (realized - EV)")
ax.set_title("Edge Realization vs EV: Separating Process Quality from Luck")
ax.set_ylabel("USD")
ax.legend(loc="best")
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(OUT_DIR / "chart_edge_realization_vs_ev.png", dpi=150)
plt.close(fig)

# ---- Chart 2: CLV trend (proxy) ----
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df["pick_date"], df["clv_proxy_bp"], marker="o", linestyle="-", alpha=0.7, label="Per-bet CLV proxy (bp)")
roll = df["clv_proxy_bp"].rolling(window=5, min_periods=2).mean()
ax.plot(df["pick_date"], roll, linewidth=3, label="5-bet rolling mean")
ax.axhline(0, color="black", linewidth=1)
ax.set_title("CLV Trend Proxy (Open Line vs Bet Line)")
ax.set_ylabel("Basis points")
ax.legend(loc="best")
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(OUT_DIR / "chart_clv_trend_proxy.png", dpi=150)
plt.close(fig)

# ---- Chart 3: Win-rate calibration ----
cal = df.copy()
cal["prob_bin"] = pd.cut(cal["model_prob"], bins=[0, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00], include_lowest=True)
calib = cal.groupby("prob_bin", observed=False).agg(
    n=("win_flag", "size"),
    pred=("model_prob", "mean"),
    actual=("win_flag", "mean")
).reset_index()
calib = calib[calib["n"] > 0].copy()

fig, ax = plt.subplots(figsize=(8, 8))
ax.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
sc = ax.scatter(calib["pred"], calib["actual"], s=calib["n"] * 35, alpha=0.85)
for _, r in calib.iterrows():
    ax.annotate(f"n={int(r['n'])}", (r["pred"], r["actual"]), textcoords="offset points", xytext=(6, 6), fontsize=9)
ax.set_xlim(0.35, 1.0)
ax.set_ylim(0.0, 1.0)
ax.set_xlabel("Predicted win probability")
ax.set_ylabel("Observed win rate")
ax.set_title("Win-Rate Calibration (Process Signal vs Outcomes)")
ax.legend(loc="lower right")
fig.tight_layout()
fig.savefig(OUT_DIR / "chart_winrate_calibration.png", dpi=150)
plt.close(fig)

# ---- Chart 4: Slippage proxy ----
fig, ax = plt.subplots(figsize=(12, 6))
colors = np.where(df["slippage"] >= 0, "#2ca02c", "#d62728")
ax.bar(df["pick_date"], df["slippage"], color=colors, alpha=0.8, label="Per-bet slippage proxy")
ax.plot(df["pick_date"], df["cum_slippage"], color="#1f77b4", linewidth=2.5, label="Cumulative slippage")
ax.axhline(0, color="black", linewidth=1)
ax.set_title("Execution Slippage Proxy (Actual vs Theoretical Settlement P&L)")
ax.set_ylabel("USD")
ax.legend(loc="best")
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(OUT_DIR / "chart_slippage_proxy.png", dpi=150)
plt.close(fig)

# Summary metrics and formulas/limitations report
n = len(df)
total_ev = df["ev"].sum()
total_actual = df["profit_loss"].sum()
edge_realization = (total_actual / total_ev) if abs(total_ev) > 1e-9 else np.nan
avg_clv_bp = df["clv_proxy_bp"].mean()
median_clv_bp = df["clv_proxy_bp"].median()
calib_mae = np.average(np.abs(calib["actual"] - calib["pred"]), weights=calib["n"]) if len(calib) else np.nan
slip_total = df["slippage"].sum()
slip_abs_mean = df["slippage"].abs().mean()

report = f"""# Process Quality Chart Pack (Sports Picks)

Generated from `dashboard/data/northstar.db` table `sports_picks` ({n} settled bets).

## Core outcomes
- Total Expected Value (EV): **${total_ev:,.2f}**
- Total Realized P&L: **${total_actual:,.2f}**
- Realization ratio (Actual / EV): **{edge_realization:,.2f}x**
- Cumulative luck component (Actual - EV): **${(total_actual-total_ev):,.2f}**
- Avg CLV proxy: **{avg_clv_bp:,.1f} bp** (median {median_clv_bp:,.1f} bp)
- Calibration weighted MAE: **{calib_mae:,.3f}**
- Total slippage proxy: **${slip_total:,.2f}**
- Mean absolute per-bet slippage proxy: **${slip_abs_mean:,.2f}**

## Formulas used
1. **Expected Value per bet**  
   EV_i = stake_i * (p_i * winProfitPerDollar_i - (1 - p_i))

2. **Luck component**  
   Luck_i = ActualPL_i - EV_i  
   Cumulative luck = sum(Luck_i)

3. **CLV proxy (open vs bet line)**  
   Convert American odds to implied probability:  
   - if odds > 0: IP = 100 / (odds + 100)  
   - if odds < 0: IP = |odds| / (|odds| + 100)  
   Then: CLVproxy_i(bp) = (IP_open - IP_bet) * 10,000

4. **Calibration**  
   Bucket bets by model probability, compare average predicted probability to observed win rate in each bucket.

5. **Slippage proxy**  
   Theoretical P&L from stake/odds and result:  
   - WIN: theoPL = stake * winProfitPerDollar  
   - LOSS: theoPL = -stake  
   Slippage proxy: ActualPL - theoPL

## Luck vs process quality separation
- **Process quality signal:** EV trajectory, CLV proxy trend, calibration alignment.
- **Luck/noise signal:** gap between realized P&L and EV (cumulative luck).
- A positive realized-vs-EV gap indicates favorable variance over this sample; negative gap indicates unfavorable variance.

## Data-model limitations (important)
- `sports_picks` has **small settled sample** (n={n}); all conclusions have high variance.
- No true **closing line** field exists; CLV uses `open_ml` vs `ml` only (proxy, not true CLV).
- No execution timestamp or fill-level data; cannot decompose market movement vs entry timing.
- Slippage proxy assumes `profit_loss` is net settlement P&L and excludes hidden costs (limits, delays, partial fills, promo effects).
- Calibration reliability is limited by sparse bins and potential class imbalance.
"""

(OUT_DIR / "process_quality_report.md").write_text(report, encoding="utf-8")
print(f"Wrote charts + report to {OUT_DIR}")
