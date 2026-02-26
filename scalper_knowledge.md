# KNOWLEDGE.md — Scalper's Knowledge Graph
*Persistent facts, patterns, and discoveries. Updated as I learn.*

---

## Kalshi API Behaviors (Hard-Won)
- PSS salt length: both MAX_LENGTH and DIGEST_LENGTH work — not the auth bug
- Auth 401 root cause: multiple competing engine instances + stale timestamp on retries
- Fix: regenerate headers on every retry attempt (fresh timestamp)
- POST /portfolio/orders with post_only=True → 400 "post only cross" if order would immediately fill
- GET auth works even when POST auth fails → suggests timing/session issue, not key issue
- `KALSHI_KEY_ID` vs `KALSHI_API_KEY_ID` — env var name mismatch breaks cron-launched engines
- Market maker engine reads `KALSHI_KEY_ID`; config.py reads `KALSHI_API_KEY_ID` — keep both in .env
- Position limit errors: engine computes Kelly size (50+) but cap was 10 → fix: clamp_count() not skip
- Denver weather markets: FV=0.010 (near-certain NO) but bid=1/ask=99 → illiquid, skip
- `post only cross` = maker order would immediately match → price touched the other side

## Weather Edge Patterns
- NYC snow (KXNYCSNOWM): +$25.97 on Feb 2026 — confirmed edge template
- Open-Meteo 30-member GFS ensemble: most Kalshi bettors don't have this data
- Min 15¢ divergence required for weather trades
- Denver weather markets often illiquid (bid=1/ask=99) — skip
- Boston snow (KXBOSSNOWM): 150 contracts open at $137.53 exposure — largest current position
- Weather NO-only filter: WEATHER_NO_ONLY=true in .env — we buy NO on near-certain non-events

## Trading P&L Facts
- Starting capital: ~$381 → current ~$191 cash + $224 portfolio = ~$415 total
- Best single trade: NYC snow +$25.97
- Worst single trade: Denver snow -$4.38
- Net realized: ~+$22.37 as of 2026-02-23
- 0 round trips from market maker (fixing now)

## API Keys & Endpoints (Verified Working)
- Kalshi: api.elections.kalshi.com/trade-api/v2 — RSA-PSS, key in .env
- Open-Meteo: api.open-meteo.com — free, no key needed
- The Odds API: 6383ef1a... — 498 req/month remaining (Feb 2026), DK+FD h2h+spreads
- Action Network v2: api.actionnetwork.com/web/v2/scoreboard/{sport} — no key needed
- KenPom: kenpom.com — must be scraped with login (chead@me.com / Kristin071814!)
- Bart Torvik: barttorvik.com — Cloudflare blocks Python; use browser relay JS fetch
- NBA Stats API: stats.nba.com/stats/leaguedashteamstats — requires NBA-specific headers
- FRED: api.stlouisfed.org/fred — key bdfd983fd0e08aa74a4991deec0b1f02
- ESPN free API: site.api.espn.com — no key, NCAAB odds via competitions[0].odds

## Edge Model Calibration
- KenPom win prob: 1 / (1 + exp(-em_diff * 0.12)) with home advantage 3.5 pts
  - May be slightly aggressive (Houston 78% home vs Kansas — actual result TBD)
- Sharp money threshold: 15pp divergence (money% vs tickets%) = signal; 25pp = HIGH confidence
- NBA net rating: logistic transform coeff 0.12, home court +3.0 pts
- Min edge for email: 1.0%; min edge for trading: 5.0%
- No trades in 40-60¢ zone unless model shows 70%+ probability

## Common Bugs & Fixes
- PowerShell `&&` → use `;` as statement separator
- Windows CP1252: never use ✓ ✗ emoji in Python print() — use [OK] / [FAIL]
- KenPom fuzzy match bug: "Eastern Michigan" was matching "Michigan" (#1) — need ≥50% word overlap
- KenPom data wrapper: `{'updated':..., 'teams':{}}` — use `d.get('teams', d)`
- engine.py lock file: 3-minute TTL — stale locks auto-remove
- Multiple main.py instances: all write to same log, compete for orders, cause 401s
- `json=body` in aiohttp sets Content-Type automatically — ok to also set manually

## Bottleneck Log (Lesson #3: Remove Every Bottleneck)
| Date | Bottleneck | Craig had to | My fix |
|------|-----------|--------------|--------|
| 2026-02-23 | Odds API key | Email inbox → paste key | Now hardcoded in .env, force-loaded |
| 2026-02-23 | Engine 401s | Nothing (I found it) | Regenerate headers per retry |
| 2026-02-23 | Multiple engines | Nothing (I found it) | Task Scheduler single-instance |
| 2026-02-23 | Position limit blocks all orders | Nothing | clamp_count() added |

---
*Updated: 2026-02-23. Add entries as new patterns discovered.*
