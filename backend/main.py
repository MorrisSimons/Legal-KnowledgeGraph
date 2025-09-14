#!/usr/bin/env python3
"""
Legal Knowledge Graph - Main Entry Point
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from legal_kg.database import get_connection, init_database
from legal_kg.models import CrawledPage

def main():
    """Main entry point for the application"""
    print("Legal Knowledge Graph Backend")
    print("=" * 40)
    
    # Initialize database if needed
    init_database()
    
    # Example usage
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if database has data
    cursor.execute("SELECT COUNT(*) FROM crawled_pages")
    count = cursor.fetchone()[0]
    print(f"Database contains {count} crawled pages")
    
    conn.close()

if __name__ == "__main__":
    main()
