# Render Deployment Guide

Complete guide to deploying the Music Recommender MLOps system to Render.

## Overview

This guide walks through deploying both the FastAPI backend and Streamlit frontend to Render's cloud platform.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Code must be in a GitHub repository
3. **AWS S3 Access**: Credentials for DVC data storage
4. **Trained Model**: Models must be available via DVC or included in Docker image

## Architecture

```
┌─────────────────┐
│  Streamlit UI   │ ← User Interface (Port 8501)
│  (Render Web)   │
└────────┬────────┘
         │ HTTP
         ↓
┌─────────────────┐
│   FastAPI API   │ ← Recommendation Engine (Port 8000)
│  (Render Web)   │
└────────┬────────┘
         │ DVC Pull
         ↓
┌─────────────────┐
│   AWS S3 + DVC  │ ← Model Storage (370 MB)
└─────────────────┘
```

## Deployment Methods

### Method 1: Using render.yaml (Recommended)

The easiest way to deploy using the pre-configured `render.yaml` file.

#### Step 1: Connect GitHub Repository

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Blueprint**
3. Connect your GitHub account if not already connected
4. Select the repository: `music-recommender-mlops`
5. Render will automatically detect `render.yaml`

#### Step 2: Configure Environment Variables

Render will create both services but you need to set secrets manually:

**For API Service (`music-recommender-api`):**

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `AWS_ACCESS_KEY_ID` | `<your-key>` | AWS access key for S3/DVC access |
| `AWS_SECRET_ACCESS_KEY` | `<your-secret>` | AWS secret key for S3/DVC access |
| `AWS_DEFAULT_REGION` | `us-east-1` | AWS region (match your S3 bucket) |
| `PORT` | `8000` | API port (auto-set by Render) |

**For UI Service (`music-recommender-ui`):**

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `API_BASE_URL` | `https://<your-api-name>.onrender.com` | URL of deployed API |
| `PORT` | `8501` | Streamlit port (auto-set by Render) |

⚠️ **Important**: Deploy the API first, then set `API_BASE_URL` in the UI service.

#### Step 3: Deploy Services

1. Click **Apply** to create both services
2. API will deploy first (takes ~5-10 minutes)
3. Once API is healthy, copy its URL
4. Update UI's `API_BASE_URL` environment variable
5. UI will automatically redeploy

---

### Method 2: Manual Deployment (Dashboard)

If you prefer step-by-step control:

#### Deploy API Service

1. **Create New Web Service**
   - Dashboard → **New** → **Web Service**
   - Connect GitHub repository
   - Select branch: `main`

2. **Configure Service**
   - Name: `music-recommender-api`
   - Region: Choose closest to your users
   - Branch: `main`
   - Root Directory: Leave blank
   - Environment: **Docker**
   - Dockerfile Path: `./docker/Dockerfile.api`
   - Docker Context: `.`

3. **Select Plan**
   - Free tier: Works but limited (512 MB RAM)
   - **Recommended**: Starter ($7/month, 512 MB RAM)
   - Better: Standard ($25/month, 2 GB RAM) - for production

4. **Environment Variables**
   - Add all variables from table above
   - Mark AWS credentials as **Secret**

5. **Advanced Settings**
   - Health Check Path: `/health`
   - Auto-Deploy: **Yes**

6. **Create Web Service**

#### Deploy Streamlit UI

1. **Create Second Web Service**
   - Repeat steps above but use:
   - Name: `music-recommender-ui`
   - Dockerfile Path: `./docker/Dockerfile.streamlit`

2. **Set API_BASE_URL**
   - Use the deployed API URL from previous step
   - Format: `https://music-recommender-api.onrender.com`

---

## Startup Process (What Happens)

When the API container starts on Render:

1. **Container Build**
   - Docker builds image from `docker/Dockerfile.api`
   - Copies `.dvc/` configuration (not cache)
   - Copies startup script: `start-render.sh`
   - Installs all dependencies

2. **Startup Script Execution** (`start-render.sh`)
   ```bash
   ✅ Verify DVC repository exists
   ✅ Check AWS credentials
   📥 Run: dvc pull -f -v
   📊 Verify model files exist (370 MB)
   🚀 Start: uvicorn src.api.main:app
   ```

3. **Health Check**
   - Render pings `/health` endpoint
   - Service marked healthy when responding

4. **Ready to Serve**
   - API available at: `https://<service-name>.onrender.com`
   - Docs available at: `https://<service-name>.onrender.com/docs`

---

## Troubleshooting Common Issues

### Issue 1: "DVC repository not found"

**Symptom**: Container fails with `.dvc directory not found`

**Cause**: `.dockerignore` was excluding `.dvc/`

**Solution**: ✅ Already fixed in this deployment setup
- `.dockerignore` now allows `.dvc/` (but excludes cache)

---

