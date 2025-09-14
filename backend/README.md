# Legal Knowledge Graph - Backend

Simple SQLite database setup for the Legal Knowledge Graph project.

## Project Structure

```
backend/
├── src/
│   └── legal_kg/          # Main package
│       ├── __init__.py
│       ├── database.py    # Database configuration
│       └── models.py      # Data models
├── scripts/               # Utility scripts
│   ├── init_db.py        # Initialize database
│   └── view_db.py        # View database contents
├── data/                 # Data storage
│   └── legal_kg.db       # SQLite database
├── main.py              # Main entry point
├── setup.py             # Package setup
└── requirements.txt     # Dependencies
```

## Quick Start

1. **Initialize the database:**
   ```bash
   python3 scripts/init_db.py
   ```

2. **Run the main application:**
   ```bash
   python3 main.py
   ```

3. **View database contents:**
   ```bash
   python3 scripts/view_db.py
   ```

## Usage

**In your code:**
```python
from legal_kg.database import get_connection
from legal_kg.models import CrawledPage

conn = get_connection()
cursor = conn.cursor()
# Your database operations here
conn.close()
```

## Database

The database contains one main table:
- `crawled_pages` - For storing web scraping data (URL, content, metadata)

## Adding New Tables

To add new tables, modify the `init_database()` function in `src/legal_kg/database.py` and run `python3 scripts/init_db.py` again.