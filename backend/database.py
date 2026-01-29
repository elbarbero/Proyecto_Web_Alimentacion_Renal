import sqlite3
from .config import DB_NAME

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def run_migrations():
    """Ensure DB has necessary columns for password reset and other features."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'reset_token' not in columns:
            print("Migrating DB: Adding reset_token...")
            cursor.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
            
        if 'reset_token_expiry' not in columns:
            print("Migrating DB: Adding reset_token_expiry...")
            cursor.execute("ALTER TABLE users ADD COLUMN reset_token_expiry REAL")

        if 'terms_accepted_at' not in columns:
            print("Migrating DB: Adding terms_accepted_at...")
            cursor.execute("ALTER TABLE users ADD COLUMN terms_accepted_at REAL")
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Migration error: {e}")
