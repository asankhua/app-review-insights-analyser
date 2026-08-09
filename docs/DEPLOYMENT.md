# Deployment Guide

## Architecture

- **Backend**: FastAPI → **Render.com** (Docker)
- **Frontend**: Static HTML/CSS/JS → **Vercel**

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
   - **Email (Render free tier):** Add `RESEND_API_KEY` — [resend.com](https://resend.com) → API Keys → Create. Copy the key (starts with `re_`); paste in Render with no extra spaces/newlines. Use `EMAIL_SENDER` (e.g. `onboarding@resend.dev`) and `EMAIL_RECIPIENT` = your Resend account email (testing mode) or a [verified domain](https://resend.com/domains).
   - **Email (local):** Use `EMAIL_SENDER` + `EMAIL_PASSWORD` (SMTP). No Resend needed.
   - **Scheduler → Render sync:** Add `REPORT_UPLOAD_SECRET` (shared with GitHub Secrets) so the scheduler can upload the report.
   - **View Report on Render free tier (no persistent disk):** Use a GitHub Gist for storage. See §7.
   - **Fee section in preview/email:** Add `FEE_EXPLANATION_URL` (fund page, e.g. INDMoney). If the page blocks fetch (403), add `EXIT_LOAD_VALUE` (e.g. `1% if redeemed within 1 year`).
   - **Email attachment:** Weekly Note is attached as DOCX (Resend supports attachments).
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
2. **Root Directory**: Set to `frontend` (recommended) or repo root. If repo root, `vercel.json` builds the frontend.
3. Deploy. **API calls are proxied** via Vercel rewrites (`/api/*` → Render), so no CORS issues.
4. If your Render URL differs, edit `vercel.json` rewrite destination.

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
CORS_ORIGINS=https://app-review-insights-analyser-dx6z.vercel.app
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

## 7. View Report on Render (Gist + Sync Upload)

The scheduler uploads reports to **both** GitHub Gist and the Render backend. For View Report to show the latest synced data:

**GitHub Secrets (workflow uploads to Gist + Render):**
- `GH_GIST_TOKEN` — PAT with `gist` scope (Settings → Developer settings → Tokens)
- `REPORT_GIST_ID` — Gist ID (from first workflow run log)
- `RENDER_URL` — Backend URL, e.g. `https://app-review-insights-analyser.onrender.com` (enables sync to Render)
- `REPORT_UPLOAD_SECRET` — Must match Render env (shared secret for sync)

**Render Environment:**
- `REPORT_GIST_ID` — Gist ID (for fetching when Gist is primary)
- `GH_GIST_TOKEN` — PAT with gist scope (improves Gist fetch reliability)

**Option A: Auto-create Gist** – Run the workflow. The first run creates a Gist and prints the ID:

1. Add `GH_GIST_TOKEN`, `RENDER_URL`, `REPORT_UPLOAD_SECRET` to GitHub Secrets
2. Run workflow (Actions → Weekly Pulse → Run workflow)
3. In the log, find `REPORT_GIST_ID = abc123...` → Add to GitHub Secrets and Render env
4. View Report will show the synced report (from Gist or local when Gist unreachable)

**Option B: Create Gist manually** – [gist.github.com](https://gist.github.com) → New gist → add `pulse.md` and `meta.json` → Create. Copy Gist ID. Add `REPORT_GIST_ID` to GitHub Secrets and Render (still need `GH_GIST_TOKEN` for uploads).

---

## 8. Syncing UI Changes

The main UI lives in `phase5_Orchestration_Web_UI/static/index.html`. For Vercel, a copy is in `frontend/public/`. After editing the UI, sync:

```bash
./scripts/sync_frontend.sh
```

Then redeploy frontend on Vercel (or use Vercel's automatic deploy on push).

