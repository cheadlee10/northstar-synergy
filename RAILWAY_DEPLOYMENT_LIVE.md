# NorthStar Synergy Dashboard — Railway Deployment Instructions

**GitHub Username:** cheadlee10  
**Deployment Target:** Railway (Free tier, $5/month credit)

---

## DEPLOYMENT STEPS (5 minutes)

### 1. Go to Railway
- Open: https://railway.app
- Sign in (or create account)

### 2. Click "New Project"
- Select "Deploy from GitHub"
- Authorize Railway to access your GitHub repos

### 3. Select Repository
- Look for: `openclaw/workspace` (or the repo containing dashboard)
- If not visible, click "Configure GitHub App" to grant access

### 4. Deploy Configuration
- **Service name:** `northstar-synergy`
- **Root directory:** `dashboard`
- **Build command:** (auto-detect Python)
- **Start command:** `python -m uvicorn app:app --host 0.0.0.0 --port $PORT`
- **Environment variables:** (none needed initially)

### 5. Click Deploy
- Railway builds automatically (~2-3 min)
- You'll get a permanent URL

### 6. Your Live Dashboard URL
Once deployed, you'll see something like:
```
https://northstar-synergy-prod-xxxx.up.railway.app
```

**That's your permanent dashboard link for your phone.**

### 7. Test It
- Open the URL in Safari/Chrome on your phone
- Verify NorthStar logo appears
- Verify data loads correctly

### 8. Bookmark It
- Add to phone home screen (iOS: Share → Add to Home Screen)
- Check it daily from anywhere

---

## Once Live, Send Me:
1. The permanent URL
2. I'll verify it works
3. I'll set up twice-daily health checks (10 AM + 4 PM PT)
4. Dashboard becomes your business command center

---

**This is your company's lifeline. Keep it bookmarked.**

---

Created: 2026-02-25  
For: Craig Headlee, NorthStar Synergy CEO
