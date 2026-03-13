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
   - **View Report on Render free tier (no persistent disk):** Use a GitHub Gist for storage. See §7.
   - **Google Doc link in email:** Add `GOOGLE_DRIVE_CREDENTIALS_JSON` (service account JSON as string) to get a "View in Google Docs" link. See §8.
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

## 7. View Report on Render Free Tier (GitHub Gist)

Render's free tier has ephemeral storage—uploaded reports are lost on restart. Use a **GitHub Gist** for persistent storage (free, no upgrade).

**Requirement:** `GITHUB_TOKEN` cannot create Gists. Create a **Personal Access Token (PAT)** with `gist` scope:

1. GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. **Generate new token** → enable **gist** → Generate
3. Add to **GitHub Secrets**: `GH_GIST_TOKEN` = your PAT

**Option A: Auto-create** – Run the workflow. The first run creates a Gist and prints the ID:

1. Add `GH_GIST_TOKEN` to GitHub Secrets (see above)
2. Run workflow (Actions → Weekly Pulse → Run workflow)
3. In the log, find `REPORT_GIST_ID = abc123...`
4. Add to **GitHub Secrets**: `REPORT_GIST_ID` = that value
5. Add to **Render** env: `REPORT_GIST_ID` = Gist ID only (e.g. `abc123def456`, not the full URL)
6. (Optional) Add `GH_GIST_TOKEN` to Render too—improves fetch reliability
7. View Report will show the synced report

**Option B: Create Gist manually** – [gist.github.com](https://gist.github.com) → New gist → add `pulse.md` and `meta.json` → Create. Copy Gist ID. Add `REPORT_GIST_ID` to GitHub Secrets and Render (still need `GH_GIST_TOKEN` for uploads).

---

## 8. Google Doc Link (Optional)

To add a "View in Google Docs" button to the email (so recipients open it as a Google Doc):

1. **Google Cloud Console** → Create project → Enable **Drive API**
2. **APIs & Services** → **Credentials** → **Create Service Account** → Download JSON key
3. Add to **Render** env: `GOOGLE_DRIVE_CREDENTIALS_JSON` = minified JSON content (or use `GOOGLE_DRIVE_CREDENTIALS_PATH` for file path)
4. The email will include a "View in Google Docs" link; the DOCX is still attached as fallback.

---

## 9. Syncing UI Changes

The main UI lives in `phase5/static/index.html`. For Vercel, a copy is in `frontend/public/`. After editing the UI, sync:

```bash
./scripts/sync_frontend.sh
```
