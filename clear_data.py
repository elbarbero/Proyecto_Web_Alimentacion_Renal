import sqlite3
import os

# Usamos la ruta directa si estamos en el servidor o la configurada en config.py
DB_PATH = 'renal_diet.db'

def clear_tables():
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encuentra la base de datos en {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # El orden es importante por las claves foráneas (primero los hijos)
        tables = ['menu_items', 'menus', 'forum_comments', 'forum_threads']
        
        for table in tables:
            print(f"Borrando datos de la tabla: {table}...")
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name=?", (table,))

        # Limpieza de usuarios (EXCEPTO los especificados)
        print("Borrando usuarios excepto administradores...")
        allowed_emails = ('elbarbero400@gmail.com', 'ypa14@hotmail.com')
        cursor.execute("DELETE FROM users WHERE email NOT IN (?, ?)", allowed_emails)
            
        conn.commit()
        conn.close()
        print("\n¡Limpieza completada con éxito! Las tablas están vacías.")
    except Exception as e:
        print(f"Error durante la limpieza: {e}")

if __name__ == "__main__":
    clear_tables()
