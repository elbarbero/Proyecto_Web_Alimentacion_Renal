import json
import sqlite3
from backend.database import get_db_connection
from backend.utils import send_json

def handle_get_countries(handler):
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT code, flag_url FROM countries ORDER BY code")
        rows = cursor.fetchall()
        conn.close()
        
        countries = []
        for row in rows:
            countries.append({
                "code": row["code"],
                "flag": row["flag_url"]
            })
            
        send_json(handler, 200, countries)
        
    except Exception as e:
        print(f"Error fetching countries: {e}")
        send_json(handler, 500, {"status": "error", "message": str(e)})
