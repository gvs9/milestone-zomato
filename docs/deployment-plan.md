# 🚀 Deployment Plan — Zomato AI Recommender

## Overview

| Component | Platform | URL Pattern |
|-----------|----------|-------------|
| **Backend API** (FastAPI) | Railway | `https://<project>.up.railway.app` |
| **Frontend UI** (Streamlit) | Streamlit Cloud | `https://<app>.streamlit.app` |

> [!IMPORTANT]
> **Why not Vercel for the frontend?**
> Vercel is designed for static sites and serverless functions (Next.js, React, etc.). Streamlit requires a **persistent Python server process** with WebSocket connections, which Vercel does not support. The recommended free deployment for Streamlit apps is **Streamlit Community Cloud** — it's purpose-built, free, and deploys directly from GitHub.
>
> If you specifically need Vercel, the frontend would need to be **rewritten** as a Next.js/React app that calls the FastAPI backend. This is covered in [Appendix A](#appendix-a-vercel-frontend-alternative).

---

## Architecture (Deployed)

```
┌─────────────────────────────────┐       ┌──────────────────────────────────┐
│   Streamlit Community Cloud     │       │         Railway                  │
│                                 │       │                                  │
│   app.py                        │──────▶│   FastAPI (src/main.py)          │
│   (Direct Python import —       │  OR   │   /recommend  /health  /metadata │
│    no API hop needed)           │       │                                  │
│                                 │       │   Groq LLM ◀──▶ Dataset Cache   │
└─────────────────────────────────┘       └──────────────────────────────────┘
```

> **Note**: The Streamlit app currently calls `RecommendationService` directly via Python imports (no HTTP). Both deployment options below work independently — you don't *need* both unless you want to expose the REST API separately.

---

## Part 1: Backend on Railway (FastAPI)

### 1.1 — Prerequisites

- [Railway account](https://railway.app/) (free tier: 500 hours/month)
- GitHub repo pushed (https://github.com/gvs9/milestone-zomato.git)
- Groq API key

### 1.2 — Required Files

#### `Procfile` (NEW — create in project root)
```
web: uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

#### `runtime.txt` (NEW — create in project root)
```
python-3.13.4
```

#### `requirements.txt` (already exists — no changes needed)
Railway auto-detects `requirements.txt` and installs dependencies.

### 1.3 — Deployment Steps

1. **Go to** [railway.app](https://railway.app/) → Sign in with GitHub
2. **Click** "New Project" → "Deploy from GitHub repo"
3. **Select** `gvs9/milestone-zomato`
4. **Add Environment Variables** (Settings → Variables):

   | Variable | Value |
   |----------|-------|
   | `GROQ_API_KEY` | `gsk_your_real_key_here` |
   | `GROQ_MODEL` | `llama-3.3-70b-versatile` |
   | `PORT` | `8000` |
   | `LOG_LEVEL` | `INFO` |
   | `DATASET_NAME` | `ManikaSaini/zomato-restaurant-recommendation` |

5. **Set Start Command** (if Procfile isn't auto-detected):
   ```
   uvicorn src.main:app --host 0.0.0.0 --port $PORT
   ```

6. **Deploy** — Railway will build and start the service
7. **Verify** — visit `https://<your-project>.up.railway.app/docs` for Swagger UI

### 1.4 — Railway Configuration Notes

- **Build**: Railway auto-installs from `requirements.txt`
- **Health Check**: Configure Railway to ping `GET /health` for uptime monitoring
- **Memory**: The dataset loads ~51K restaurants into memory (~80MB). Free tier (512MB) is sufficient.
- **Cold Starts**: First request after idle period takes ~5–10s (dataset download). Subsequent requests are instant.

### 1.5 — Verify Backend

```bash
# Health check
curl https://<your-project>.up.railway.app/health

# Test recommendation
curl -X POST https://<your-project>.up.railway.app/recommend \
  -H "Content-Type: application/json" \
  -d '{"location":"Bangalore","budget":"medium","cuisine":"Italian","min_rating":4.0}'
```

---

## Part 2: Frontend on Streamlit Community Cloud

### 2.1 — Prerequisites

- [Streamlit Cloud account](https://share.streamlit.io/) (free, unlimited public apps)
- GitHub repo pushed

### 2.2 — Deployment Steps

1. **Go to** [share.streamlit.io](https://share.streamlit.io/) → Sign in with GitHub
2. **Click** "New app"
3. **Configure**:

   | Field | Value |
   |-------|-------|
   | Repository | `gvs9/milestone-zomato` |
   | Branch | `main` |
   | Main file path | `app.py` |

4. **Add Secrets** (Advanced settings → Secrets):
   ```toml
   GROQ_API_KEY = "gsk_your_real_key_here"
   GROQ_MODEL = "llama-3.3-70b-versatile"
   DATASET_NAME = "ManikaSaini/zomato-restaurant-recommendation"
   ```

5. **Click "Deploy"** — Streamlit Cloud builds and launches the app

### 2.3 — Streamlit Cloud Configuration Notes

- **Secrets**: Streamlit Cloud uses `secrets.toml` format (different from `.env`). Add secrets via the UI dashboard.
- **Python Version**: Streamlit Cloud uses Python 3.11+ by default. Our code is compatible.
- **Dependencies**: Auto-installed from `requirements.txt`
- **Memory**: Free tier provides 1GB RAM — sufficient for the dataset
- **URL**: Your app will be at `https://<app-name>.streamlit.app`

### 2.4 — Required Code Change for Secrets

Streamlit Cloud loads secrets differently from `.env`. To ensure compatibility, add this to `src/config.py` so it reads from Streamlit secrets when deployed:

```python
# In _load_env_file() or after settings initialization, add:
try:
    import streamlit as st
    if hasattr(st, "secrets"):
        for key in ["GROQ_API_KEY", "GROQ_MODEL", "DATASET_NAME"]:
            if key in st.secrets and key not in os.environ:
                os.environ[key] = st.secrets[key]
except ImportError:
    pass
```

---

## Part 3: Deployment Checklist

### Pre-Deployment

- [ ] Ensure `.env` is in `.gitignore` (✅ already done)
- [ ] Ensure `.env.example` documents all required variables (✅ already done)
- [ ] Ensure no hardcoded API keys in source code
- [ ] All 94 tests pass locally (`pytest tests/ -v`)
- [ ] Create `Procfile` for Railway
- [ ] Create `runtime.txt` for Railway
- [ ] Push latest code to GitHub

### Railway (Backend)

- [ ] Create Railway project from GitHub repo
- [ ] Set all environment variables
- [ ] Verify health endpoint: `GET /health`
- [ ] Verify Swagger docs: `GET /docs`
- [ ] Test recommendation endpoint: `POST /recommend`

### Streamlit Cloud (Frontend)

- [ ] Create Streamlit Cloud app from GitHub repo
- [ ] Set secrets (GROQ_API_KEY, etc.)
- [ ] Verify app loads with sidebar and welcome hero
- [ ] Test full recommendation flow
- [ ] Verify fallback mode works (remove GROQ_API_KEY temporarily)

### Post-Deployment

- [ ] Share public URLs
- [ ] Monitor Railway logs for errors
- [ ] Monitor Streamlit Cloud analytics

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | **Yes** | — | Groq API key from console.groq.com |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | LLM model identifier |
| `MAX_CANDIDATES` | No | `20` | Max restaurants sent to LLM |
| `BUDGET_LOW_MAX` | No | `500` | Upper bound for "low" budget tier (₹) |
| `BUDGET_MEDIUM_MAX` | No | `1500` | Upper bound for "medium" budget tier (₹) |
| `DATASET_NAME` | No | `ManikaSaini/zomato-restaurant-recommendation` | Hugging Face dataset |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `PORT` | No | `8000` | Server port (Railway sets this automatically) |

---

## Cost Estimate

| Service | Plan | Monthly Cost | Limits |
|---------|------|-------------|--------|
| Railway | Free Tier | **$0** | 500 hours/month, 512MB RAM, 1GB disk |
| Streamlit Cloud | Community | **$0** | Unlimited public apps, 1GB RAM |
| Groq API | Free Tier | **$0** | 30 req/min, 14,400 req/day |
| **Total** | | **$0/month** | |

---

## Appendix A: Vercel Frontend Alternative

If you specifically want to use Vercel, the Streamlit frontend must be **rewritten** as a static React/Next.js app that calls the Railway-hosted FastAPI backend via HTTP.

### High-Level Steps

1. **Create a Next.js app** in a `frontend/` directory
2. **Build React components** that mirror the current Streamlit UI (sidebar form, result cards)
3. **Call the FastAPI backend** via `fetch()`:
   ```javascript
   const response = await fetch('https://<railway-url>/recommend', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ location, budget, cuisine, min_rating })
   });
   const data = await response.json();
   ```
4. **Deploy to Vercel** via GitHub integration
5. **Set CORS** on Railway backend to allow the Vercel domain

> **Estimated effort**: 2–3 days to rewrite the frontend in React/Next.js.
> **Recommendation**: Use Streamlit Cloud (free, zero rewrite effort) unless you have a specific reason to need Vercel.

---

*Last updated: August 2026*
