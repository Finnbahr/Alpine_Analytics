# Deployment Guide

Complete guide to deploy the FIS Alpine Analytics application to production.

## Overview

- **Backend**: FastAPI → Render or Railway
- **Frontend**: React → Vercel or Netlify
- **Database**: Your existing PostgreSQL instance (needs to be accessible from the internet)

## Prerequisites

1. GitHub account
2. Account on deployment platforms (Render/Railway for backend, Vercel/Netlify for frontend)
3. PostgreSQL database accessible from the internet (or use a managed database service)

---

## Option 1: Quick Deploy (Recommended)

### Step 1: Prepare Repository

```bash
# Navigate to project root
cd "/Users/finnbahr/Desktop/FIS Scraping"

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit: FIS Alpine Analytics"

# Create GitHub repository and push
gh repo create fis-alpine-analytics --public --source=. --push
# Or manually create on GitHub and:
git remote add origin https://github.com/YOUR_USERNAME/fis-alpine-analytics.git
git push -u origin main
```

### Step 2: Deploy Backend to Render

1. Go to [https://render.com](https://render.com) and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `fis-alpine-api`
   - **Region**: Choose closest to your database
   - **Branch**: `main`
   - **Root Directory**: `fis-api`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free or Starter
5. Add Environment Variables:
   - `DB_HOST`: Your PostgreSQL host
   - `DB_PORT`: Your PostgreSQL port (default: 5432)
   - `DB_USER`: Your database user
   - `DB_PASSWORD`: Your database password
   - `DB_NAME`: alpine_analytics
   - `CORS_ORIGINS`: https://YOUR-FRONTEND-URL.vercel.app
6. Click "Create Web Service"
7. Wait for deployment (3-5 minutes)
8. **Save your API URL**: `https://fis-alpine-api.onrender.com`

### Step 3: Deploy Frontend to Vercel

1. Go to [https://vercel.com](https://vercel.com) and sign in
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `fis-frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add Environment Variable:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://fis-alpine-api.onrender.com/api/v1`
6. Click "Deploy"
7. Wait for deployment (1-2 minutes)
8. **Your app is live!** `https://YOUR-PROJECT.vercel.app`

### Step 4: Update CORS

1. Go back to Render dashboard
2. Open your backend service
3. Go to "Environment"
4. Update `CORS_ORIGINS`:
   ```
   https://YOUR-PROJECT.vercel.app
   ```
5. Click "Save Changes" (service will redeploy)

---

## Option 2: Deploy with Railway (Backend)

### Deploy Backend

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Navigate to backend
cd "/Users/finnbahr/Desktop/FIS Scraping/fis-api"

# Initialize and deploy
railway init
railway up

# Add environment variables
railway variables set DB_HOST=your-db-host
railway variables set DB_PORT=5432
railway variables set DB_USER=your-db-user
railway variables set DB_PASSWORD=your-db-password
railway variables set DB_NAME=alpine_analytics
railway variables set CORS_ORIGINS=https://your-frontend.vercel.app

# Get your deployment URL
railway domain
```

---

## Option 3: Deploy with Netlify (Frontend)

### Deploy Frontend

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Navigate to frontend
cd "/Users/finnbahr/Desktop/FIS Scraping/fis-frontend"

# Build
npm run build

# Deploy
netlify deploy --prod --dir=dist

# Add environment variable via Netlify UI:
# Site settings > Environment variables > Add a variable
# Key: VITE_API_BASE_URL
# Value: https://your-backend-url.com/api/v1
```

---

## Database Configuration

### Option A: Use Existing Database (Local PostgreSQL)

**Warning**: Your local database needs to be accessible from the internet. This requires:
1. Port forwarding on your router
2. Static IP or dynamic DNS
3. Firewall configuration
4. **Not recommended for production**

### Option B: Managed PostgreSQL (Recommended)

#### Render PostgreSQL

1. In Render dashboard, click "New +" → "PostgreSQL"
2. Name: `fis-alpine-db`
3. Choose plan (Free tier available)
4. Click "Create Database"
5. Copy connection details
6. **Migrate your data**:
   ```bash
   # Export from local
   pg_dump -h 127.0.0.1 -p 5433 -U alpine_analytics alpine_analytics > backup.sql

   # Import to Render (use connection string from Render)
   psql postgresql://user:pass@host/dbname < backup.sql
   ```

#### Railway PostgreSQL

```bash
railway add postgresql
railway variables
# Note down the DATABASE_URL
```

#### Neon (Serverless Postgres)

1. Go to [https://neon.tech](https://neon.tech)
2. Create new project
3. Get connection string
4. Import data

---

## Verification Checklist

After deployment, verify everything works:

### Backend
- [ ] Health check: `https://your-api.com/health`
- [ ] API docs: `https://your-api.com/docs`
- [ ] Test endpoint: `https://your-api.com/api/v1/leaderboards/Slalom?limit=5`

### Frontend
- [ ] Site loads: `https://your-frontend.com`
- [ ] Navigation works
- [ ] Leaderboards page loads data
- [ ] Athlete profile loads (click on any athlete)
- [ ] Courses page works
- [ ] Analytics page works
- [ ] Search works (Cmd+K or Ctrl+K)

### Integration
- [ ] No CORS errors in browser console
- [ ] All API calls succeed
- [ ] Images/icons load correctly

---

## Troubleshooting

### Backend Issues

**Error: Connection refused**
- Check database host is accessible
- Verify database credentials
- Check firewall rules

**Error: CORS policy**
- Add frontend URL to `CORS_ORIGINS` environment variable
- Format: `https://your-domain.com` (no trailing slash)

**Error: Module not found**
- Check `requirements.txt` includes all dependencies
- Verify build command ran successfully

### Frontend Issues

**Error: Failed to fetch**
- Verify `VITE_API_BASE_URL` is set correctly
- Check backend is deployed and accessible
- Open browser DevTools → Network tab to see actual error

**Error: 404 on refresh**
- Vercel: `vercel.json` should be present (already created)
- Netlify: `netlify.toml` should be present (already created)

**Blank page**
- Check browser console for errors
- Verify build completed successfully
- Check environment variables are set

---

## Environment Variables Reference

### Backend (fis-api)

| Variable | Example | Required |
|----------|---------|----------|
| DB_HOST | db.example.com | Yes |
| DB_PORT | 5432 | Yes |
| DB_USER | alpine_analytics | Yes |
| DB_PASSWORD | your_password | Yes |
| DB_NAME | alpine_analytics | Yes |
| CORS_ORIGINS | https://app.vercel.app | Yes |
| API_TITLE | FIS Alpine Analytics API | No |
| API_VERSION | 1.0.0 | No |

### Frontend (fis-frontend)

| Variable | Example | Required |
|----------|---------|----------|
| VITE_API_BASE_URL | https://api.example.com/api/v1 | Yes |

---

## Cost Estimates

### Free Tier (Recommended for testing)

- **Render**: Free (spins down after inactivity, 90 sec startup time)
- **Vercel**: Free (100 GB bandwidth/month)
- **Database**: Use existing local OR Render free tier (90 days)

**Total**: $0/month (with limitations)

### Production Tier

- **Render Starter**: $7/month (always on, better performance)
- **Vercel Pro**: $20/month (team features, more bandwidth)
- **Database (Render)**: $7/month (2 GB storage)

**Total**: ~$34/month

### Scalable Tier

- **Render Standard**: $25/month
- **Vercel Pro**: $20/month
- **Database (Render)**: $20/month (10 GB)

**Total**: ~$65/month

---

## Custom Domain (Optional)

### Frontend

**Vercel**:
1. Go to Project Settings → Domains
2. Add your domain
3. Follow DNS configuration instructions

**Netlify**:
1. Site settings → Domain management
2. Add custom domain
3. Configure DNS

### Backend

**Render**:
1. Service → Settings → Custom Domain
2. Add your domain (e.g., `api.yourdomain.com`)
3. Configure DNS (CNAME record)

---

## Monitoring & Maintenance

### Render
- View logs: Dashboard → Service → Logs
- Monitor metrics: Dashboard → Service → Metrics
- Set up alerts: Dashboard → Service → Settings → Notifications

### Vercel
- Analytics: Project → Analytics
- Function logs: Project → Deployments → [deployment] → Function Logs
- Real User Monitoring available on Pro plan

### Health Checks

Set up uptime monitoring:
- [UptimeRobot](https://uptimerobot.com) (free)
- [Pingdom](https://www.pingdom.com)
- [Better Uptime](https://betteruptime.com)

Monitor endpoints:
- Backend: `https://your-api.com/health`
- Frontend: `https://your-app.com`

---

## Next Steps

After successful deployment:

1. **Set up CI/CD**: Auto-deploy on git push (already configured by Vercel/Render)
2. **Add analytics**: Google Analytics, Plausible, or Fathom
3. **Set up error tracking**: Sentry for backend and frontend
4. **Implement rate limiting**: Protect your API
5. **Add authentication**: If needed for admin features
6. **Database backups**: Schedule regular backups
7. **SSL/HTTPS**: Automatic with Vercel/Render

---

## Support

If you encounter issues:

1. Check deployment logs
2. Verify environment variables
3. Test API endpoints directly
4. Check browser console for frontend errors
5. Review this guide's troubleshooting section

---

**Last Updated**: February 14, 2026
