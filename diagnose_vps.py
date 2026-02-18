import sqlite3
import os

DB_PATH = '/root/web_renal/renal_diet.db'

def diagnose():
    print("\n--- DIAGNÓSTICO DE SISTEMA ---")
    print(f"Directorio actual: {os.getcwd()}")
    
    # Verificar imágenes
    avatar_dir = '/root/web_renal/images/avatars'
    if os.path.exists(avatar_dir):
        print(f"Archivos en {avatar_dir}: {os.listdir(avatar_dir)}")
    else:
        print(f"ERROR: Directorio de avatares no encontrado en {avatar_dir}")

    # Verificar Base de Datos
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, email, avatar_url FROM users")
            rows = cursor.fetchall()
            print("\n--- DATOS DE USUARIOS ---")
            for r in rows:
                print(f"ID {r[0]}: {r[1]} -> Avatar: {r[2]}")
            conn.close()
        except Exception as e:
            print(f"Error accediendo a la DB: {e}")
    else:
        print(f"ERROR: Base de datos no encontrada en {DB_PATH}")

if __name__ == "__main__":
    diagnose()
