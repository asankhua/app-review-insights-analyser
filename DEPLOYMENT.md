# Deployment Guide

## Architecture

- **Frontend**: Static HTML/CSS/JS → **Vercel** (recommended) or Docker
- **Backend**: FastAPI → **Railway** (Docker)

---

## 1. Deploy Backend to Railway

### Via Docker

1. Create a new project on [Railway](https://railway.app)
2. Connect your GitHub repo
3. Set **Root Directory** to `.` (project root)
4. Railway will detect the `Dockerfile` and build it
5. Add **Environment Variables** in Railway dashboard:
   - `GROQ_API_KEY`
   - `GEMINI_API_KEY`
   - `EMAIL_SENDER`
   - `EMAIL_PASSWORD`
   - `EMAIL_RECIPIENT`
   - `CORS_ORIGINS` = `https://app-review-insights-analyser.vercel.app` (add after deploying frontend; use your actual Vercel URL)
6. Deploy. **Backend URL:** `https://app-review-insights-analyser-production.up.railway.app`

---

## 2. Deploy Frontend to Vercel

### Option A: Vercel (Recommended – no Docker)

1. Go to [Vercel](https://vercel.com) and import your repo
2. **Root Directory**: Leave as `.` (repo root) — `vercel.json` at root handles the build
3. Add **Environment Variable** (optional — defaults to Railway URL):
   - `API_URL` = `https://app-review-insights-analyser-production.up.railway.app`
4. Deploy. Vercel will run `npm run build` which injects the API URL into the frontend
5. After deploy, copy your Vercel URL (e.g. `https://app-review-insights-analyser.vercel.app`) and add it to Railway's `CORS_ORIGINS`

### Option B: Frontend via Docker (e.g. Railway, Fly.io)

If you prefer to run the frontend in Docker:

```bash
# Build with your Railway API URL
docker build --build-arg API_URL=https://your-api.railway.app -f frontend/Dockerfile frontend/

# Run
docker run -p 80:80 <image>
```

---

## 3. CORS Setup

The backend must allow your frontend origin. In Railway → Variables, add:

```
CORS_ORIGINS=https://app-review-insights-analyser.vercel.app
```

Use your actual Vercel URL (from Vercel dashboard after deploy). Comma-separate for multiple: `https://app.vercel.app,https://custom.com`

---

## 4. Local Development (Combined)

Run both together locally:

```bash
# Terminal 1: Backend
python run_web.py

# Open http://localhost:8000 — serves frontend + API from same origin
```

---

## 5. Local Development (Split – matches production)

```bash
# Terminal 1: Backend
python run_web.py
# API at http://localhost:8000

# Terminal 2: Frontend (serve built static files)
cd frontend && API_URL=http://localhost:8000 npm run build
npx serve public -p 3000
# Open http://localhost:3000
```

Set `CORS_ORIGINS` to include `http://localhost:3000` when testing the split setup.

---

## 6. Syncing UI Changes

The main UI lives in `phase5/static/index.html`. For Vercel, a copy is in `frontend/public/`. After editing the UI, sync:

```bash
./scripts/sync_frontend.sh
```
