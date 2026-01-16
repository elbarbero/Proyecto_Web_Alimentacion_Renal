import sqlite3
import os

DB_NAME = "renal_diet.db"

# Datos iniciales (mismos que script.js)
initial_foods = [
    (1, "Manzana", "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60", 0.3, 10.4, 0.2, 107, 11, 0.001),
    (2, "Pollo (Pechuga)", "https://images.unsplash.com/photo-1604503468506-a8da13d82791?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60", 31, 0, 3.6, 256, 228, 0.1),
    (3, "Arroz Blanco", "https://images.unsplash.com/photo-1586201375761-83865001e31c?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60", 2.7, 0.1, 0.3, 35, 43, 0.01),
    (4, "Salmón", "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60", 20, 0, 13, 363, 200, 0.05),
    (5, "Huevo", "https://images.unsplash.com/photo-1506976785307-8732e854ad03?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60", 13, 1.1, 11, 126, 198, 0.12),
    (6, "Espinacas", "https://images.unsplash.com/photo-1576045057995-568f588f82fb?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60", 2.9, 0.4, 0.4, 558, 49, 0.07)
]

def init_db():
    # Eliminar si existe para regenerar (desarrollo)
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Base de datos {DB_NAME} eliminada para regeneración.")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Crear tabla
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        image_url TEXT,
        protein REAL,
        sugar REAL,
        fat REAL,
        potassium REAL,
        phosphorus REAL,
        salt REAL
    )
    ''')

    # Insertar datos
    cursor.executemany('''
    INSERT INTO foods (id, name, image_url, protein, sugar, fat, potassium, phosphorus, salt)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', initial_foods)

    conn.commit()
    print(f"Base de datos {DB_NAME} creada e inicializada con {len(initial_foods)} alimentos.")
    
    # Verificar
    cursor.execute("SELECT * FROM foods")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    conn.close()

if __name__ == "__main__":
    init_db()
