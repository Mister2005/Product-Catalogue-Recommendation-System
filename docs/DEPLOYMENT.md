# Deployment Guide

This guide covers deploying the SHL Assessment Recommendation Engine to production environments.

---

## Table of Contents

- [Overview](#overview)
- [Deployment Options](#deployment-options)
- [Backend Deployment (Render)](#backend-deployment-render)
- [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
- [Database Setup (Supabase)](#database-setup-supabase)
- [Cache Setup (Redis/Upstash)](#cache-setup-redisupstash)
- [Environment Variables](#environment-variables)
- [Post-Deployment](#post-deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Overview

The application consists of three main components:

1. **Backend API** (FastAPI) → Deploy to Render
2. **Frontend** (Next.js) → Deploy to Vercel
3. **Database** (PostgreSQL) → Managed by Supabase
4. **Cache** (Redis) → Optional, use Upstash free tier

**Recommended Stack**:
- Backend: Render (Free tier: 512MB RAM, auto-sleep after 15 min)
- Frontend: Vercel (Free tier: Unlimited bandwidth)
- Database: Supabase (Free tier: 500MB storage, 2GB bandwidth)
- Cache: Upstash (Free tier: 10K commands/day)

**Total Cost**: $0/month (free tiers) or $7/month (Render paid tier for no cold starts)

---

## Deployment Options

### Option 1: Free Tier (Recommended for Development)

| Service | Platform | Cost | Limitations |
|---------|----------|------|-------------|
| Backend | Render Free | $0 | 512MB RAM, cold starts after 15 min |
| Frontend | Vercel Free | $0 | Unlimited bandwidth |
| Database | Supabase Free | $0 | 500MB storage, 2GB bandwidth/month |
| Cache | Upstash Free | $0 | 10K commands/day |

### Option 2: Production (Recommended for Production)

| Service | Platform | Cost | Benefits |
|---------|----------|------|----------|
| Backend | Render Starter | $7/month | 512MB RAM, no cold starts |
| Frontend | Vercel Pro | $20/month | Advanced analytics, more bandwidth |
| Database | Supabase Pro | $25/month | 8GB storage, 50GB bandwidth |
| Cache | Upstash Pro | $10/month | 1M commands/day |

---

## Backend Deployment (Render)

### Prerequisites

1. GitHub account with repository
2. Render account ([render.com](https://render.com))
3. Environment variables ready (see [Environment Variables](#environment-variables))

### Step 1: Prepare Repository

```bash
# Ensure all changes are committed
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### Step 2: Create Render Service

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml` blueprint
5. Click **"Apply"** to use the blueprint

### Step 3: Configure Environment Variables

In Render dashboard, add these environment variables:

**Required**:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key
- `GEMINI_API_KEY`: Your Google Gemini API key
- `HUGGINGFACE_API_KEY`: Your HuggingFace API token
- `ALLOWED_ORIGINS`: Your frontend URL (e.g., `https://product-catalogue-recommendation-sy.vercel.app`)

**Optional**:
- `REDIS_URL`: Upstash Redis URL (recommended for better performance)

**Auto-Generated**:
- `SECRET_KEY`: Render will generate this automatically

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait for build to complete (~5-10 minutes)
3. Render will run health checks
4. Service will be live at `https://shl-recommendation-api-30oz.onrender.com`

### Step 5: Verify Deployment

```bash
# Test health endpoint
curl https://shl-recommendation-api-30oz.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-12-19T...",
  "version": "2.0.0",
  "environment": "production"
}
```

---

## Frontend Deployment (Vercel)

### Prerequisites

1. Vercel account ([vercel.com](https://vercel.com))
2. Backend deployed and URL available

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Deploy

```bash
cd frontend-nextjs

# Login to Vercel
vercel login

# Deploy
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: shl-recommendation-frontend
# - Directory: ./
# - Override settings? No
```

### Step 3: Set Environment Variable

```bash
# Add backend URL
vercel env add NEXT_PUBLIC_API_URL production

# Enter value: https://shl-recommendation-api-30oz.onrender.com
```

### Step 4: Redeploy with Environment Variable

```bash
vercel --prod
```

### Step 5: Update Backend CORS

Update `ALLOWED_ORIGINS` in Render dashboard to include your Vercel URL:
```
https://product-catalogue-recommendation-sy.vercel.app
```

---

## Database Setup (Supabase)

### Step 1: Create Project

1. Go to [supabase.com](https://supabase.com)
2. Click **"New Project"**
3. Choose organization and region
4. Set database password (save this!)
5. Wait for project to be created (~2 minutes)

### Step 2: Run SQL Setup

1. Go to **SQL Editor** in Supabase dashboard
2. Create new query
3. Copy contents of `data/SUPABASE_SQL_SETUP_SIMPLE.sql`
4. Run the query

This creates:
- `assessments` table with all fields
- `embedding` column for vector search
- Indexes for performance

### Step 3: Migrate Data

```bash
cd data
python migrate_to_supabase_simple.py
```

This will:
- Load 518 assessments from JSON
- Generate embeddings using HuggingFace API
- Insert into Supabase
- Verify migration

### Step 4: Verify Data

```bash
python ../scripts/verify_supabase_migration.py
```

Expected output:
```
✅ Connected to Supabase
📊 Assessments in database: 517/518 (99.8%)
✅ Embeddings found: 517/517 assessments have embeddings
```

---

## Cache Setup (Redis/Upstash)

### Option 1: Upstash (Recommended)

1. Go to [upstash.com](https://upstash.com)
2. Create account
3. Click **"Create Database"**
4. Choose region closest to your Render deployment
5. Copy **REST URL** (not Redis URL)
6. Add to Render as `REDIS_URL`

### Option 2: Skip Redis

The application works without Redis, but:
- Responses will be slower
- No caching of recommendations
- Higher database load

To skip Redis:
- Don't set `REDIS_URL` environment variable
- Backend will detect and skip Redis initialization

---

## Environment Variables

### Backend (Render)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SUPABASE_URL` | ✅ | Supabase project URL | `https://abc.supabase.co` |
| `SUPABASE_KEY` | ✅ | Supabase anon key | `eyJhbG...` |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key | `AIza...` |
| `HUGGINGFACE_API_KEY` | ✅ | HuggingFace token | `hf_...` |
| `ALLOWED_ORIGINS` | ✅ | Frontend URL for CORS | `https://app.vercel.app` |
| `REDIS_URL` | ⚠️ | Redis connection URL | `redis://...` |
| `SECRET_KEY` | Auto | Auto-generated | - |
| `ENVIRONMENT` | Auto | Set to `production` | `production` |
| `DEBUG` | Auto | Set to `false` | `false` |
| `LOG_LEVEL` | Auto | Logging level | `INFO` |

### Frontend (Vercel)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend API URL | `https://api.onrender.com` |

---

## Post-Deployment

### 1. Test All Endpoints

```bash
# Health check
curl https://shl-recommendation-api-30oz.onrender.com/health

# Get recommendations
curl -X POST https://shl-recommendation-api-30oz.onrender.com/api/v1/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Software Engineer",
    "required_skills": ["Python"],
    "engine": "hybrid"
  }'

# List assessments
curl https://shl-recommendation-api-30oz.onrender.com/api/v1/assessments?limit=5

# API documentation
open https://shl-recommendation-api-30oz.onrender.com/docs
```

### 2. Test All Engines

Test each recommendation engine:
- `hybrid` (default)
- `gemini`
- `rag`
- `nlp`
- `clustering`

### 3. Monitor Performance

- **Cold Start**: First request after 15 min inactivity: ~30-60s
- **Warm Requests**: Subsequent requests: <2s
- **Memory Usage**: Should stay under 400MB

### 4. Set Up Monitoring

**Render Dashboard**:
- Monitor memory usage
- Check error logs
- Set up alerts for downtime

**Health Check Cron**:
Keep service warm by pinging `/health` every 10 minutes:

```bash
# Use a service like cron-job.org or UptimeRobot
GET https://shl-recommendation-api-30oz.onrender.com/health
```

---

## Monitoring

### Application Logs

**Render**:
- Go to your service dashboard
- Click "Logs" tab
- View real-time logs

**Log Levels**:
- `INFO`: Normal operations
- `WARNING`: Non-critical issues
- `ERROR`: Critical errors

### Performance Metrics

**Render Dashboard**:
- CPU usage
- Memory usage
- Request count
- Response times

**Custom Monitoring**:
- Set up Sentry for error tracking
- Use Prometheus for metrics
- Configure alerts for downtime

---

## Troubleshooting

### Build Fails

**Issue**: Build fails during `pip install`

**Solutions**:
1. Check Python version is 3.11
2. Verify all dependencies in `requirements.txt`
3. Check build logs for specific errors
4. Ensure `render.yaml` is correct

### Health Check Fails

**Issue**: Health check endpoint returns 503

**Solutions**:
1. Wait 2-3 minutes for initial startup
2. Check environment variables are set
3. Review application logs for errors
4. Verify Supabase connection

### Slow Response Times

**Issue**: API responses take >10 seconds

**Solutions**:
1. **Cold Start**: Normal for first request after inactivity
   - Solution: Set up cron job to keep warm
2. **Missing Redis**: Responses slower without caching
   - Solution: Add Upstash Redis
3. **Database Slow**: Supabase queries taking too long
   - Solution: Check indexes, optimize queries

### Memory Issues

**Issue**: Service crashes with "Out of Memory"

**Solutions**:
1. Render free tier: 512MB RAM limit
2. Backend uses lazy loading to minimize memory
3. Upgrade to paid tier ($7/month for 2GB RAM)
4. Optimize model loading

### CORS Errors

**Issue**: Frontend can't connect to backend

**Solutions**:
1. Add frontend URL to `ALLOWED_ORIGINS`
2. Include `https://` in URL
3. Restart backend service after changing env vars

### HuggingFace API Errors

**Issue**: Embedding generation fails

**Solutions**:
1. Verify `HUGGINGFACE_API_KEY` is set
2. Check API key is valid
3. Ensure rate limits not exceeded
4. Check HuggingFace API status

---

## Scaling

### Horizontal Scaling

**Render**:
- Upgrade to paid tier
- Add more instances
- Use load balancer

**Vercel**:
- Automatically scales
- No configuration needed

### Database Scaling

**Supabase**:
- Upgrade to Pro plan
- Increase connection pool
- Add read replicas

### Cache Scaling

**Upstash**:
- Upgrade plan for more commands
- Use Redis cluster for high availability

---

## Security Checklist

- [ ] All environment variables set securely
- [ ] `DEBUG=false` in production
- [ ] `SECRET_KEY` is strong and unique
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] HTTPS enforced
- [ ] Database credentials secured
- [ ] API keys not exposed in frontend

---

## Cost Optimization

### Free Tier Strategy

1. **Backend**: Render free tier with cold starts
2. **Frontend**: Vercel free tier
3. **Database**: Supabase free tier
4. **Cache**: Upstash free tier or skip Redis

**Total**: $0/month

### Production Strategy

1. **Backend**: Render Starter ($7/month) - no cold starts
2. **Frontend**: Vercel free tier (sufficient)
3. **Database**: Supabase free tier (upgrade if needed)
4. **Cache**: Upstash free tier (upgrade if needed)

**Total**: $7/month

---

## Backup and Recovery

### Database Backups

**Supabase**:
- Automatic daily backups (Pro plan)
- Point-in-time recovery (Pro plan)
- Manual backups via SQL export

### Code Backups

**GitHub**:
- All code in version control
- Tag releases for easy rollback
- Use branches for staging

---

## CI/CD Pipeline

### Automatic Deployment

**Render**:
- Auto-deploys on push to `main` branch
- Can configure branch-specific deployments

**Vercel**:
- Auto-deploys on push to `main`
- Preview deployments for PRs

### Manual Deployment

```bash
# Backend (Render)
git push origin main  # Triggers auto-deploy

# Frontend (Vercel)
vercel --prod
```

---

## Support

For deployment issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Review application logs
3. Check service status pages
4. Open GitHub issue

---

**Last Updated**: December 2025  
**Version**: 2.0.0
