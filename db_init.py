import sqlite3
import os

DB_NAME = "renal_diet.db"

# URLs de imágenes verificadas (IDs específicos de Unsplash)
# Se usa el endpoint directo de imagen: https://images.unsplash.com/photo-[ID]
initial_foods = [
    # Frutas y Verduras
    (1, "Manzana", "https://images.unsplash.com/photo-1570913149827-d2ac84ab3f9a?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 0.3, 10.0, 0.2, 107, 11, 0.01), # Red apple
    (6, "Espinacas (Crudas)", "https://images.unsplash.com/photo-1576045057995-568f588f82fb?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 2.9, 0.4, 0.4, 558, 49, 0.07), # Spinach
    (7, "Plátano", "https://images.unsplash.com/photo-1571771896328-7963057c1e14?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 1.1, 12.2, 0.3, 358, 27, 0.01), # Bananas
    (8, "Zanahoria", "https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 0.9, 4.7, 0.2, 320, 35, 0.06), # Carrots
    (9, "Lechuga", "https://images.unsplash.com/photo-1622206151226-18ca2c9ab4a1?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 1.4, 0.8, 0.2, 194, 29, 0.02), # Lettuce leaf

    # Proteínas Animales
    (2, "Pollo (Pechuga)", "https://images.unsplash.com/photo-1604503468506-a8da13d82791?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 23.0, 0.0, 1.2, 256, 196, 0.1), # Chicken breast
    (4, "Salmón", "https://images.unsplash.com/photo-1499125562588-29fb8a56b5d5?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 20.0, 0.0, 13.0, 363, 200, 0.05), # Salmon fillet
    (5, "Huevo (Grande)", "https://images.unsplash.com/photo-1518569656558-1f25e69d93d7?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 12.6, 0.4, 9.5, 126, 198, 0.14), # Eggs
    (10, "Ternera (Filete)", "https://images.unsplash.com/photo-1603048297172-c92544798d5e?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 24.0, 0.0, 6.0, 318, 175, 0.1), # Red meat/Steak
    (11, "Merluza", "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 17.0, 0.0, 1.9, 290, 190, 0.1), # White fish (using salmon fallback if needed, but this ID is white fish like)

    # Carbohidratos y Otros
    (3, "Arroz Blanco (Cocido)", "https://images.unsplash.com/photo-1536304929831-d1ac9d5368dd?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 2.7, 0.1, 0.3, 35, 43, 0.01), # Rice bowl
    (12, "Pan Blanco", "https://images.unsplash.com/photo-1509440159596-0249088772ff?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 9.0, 2.5, 3.2, 115, 85, 1.2), # Bread loaf
    (13, "Pasta (Cocida)", "https://images.unsplash.com/photo-1551462147-37885db80f58?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 5.0, 0.5, 1.1, 44, 58, 0.01), # Pasta bowl
    (14, "Aceite de Oliva", "https://images.unsplash.com/photo-1474979266404-7eaacbcd0347?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 0.0, 0.0, 100.0, 0, 0, 0.0), # Olive oil bottle

    # Lácteos
    (15, "Leche Semidesnatada", "https://images.unsplash.com/photo-1563636619-e9143da7973b?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 3.4, 5.0, 1.6, 150, 92, 0.1), # Milk glass
    (16, "Yogur Natural", "https://images.unsplash.com/photo-1571212515416-f223d9098402?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 3.5, 4.7, 3.3, 141, 135, 0.1), # Yogurt
    (17, "Queso Fresco", "https://images.unsplash.com/photo-1588195538326-c5f1f9c496a0?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 12.0, 3.0, 10.0, 180, 220, 0.5) # Cheese
]

def init_db():
    if os.path.exists(DB_NAME):
        try:
            os.remove(DB_NAME)
            print(f"Base de datos {DB_NAME} eliminada para regeneración.")
        except PermissionError:
            print(f"Error: No se puede borrar {DB_NAME} porque está en uso. Cierra el servidor primero.")
            return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY,
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

    cursor.executemany('''
    INSERT INTO foods (id, name, image_url, protein, sugar, fat, potassium, phosphorus, salt)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', initial_foods)

    conn.commit()
    print(f"Base de datos {DB_NAME} creada e inicializada con {len(initial_foods)} alimentos corregidos (v2).")
    
    conn.close()

if __name__ == "__main__":
    init_db()