### Issue 2: "DVC pull fails with AWS credentials error"

**Symptom**:
```
ERROR: failed to pull data from the cloud - ...
```

**Solutions**:
1. Verify AWS credentials are set in Render dashboard
2. Check credentials have S3 read permissions
3. Verify bucket name in `.dvc/config` matches your S3 bucket
4. Check AWS region matches bucket region

**Test AWS credentials locally**:
```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
dvc pull -v
```

---

### Issue 3: "start.sh: No such file or directory"

**Symptom**: Container starts but can't find startup script

**Cause**: Script not copied to image or wrong path

**Solution**: ✅ Already fixed
- Dockerfile copies script: `COPY docker/start-render.sh /app/start-render.sh`
- Made executable: `RUN chmod +x /app/start-render.sh`
- CMD uses absolute path: `CMD ["/app/start-render.sh"]`

---

### Issue 4: "Command not found" or "Unrecognized arguments"

**Symptom**: Render treats chained commands as single command

**Cause**: Using inline `&&` in Render start command field

**Solution**: ✅ Already fixed
- Use shell script instead (`start-render.sh`)
- Dockerfile CMD executes the script properly

---

### Issue 5: Health Check Failing

**Symptom**: Service keeps restarting, shows unhealthy

**Possible Causes**:
1. Models not loaded (DVC pull failed)
2. Port mismatch
3. Service taking too long to start

**Solutions**:
1. Check logs: Dashboard → Service → Logs
2. Verify models downloaded:
   ```
   Look for: ✅ Models found in Docker image
   ```
3. Increase health check timeout in `render.yaml`:
   ```yaml
   healthCheckPath: /health
   healthCheckTimeout: 30  # Add this
   ```

---

### Issue 6: Out of Memory (OOM)

**Symptom**: Service crashes, logs show killed/OOM

**Cause**: Model files (370 MB) + runtime exceeds plan limits

**Solutions**:
1. **Upgrade Plan**: Switch to Standard (2 GB RAM)
2. **Optimize Memory**: Use smaller model or factors
3. **Monitor Usage**: Render dashboard shows memory graph

**Minimum Requirements**:
- Free/Starter (512 MB): Might work but risky
- **Standard (2 GB)**: Recommended for production
- Pro (4 GB+): Best for high traffic

---

### Issue 7: Streamlit Can't Connect to API

**Symptom**: UI loads but shows connection errors

**Causes**:
1. Wrong `API_BASE_URL`
2. API service not healthy
3. CORS issues

**Solutions**:
1. Verify API URL format: `https://music-recommender-api.onrender.com`
2. Test API directly: `curl https://<api-url>/health`
3. Check API logs for CORS errors
4. CORS is enabled in code (already configured)

---

## Monitoring & Logs

### Viewing Logs

1. **Real-time Logs**:
   - Dashboard → Service → Logs
   - Shows startup script output
   - DVC pull progress
   - Uvicorn server logs

2. **Download Logs**:
   - Click **Download** in logs view
   - Useful for debugging

### Health Monitoring

1. **Built-in Metrics** (Render Dashboard):
   - CPU usage
   - Memory usage
   - Response times
   - Request count

2. **Custom Endpoint**:
   - API exposes: `/health`
   - Returns model status:
     ```json
     {
       "status": "healthy",
       "model_loaded": true,
       "model_info": {
         "n_users": 126442,
         "n_artists": 358622,
         "n_factors": 100
       }
     }
     ```

### Prometheus/Grafana Alternative

Since Render free/starter tiers don't support multiple containers, the local Prometheus/Grafana stack won't work.

**Alternatives**:
1. **Render Metrics**: Built-in dashboard (free)
2. **External APM**:
   - Datadog (has free tier)
   - New Relic (has free tier)
   - Sentry (error tracking)

---

## Performance Optimization

### Reduce Build Time

1. **Multi-stage Builds**: Split build/runtime stages
2. **Layer Caching**: Order Dockerfile to maximize cache hits
3. **Exclude Data**: Use `.dockerignore` properly (✅ done)

### Reduce Startup Time

Current startup time breakdown:
- DVC pull: 1-3 minutes (370 MB download)
- Model loading: 5-10 seconds
- Server startup: 2-3 seconds

**Option 1**: Include models in Docker image (slower builds, faster startup)
```dockerfile
# In Dockerfile.api, keep this line:
COPY models/ ./models/
# Skip DVC pull in startup script
```

**Option 2**: Use Render Disk (persistent storage)
- Add Render Disk ($0.25/GB/month)
- Store models on disk
- Only pull once, reuse across deploys

**Option 3**: Current setup (recommended)
- Pull from S3 on each deploy
- Slower startup but always fresh data
- No extra costs

---

## Cost Estimation

