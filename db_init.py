import sqlite3
import os

DB_NAME = "renal_diet.db"

# Datos nutricionales aproximados (Fuente: Bases de datos estándar como USDA/BEDCA)
# Valores por 100g de porción comestible
initial_foods = [
    # Frutas y Verduras
    (1, "Manzana", "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 0.3, 10.0, 0.2, 107, 11, 0.01),
    (6, "Espinacas (Crudas)", "https://images.unsplash.com/photo-1576045057995-568f588f82fb?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 2.9, 0.4, 0.4, 558, 49, 0.07), # OJO: Alto Potasio
    (7, "Plátano", "https://images.unsplash.com/photo-1603833665858-e61d17a86224?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 1.1, 12.2, 0.3, 358, 27, 0.01), # URL Actualizada
    (8, "Zanahoria", "https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 0.9, 4.7, 0.2, 320, 35, 0.06),
    (9, "Lechuga", "https://images.unsplash.com/photo-1622206151226-18ca2c9ab4a1?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 1.4, 0.8, 0.2, 194, 29, 0.02),

    # Proteínas Animales
    (2, "Pollo (Pechuga)", "https://images.unsplash.com/photo-1604503468506-a8da13d82791?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 23.0, 0.0, 1.2, 256, 196, 0.1),
    (4, "Salmón", "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 20.0, 0.0, 13.0, 363, 200, 0.05),
    (5, "Huevo (Grande)", "https://images.unsplash.com/photo-1506976785307-8732e854ad03?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 12.6, 0.4, 9.5, 126, 198, 0.14),
    (10, "Ternera (Filete)", "https://images.unsplash.com/photo-1588168333986-5078d3ae3976?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 24.0, 0.0, 6.0, 318, 175, 0.1), # URL Actualizada
    (11, "Merluza", "https://images.unsplash.com/photo-1534942080777-6f0a4e768686?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 17.0, 0.0, 1.9, 290, 190, 0.1), # URL Actualizada

    # Carbohidratos y Otros
    (3, "Arroz Blanco (Cocido)", "https://images.unsplash.com/photo-1586201375761-83865001e31c?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 2.7, 0.1, 0.3, 35, 43, 0.01),
    (12, "Pan Blanco", "https://images.unsplash.com/photo-1555507036-ab1f4038808a?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 9.0, 2.5, 3.2, 115, 85, 1.2),
    (13, "Pasta (Cocida)", "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 5.0, 0.5, 1.1, 44, 58, 0.01), # URL Actualizada
    (14, "Aceite de Oliva", "https://images.unsplash.com/photo-1474979266404-7eaacbcd0347?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 0.0, 0.0, 100.0, 0, 0, 0.0), # (Esta funcionaba pero la refresco por si acaso)

    # Lácteos
    (15, "Leche Semidesnatada", "https://images.unsplash.com/photo-1550583724-b2692b85b150?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 3.4, 5.0, 1.6, 150, 92, 0.1),
    (16, "Yogur Natural", "https://images.unsplash.com/photo-1488477181946-6428a0291777?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 3.5, 4.7, 3.3, 141, 135, 0.1),
    (17, "Queso Fresco", "https://images.unsplash.com/photo-1563223605-c1fa9a272370?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=80", 12.0, 3.0, 10.0, 180, 220, 0.5)
]

def init_db():
    if os.path.exists(DB_NAME):
        try:
            os.remove(DB_NAME)
            print(f"Base de datos {DB_NAME} eliminada para regeneración.")
        except PermissionError:
            print(f"Error: No se puede borrar {DB_NAME} porque está en uso. Cierra el servidor primero (Ctrl+C en la terminal donde corre 'python server.py').")
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
    print(f"Base de datos {DB_NAME} creada e inicializada con {len(initial_foods)} alimentos corregidos.")
    
    conn.close()

if __name__ == "__main__":
    init_db()
