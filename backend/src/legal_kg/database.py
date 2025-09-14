import sqlite3
import os
from pathlib import Path

# Database configuration
DB_PATH = Path(__file__).parent.parent.parent / "data" / "legal_kg.db"

def get_connection():
    """Get SQLite database connection"""
    return sqlite3.connect(DB_PATH)

def init_database():
    """Initialize the database with required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create crawled_pages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crawled_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            domain TEXT NOT NULL,
            path TEXT NOT NULL,
            title TEXT,
            html_content TEXT,
            text_content TEXT,
            status_code INTEGER,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    """)
    
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_database()