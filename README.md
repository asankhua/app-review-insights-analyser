# INDMoney Review Insights Analyzer

Transform Google Play Store reviews into actionable weekly insights — top themes, user quotes, and action ideas — for product, growth, and leadership teams.

The goal is to simulate how Product and Support teams use AI to generate structured internal updates and standardized explanations.

### Who This Helps

| Team | Benefit |
|------|---------|
| **Product / Growth** | Understand what to fix next — prioritised themes from real user feedback |
| **Support** | Know what users are saying and where to acknowledge or escalate |
| **Leadership** | Quick weekly health pulse — scannable one-pager, no manual review digging |

### What You Get

- **Top themes** (max 5) with mention counts — what users care about most
- **Real user quotes** — verbatim feedback grouped by theme
- **Three action ideas** — concrete next steps inferred from reviews
- **One-page weekly pulse** — ≤400 words, ready to share or email

### Essential Points

- **PII-free** — no usernames, emails, or IDs in any output
- **INDMoney focus** — targets `in.indwealth` (Google Play)
- **8 weeks, 100 reviews** — light, fast runs (no 5000-review batch)
- **CLI + Web UI** — run locally, schedule via GitHub Actions, or deploy

---

## URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend (Vercel)** | https://app-review-insights-analyser.vercel.app | Web UI (Run Pipeline, View Report, Send Email) |
| **Backend (Render)** | https://app-review-insights-analyser.onrender.com | FastAPI REST API |
| **Local Web UI** | http://localhost:8000 | Single-page Web UI (`python run_web.py`) |
| **Resend** | https://resend.com | Email API (used on Render free tier; SMTP blocked) |
| **GitHub Gist** | https://gist.github.com | Report storage for View Report on Render free tier |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | / | Web UI (HTML) |
| `GET` | /api/status | Pipeline status (reviews, themes, last run, last synced) |
| `POST` | /api/run | Run full pipeline (Phases 1–4) |
| `GET` | /api/report | Latest weekly pulse (markdown; from Gist when REPORT_GIST_ID set) |
| `POST` | /api/email/send | Send latest report via Resend/SMTP |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.10+, FastAPI, Uvicorn |
| **Frontend** | Static HTML/CSS/JS (vanilla) |
| **AI/LLM** | Groq (themes, classification), Google Gemini (weekly note) |
| **Email** | Resend API (Render) or SMTP (local); DOCX attachment |
| **Hosting** | Render.com (backend), Vercel (frontend) |
| **Scheduler** | GitHub Actions — Sunday **9:00 AM IST** |
| **Report Storage** | GitHub Gist (persistent; Render free tier has ephemeral disk) |

---

## Features

- **Scrape** Google Play Store reviews (INDMoney `in.indwealth`)
- **Discover themes** and classify reviews (Groq LLM)
- **Generate weekly pulse** (Gemini LLM) — themes, quotes, actions
- **Email delivery** — Resend API (deployed) or SMTP (local); Weekly Note attached as DOCX
- **Web UI** — Run pipeline, view report, send email
- **Scheduler** — Weekly run at **9:00 AM IST** every Sunday (GitHub Actions)
- **View Report** — Fetches from GitHub Gist when `REPORT_GIST_ID` set (Render free tier)

---

## Project Structure

```
app-review-insights-analyser/
├── phase1/            # Data Ingestion (scrape reviews)
├── phase2a/           # Theme Discovery (Groq)
├── phase2b/           # Review Classification (Groq)
├── phase3/            # Weekly Note Generation (Gemini)
├── phase4/            # Email Delivery (SMTP)
├── phase5/            # Orchestration, API
│   ├── api.py
│   ├── pipeline.py
│   └── static/        # Static UI (copied to frontend for Vercel)
├── phase6/            # Scheduler (100 reviews, 8 weeks)
├── frontend/          # Frontend for Vercel deployment
│   ├── public/       # Static HTML (build injects API URL)
│   ├── Dockerfile    # Optional: Docker deploy
│   └── vercel.json
├── src/               # Shared config and services
├── main.py            # CLI entry point
├── run_web.py         # Start Web UI server (serves phase5/static locally)
├── Dockerfile         # Backend for Railway
├── .github/workflows/ # GitHub Actions (weekly-pulse.yml)
├── data/              # reviews, reports, drafts, deliveries, cache
└── scripts/           # seed_sample_data.py, etc.
```

---

## Quick Start

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd app-review-insights-analyser
./setup.sh
```

Or manually:

```bash
pip install -r requirements.txt
cp .env.example .env
mkdir -p data/reports data/drafts data/deliveries data/logs data/cache
```

### 2. Configure Environment

Edit `.env`:

```bash
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password   # local SMTP
EMAIL_RECIPIENT=recipient@example.com
# RESEND_API_KEY=re_xxx   # for Render (SMTP blocked on free tier)
```

### 3. Run Locally

**Web UI** (recommended):

```bash
python run_web.py
```

Then open **http://localhost:8000**

**CLI**:

```bash
# Full pipeline (scrape → themes → classify → note → email draft)
python main.py --phase run

