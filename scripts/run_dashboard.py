"""
Script to launch the LotTrace AI Streamlit Business Dashboard.
Usage:
    python scripts/run_dashboard.py
"""

import sys
import subprocess
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
dashboard_entry = BASE_DIR / "dashboard" / "app.py"

if __name__ == "__main__":
    print(f"\n========================================================")
    print(f"  LAUNCHING LOTTRACE AI STREAMLIT BUSINESS DASHBOARD")
    print(f"  Dashboard File: {dashboard_entry}")
    print(f"========================================================\n")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(dashboard_entry),
        "--server.headless=true",
    ]
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nDashboard server terminated by user.")
