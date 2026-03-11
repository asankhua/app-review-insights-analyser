#!/usr/bin/env python3
"""Start the Phase 5 Web UI server.
Usage: python run_web.py
Then open http://localhost:8000
"""
# Reduce OpenBLAS threads before any heavy imports (avoids segfault on ARM macOS)
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*OpenSSL.*LibreSSL.*")

import uvicorn
import sys
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

if __name__ == "__main__":
    uvicorn.run(
        "phase5.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        loop="asyncio",  # Avoid uvloop segfaults on macOS
    )
