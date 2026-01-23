import sqlite3
import os
import shutil

DB_NAME = "renal_diet.db"
BACKUP_NAME = "renal_diet.db.bak"

def migrate():
    # 1. Backup
    print(f"Creando copia de seguridad en {BACKUP_NAME}...")
    shutil.copy2(DB_NAME, BACKUP_NAME)

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 2. Crear nuevas tablas
        print("Creando nuevas tablas...")
        
        cursor.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE NOT NULL, icon_url TEXT, color_hex TEXT)")
        
        cursor.execute("CREATE TABLE IF NOT EXISTS foods_new (id INTEGER PRIMARY KEY AUTOINCREMENT, image_url TEXT)")
        
        cursor.execute("CREATE TABLE IF NOT EXISTS food_categories (food_id INTEGER, category_id INTEGER, PRIMARY KEY(food_id, category_id), FOREIGN KEY(food_id) REFERENCES foods_new(id), FOREIGN KEY(category_id) REFERENCES categories(id))")
        
        cursor.execute("CREATE TABLE IF NOT EXISTS food_translations (id INTEGER PRIMARY KEY AUTOINCREMENT, food_id INTEGER, lang TEXT, name TEXT, FOREIGN KEY(food_id) REFERENCES foods_new(id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS nutrients (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE NOT NULL, name_es TEXT, unit TEXT)")
        
        cursor.execute("CREATE TABLE IF NOT EXISTS food_nutrients (food_id INTEGER, nutrient_id INTEGER, value REAL, PRIMARY KEY(food_id, nutrient_id), FOREIGN KEY(food_id) REFERENCES foods_new(id), FOREIGN KEY(nutrient_id) REFERENCES nutrients(id))")

        # 3. Inicializar Nutrientes
        print("Inicializando catálogo de nutrientes...")
        nutrients_data = [
            ('protein', 'Proteínas', 'g'),
            ('sugar', 'Azúcares', 'g'),
            ('fat', 'Grasas', 'g'),
            ('potassium', 'Potasio', 'mg'),
            ('phosphorus', 'Fósforo', 'mg'),
            ('salt', 'Sal', 'g'),
            ('calcium', 'Calcio', 'mg')
        ]
        cursor.executemany("INSERT OR IGNORE INTO nutrients (key, name_es, unit) VALUES (?, ?, ?)", nutrients_data)
        
        # Obtener IDs de nutrientes para el mapeo
        cursor.execute("SELECT id, key FROM nutrients")
        nutrient_map = {row['key']: row['id'] for row in cursor.fetchall()}

        # 4. Migrar Alimentos
        print("Migrando alimentos...")
        cursor.execute("SELECT * FROM foods")
        old_foods = cursor.fetchall()
        
        for old in old_foods:
            # a. Insertar food_new
            cursor.execute("INSERT INTO foods_new (id, image_url) VALUES (?, ?)", 
                           (old['id'], old['image_url']))
            food_id = old['id']

            # b. Manejar Categorías (Soporte multi-categoría)
            cat_string = old['category'] if old['category'] else 'others'
            cat_list = [c.strip() for c in cat_string.split(',') if c.strip()]
            
            for cat_key in cat_list:
                cursor.execute("INSERT OR IGNORE INTO categories (key) VALUES (?)", (cat_key,))
                cursor.execute("SELECT id FROM categories WHERE key = ?", (cat_key,))
                cat_id = cursor.fetchone()[0]
                cursor.execute("INSERT OR IGNORE INTO food_categories (food_id, category_id) VALUES (?, ?)", (food_id, cat_id))

            # c. Insertar Traducciones
            translations = [
                ('es', old['name']),
                ('en', old['name_en']),
                ('de', old['name_de']),
                ('fr', old['name_fr']),
                ('pt', old['name_pt']),
                ('ja', old['name_ja'])
            ]
            for lang, name in translations:
                if name:
                    cursor.execute("INSERT INTO food_translations (food_id, lang, name) VALUES (?, ?, ?)", (food_id, lang, name))

            # d. Insertar Nutrientes
            nut_values = [
                ('protein', old['protein']),
                ('sugar', old['sugar']),
                ('fat', old['fat']),
                ('potassium', old['potassium']),
                ('phosphorus', old['phosphorus']),
                ('salt', old['salt']),
                ('calcium', old['calcium'])
            ]
            for key, val in nut_values:
                if val is not None:
                    cursor.execute("INSERT INTO food_nutrients (food_id, nutrient_id, value) VALUES (?, ?, ?)", 
                                   (food_id, nutrient_map[key], val))

        # 5. Intercambiar tablas
        print("Finalizando migración de tablas...")
        cursor.execute("DROP TABLE foods")
        cursor.execute("ALTER TABLE foods_new RENAME TO foods")

        conn.commit()
        print("¡Migración completada con éxito!")

    except Exception as e:
        conn.rollback()
        print(f"ERROR durante la migración: {e}")
        print("Se ha realizado el rollback. La base de datos no ha sido modificada permanentemente.")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
