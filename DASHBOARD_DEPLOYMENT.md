# NorthStar Synergy Dashboard — Permanent Live Deployment

**Mission:** Get dashboard live at permanent URL with company name.

---

## THE DEPLOYMENT (Choose One)

### Option 1: Railway (Recommended — 5 minutes)

1. **Go to:** https://railway.app
2. **Sign in** (or create account with GitHub)
3. **Click:** "New Project"
4. **Select:** "Deploy from GitHub"
5. **Connect:** Your GitHub account
6. **Select repo:** `openclaw/workspace` (or upload dashboard folder)
7. **Configure:**
   - Service name: `northstar-synergy`
   - Port: `8000`
   - Start command: `python -m uvicorn app:app --host 0.0.0.0 --port 8000`
8. **Deploy** — Railway builds + deploys automatically
9. **URL:** `https://northstar-synergy-prod.up.railway.app` (example)
   - Will show live URL in dashboard

**Cost:** Free tier gets $5/month credit (dashboard uses <$5/month)

---

### Option 2: Vercel (Alternative)

1. **Go to:** https://vercel.com
2. **Import project** from GitHub
3. **Framework:** "Other" (FastAPI)
4. **Environment:** Python
5. **Deploy**
6. **URL:** `https://northstar-synergy.vercel.app`

---

### Option 3: Cloudflare Tunnel (If you have domain)

If you own a domain (e.g., `yourdomain.com`):
1. Run: `cloudflared.exe tunnel create northstar-synergy`
2. Run: `cloudflared.exe tunnel route dns northstar-synergy yourdomain.com`
3. Dashboard live at: `https://northstar-synergy.yourdomain.com`

---

## ONCE DEPLOYED

After deployment succeeds:

1. **Get the live URL** from Railway/Vercel dashboard
2. **Test it:** Open in phone browser
3. **Bookmark it** (add to home screen on phone)
4. **Send me the URL** → I'll:
   - Verify all data syncs correctly
   - Set up twice-daily health checks
   - Create monitoring cron jobs

---

## FILES READY FOR DEPLOYMENT

| File | Purpose |
|------|---------|
| `dashboard/app.py` | FastAPI server |
| `dashboard/Procfile` | Deployment config |
| `dashboard/requirements.txt` | Python dependencies |
| `dashboard/data/northstar.db` | SQLite database |
| `dashboard/static/` | Frontend (HTML/CSS/JS) |

---

## WHAT THE DASHBOARD SHOWS

Once live, anyone can access:

- **P&L Summary** — Total revenue, expenses, profit
- **Kalshi Trading** — Live balance, positions, P&L
- **Anthropic Usage** — Cost per agent (Cliff, Scalper, John)
- **John's Jobs** — Pipeline status, revenue
- **Sports Picks** — NCAAB performance, edge tracking

---

## AFTER DEPLOYMENT

**I will automatically:**
1. ✅ Check dashboard twice daily (10 AM + 4 PM PT)
2. ✅ Verify all data is fresh (<30 min old)
3. ✅ Alert you if anything is wrong
4. ✅ Fix any data corruption immediately
5. ✅ Log health checks to memory/dashboard_health.md

**This becomes THE source of truth for NorthStar Synergy.**

---

## QUICK START (If you want me to deploy)

Tell me:
1. Do you have a GitHub account?
2. Do you own a custom domain? (optional)
3. Do you want Railway or Vercel?

I can do the deployment for you if you give access.

---

**Bottom line:** Once this is live, you have a permanent business dashboard you can access from your phone anytime. That's how you know what's working and what's not.

No dashboard = no business intelligence.  
With dashboard = full visibility into money flowing in/out.

---

Created: 2026-02-25  
By: Cliff (Dashboard Manager)
