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

# Create data dirs. Copy repo data to /app/data_repo (mount overlays /app/data at runtime)
RUN mkdir -p data/reviews data/reports data/drafts data/deliveries data/logs data/cache
COPY sample_data/pulse-2025-01-01.md data/reports/
# Bundle repo data for seeding when Render disk is empty (mount overlays image's data/)
COPY data/ /app/data_repo/
RUN python scripts/seed_sample_data.py 2>/dev/null || true

EXPOSE 8000

# Render: seed from repo when mount empty, then start server
CMD sh -c 'mkdir -p data/reports data/reviews data/logs && \
  if ! find data/reports -maxdepth 1 -name "pulse-*.md" 2>/dev/null | grep -q .; then \
    if [ -d /app/data_repo/reports ] && [ -n "$(ls -A /app/data_repo/reports 2>/dev/null)" ]; then \
      cp -r /app/data_repo/reports/* data/reports/ 2>/dev/null || true; \
      cp -r /app/data_repo/logs/* data/logs/ 2>/dev/null || true; \
    else \
      python scripts/seed_sample_data.py 2>/dev/null || true; cp sample_data/pulse-2025-01-01.md data/reports/ 2>/dev/null || true; \
    fi; \
  fi; \
  uvicorn phase5_Orchestration_Web_UI.api:app --host 0.0.0.0 --port ${PORT:-8000}'
