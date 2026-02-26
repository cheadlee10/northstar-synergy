# Deploy NorthStar Dashboard to Railway (Free)

**Time:** 5 minutes  
**Cost:** FREE ($5/month credit)  
**Result:** Permanent URL like `https://northstar-synergy-prod.up.railway.app`

---

## STEP-BY-STEP

### 1. Create Railway Account
- Go to: https://railway.app
- Click "Start Free"
- Sign up with GitHub (easiest)

### 2. Create New Project
- Click "Create New Project"
- Select "Deploy from GitHub"
- Authorize Railway to access your GitHub
- Select the repo containing the dashboard folder

### 3. Configure App
- **Root Directory:** `dashboard`
- **Start Command:** `python -m uvicorn app:app --host 0.0.0.0 --port $PORT`
- **Port:** Let Railway auto-detect (uses $PORT env var)

### 4. Deploy
- Click "Deploy"
- Railway builds automatically (~2 min)
- You get a permanent URL

### 5. Get Your URL
- In Railway dashboard, find your deployment
- Copy the public URL (looks like: `https://northstar-synergy-prod-xxxx.up.railway.app`)
- That's your permanent dashboard link

### 6. Test It
- Open the URL in your phone browser
- You should see NorthStar Synergy logo + dashboard
- Bookmark it

---

## Your Permanent URL (Once Deployed)

`https://northstar-synergy-prod.up.railway.app` (or similar)

This is what you'll use every day from your phone.

---

**Once deployed, send me the URL and I'll:**
1. Verify it works
2. Set up twice-daily health checks (10 AM + 4 PM PT)
3. Add monitoring
4. Dashboard Manager skill takes over

---

## If You Want Me to Deploy It For You

Tell me you have a GitHub account, I can do it for you (need brief access).

Otherwise, follow steps 1-6 above (5 min total).
