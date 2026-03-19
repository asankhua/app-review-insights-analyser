#!/bin/bash
# Sync phase5_Orchestration_Web_UI/static/index.html to frontend/public/ for Vercel deployment
# Run after editing phase5_Orchestration_Web_UI/static/index.html
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cp "$ROOT/phase5_Orchestration_Web_UI/static/index.html" "$ROOT/frontend/public/index.html"
echo "Synced phase5_Orchestration_Web_UI/static/index.html -> frontend/public/index.html"
