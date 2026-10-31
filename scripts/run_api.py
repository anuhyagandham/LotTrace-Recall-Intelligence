"""
Script to launch the LotTrace AI Flask REST API server.
Usage:
    python scripts/run_api.py
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api import app
from config import API_HOST, API_PORT
from src.utils.logging_config import logger

if __name__ == "__main__":
    logger.info(f"Starting LotTrace AI REST API on http://{API_HOST}:{API_PORT}")
    print(f"\n========================================================")
    print(f"  LOTTRACE AI REST API SERVER RUNNING")
    print(f"  URL: http://{API_HOST}:{API_PORT}")
    print(f"  Health Check: http://{API_HOST}:{API_PORT}/api/health")
    print(f"  Dashboard Summary: http://{API_HOST}:{API_PORT}/api/dashboard/summary")
    print(f"========================================================\n")
    app.run(host=API_HOST, port=API_PORT, debug=False)
