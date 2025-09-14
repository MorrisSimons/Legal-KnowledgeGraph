#!/usr/bin/env python3
"""
Simple script to initialize the SQLite database
Run this to create the database and tables
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from legal_kg.database import init_database

if __name__ == "__main__":
    print("Initializing Legal Knowledge Graph database...")
    init_database()
    print("Database setup complete!")