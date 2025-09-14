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

## COMMAND TO START SQLITE BROWSER WITH OUR DATA

To open the SQLite database in DB Browser for SQLite, run:

```bash
cd backend && sqlitebrowser data/legal_kg.db
```


