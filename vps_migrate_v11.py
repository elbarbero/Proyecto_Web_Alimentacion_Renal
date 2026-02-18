import sqlite3
import os
import shutil

DB_NAME = "renal_diet.db"
BACKUP_NAME = "renal_diet_v11_prebackup.db"

def migrate():
    if not os.path.exists(DB_NAME):
        print(f"Error: {DB_NAME} no encontrado.")
        return

    # 1. Backup
    print(f"Creando copia de seguridad en {BACKUP_NAME}...")
    shutil.copy2(DB_NAME, BACKUP_NAME)

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 2. Add 'unit' column if not exists
        print("Verificando columna 'unit' en la tabla 'foods'...")
        cursor.execute("PRAGMA table_info(foods)")
        columns = [row['name'] for row in cursor.fetchall()]
        
        if 'unit' not in columns:
            print("Añadiendo columna 'unit' a 'foods'...")
            cursor.execute("ALTER TABLE foods ADD COLUMN unit TEXT DEFAULT 'g'")
        else:
            print("La columna 'unit' ya existe.")

        # 3. Update liquids to 'ml'
        # Basado en la lógica de populate_foods.py (Aceites, Bebidas, Lácteos líquidos)
        print("Actualizando unidades para líquidos (ml)...")
        
        # Lista de palabras clave para identificar líquidos por nombre
        liquid_keywords = [
            'aceite', 'vinagre', 'agua', 'cerveza', 'vino', 'refresco', 'zumo', 
            'leche', 'batido', 'bebida', 'té', 'infusión', 'café', 'yogur líquido'
        ]
        
        for kw in liquid_keywords:
            cursor.execute("""
                UPDATE foods 
                SET unit = 'ml' 
                WHERE id IN (
                    SELECT food_id 
                    FROM food_translations 
                    WHERE lang = 'es' AND LOWER(name) LIKE ?
                )
            """, (f'%{kw}%',))
            
        print(f"Filas actualizadas: {cursor.rowcount} (aproximadamente)")

        conn.commit()
        print("¡Migración completada con éxito en el VPS!")

    except Exception as e:
        conn.rollback()
        print(f"ERROR durante la migración: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
