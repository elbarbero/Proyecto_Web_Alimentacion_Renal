import sqlite3
import os
import urllib.parse

DB_NAME = "renal_diet.db"

# Función helper para generar URLs de Bing Thumbnails (Estables y Cuadradas)
def get_image_url(query):
    base_url = "https://tse2.mm.bing.net/th"
    params = {
        "q": query,
        "w": "500",
        "h": "500",
        "c": "7", # Smart Crop
        "rs": "1",
        "p": "0"
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"

# Datos nutricionales aproximados (Fuente: Bases de datos estándar como USDA/BEDCA)
# Valores por 100g de porción comestible
# Orden: id, name, image_url, protein, sugar, fat, potassium, phosphorus, salt, CALCIUM
initial_foods = [
    # Frutas y Verduras
    (1, "Manzana", "Apple", "Apfel", "Pomme", "Maçã", "リンゴ", get_image_url("red apple fruit"), 0.3, 10.0, 0.2, 107, 11, 0.01, 6),
    (6, "Espinacas", "Spinach", "Spinat", "Épinards", "Espinafre", "ほうれん草", get_image_url("fresh spinach leaves"), 2.9, 0.4, 0.4, 558, 49, 0.07, 99),
    (7, "Plátano", "Banana", "Banane", "Banane", "Banana", "バナナ", get_image_url("banana fruit"), 1.1, 12.2, 0.3, 358, 27, 0.01, 5),
    (8, "Zanahoria", "Carrot", "Karotte", "Carotte", "Cenoura", "人参", get_image_url("fresh carrots"), 0.9, 4.7, 0.2, 320, 35, 0.06, 33),
    (9, "Lechuga", "Lettuce", "Salat", "Laitue", "Alface", "レタス", get_image_url("fresh lettuce head"), 1.4, 0.8, 0.2, 194, 29, 0.02, 36),

    # Proteínas Animales
    (2, "Pollo", "Chicken", "Hähnchen", "Poulet", "Frango", "鶏肉", get_image_url("raw chicken breast meat"), 23.0, 0.0, 1.2, 256, 196, 0.1, 15),
    (4, "Salmón", "Salmon", "Lachs", "Saumon", "Salmão", "サーモン", get_image_url("raw salmon fillet"), 20.0, 0.0, 13.0, 363, 200, 0.05, 12),
    (5, "Huevo", "Egg", "Ei", "Œuf", "Ovo", "卵", get_image_url("chicken eggs"), 12.6, 0.4, 9.5, 126, 198, 0.14, 56),
    (10, "Ternera", "Beef", "Rindfleisch", "Bœuf", "Carne Bovina", "牛肉", get_image_url("raw beef steak"), 24.0, 0.0, 6.0, 318, 175, 0.1, 18),
    (11, "Merluza", "Hake", "Seehecht", "Colin", "Pescada", "メルルーサ", get_image_url("raw white fish fillet"), 17.0, 0.0, 1.9, 290, 190, 0.1, 41),

    # Carbohidratos y Otros
    (3, "Arroz", "Rice", "Reis", "Riz", "Arroz", "米", get_image_url("cooked white rice bowl"), 2.7, 0.1, 0.3, 35, 43, 0.01, 10),
    (12, "Pan Blanco", "White Bread", "Weißbrot", "Pain Blanc", "Pão Branco", "白パン", get_image_url("white bread loaf"), 9.0, 2.5, 3.2, 115, 85, 1.2, 26),
    (13, "Pasta", "Pasta", "Nudeln", "Pâtes", "Massa", "パスタ", get_image_url("cooked pasta bowl"), 5.0, 0.5, 1.1, 44, 58, 0.01, 14),
    (14, "Aceite de Oliva", "Olive Oil", "Olivenöl", "Huile d'Olive", "Azeite", "オリーブオイル", get_image_url("olive oil bottle"), 0.0, 0.0, 100.0, 0, 0, 0.0, 0),

    # Lácteos
    (15, "Leche", "Milk", "Milch", "Lait", "Leite", "牛乳", get_image_url("glass of milk"), 3.4, 5.0, 1.6, 150, 92, 0.1, 120),
    (16, "Yogur", "Yogurt", "Joghurt", "Yaourt", "Iogurte", "ヨーグルト", get_image_url("plain yogurt bowl"), 3.5, 4.7, 3.3, 141, 135, 0.1, 140),
    (17, "Queso Fresco", "Fresh Cheese", "Frischkäse", "Fromage Frais", "Queijo Fresco", "フレッシュチーズ", get_image_url("fresh white cheese"), 12.0, 3.0, 10.0, 180, 220, 0.5, 550)
]

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Crear Tablas Profesionales
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        key TEXT UNIQUE NOT NULL, 
        icon_url TEXT, 
        color_hex TEXT
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        category_id INTEGER, 
        image_url TEXT, 
        FOREIGN KEY(category_id) REFERENCES categories(id)
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS food_translations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        food_id INTEGER, 
        lang TEXT, 
        name TEXT, 
        FOREIGN KEY(food_id) REFERENCES foods(id)
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nutrients (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        key TEXT UNIQUE NOT NULL, 
        name_es TEXT, 
        unit TEXT
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS food_nutrients (
        food_id INTEGER, 
        nutrient_id INTEGER, 
        value REAL, 
        PRIMARY KEY(food_id, nutrient_id), 
        FOREIGN KEY(food_id) REFERENCES foods(id), 
        FOREIGN KEY(nutrient_id) REFERENCES nutrients(id)
    )""")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT,
        surnames TEXT,
        birthdate TEXT,
        has_insufficiency INTEGER,
        treatment_type TEXT,
        kidney_stage TEXT,
        avatar_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 2. Inicializar Catálogos
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

    conn.commit()
    print(f"Base de datos {DB_NAME} inicializada con el esquema profesional.")
    conn.close()

if __name__ == "__main__":
    init_db()
