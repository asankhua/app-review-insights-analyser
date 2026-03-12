#!/bin/bash
# Sync phase5/static/index.html to frontend/public/ for Vercel deployment
# Run after editing phase5/static/index.html
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cp "$ROOT/phase5/static/index.html" "$ROOT/frontend/public/index.html"
echo "Synced phase5/static/index.html -> frontend/public/index.html"
