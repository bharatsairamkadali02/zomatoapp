"""
Main Runner for 3-Tier Application
Starts Tier 3 (Database), launches Tier 2 (Application), and serves Tier 1 (Web).
"""
import os
import sys

# Ensure root directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db
from application.app import app

if __name__ == "__main__":
    print("=" * 60)
    print("[*] Starting 3-Tier Multi-Role Zomato Application")
    print("=" * 60)
    print("1. [Tier 3: Database] Initializing Database Schema...")
    init_db()

    print("2. [Tier 2: Application] Starting Flask Backend API...")
    print("3. [Tier 1: Web] Serving Web UI on Port 8000...")
    print("=" * 60)
    print("[*] Open in your browser: http://localhost:8000 (or http://127.0.0.1:8000)")
    print("[*] Available Path Routes: /home , /cart , /orders , /login , /signup")
    print("=" * 60)

    app.run(host="0.0.0.0", port=8000, debug=True)
