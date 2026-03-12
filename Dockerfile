# Backend API for Render.com (Docker)
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data/reviews data/reports data/drafts data/deliveries data/logs data/cache

EXPOSE 8000

# Render injects PORT at runtime; default to 8000 for local
CMD sh -c 'uvicorn phase5.api:app --host 0.0.0.0 --port ${PORT:-8000}'
