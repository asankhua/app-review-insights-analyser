# Backend API for Render.com (Docker)
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories and seed sample data (status tiles, View Report)
RUN mkdir -p data/reviews data/reports data/drafts data/deliveries data/logs data/cache
COPY sample_data/pulse-2025-01-01.md data/reports/
RUN python scripts/seed_sample_data.py && \
    python -c "from datetime import datetime; from zoneinfo import ZoneInfo; open('data/logs/last_run.txt','w').write(datetime.now(ZoneInfo('Asia/Kolkata')).isoformat())"

EXPOSE 8000

# Render injects PORT at runtime; default to 8000 for local
# Init: when persistent disk has no reports, seed sample (scheduler upload replaces this)
CMD sh -c 'mkdir -p data/reports data/reviews data/logs && (find data/reports -maxdepth 1 -name "pulse-*.md" 2>/dev/null | grep -q . || (python scripts/seed_sample_data.py && cp sample_data/pulse-2025-01-01.md data/reports/)); uvicorn phase5.api:app --host 0.0.0.0 --port ${PORT:-8000}'
