# Netlify Deployment Guide for Nexora AI

## Architecture: Frontend (Netlify) + Backend (Railway/Render)

Netlify serves **static files only** — no Flask, no API keys. You need:

1. **Netlify** → Serves `viser-ai-modern.html` (frontend)
2. **Railway or Render** → Runs `flask_server.py` (backend with API keys, Socket.IO)

The frontend is configured to call your backend URL when hosted on Netlify.

## Setup Steps

### 1. Deploy Flask Backend (Railway or Render)

**Railway:**
1. Sign up at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub → Select your repo
3. Set root directory to repo root (or where `flask_server.py` lives)
4. Add environment variables from `.env.example`
5. Set start command: `python flask_server.py`
6. Copy your public URL (e.g. `https://nexora-xxx.railway.app`)

**Render:**
1. Sign up at [render.com](https://render.com)
2. New Web Service → Connect GitHub repo
3. Build: `pip install -r requirements.txt`
4. Start: `python flask_server.py`
5. Add environment variables
6. Copy your URL (e.g. `https://nexora.onrender.com`)

### 2. Point Frontend to Backend

Edit `viser-ai-modern.html` and replace the placeholder:

```javascript
window.API_BASE = (window.location.hostname.includes('netlify.app') || ...)
    ? 'https://YOUR-BACKEND-URL.railway.app'  // ← Paste your Railway/Render URL here
    : '';
```

### 3. Deploy Frontend to Netlify

Push to your repo. Netlify will deploy the static site. The frontend will call your backend for all API and Socket.IO.

## Important Notes

⚠️ **Netlify serves static files only:**
- No Flask, no API keys on Netlify
- All `/api/*` and Socket.IO requests go to your backend URL

## Option 1: Deploy API Only (Without SocketIO)

If you only need the REST API endpoints:

1. **Set Environment Variables in Netlify Dashboard:**
   - Go to your Netlify site dashboard
   - Navigate to: **Site settings > Environment variables**
   - Add all variables from `.env.example`:
     - `OPENAI_API_KEY`
     - `GROQ_API_KEY`
     - `GEMINI_API_KEY`
     - `OWNER_NAME`
     - `AI_PROVIDER`
     - `EMAIL_ENABLED`
     - `SMTP_SERVER`
     - `SMTP_PORT`
     - `SENDER_EMAIL`
     - `APP_PASSWORD`
     - `OWNER_EMAIL`
     - `DEFAULT_RECIPIENT`
     - And any other variables from `.env.example`

2. **Create Serverless Functions:**
   - Create `netlify/functions/flask-api.py` (see example below)
   - Update `netlify.toml` redirects to point to your function

3. **Deploy:**
   ```bash
   git add .
   git commit -m "Configure for Netlify deployment"
   git push
   ```

## Option 2: Deploy Full App (Recommended: Use Railway/Render)

For full Flask app with SocketIO support:

### Railway Deployment:
1. Sign up at [railway.app](https://railway.app)
2. Create new project from GitHub repo
3. Add environment variables in Railway dashboard
4. Railway auto-detects Flask and deploys

### Render Deployment:
1. Sign up at [render.com](https://render.com)
2. Create new Web Service
3. Connect GitHub repo
4. Set build command: `pip install -r "Core Engine 2.0/requirements.txt"`
5. Set start command: `python flask_server.py`
6. Add environment variables in Render dashboard

## Environment Variables Setup

Copy all variables from `.env.example` and set them in your deployment platform's environment variables section.

## Local Development

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your actual API keys and configuration in `.env`

3. Run locally:
   ```bash
   python flask_server.py
   ```

## Security Notes

- ✅ `.env` is already in `.gitignore` - your secrets won't be committed
- ✅ Never commit actual API keys to the repository
- ✅ Use environment variables for all sensitive data
- ✅ Rotate API keys if they were previously committed
