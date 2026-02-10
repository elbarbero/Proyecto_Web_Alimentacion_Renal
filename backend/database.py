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

        # Create Menus Tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS menus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            is_public INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
        
        # Check if is_public column exists (for existing tables)
        cursor.execute("PRAGMA table_info(menus)")
        menu_columns = [info[1] for info in cursor.fetchall()]
        if 'is_public' not in menu_columns:
            print("Migrating DB: Adding is_public to menus...")
            cursor.execute("ALTER TABLE menus ADD COLUMN is_public INTEGER DEFAULT 0")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_id INTEGER,
            food_id INTEGER,
            quantity REAL,
            meal_type TEXT,
            FOREIGN KEY(menu_id) REFERENCES menus(id),
            FOREIGN KEY(food_id) REFERENCES foods(id)
        )""")
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Migration error: {e}")
