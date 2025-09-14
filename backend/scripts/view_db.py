#!/usr/bin/env python3
"""
Simple script to view database contents
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from legal_kg.database import get_connection

def view_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Show tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database:")
    for table in tables:
        print(f"  - {table[0]}")
    
    print("\n" + "="*50)
    
    # Show crawled_pages data
    cursor.execute("SELECT COUNT(*) FROM crawled_pages")
    count = cursor.fetchone()[0]
    print(f"Total crawled pages: {count}")
    
    if count > 0:
        cursor.execute("SELECT id, url, domain, title, crawled_at FROM crawled_pages LIMIT 5")
        rows = cursor.fetchall()
        print("\nFirst 5 records:")
        for row in rows:
            print(f"  ID: {row[0]}, URL: {row[1]}, Domain: {row[2]}, Title: {row[3]}, Date: {row[4]}")
    
    conn.close()

if __name__ == "__main__":
    view_database()
