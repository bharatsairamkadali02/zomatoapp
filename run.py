"""
Tier 2 — Application Server Runner
====================================
Starts the Flask REST API (Tier 2) and initializes the database schema (Tier 3).

Usage on App Server EC2:
    export ALLOWED_ORIGIN=http://<TIER1_WEB_SERVER_IP>
    export SECRET_KEY=your_strong_secret_key
    python run.py
"""
import os
import sys

# Ensure root directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db
from application.app import app

if __name__ == "__main__":
    print("=" * 60)
    print("[*] Starting 3-Tier Zomato Application — App Server (Tier 2)")
    print("=" * 60)
    print("1. [Tier 3: Database] Initializing AWS RDS MySQL Schema...")
    init_db()

    print("2. [Tier 2: App Server] Starting Flask REST API on Port 5000...")
    print("=" * 60)
    print("[*] Tier 1 (Web Server) should point config.js API_BASE to this machine.")
    print(f"[*] ALLOWED_ORIGIN = {os.getenv('ALLOWED_ORIGIN', '* (dev mode — restrict in production!)')}")
    print("[*] API Base: http://0.0.0.0:5000")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=False)
