# INDMoney Review Insights Analyzer

Transform Google Play Store reviews into actionable weekly insights — top themes, user quotes, and action ideas — for product, growth, and leadership teams.

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

## URLs Reference

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend (Vercel)** | https://app-review-insights-analyser.vercel.app | Web UI (View Report, Preview Email, Send Email) |
| **Backend (Render)** | https://app-review-insights-analyser.onrender.com | FastAPI REST API |
| **API Base** | https://app-review-insights-analyser.onrender.com/api | REST endpoints (status, report, email) |
| **Local Web UI** | http://localhost:8000 | Single-page Web UI (`python run_web.py` or `.venv/bin/python run_web.py`) |
| **Resend** | https://resend.com | Email API (Render free tier; SMTP blocked) |
| **GitHub Gist** | https://gist.github.com | Report storage for View Report (Render free tier) |
| **GitHub Actions** | .github/workflows/weekly-pulse.yml | Scheduler: Sunday 9:00 AM IST |
| **Google Doc** | https://docs.google.com/document/d/18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0/edit?tab=t.0 | Combined weekly pulse + fee explanation (Phase 8 MCP) |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | / | Web UI (HTML) |
| `GET` | /api/status | Pipeline status (reviews, themes, Scheduler Run, Last Email Sent) |
| `GET` | /api/report | Latest weekly pulse (markdown; sample=1 for sample data) |
| `GET` | /api/email/preview | Email preview HTML (sample=1 for sample data) |
| `POST` | /api/email/send | Send latest report via Resend/SMTP |
| `POST` | /api/upload/sync | Scheduler upload (report to backend; secured with REPORT_UPLOAD_SECRET) |

---

## Deployment Architecture

| Layer | Hosting | Notes |
|-------|---------|-------|
| **Backend** | **Render.com** | Docker; FastAPI + Uvicorn |
| **Frontend** | **Vercel** | Static HTML/CSS/JS; `frontend/` root dir |
| **Email** | Resend API | Required on Render (SMTP blocked on free tier) |
| **Report Storage** | GitHub Gist | View Report on Render (ephemeral disk) |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **Frontend** | Static HTML/CSS/JS (vanilla) |
| **AI/LLM** | Groq (themes, classification), Google Gemini (weekly note) |
| **Email** | Resend API (Render) or SMTP (local); DOCX attachment (python-docx) |
| **Hosting** | **Render.com** (backend), **Vercel** (frontend) |
| **Scheduler** | GitHub Actions — Sunday **9:00 AM IST** |
| **Report Storage** | GitHub Gist |
| **Phase 8** | MCP (google-docs-mcp-server) → Google Doc |

---

## Features

- **Scrape** Google Play Store reviews (INDMoney `in.indwealth`)
- **Discover themes** and classify reviews (Groq LLM)
- **Generate weekly pulse** (Gemini LLM) — themes, quotes, actions
- **Email delivery** — Resend API (deployed) or SMTP (local); Weekly Note + Fee section as DOCX attachment
- **Web UI** — View report, preview email, send email
- **Scheduler** — Weekly run at **9:00 AM IST** every Sunday (GitHub Actions)
- **View Report** — From Gist (synced) or sample data (checkbox)
- **Phase 7** — Fee explanation (exit load from FEE_EXPLANATION_URL)
- **Phase 8** — Combined JSON appended to Google Doc via MCP

---

## Phases

| Phase | Name |
|-------|------|
| Phase 1 | Data Ingestion |
| Phase 2a | Theme Discovery |
| Phase 2b | Review Classification |
| Phase 3 | Weekly Note Generation |
| Phase 4 | Email Delivery |
| Phase 5 | Orchestration & Web UI |
| Phase 6 | Scheduler |
| Phase 7 | Fee Explanation |
| Phase 8 | Combined JSON → Google Doc (MCP) |

---

## Project Structure

```
app-review-insights-analyser/
├── phase1_Data_Ingestion/           # Phase 1: Scrape reviews
├── phase2a_Theme_Discovery/        # Phase 2a: Theme Discovery (Groq)
├── phase2b_Review_Classification/  # Phase 2b: Classification (Groq)
├── phase3_Weekly_Note_Generation/   # Phase 3: Weekly Note (Gemini)
├── phase4_Email_Delivery/          # Phase 4: Email (Resend/SMTP)
├── phase5_Orchestration_Web_UI/    # Phase 5: API + Web UI
│   ├── api.py
│   ├── pipeline.py
│   └── static/                    # Static UI (synced to frontend/)
├── phase6_Scheduler/               # Phase 6: GitHub Actions
├── phase7_Fee_Explanation/         # Phase 7: Exit load / fee from URL
├── phase8_Combined_JSON_Google_Doc_MCP/  # Phase 8: MCP → Google Doc
├── frontend/                       # Vercel deployment
│   ├── public/                    # index.html (build injects API_URL)
│   └── vercel.json
├── docs/                           # Documentation
│   ├── DEPLOYMENT.md
│   ├── LOCAL_RUN.md
│   └── MCP_GOOGLE_DOCS_SETUP.md
├── src/
├── main.py
├── run_web.py
├── Dockerfile                      # Backend for Render
├── render.yaml
├── .github/workflows/
└── scripts/
```

---

## Quick Start

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd app-review-insights-analyser
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
mkdir -p data/reports data/drafts data/deliveries data/logs data/cache
```

### 2. Configure Environment

Edit `.env` (see `.env.example`). Required: `GROQ_API_KEY`, `GEMINI_API_KEY`, `EMAIL_SENDER`, `EMAIL_RECIPIENT`. For Render: `RESEND_API_KEY`. For View Report: `REPORT_GIST_ID`, `GH_GIST_TOKEN`.

### 3. Run Locally

```bash
.venv/bin/python run_web.py
```

Then open **http://localhost:8000**

---

## Web UI

1. **View Report** — Latest weekly pulse (from Gist or local). Check "Use sample data" for sample.
2. **Preview Email** — HTML preview (respects sample checkbox).
3. **Send Email** — Send report via Resend (deployed) or SMTP (local); DOCX attached.
4. **Status panel** — Reviews, Themes, Scheduler Run, Last Email Sent, Google Doc (MCP).

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Render + Vercel deployment |
| [docs/LOCAL_RUN.md](docs/LOCAL_RUN.md) | Local development guide |
| [docs/MCP_GOOGLE_DOCS_SETUP.md](docs/MCP_GOOGLE_DOCS_SETUP.md) | Phase 8 MCP setup |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Phase details, design |

---

## License

[Add your license here]
