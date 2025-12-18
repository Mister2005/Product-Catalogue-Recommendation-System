# Deployment Guide

This guide covers deploying the SHL Assessment Recommendation Engine to production using **Vercel** (frontend) and **Render** (backend).

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Part 1: Deploy Backend to Render](#part-1-deploy-backend-to-render)
- [Part 2: Deploy Frontend to Vercel](#part-2-deploy-frontend-to-vercel)
- [Part 3: Post-Deployment Configuration](#part-3-post-deployment-configuration)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

1. **GitHub Repository**: Push your code to GitHub (public or private)
2. **Supabase Project**: Database already set up with tables created
3. **Redis Instance**: Use [Upstash](https://upstash.com) for free managed Redis
4. **API Keys**: Gemini API key ready
5. **Accounts**: Create free accounts on [Render](https://render.com) and [Vercel](https://vercel.com)

---

## Part 1: Deploy Backend to Render

### Step 1: Prepare Backend for Deployment

Create a `render.yaml` file in the project root (optional, for Infrastructure as Code):

```yaml
services:
  - type: web
    name: shl-recommendation-api
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    rootDir: backend
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

### Step 2: Create Web Service on Render

1. Go to [render.com](https://render.com) and sign in
2. Click **New** → **Web Service**
3. Connect your GitHub repository
4. Configure the service:

| Setting | Value |
|---------|-------|
| Name | `shl-recommendation-api` |
| Region | Choose nearest to your users |
| Branch | `main` |
| Root Directory | `backend` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

### Step 3: Configure Environment Variables on Render

In the Render dashboard, go to **Environment** and add:

| Variable | Value |
|----------|-------|
| `SUPABASE_URL` | `https://your-project.supabase.co` |
| `SUPABASE_KEY` | Your Supabase anon key |
| `SUPABASE_DB_PASSWORD` | Your database password |
| `REDIS_URL` | `redis://default:xxx@your-redis.upstash.io:6379` |
| `GEMINI_API_KEY` | Your Gemini API key |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `LOG_LEVEL` | `INFO` |
| `SECRET_KEY` | Generate a secure random string |
| `ALLOWED_ORIGINS` | `https://your-app.vercel.app` (update after Vercel deploy) |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `GEMINI_TEMPERATURE` | `0.7` |
| `GEMINI_MAX_TOKENS` | `2048` |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` |
| `VECTOR_DIMENSION` | `384` |
| `TOP_K_RESULTS` | `10` |
| `DEFAULT_RECOMMENDATION_ENGINE` | `hybrid` |
| `MAX_RECOMMENDATIONS` | `10` |
| `RATE_LIMIT_PER_MINUTE` | `60` |

### Step 4: Deploy

1. Click **Create Web Service**
2. Wait for the build to complete (5-10 minutes for first deploy)
3. Note your backend URL: `https://shl-recommendation-api.onrender.com`

### Step 5: Verify Backend Deployment

Visit these URLs to verify:
- Health check: `https://your-api.onrender.com/health`
- API docs: `https://your-api.onrender.com/docs`

---

## Part 2: Deploy Frontend to Vercel

### Step 1: Prepare Frontend for Deployment

The Next.js frontend is already configured for Vercel deployment. Verify `next.config.js` exists in `frontend-nextjs/`.

### Step 2: Deploy to Vercel

**Option A: Using Vercel Dashboard (Recommended)**

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **Add New** → **Project**
3. Import your GitHub repository
4. Configure the project:

| Setting | Value |
|---------|-------|
| Framework Preset | `Next.js` |
| Root Directory | `frontend-nextjs` |
| Build Command | `npm run build` |
| Output Directory | `.next` |

### Step 3: Configure Environment Variables on Vercel

In the Vercel dashboard, go to **Settings** → **Environment Variables** and add:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://shl-recommendation-api.onrender.com` |

**Important**: Use your actual Render backend URL.

### Step 4: Deploy

1. Click **Deploy**
2. Wait for deployment to complete (2-5 minutes)
3. Note your frontend URL: `https://your-app.vercel.app`

**Option B: Using Vercel CLI**

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to frontend directory
cd frontend-nextjs

# Deploy
vercel

# Follow the prompts:
# - Set up and deploy? Yes
# - Which scope? Select your account
# - Link to existing project? No
# - Project name: shl-recommendation-app
# - Directory: ./
# - Override settings? No
```

---

## Part 3: Post-Deployment Configuration

### Step 1: Update CORS on Render

After deploying to Vercel, update the `ALLOWED_ORIGINS` environment variable on Render:

```
ALLOWED_ORIGINS=https://your-app.vercel.app,https://shl-recommendation-app.vercel.app
```

Then redeploy the Render service.

### Step 2: Verify Full Stack

1. Open your Vercel frontend URL
2. Try getting recommendations
3. Test the AI chatbot
4. Check browser console for any errors

### Step 3: Set Up Custom Domain (Optional)

**Vercel:**
1. Go to **Settings** → **Domains**
2. Add your custom domain
3. Configure DNS as instructed

**Render:**
1. Go to **Settings** → **Custom Domains**
2. Add your API subdomain (e.g., `api.yourdomain.com`)
3. Configure DNS as instructed

---

## Upstash Redis Setup (Free Tier)

If you don't have Redis yet:

1. Go to [upstash.com](https://upstash.com)
2. Sign up for free
3. Create a new Redis database
4. Copy the Redis URL in format: `redis://default:password@endpoint:port`
5. Use this URL for `REDIS_URL` environment variable

---

## Production Checklist

Before going live, verify:

- [ ] Backend health check returns `healthy`
- [ ] Frontend loads without errors
- [ ] Recommendations work correctly
- [ ] Chatbot responds appropriately
- [ ] CORS is configured correctly
- [ ] Environment variables are set (not exposed in client)
- [ ] API keys are kept secret
- [ ] Rate limiting is enabled
- [ ] Database connection is stable

---

## Troubleshooting

### Backend Issues

**Build Fails on Render:**
- Check Python version is 3.11+
- Verify `requirements.txt` is in the `backend/` directory
- Check build logs for missing dependencies

**Database Connection Error:**
- Verify Supabase URL and key are correct
- Check IP allowlist in Supabase (may need to allow all IPs for Render)
- Ensure database tables are created

**Redis Connection Error:**
- Verify Redis URL format is correct
- Check Upstash dashboard for connection details
- Ensure TLS is enabled if required

### Frontend Issues

**Build Fails on Vercel:**
- Check Node.js version (should be 18+)
- Run `npm run build` locally first to catch errors
- Verify all dependencies are in `package.json`

**API Requests Fail:**
- Check `NEXT_PUBLIC_API_URL` is set correctly
- Verify CORS is configured on backend
- Check browser console for specific errors

**502 Bad Gateway:**
- Backend might be cold starting (wait 30 seconds)
- Check Render logs for errors
- Verify start command is correct

### CORS Errors

If you see CORS errors:
1. Verify `ALLOWED_ORIGINS` includes your Vercel URL
2. Include both `https://` prefix and exact domain
3. Redeploy backend after changing environment variables

---

## Cost Estimates

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Render | 750 hours/month (spins down after inactivity) | $7/month (always on) |
| Vercel | 100GB bandwidth, unlimited deploys | $20/month (team features) |
| Supabase | 500MB database, 2GB bandwidth | $25/month (more resources) |
| Upstash | 10,000 commands/day | $0.20/100K commands |

**Note**: Render's free tier spins down after 15 minutes of inactivity, causing ~30 second cold starts.

---

## Alternative: Docker Deployment

For other platforms (AWS, GCP, etc.), use Docker:

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t shl-api ./backend
docker run -p 8000:8000 --env-file .env shl-api
```
