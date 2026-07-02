# Deployment Guide

This guide covers deploying the AI Knowledge Assistant to production using Vercel (frontend) and Render (backend).

## Prerequisites

- GitHub account with the project repository
- Vercel account (free tier available)
- Render account (free tier available)
- PostgreSQL database (Render provides managed PostgreSQL)
- Ollama running locally or on a separate server for AI inference

## Architecture Overview

```
┌─────────────┐         ┌─────────────┐         ┌──────────────┐
│   Vercel    │  HTTPS  │   Render    │  HTTPS  │   Render DB  │
│  (Frontend) │◄────────►│  (Backend)  │◄────────►│  PostgreSQL  │
│  Next.js    │         │   FastAPI   │         │              │
└─────────────┘         └─────────────┘         └──────────────┘
                                │
                                │ HTTP
                                ▼
                        ┌─────────────┐
                        │   Ollama    │
                        │   (Local)   │
                        └─────────────┘
```

## Step 1: Deploy Backend to Render

### 1.1 Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Authorize Render to access your repository

### 1.2 Deploy Using render.yaml

1. Push your code to GitHub
2. In Render dashboard, click "New +"
3. Select "Web Service"
4. Connect your GitHub repository
5. Render will automatically detect the `render.yaml` file
6. Review the configuration and click "Deploy Web Service"

### 1.3 Configure Environment Variables

Render will automatically create a PostgreSQL database based on your `render.yaml`. The `DATABASE_URL` will be automatically injected.

You need to manually set these environment variables in the Render dashboard:

```bash
# Required
JWT_SECRET_KEY=your-strong-random-secret-key-min-32-chars
FERNET_SECRET_KEY=your-fernet-secret-key-32-bytes

# CORS - Replace with your Vercel frontend URL
BACKEND_CORS_ORIGINS=["https://your-frontend.vercel.app"]

# Optional - If using external Ollama
OLLAMA_BASE_URL=http://your-ollama-server:11434
```

### 1.4 Run Database Migrations

After the backend is deployed:

1. Go to your Render web service
2. Click "Shell" in the sidebar
3. Run:
```bash
cd /opt/render/project/src
alembic upgrade head
```

### 1.5 Note the Backend URL

After deployment, Render will provide a URL like:
```
https://ai-knowledge-assistant-backend.onrender.com
```

Copy this URL - you'll need it for the frontend configuration.

## Step 2: Deploy Frontend to Vercel

### 2.1 Create Vercel Account

1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Authorize Vercel to access your repository

### 2.2 Deploy Frontend

1. In Vercel dashboard, click "Add New Project"
2. Select your GitHub repository
3. Navigate to the `frontend` folder
4. Vercel will automatically detect Next.js
5. Configure the project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### 2.3 Configure Environment Variables

In Vercel project settings → Environment Variables, add:

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-backend.onrender.com/api/v1
```

Replace with your actual Render backend URL from Step 1.5.

### 2.4 Deploy

Click "Deploy". Vercel will build and deploy your frontend.

### 2.5 Note the Frontend URL

After deployment, Vercel will provide a URL like:
```
https://ai-knowledge-assistant.vercel.app
```

## Step 3: Update Backend CORS

1. Go to your Render backend service
2. Navigate to "Environment"
3. Update `BACKEND_CORS_ORIGINS`:
```bash
BACKEND_CORS_ORIGINS=["https://your-frontend.vercel.app"]
```
4. Redeploy the service

## Step 4: Configure Ollama (AI Inference)

### Option A: Local Ollama (Development/Personal Use)

1. Install Ollama on your local machine
2. Pull required models:
```bash
ollama pull llama3
ollama pull mistral
```
3. Ensure Ollama is accessible from your Render backend (requires port forwarding or VPN)

### Option B: Cloud Ollama (Production)

For production, consider:
- Running Ollama on a separate VPS (e.g., DigitalOcean, AWS EC2)
- Using a managed AI service (OpenAI, Anthropic) via the `LLM_PROVIDER` setting

To use a cloud Ollama instance:

1. Update Render environment variable:
```bash
OLLAMA_BASE_URL=http://your-ollama-server-ip:11434
```

2. Update `ENFORCE_LOCAL_ONLY_AI=false` in backend config if needed

## Step 5: Verify Deployment

### Check Backend Health

```bash
curl https://your-backend.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "production"
}
```

### Check Frontend

1. Open your Vercel frontend URL
2. You should see the landing page
3. Try logging in/registering
4. Upload a document and test chat functionality

## Step 6: Configure Custom Domains (Optional)

### Frontend (Vercel)

1. In Vercel project → Settings → Domains
2. Add your custom domain
3. Follow DNS instructions provided by Vercel

### Backend (Render)

1. In Render service → Settings → Custom Domains
2. Add your custom domain
3. Follow DNS instructions provided by Render

4. Update CORS in Render environment variables:
```bash
BACKEND_CORS_ORIGINS=["https://your-custom-domain.com"]
```

## Step 7: Monitor and Scale

### Monitoring

- **Render**: View logs in the Render dashboard
- **Vercel**: View logs in the Vercel dashboard
- **Database**: Monitor PostgreSQL metrics in Render dashboard

### Scaling

**Render (Backend)**:
- Free tier: 512MB RAM, 0.1 CPU
- Upgrade to Standard/Pro for more resources
- Add horizontal scaling with multiple instances

**Vercel (Frontend)**:
- Free tier: 100GB bandwidth/month
- Pro tier: Unlimited bandwidth, faster builds
- Edge functions for global distribution

## Troubleshooting

### Backend Issues

**Database Connection Errors**:
- Verify `DATABASE_URL` is correctly set
- Check PostgreSQL is running
- Ensure SSL is enabled in production

**CORS Errors**:
- Verify `BACKEND_CORS_ORIGINS` includes your frontend URL
- Check frontend URL is HTTPS (required for cookies)

**Ollama Connection Errors**:
- Verify `OLLAMA_BASE_URL` is accessible
- Check Ollama is running
- Ensure firewall allows connection

### Frontend Issues

**API Connection Errors**:
- Verify `NEXT_PUBLIC_API_BASE_URL` is correct
- Check backend is running and accessible
- Verify CORS is configured correctly

**Build Errors**:
- Check environment variables are set in Vercel
- Verify all dependencies are in `package.json`

## Security Checklist

- [ ] Change all default secret keys
- [ ] Enable HTTPS (automatic on Vercel/Render)
- [ ] Configure CORS to only allow your domains
- [ ] Enable SSL for PostgreSQL (automatic in Render)
- [ ] Set strong password for database
- [ ] Disable API docs in production (automatic)
- [ ] Enable rate limiting (already configured)
- [ ] Monitor logs for suspicious activity
- [ ] Regular security updates

## Cost Estimates

**Free Tier**:
- Vercel: $0/month (100GB bandwidth)
- Render: $0/month (512MB RAM, 0.1 CPU)
- Render PostgreSQL: $0/month (90 days, then $7/month)
- Total: $0/month (first 90 days), then ~$7/month

**Recommended Production**:
- Vercel Pro: $20/month
- Render Standard: $25/month
- Render PostgreSQL: $7/month
- Total: ~$52/month

## Next Steps

After deployment:
1. Set up monitoring and alerting
2. Configure backup strategy for database
3. Set up CI/CD pipeline
4. Implement logging aggregation (e.g., Sentry, LogRocket)
5. Configure CDN for static assets
6. Set up analytics (e.g., Google Analytics)
