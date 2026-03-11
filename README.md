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

| Environment | URL | Description |
|-------------|-----|-------------|
| **Local Web UI** | http://localhost:8000 | Single-page Web UI (Run Pipeline, View Report, Send Email) |
| **Local API Base** | http://localhost:8000/api | REST API base for status, run, report, email |
| **Live (deployment)** | *Add your deployed URL here* | Deploy to Railway, Render, Fly.io, or any Python host |

### API Endpoints (localhost)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | http://localhost:8000/ | Web UI (HTML) |
| `GET` | http://localhost:8000/api/status | Pipeline status (reviews, themes, report, last synced) |
| `POST` | http://localhost:8000/api/run | Run full pipeline (Phases 1–4) |
| `GET` | http://localhost:8000/api/report | Latest weekly pulse (markdown) |
| `POST` | http://localhost:8000/api/email/send | Send latest report via email |

---

## Features

- **Scrape** Google Play Store reviews (INDMoney `in.indwealth`)
- **Discover themes** and classify reviews (Groq LLM)
- **Generate weekly pulse** (Gemini LLM) — themes, quotes, actions
- **Email delivery** — SMTP with draft/send modes
- **Web UI** — Run pipeline, view report, send email
- **Scheduler** — Weekly run at 9:00 AM IST (Phase 6 + GitHub Actions)

---

## Project Structure

```
app-review-insights-analyser/
├── phase1/           # Data Ingestion (scrape reviews)
├── phase2a/           # Theme Discovery (Groq)
├── phase2b/           # Review Classification (Groq)
├── phase3/            # Weekly Note Generation (Gemini)
├── phase4/            # Email Delivery (SMTP)
├── phase5/            # Orchestration, API, Web UI
│   ├── api.py
│   ├── pipeline.py
│   └── static/index.html
├── phase6/            # Scheduler (100 reviews, 8 weeks)
├── src/               # Shared config and services
├── main.py            # CLI entry point
├── run_web.py         # Start Web UI server
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
EMAIL_PASSWORD=your_gmail_app_password
EMAIL_RECIPIENT=recipient@example.com
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

1. **Run Pipeline** — Scrape, discover themes, classify, generate weekly pulse
2. **View Report** — Show latest weekly pulse (markdown)
3. **Send Email** — Send report to configured recipient  
4. **Use sample data** — Checkbox to run without API keys (mock mode)

**URL:** http://localhost:8000

---

## Phase 6: Scheduler

**Scope:** 100 reviews, 8 weeks. Runs every Sunday at 9:00 AM IST.

| Mode | Command |
|------|---------|
| One-shot | `python -m phase6.scheduler` |
| Daemon | `python -m phase6.daemon` |

**Fixed recipient:** ashishmyweb@gmail.com (in `phase6/config.py`)

---

## GitHub Actions

Workflow: `.github/workflows/weekly-pulse.yml`

- **Schedule:** Sunday 3:30 AM UTC (= 9:00 AM IST)
- **Manual:** Actions → Weekly Pulse → Run workflow

**Secrets (Settings → Secrets and variables → Actions):**

- `GROQ_API_KEY`
- `GEMINI_API_KEY`
- `EMAIL_SENDER`
- `EMAIL_PASSWORD`

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Theme discovery & classification (Phase 2) |
| `GEMINI_API_KEY` | Weekly note generation (Phase 3) |
| `EMAIL_SENDER` | SMTP sender |
| `EMAIL_PASSWORD` | Gmail App Password |
| `EMAIL_RECIPIENT` | Default email recipient |

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

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for phase details, dependencies, and design.

---

## License

[Add your license here]
