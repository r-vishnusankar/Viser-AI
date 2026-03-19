# Deploy Nexora: Render (Backend) + Netlify (Frontend)

## Architecture

- **Render**: Flask API (`flask_server.py`)
- **Netlify**: Static frontend (`viser-ai-modern.html`)

---

## Step 1: Render (Backend)

### 1.1 Create Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. **New** → **Web Service**
3. Connect your repo (Nexora.ai)
4. Configure:
   - **Name**: `nexora-api` (or your choice)
   - **Root Directory**: (leave empty if repo root has `flask_server.py`)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python flask_server.py` (or `gunicorn` if you add it for production)
   - **Instance Type**: Free (or paid)

### 1.2 Environment Variables (Render)

In **Environment** → **Environment Variables**, add:

| Key | Value |
|-----|-------|
| `OPENAI_API_KEY` | `sk-...` |
| `GROQ_API_KEY` | `gmx_...` |
| `USERS_CONFIG_JSON` | See below |

### 1.3 Enable Login (USERS_CONFIG_JSON)

Set `USERS_CONFIG_JSON` to a JSON string. Example (escape quotes for env var):

```
{"password":"Valoriz@123","users":[{"email":"vishnu.sankar@valoriz.com","name":"Vishnu Sankar","workspace":"qa"},{"email":"aju.joseph@valoriz.com","name":"Aju Joseph","workspace":"hr"},{"email":"shilpa.s.nair@valoriz.com","name":"Shilpa S Nair","workspace":"hr"},{"email":"joel.antony@valoriz.com","name":"Joel Antony","workspace":"ba"}]}
```

**Tip**: In Render, paste the JSON as-is. If you get errors, try escaping: wrap in single quotes and escape inner double quotes.

### 1.4 Note Your Render URL

After deploy, you'll get a URL like: `https://nexora-api.onrender.com`

---

## Step 2: Netlify (Frontend)

### 2.1 Deploy Site

1. Go to [Netlify Dashboard](https://app.netlify.com)
2. **Add new site** → **Import an existing project**
3. Connect your repo
4. Configure:
   - **Base directory**: (leave empty or set if needed)
   - **Build command**: (leave empty for static)
   - **Publish directory**: `/` or `.` (where `viser-ai-modern.html` lives)

### 2.2 Set API URL

The frontend must call your Render API. Edit `viser-ai-modern.html`:

Find (around line 3906):
```javascript
window.API_BASE = (window.location.hostname.includes('netlify.app') || ...)
    ? 'https://viser-ai.onrender.com'
    : '';
```

**Change** `https://viser-ai.onrender.com` to **your Render URL** (e.g. `https://nexora-api.onrender.com`).

### 2.3 Custom Domain (Optional)

- Netlify: Add custom domain in **Domain settings**
- If you use a custom domain, update the `hostname.includes()` check if needed, or add your domain

---

## Step 3: CORS

The Flask app uses `CORS(app)` which allows all origins. For production, you can restrict:

In `flask_server.py`:
```python
CORS(app, origins=["https://your-site.netlify.app", "https://yourdomain.com"])
```

---

## Step 4: Verify

1. Open your Netlify URL
2. You should see the **login page** (if `USERS_CONFIG_JSON` is set)
3. Log in with: `vishnu.sankar@valoriz.com` / `Valoriz@123`
4. Test chat, uploads, etc.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Still shows Guest | `USERS_CONFIG_JSON` not set or invalid JSON on Render |
| API calls fail | Check `API_BASE` in HTML matches your Render URL |
| CORS errors | Ensure `CORS(app)` or add your Netlify domain |
| 503 on login | Auth config not loaded – check Render env vars and logs |
