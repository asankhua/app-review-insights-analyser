# Backend API for Render.com (Docker)
# Frontend: Vercel (frontend/). Backend: Render. See docs/DEPLOYMENT.md
# Required env vars on Render: GROQ_API_KEY, GEMINI_API_KEY, EMAIL_SENDER, EMAIL_RECIPIENT,
#   RESEND_API_KEY, CORS_ORIGINS, REPORT_UPLOAD_SECRET, REPORT_GIST_ID, GH_GIST_TOKEN
FROM python:3.11-slim

WORKDIR /app

# Install dependencies (includes python-docx for email attachment)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories and seed sample data (View Report fallback)
RUN mkdir -p data/reviews data/reports data/drafts data/deliveries data/logs data/cache
COPY sample_data/pulse-2025-01-01.md data/reports/
RUN python scripts/seed_sample_data.py 2>/dev/null || true && \
    python -c "from datetime import datetime; from zoneinfo import ZoneInfo; open('data/logs/last_run.txt','w').write(datetime.now(ZoneInfo('Asia/Kolkata')).isoformat())"

EXPOSE 8000

# Render: PORT injected at runtime. Init: seed sample if no pulse (scheduler upload replaces)
CMD sh -c 'mkdir -p data/reports data/reviews data/logs && (find data/reports -maxdepth 1 -name "pulse-*.md" 2>/dev/null | grep -q . || (python scripts/seed_sample_data.py 2>/dev/null || true && cp sample_data/pulse-2025-01-01.md data/reports/)); uvicorn phase5_Orchestration_Web_UI.api:app --host 0.0.0.0 --port ${PORT:-8000}'