# With email send
python main.py --phase run --send --recipient ashishmyweb@gmail.com

# Offline test (no API keys)
python main.py --phase run --mock
```

---

## CLI Commands

| Phase | Command |
|-------|---------|
| Scrape | `python main.py --phase scrape --weeks 8 --count 100` |
| Run all | `python main.py --phase run` |
| Run + send | `python main.py --phase run --send --recipient ashishmyweb@gmail.com` |
| Mock data | `python main.py --phase run --mock` |
| Status | `python main.py --phase status` |

---

## Web UI

1. **Run Pipeline** — Scrape, discover themes, classify, generate weekly pulse (blocked if scheduler ran today)
2. **View Report** — Show latest weekly pulse from Gist; shows "Scheduler/Pipeline already ran today" when sync date is today
3. **Send Email** — Send report via Resend (deployed) or SMTP (local); Weekly Note attached as DOCX
4. **Use previous synced data** — Checkbox: run with mock data; View Report fetches from Gist when checked

**URLs:** http://localhost:8000 (local) | https://app-review-insights-analyser.vercel.app (live)

---

## Phase 6: Scheduler

**Scope:** 100 reviews, 8 weeks. Runs every **Sunday at 9:00 AM IST** (3:30 AM UTC).

| Mode | Command |
|------|---------|
| One-shot | `python -m phase6.scheduler` |
| Daemon | `python -m phase6.daemon` |
| **GitHub Actions** | `.github/workflows/weekly-pulse.yml` — cron `30 3 * * 0` |

**Email:** Sent from Web UI only (scheduler fetches data, no email).

---

## GitHub Actions

Workflow: `.github/workflows/weekly-pulse.yml`

- **Schedule:** Sunday **9:00 AM IST** (3:30 AM UTC)
- **Manual:** Actions → Weekly Pulse → Run workflow

**Secrets (Settings → Secrets and variables → Actions):**

| Secret | Purpose |
|--------|---------|
| `GROQ_API_KEY` | Theme discovery, classification |
| `GEMINI_API_KEY` | Weekly note generation |
| `GH_GIST_TOKEN` | PAT with `gist` scope — upload report to Gist |
| `REPORT_GIST_ID` | Gist ID (auto-created on first run; add to secrets + Render) |
| `RENDER_URL` | Backend URL (optional) |
| `REPORT_UPLOAD_SECRET` | Match Render env (optional) |

**Email:** `EMAIL_SENDER`, `RESEND_API_KEY` (on Render; not in Actions)

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Theme discovery & classification (Phase 2) |
| `GEMINI_API_KEY` | Weekly note generation (Phase 3) |
| `EMAIL_SENDER` | From address (Resend or SMTP) |
| `EMAIL_PASSWORD` | Gmail App Password (local SMTP) |
| `EMAIL_RECIPIENT` | Default email recipient |
| `RESEND_API_KEY` | Resend API (Render free tier; SMTP blocked) |
| `REPORT_GIST_ID` | Gist ID for View Report (Render env) |
| `GH_GIST_TOKEN` | PAT with gist scope (GitHub Secrets, optional on Render) |

---

## Data Flow

```
Play Store → Phase 1 (Scrape) → Phase 2a (Themes) → Phase 2b (Classify) → Phase 3 (Note) → Phase 4 (Email)
```

**Outputs:**

- `data/reviews/YYYY-MM-DD.json` — Scraped reviews
- `data/reports/themes-*.json` — Discovered themes
- `data/reports/grouped_reviews-*.json` — Classified reviews
- `data/reports/pulse-*.md` — Weekly pulse (markdown)
- `data/drafts/*.eml` — Email drafts
- **Email**: Weekly Note attached as `.docx` (DOCX)

---

## Troubleshooting

**Python quit unexpectedly / segfault:** On macOS with system Python, uvloop (used by uvicorn) can crash. The server is configured to use `loop="asyncio"` instead. If issues persist, run: `uvicorn phase5.api:app --loop asyncio --reload --port 8000`

**NumPy/OpenBLAS crash (gemm_thread_n):** On ARM macOS, NumPy’s OpenBLAS can segfault. The app sets `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1` before imports. If it still crashes, try: `OPENBLAS_NUM_THREADS=1 python main.py --phase run --mock`

## Testing

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## Deployment

- **Backend (API)**: Render.com (Docker)
- **Frontend**: Vercel
- **Email**: Resend (Render free tier); DOCX attachment included
- **Report Storage**: GitHub Gist (View Report on Render free tier)

See [DEPLOYMENT.md](DEPLOYMENT.md) for full instructions.

---

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for phase details, dependencies, and design.

---

## License

[Add your license here]
