# 🚀 Deployment Checklist

Follow these steps exactly to deploy your application.

## ✅ Pre-Deployment Checklist

- [x] Backend API working locally (http://localhost:8000)
- [x] Frontend working locally (http://localhost:5174)
- [x] All TypeScript errors fixed
- [x] Production build successful
- [ ] Git repository initialized
- [ ] Code pushed to GitHub
- [ ] Backend deployed
- [ ] Frontend deployed
- [ ] Environment variables configured

---

## Step 1: Initialize Git & Push to GitHub (5 minutes)

### 1.1 Initialize Git Repository

```bash
cd "/Users/finnbahr/Desktop/FIS Scraping"
git init
git add .
git commit -m "Initial commit: FIS Alpine Analytics - Full Stack Application"
```

### 1.2 Create GitHub Repository

**Option A - Using GitHub CLI (Recommended)**
```bash
# Install GitHub CLI if you haven't
brew install gh

# Login
gh auth login

# Create and push repository
gh repo create fis-alpine-analytics --public --source=. --push
```

**Option B - Manual**
1. Go to https://github.com/new
2. Repository name: `fis-alpine-analytics`
3. Description: "FIS Alpine Skiing Analytics - Full Stack Application"
4. Public or Private (your choice)
5. Don't initialize with README (we have one)
6. Click "Create repository"
7. Run these commands:
   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/fis-alpine-analytics.git
   git branch -M main
   git push -u origin main
   ```

---

## Step 2: Deploy Backend to Render (10 minutes)

### 2.1 Create Render Account
1. Go to https://render.com
2. Click "Get Started" or "Sign Up"
3. Choose "Sign up with GitHub" (easiest)
4. Authorize Render to access your GitHub

### 2.2 Create PostgreSQL Database (IMPORTANT: Do this FIRST)

Since your database is currently local, you need a cloud database:

1. In Render Dashboard, click "New +" → "PostgreSQL"
2. Name: `fis-alpine-db`
3. Database: `alpine_analytics`
4. User: `alpine_analytics`
5. Region: Choose closest to you (Oregon for US West)
6. Plan: **Free** (90 days free, then $7/month) OR **Starter** ($7/month)
7. Click "Create Database"
8. Wait 2-3 minutes for creation
9. **SAVE THESE VALUES** (you'll need them):
   - Internal Database URL
   - External Database URL
   - Host
   - Port
   - Database
   - Username
   - Password

### 2.3 Migrate Your Data to Cloud Database

```bash
# Export from local database
pg_dump -h 127.0.0.1 -p 5433 -U alpine_analytics -d alpine_analytics -F c -f ~/Desktop/fis_backup.dump

# Import to Render (use External Database URL from Render)
pg_restore -h YOUR-RENDER-HOST -p 5432 -U alpine_analytics -d alpine_analytics -v ~/Desktop/fis_backup.dump

# Or use the full connection string:
pg_restore -d "postgres://alpine_analytics:PASSWORD@HOST:5432/alpine_analytics" ~/Desktop/fis_backup.dump
```

**Troubleshooting**: If you get "already exists" errors, that's OK - it means the data is there.

### 2.4 Deploy FastAPI Application

1. In Render Dashboard, click "New +" → "Web Service"
2. Click "Connect account" if GitHub isn't connected
3. Select your repository: `fis-alpine-analytics`
4. Click "Connect"

**Configure the service:**
- **Name**: `fis-alpine-api`
- **Region**: Same as your database (e.g., Oregon)
- **Branch**: `main`
- **Root Directory**: `fis-api`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Instance Type**: **Free** (spins down after inactivity) OR **Starter** ($7/month, always on)

**Environment Variables** - Click "Add Environment Variable" for each:

| Key | Value | Example |
|-----|-------|---------|
| `DB_HOST` | From Render DB (Internal hostname) | `dpg-xxxxx-a` |
| `DB_PORT` | `5432` | `5432` |
| `DB_USER` | From Render DB | `alpine_analytics` |
| `DB_PASSWORD` | From Render DB | Your password |
| `DB_NAME` | `alpine_analytics` | `alpine_analytics` |
| `CORS_ORIGINS` | `*` (for now, we'll fix later) | `*` |

5. Click "Create Web Service"
6. **Wait 5-10 minutes** for deployment
7. Watch the logs - you'll see:
   ```
   Building...
   Installing dependencies...
   Starting server...
   INFO: Application startup complete.
   ```

8. **Test your API**:
   - Your API URL: `https://fis-alpine-api.onrender.com`
   - Test: https://fis-alpine-api.onrender.com/health
   - Should return: `{"status":"healthy","database":"connected","version":"1.0.0"}`
   - Test endpoint: https://fis-alpine-api.onrender.com/api/v1/leaderboards/Slalom?limit=3

9. **SAVE YOUR API URL**: `https://fis-alpine-api.onrender.com`

---

## Step 3: Deploy Frontend to Vercel (5 minutes)

### 3.1 Create Vercel Account
1. Go to https://vercel.com
2. Click "Sign Up"
3. Choose "Continue with GitHub"
4. Authorize Vercel

### 3.2 Deploy Application

1. Click "Add New..." → "Project"
2. Find and select `fis-alpine-analytics` repository
3. Click "Import"

**Configure the project:**
- **Framework Preset**: Vite (should auto-detect)
- **Root Directory**: `fis-frontend`
- **Build Command**: `npm run build` (auto-filled)
- **Output Directory**: `dist` (auto-filled)
- **Install Command**: `npm install` (auto-filled)

**Environment Variables** - Click "Add" next to Environment Variables:
- **Key**: `VITE_API_BASE_URL`
- **Value**: `https://fis-alpine-api.onrender.com/api/v1`
  (Use your actual Render URL from Step 2)

4. Click "Deploy"
5. **Wait 1-2 minutes** for deployment
6. You'll see:
   ```
   Building...
   Uploading...
   Deploying...
   ✓ Ready!
   ```

7. **Your app is live!**
   - URL: `https://YOUR-PROJECT.vercel.app`
   - Click "Visit" to open it

### 3.3 Test Your Deployed Application

1. Open your Vercel URL
2. Check:
   - [ ] Home page loads
   - [ ] Leaderboards page shows data
   - [ ] Click an athlete - profile loads
   - [ ] Courses page works
   - [ ] Analytics page works
   - [ ] Search works (Cmd+K)

---

## Step 4: Update CORS Configuration (5 minutes)

Now that you have your frontend URL, update the backend to allow it:

1. Go to Render Dashboard
2. Open `fis-alpine-api` service
3. Go to "Environment"
4. Find `CORS_ORIGINS`
5. Update value to: `https://YOUR-PROJECT.vercel.app`
   (Replace with your actual Vercel URL)
6. Click "Save Changes"
7. Service will automatically redeploy (2-3 minutes)

---

## Step 5: Verification & Testing (5 minutes)

### Test Everything:

**Backend**:
- [ ] Health: https://fis-alpine-api.onrender.com/health
- [ ] API Docs: https://fis-alpine-api.onrender.com/docs
- [ ] Leaderboard: https://fis-alpine-api.onrender.com/api/v1/leaderboards/Slalom?limit=3
- [ ] Hot Streak: https://fis-alpine-api.onrender.com/api/v1/leaderboards/hot-streak?limit=5

**Frontend**:
- [ ] Home page loads with data
- [ ] Leaderboards page works
- [ ] Athlete profiles load
- [ ] Charts render correctly
- [ ] Search works
- [ ] No errors in browser console (F12 → Console)

**Mobile**:
- [ ] Open on phone
- [ ] Responsive layout works
- [ ] Touch navigation works

---

## ✅ Success! You're Live!

**Your URLs:**
- **Frontend**: https://YOUR-PROJECT.vercel.app
- **Backend**: https://fis-alpine-api.onrender.com
- **API Docs**: https://fis-alpine-api.onrender.com/docs

---

## Optional: Custom Domain (15 minutes)

### For Frontend (Vercel):
1. Buy domain (Namecheap, Google Domains, etc.)
2. In Vercel: Project → Settings → Domains
3. Add your domain (e.g., `fis-analytics.com`)
4. Follow DNS configuration instructions
5. Wait for DNS propagation (5-60 minutes)

### For Backend (Render):
1. In Render: Service → Settings → Custom Domain
2. Add subdomain (e.g., `api.fis-analytics.com`)
3. Add CNAME record to your DNS:
   - Name: `api`
   - Value: `fis-alpine-api.onrender.com`
4. Wait for verification

---

## Troubleshooting

### "Failed to fetch" error in frontend
- Check browser console for actual error
- Verify `VITE_API_BASE_URL` is set correctly in Vercel
- Verify backend is running (visit health endpoint)
- Check CORS_ORIGINS includes your frontend URL

### Backend shows "Database connection failed"
- Verify all database environment variables are correct
- Check database is running in Render
- Try connecting to database with `psql` to test credentials

### Frontend shows blank page
- Check Vercel deployment logs
- Verify build succeeded
- Check browser console for JavaScript errors
- Verify `dist` folder was created during build

### API is slow on first request
- This is normal for Render Free tier (spins down after 15 min)
- First request wakes it up (takes ~30 seconds)
- Upgrade to Starter plan ($7/month) for always-on

---

## Cost Summary

### Free Tier (Good for testing):
- Render Backend: Free (spins down after inactivity)
- Render Database: Free for 90 days, then $7/month
- Vercel Frontend: Free (100 GB bandwidth)
- **Total**: $0/month for 90 days, then $7/month

### Production Tier (Recommended):
- Render Backend (Starter): $7/month
- Render Database: $7/month
- Vercel Pro: $20/month (optional, only if you need more bandwidth)
- **Total**: $14-34/month

---

## Next Steps After Deployment

1. **Set up monitoring**:
   - Add UptimeRobot for uptime monitoring
   - Set up error tracking with Sentry

2. **Share your app**:
   - Add to portfolio
   - Share on LinkedIn
   - Submit to skiing communities

3. **Gather feedback**:
   - Share with friends
   - Post on Reddit r/skiing
   - Ask for feature requests

4. **Iterate**:
   - Add requested features
   - Optimize performance
   - Expand analytics

---

**Questions?** Check DEPLOYMENT.md for detailed troubleshooting guide.

**Ready to deploy?** Start with Step 1! 🚀
