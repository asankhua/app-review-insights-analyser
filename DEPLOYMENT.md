# Deployment Guide

## Architecture

- **Frontend**: Static HTML/CSS/JS → **Vercel** (recommended) or Docker
- **Backend**: FastAPI → **Render.com** (Docker)

---

## 1. Deploy Backend to Render.com

### Via Docker (Blueprint)

1. Go to [Render](https://render.com) → **New** → **Blueprint**
2. Connect your GitHub repo
3. Render will detect `render.yaml` and create the web service
4. Add **Environment Variables** in the Dashboard (secrets from `.env`):
   - `GROQ_API_KEY`
   - `GEMINI_API_KEY`
   - `EMAIL_SENDER`
   - `EMAIL_RECIPIENT`
   - `CORS_ORIGINS` = `https://your-frontend.vercel.app` (add after deploying frontend)
   - **Email (Render free tier):** Add `RESEND_API_KEY` — [resend.com](https://resend.com) free tier, works on Render (SMTP blocked). Use `EMAIL_SENDER` with a [verified domain](https://resend.com/domains).
   - **Email (local):** Use `EMAIL_SENDER` + `EMAIL_PASSWORD` (SMTP). No Resend needed.
   - **Scheduler → Render sync:** Add `REPORT_UPLOAD_SECRET` (shared with GitHub Secrets) so the scheduler can upload the report.
5. Deploy. **Backend URL:** `https://app-review-insights-analyser.onrender.com`

### Via Docker (Manual)

1. **New** → **Web Service**
2. Connect repo, set **Environment** to **Docker**
3. **Dockerfile Path**: `./Dockerfile` (or leave default if Dockerfile is at root)
4. Add the same environment variables as above
5. Deploy

---

## 2. Deploy Frontend to Vercel

### Option A: Vercel (Recommended)

1. Go to [Vercel](https://vercel.com) and import your repo
2. **Root Directory**: Set to `frontend` (recommended — avoids Python auto-detection). If using repo root, `vercel.json` sets `installCommand` to build the frontend.
3. Add **Environment Variable**:
   - `API_URL` = `https://app-review-insights-analyser.onrender.com` (optional; this is the default)
4. Deploy. Vercel runs `npm run build` which injects the API URL into the frontend
5. Copy your Vercel URL and add it to Render's `CORS_ORIGINS`

### Option B: Frontend via Docker

If you prefer to run the frontend in Docker (e.g. on Render, Fly.io):

```bash
# Build with your Render API URL
docker build --build-arg API_URL=https://app-review-insights-analyser.onrender.com -f frontend/Dockerfile frontend/

# Run
docker run -p 80:80 <image>
```

---

## 3. CORS Setup

The backend must allow your frontend origin. In Render → Environment, add:

```
CORS_ORIGINS=https://app-review-insights-analyser.vercel.app
```

Use your actual Vercel URL. Comma-separate for multiple: `https://app.vercel.app,https://custom.com`

---

## 4. Local Development (Combined)

Run both together locally:

```bash
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
