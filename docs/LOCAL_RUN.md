# Run locally and test

## 1. One-time setup

```bash
cd /path/to/app-review-insights-analyser

# Create virtual env (recommended)
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Ensure .env exists and has required keys (copy from .env.example if needed).
# Required: GROQ_API_KEY, GEMINI_API_KEY, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT
# Use KEY=value (no spaces around =). Only KEY=VALUE or # comment lines—otherwise dotenv may fail to parse.
```

## 2. Quick test (no API keys for scrape/LLM) — mock run

Uses sample data under `sample_data/`. No Groq/Gemini needed for this test.

```bash
# Seed sample data if not already present
python scripts/seed_sample_data.py

# Run full pipeline with mock data (Phases 1–4 use sample files)
python main.py --phase run --mock
```

You should see phases 1–4 complete and an email **draft** under `data/drafts/` (no email sent).

## 3. Full pipeline (real APIs)

Requires valid `.env`: `GROQ_API_KEY`, `GEMINI_API_KEY`, and email settings.

```bash
# Run pipeline (scrape → themes → classify → note → email draft)
python main.py --phase run --weeks 8 --count 100

# Optional: send email (uses EMAIL_RECIPIENT or override)
python main.py --phase run --send --recipient your@email.com
```

## 4. Web UI (recommended for testing)

Serves the app at **http://localhost:8000** (single page: Run Pipeline, View Report, Send Email).

```bash
python run_web.py
```

Then open **http://localhost:8000** in your browser.

- **Run Pipeline** — runs the full pipeline (or mock if “Use previous synced data” is checked).
- **View Report** — shows latest weekly pulse (from local `data/reports/` or Gist if `REPORT_GIST_ID` is set).
- **Send Email** — sends the latest report via Resend (if `RESEND_API_KEY` set) or SMTP (local).

## 5. Email: easy & free (Brevo recommended)

**Brevo** (free 300 emails/day) — uses SMTP, avoids proxy issues. Recommended when Resend API is blocked.

1. Sign up at [brevo.com](https://www.brevo.com)
2. **Settings → SMTP & API → SMTP** → Create an SMTP key
3. Verify your sender email (or use the one you signed up with)
4. Add to `.env` (comment out `RESEND_API_KEY` if set):
   ```bash
   SMTP_HOST=smtp-relay.brevo.com
   SMTP_PORT=587
   EMAIL_SENDER=your@verified-email.com
   EMAIL_PASSWORD=<your Brevo SMTP key>
   EMAIL_RECIPIENT=recipient@example.com
   ```
5. **Send Email** will use Brevo SMTP.

**Resend** (optional, 100 emails/day) — uses API; can fail behind corporate proxy:
```bash
RESEND_API_KEY=re_xxxx
EMAIL_SENDER=onboarding@resend.dev
EMAIL_RECIPIENT=your@email.com
```

**Gmail SMTP** — use App Password: `SMTP_HOST=smtp.gmail.com`, `EMAIL_SENDER`, `EMAIL_PASSWORD` (16-char app password).

## 6. Optional: Phase 7 and Phase 8

- **Phase 7 (fee in email):** In `.env` set `FEE_EXPLANATION_URL=https://...` (fund page URL). Leave unset to skip. If the fund page blocks automated fetch (403), set `EXIT_LOAD_VALUE=1% if redeemed within 1 year` (or the actual text) so the email and doc still show the exit load and the fund page link.
- **Phase 8 (append to Google Doc):** In `.env` set `GOOGLE_DOC_ID=...` and `GOOGLE_DRIVE_CREDENTIALS_PATH=...` (or `_JSON`). Leave unset to skip.

### Test MCP (Phase 8 Google Doc append)

To run the MCP test and see success/failure on the UI after a pipeline run, add the following to `.env`:

| Variable | Required | Example / note |
|----------|---------|----------------|
| `GOOGLE_DOC_ID` | Yes (for append) | Doc ID or full URL, e.g. `18QNI1O7hYnT4U8VtO7bfuvIIiD819I2tMVL8D2jL7H0` |
| `MCP_GOOGLE_DOCS_USE_MCP` | Yes (for MCP path) | `1` or `true` |
| `MCP_GOOGLE_DOCS_MCP_COMMAND` | Yes (for MCP) | `uvx` or `npx` or path to node/python |
| `MCP_GOOGLE_DOCS_MCP_ARGS` | Optional | `google-docs-mcp-server` (or JSON array) |
| `MCP_GOOGLE_DOCS_SERVICE_ACCOUNT_PATH` | Yes (for MCP server auth) | **Absolute path** to your Google service account JSON file |
| `MCP_GOOGLE_DOCS_SUBJECT_EMAIL` | Yes (domain-wide delegation) | Email of the user to impersonate (e.g. `you@yourdomain.com`) |

1. Create a Google Doc and share it with the **client email** from your service account JSON (e.g. `xxx@yyy.iam.gserviceaccount.com`).
2. Install the MCP server (e.g. `uvx google-docs-mcp-server` or `npx -y google-docs-mcp-server` if available).
3. Run the MCP test from project root: `python scripts/test_mcp.py`. It will append a small test block and print success or the error message.
4. Run the full pipeline; the UI status panel will show **Google Doc (MCP)** with a success or failure message.

**Step-by-step to get real values for the two placeholders:** see [MCP_GOOGLE_DOCS_SETUP.md](MCP_GOOGLE_DOCS_SETUP.md) (create service account, download JSON, set path and subject email, share Doc).

Phase 8 unit tests (no real Doc/MCP): `pytest tests/test_pipeline_integration.py -v -k phase8`

## 7. High-level integration test

Single script that runs: **pipeline → view report → email preview → send path**, plus **Phase 7 (fee)** and **Phase 8 (combined JSON / MCP)**.

```bash
# From project root (needs GEMINI_API_KEY for pipeline Phase 3)
python scripts/run_integration_test.py
```

Or run the pytest integration tests (same flow; some tests skip if keys are missing):

```bash
pytest tests/test_pipeline_integration.py -v -m integration
```

- Step 1: seeds sample data.
- Step 2: runs `main.py --phase run --mock` (Phase 3 needs `GEMINI_API_KEY`).
- Steps 3–5: view report, email preview, send-email API.
- Step 6: Phase 7 fee (skipped if `FEE_EXPLANATION_URL` unset).
- Step 7: Phase 8 combined JSON (and optional Google Doc / MCP if configured).

## 8. Troubleshooting

- **“No themes file found” / “No classified reviews”** — Run without `--mock` once (with real API keys), or run `python scripts/seed_sample_data.py` and use `--mock`.
- **Email not sending (local):** Use Gmail App Password in `EMAIL_PASSWORD`, not your normal password.
- **Port 8000 in use:** Edit `run_web.py` and change `port=8000` to another port (e.g. `8001`).
- **Integration test fails at “Running pipeline”:** Set `GEMINI_API_KEY` in `.env` so Phase 3 can generate the report.
- **"Python-dotenv could not parse statement":** Use `KEY=value` in `.env` (no spaces around `=`). Use `GH_GIST_TOKEN=...` and `REPORT_GIST_ID=...` for Gist (not free-form lines).