### Free Tier
- ✅ 750 hours/month free
- ❌ Services sleep after 15 min inactivity
- ❌ Cold starts (30+ seconds)
- ❌ Limited to 512 MB RAM
- **Use for**: Testing only

### Starter Plan ($7/month per service)
- ✅ No sleeping
- ✅ 512 MB RAM
- ✅ Custom domains
- ⚠️ Might OOM with large models
- **Use for**: Demo/staging

### Standard Plan ($25/month per service)
- ✅ 2 GB RAM (recommended minimum)
- ✅ Faster build times
- ✅ Better performance
- **Use for**: Production

**Total Cost for Production**:
- API (Standard): $25/month
- UI (Starter): $7/month
- **Total**: $32/month

---

## Security Best Practices

### 1. Environment Variables

✅ **DO**:
- Store AWS credentials as secrets
- Use Render's environment variable encryption
- Rotate credentials regularly

❌ **DON'T**:
- Commit credentials to Git
- Hardcode API keys
- Share secrets in plain text

### 2. API Authentication

⚠️ **CRITICAL**: The API currently has NO authentication!

**Before production, implement**:
```python
# src/api/main.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

@app.get("/recommend")
async def recommend(api_key: str = Security(API_KEY_HEADER)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(403, "Invalid API key")
    # ... recommendation logic
```

**Then set in Render**:
- API service: `API_KEY=<random-secure-key>`
- UI service: `API_KEY=<same-key>`

### 3. HTTPS

- ✅ Automatic: Render provides free SSL/TLS
- All services get `https://` URLs
- Update `API_BASE_URL` to use `https://`

---

## Deployment Checklist

Before deploying to production:

- [ ] AWS credentials configured in Render
- [ ] Both services created (API + UI)
- [ ] API_BASE_URL set in UI service
- [ ] Health checks passing
- [ ] Test `/health` endpoint
- [ ] Test `/recommend` endpoint with sample data
- [ ] Verify DVC pull works (check logs)
- [ ] Monitor memory usage for 24 hours
- [ ] Set up alerts for downtime
- [ ] Add API authentication (security)
- [ ] Configure custom domain (optional)
- [ ] Set up monitoring (Datadog/New Relic)
- [ ] Document URLs for professor access

---

## Providing Access to Professor

Once deployed, share:

1. **Streamlit UI URL**: `https://music-recommender-ui.onrender.com`
   - Main interface for testing
   - No login required (public)

2. **API Documentation**: `https://music-recommender-api.onrender.com/docs`
   - Interactive API docs
   - Can test endpoints directly

3. **Health Check**: `https://music-recommender-api.onrender.com/health`
   - Shows system status
   - Verifies model is loaded

**Email Template**:
```
Subject: Music Recommender System - Deployed and Ready

Hi Professor,

The Music Recommender MLOps system is now deployed and accessible:

🎵 Web Interface: https://music-recommender-ui.onrender.com
📖 API Documentation: https://music-recommender-api.onrender.com/docs
💚 Health Check: https://music-recommender-api.onrender.com/health

Features:
- Get personalized music recommendations
- Find similar artists
- Browse top charts
- Mood-based recommendations

Technical Details:
- FastAPI backend with ALS collaborative filtering
- 358K users, 126K artists
- Deployed on Render with DVC for data versioning
- Full CI/CD pipeline with GitHub Actions

Please let me know if you have any questions!

Best regards,
[Your Name]
```

---

## Next Steps After Deployment

1. **Monitor Performance**
   - Check logs daily for first week
   - Watch memory usage
   - Track response times

2. **Add Features**
   - User authentication
   - Recommendation history
   - User feedback collection
   - A/B testing different models

3. **Scale as Needed**
   - Upgrade to Standard plan if needed
   - Add caching (Redis)
   - Implement rate limiting

4. **Documentation**
   - Add architecture diagrams
   - Document API endpoints
   - Create user guide

---

## Rollback Procedure

If deployment fails:

1. **Revert to Previous Deploy**:
   - Dashboard → Service → Deploys
   - Click **Rollback** on last working deploy

2. **Check Logs**:
   - Identify what failed
   - Fix locally
   - Test Docker build locally
   - Push fix and redeploy

3. **Emergency Fallback**:
   - Disable auto-deploy
   - Deploy from specific Git commit
   - Pin to last known good state

---

## Support & Resources

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **DVC Docs**: https://dvc.org/doc
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Streamlit Docs**: https://docs.streamlit.io

---

## Summary

Your deployment is now configured with:

✅ Fixed `.dockerignore` to include DVC config
✅ Production startup script with DVC pull
✅ Updated Dockerfile to copy all necessary files
✅ render.yaml for one-click deployment
✅ Environment variable configuration
✅ Comprehensive error handling
✅ Health check monitoring

**You're ready to deploy!** 🚀

Simply push to GitHub and connect to Render using the Blueprint method.
