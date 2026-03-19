# INDMoney Review Insights Analyzer
https://github.com/user-attachments/assets/3f503e21-58d6-4d36-be59-a09c2f3e3845
Transform Google Play Store reviews into actionable weekly insights — top themes, user quotes, action ideas, and fee explainer — for product, growth, support, and leadership teams.

---

## Live URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend (Vercel)** | https://app-review-insights-analyser-dx6z.vercel.app | Web UI: View Report, Preview Email, Send Email |
| **Backend (Render)** | https://app-review-insights-analyser.onrender.com | FastAPI REST API (Docker) |
| **API Base** | https://app-review-insights-analyser.onrender.com/api | REST endpoints |
| **Health Check** | https://app-review-insights-analyser.onrender.com/api/health | Lightweight liveness probe |
| **Debug (Fee Config)** | https://app-review-insights-analyser.onrender.com/api/debug/fee | Verify FEE_EXPLANATION_URL / EXIT_LOAD_VALUE on Render |
| **Resend** | https://resend.com | Email delivery (used on Render; SMTP blocked on free tier) |
| **GitHub Gist** | https://gist.github.com | Report storage for View Report (Render has ephemeral disk) |
| **Google Doc** | [Combined Report](https://docs.google.com/document/d/18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0/edit?tab=t.0) | Phase 8 MCP appends weekly pulse + fee |
| **GitHub Actions** | .github/workflows/weekly-pulse.yml | Scheduler: Sunday 9:00 AM IST |
| **Local Web UI** | http://localhost:8000 | Run `python run_web.py` |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **Frontend** | Static HTML/CSS/JS (vanilla, no framework) |
| **AI/LLM** | Groq (theme discovery, classification), Google Gemini (weekly note generation) |
| **Email** | Resend API (Render) or SMTP (local); DOCX attachment (python-docx) |
| **Scraping** | google-play-scraper |
| **Hosting** | Render.com (backend), Vercel (frontend) |
| **Scheduler** | GitHub Actions — Sunday 9:00 AM IST |
| **Report Storage** | GitHub Gist (persistent; Render free tier has ephemeral disk) |
| **Phase 8** | MCP (google-docs-mcp-server) → append combined JSON to Google Doc |

---

## Third-Party Services

| Service | Purpose | Required For |
|---------|---------|--------------|
| **Render.com** | Hosts backend (FastAPI + Uvicorn). Docker deploy. Free tier: ephemeral disk, SMTP blocked. | Backend API, status, report fetch, email send |
| **Vercel** | Hosts frontend. Static HTML/CSS/JS. Proxies `/api/*` to Render. | Web UI |
| **Resend** | Email API. Used on Render because SMTP ports are blocked on free tier. | Send Email (deployed) |
| **GitHub Gist** | Stores `pulse.md` + `meta.json` from scheduler. Backend fetches for View Report when `REPORT_GIST_ID` set. | View Report on Render |
| **Groq** | LLM for theme discovery and review classification (llama-3.3-70b-versatile). | Phases 2a, 2b |
| **Google Gemini** | LLM for weekly note generation (gemini-1.5-flash). | Phase 3 |
| **MCP (Google Docs)** | Appends combined weekly pulse + fee explanation to a Google Doc via `append_text` tool. | Phase 8 (optional) |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web UI (HTML) |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/status` | Pipeline status (reviews, themes, Scheduler Run, Last Email Sent, Fee, MCP) |
| `GET` | `/api/report` | Latest weekly pulse (markdown; `?sample=1` for sample data) |
| `GET` | `/api/email/preview` | Email preview HTML |
| `POST` | `/api/email/send` | Send latest report via Resend/SMTP (DOCX attached) |
| `GET` | `/api/email/send-status` | Poll send result |
| `POST` | `/api/upload/sync` | Scheduler upload (secured with `X-Upload-Secret`) |
| `GET` | `/api/debug/fee` | Debug fee config (no secrets) |

---

## External APIs Used

| API | Base URL / Docs | Auth | Purpose | Phase |
|-----|-----------------|------|---------|-------|
| **Groq** | https://console.groq.com, https://api.groq.com | `GROQ_API_KEY` (Bearer) | Theme discovery, review classification (llama-3.3-70b-versatile) | 2a, 2b |
| **Google Gemini** | https://ai.google.dev, https://generativelanguage.googleapis.com | `GEMINI_API_KEY` | Weekly note generation (gemini-1.5-flash) | 3 |
| **Resend** | https://api.resend.com | `RESEND_API_KEY` (Bearer) | Send email with DOCX attachment | 4 |
| **GitHub Gist** | https://api.github.com/gists | `GH_GIST_TOKEN` (Bearer) or none (public) | Fetch/create/update `pulse.md` + `meta.json` for View Report | 5, scripts |
| **Google Docs** | https://docs.googleapis.com | Service account (JSON) | Append combined report to Google Doc (Phase 8 fallback) | 8 |
| **Google Play** | Via google-play-scraper (no official API) | None | Scrape app reviews | 1 |
| **HTTP fetch** | `FEE_EXPLANATION_URL` (configurable) | None | Fetch fund page HTML for exit load (Phase 7) | 7 |

---

## Features

- **Scrape** Google Play Store reviews (INDMoney `in.indwealth`)
- **Discover themes** and classify reviews (Groq LLM)
- **Generate weekly pulse** (Gemini LLM) — themes, quotes, actions
- **Fee explanation** (Phase 7) — exit load from `FEE_EXPLANATION_URL`; fallback with `EXIT_LOAD_VALUE` when fetch blocked
- **Email delivery** — Resend API (deployed) or SMTP (local); Weekly Note + Fee section in body and DOCX attachment
- **Web UI** — View report, preview email, send email
- **Scheduler** — Weekly run at 9:00 AM IST (GitHub Actions)
- **View Report** — From Gist (synced) or sample data (checkbox)
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

## Environment Variables (Reviewer Reference)

| Variable | Purpose | Where |
|----------|---------|-------|
| `GROQ_API_KEY` | Groq LLM (themes, classification) | GitHub Secrets, Render |
| `GEMINI_API_KEY` | Gemini (weekly note) | GitHub Secrets, Render |
| `EMAIL_SENDER` | From address | .env, Render |
| `EMAIL_RECIPIENT` | Default recipient | .env, Render |
| `RESEND_API_KEY` | Resend API (required on Render) | Render |
| `REPORT_GIST_ID` | Gist ID for View Report | GitHub Secrets, Render |
| `GH_GIST_TOKEN` | PAT with `gist` scope (classic) | GitHub Secrets, Render |
| `RENDER_URL` | Backend URL for sync upload | GitHub Secrets |
| `REPORT_UPLOAD_SECRET` | Shared secret for sync | GitHub Secrets, Render |
| `FEE_EXPLANATION_URL` | Fund page URL for fee section | Render |
| `EXIT_LOAD_VALUE` | Fallback exit load when fetch fails | Render |
| `GOOGLE_DOC_ID` | Target Google Doc (Phase 8) | .env, Render |
| `MCP_GOOGLE_DOCS_USE_MCP` | Use MCP for Phase 8 | .env |

---

## Project Structure

```
app-review-insights-analyser/
├── phase1_Data_Ingestion/           # Scrape Google Play reviews
├── phase2a_Theme_Discovery/         # Groq theme discovery
├── phase2b_Review_Classification/   # Groq classification
├── phase3_Weekly_Note_Generation/   # Gemini weekly note
├── phase4_Email_Delivery/           # Resend/SMTP + DOCX
├── phase5_Orchestration_Web_UI/    # FastAPI + pipeline + static UI
├── phase6_Scheduler/               # GitHub Actions (Phases 1–3)
├── phase7_Fee_Explanation/          # Exit load from FEE_EXPLANATION_URL
├── phase8_Combined_JSON_Google_Doc_MCP/  # MCP → Google Doc
├── frontend/                       # Vercel deploy (public/index.html)
├── src/                            # Shared config, models, services
├── docs/                           # DEPLOYMENT, LOCAL_RUN, MCP setup
├── scripts/                        # upload_sync, seed_sample_data, sync_frontend
├── main.py                         # CLI entry
├── run_web.py                      # Web server
├── Dockerfile                      # Render backend
├── render.yaml                     # Render config
└── .github/workflows/weekly-pulse.yml
```

---

## Quick Start

```bash
git clone <repo-url>
cd app-review-insights-analyser
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# Edit .env: GROQ_API_KEY, GEMINI_API_KEY, EMAIL_SENDER, EMAIL_RECIPIENT
mkdir -p data/reports data/drafts data/deliveries data/logs data/cache
.venv/bin/python run_web.py
```

Open **http://localhost:8000**

---

## Web UI

1. **View Report** — Latest weekly pulse (from Gist or local). Check "Use sample data" for sample.
2. **Preview Email** — HTML preview (respects sample checkbox).
3. **Send Email** — Send report via Resend (deployed) or SMTP (local); DOCX attached.
4. **Status panel** — Reviews, Themes, Scheduler Run, Last Email Sent, Fee (email/doc), Google Doc (MCP).

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Render + Vercel deployment |
| [docs/LOCAL_RUN.md](docs/LOCAL_RUN.md) | Local development |
| [docs/MCP_GOOGLE_DOCS_SETUP.md](docs/MCP_GOOGLE_DOCS_SETUP.md) | Phase 8 MCP setup |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Phase details, design, API |

---

## Recent Changes

- **Fee explainer** — Included in email body and DOCX; sanitized `FEE_EXPLANATION_URL` / `EXIT_LOAD_VALUE`; `EXIT_LOAD_VALUE` fallback when fetch blocked.
- **Gist 401** — Token sanitization; retry without auth for public Gists.
- **Debug endpoint** — `GET /api/debug/fee` to verify fee config on Render.
- **UI status** — Fee (Configured / Not set) shown in status panel.
