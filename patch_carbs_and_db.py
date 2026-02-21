import sqlite3
import re

CARBS = {
    'Zanahoria': 9.6, 'Espinacas': 3.6, 'Brócoli': 6.6, 'Coliflor': 5.0, 'Calabacín': 3.1, 'Berenjena': 5.9,
    'Pimiento Rojo': 6.0, 'Pimiento Verde': 4.6, 'Tomate': 3.9, 'Pepino': 3.6, 'Cebolla': 9.3, 'Ajo': 33.0,
    'Apio': 3.0, 'Champiñones': 3.3, 'Espárragos': 3.9, 'Judías Verdes': 7.0, 'Guisantes': 14.0, 'Calabaza': 6.5,
    'Puerro': 14.1, 'Remolacha': 9.6, 'Rábano': 3.4, 'Alcachofa': 10.5, 'Kale': 8.8, 'Bok Choy': 2.2,
    'Okra': 7.5, 'Daikon': 4.1, 'Hinojo': 7.3, 'Col de Bruselas': 9.0, 'Maíz Dulce': 19.0, 'Acelga': 3.7,
    'Patata': 17.5, 'Batata': 20.1, 'Yuca': 38.1, 'Ñame': 27.9,
    'Manzana': 13.8, 'Plátano': 22.8, 'Pera': 15.2, 'Naranja': 11.8, 'Mandarina': 13.3, 'Uvas': 18.1,
    'Melón': 8.2, 'Sandía': 7.6, 'Piña': 13.1, 'Kiwi': 14.7, 'Fresas': 7.7, 'Arándanos': 14.5,
    'Frambuesas': 11.9, 'Moras': 9.6, 'Limón': 9.3, 'Lima': 10.5, 'Pomelo': 10.7, 'Melocotón': 9.5,
    'Albaricoque': 11.1, 'Nectarina': 10.6, 'Ciruela': 11.4, 'Cereza': 16.0, 'Mango': 15.0, 'Papaya': 10.8,
    'Higos': 19.2, 'Granada': 18.7, 'Caqui': 18.6, 'Chirimoya': 17.7, 'Aguacate': 8.5, 'Coco': 15.2,
    'Lichi': 16.5, 'Fruta del Dragón': 11.0, 'Durian': 27.1, 'Maracuyá': 23.4, 'Guayaba': 14.3, 'Dátiles': 75.0,
    'Pollo (Pechuga)': 0.0, 'Pollo (Muslo)': 0.0, 'Pollo (Alitas)': 0.0, 'Pavo': 0.0, 'Pato': 0.0,
    'Ternera (Solomillo)': 0.0, 'Ternera (Entrecot)': 0.0, 'Ternera (Picada)': 0.0, 'Cerdo (Lomo)': 0.0,
    'Cerdo (Chuleta)': 0.0, 'Cerdo (Panceta)': 0.0, 'Cordero': 0.0, 'Conejo': 0.0, 'Codorniz': 0.0,
    'Hígado (Ternera)': 3.9, 'Hígado (Pollo)': 0.9, 'Salchicha (Cerdo)': 2.0, 'Chorizo': 2.0,
    'Jamón Serrano': 0.0, 'Jamón York': 1.0, 'Huevo': 1.1,
    'Salmón': 0.0, 'Merluza': 0.0, 'Bacalao': 0.0, 'Atún': 0.0, 'Sardinas': 0.0, 'Lenguado': 0.0,
    'Dorada': 0.0, 'Lubina': 0.0, 'Trucha': 0.0, 'Emperador': 0.0, 'Rodaballo': 0.0, 'Rape': 0.0,
    'Mero': 0.0, 'Calamar': 3.1, 'Sepia': 0.8, 'Pulpo': 2.2, 'Gambas': 0.2, 'Mejillones': 3.7,
    'Vieras': 2.4, 'Almejas': 5.1, 'Ostras': 3.9, 'Anchoas': 0.0, 'Arenque': 0.0, 'Caballa': 0.0,
    'Congrio': 0.0, 'Gallo': 0.0, 'Perca': 0.0, 'Salmonete': 0.0, 'Boquerón': 0.0, 'Anguila': 0.0, 'Caviar': 4.0,
    'Quinoa': 21.3, 'Lentejas': 20.1, 'Garbanzos': 27.4, 'Judías Blancas': 24.0, 'Judías Negras': 23.7, 'Soja': 15.0,
    'Arroz Blanco': 28.0, 'Arroz Integral': 23.0, 'Espaguetis': 31.0, 'Macarrones': 31.0, 'Tallarines': 25.0,
    'Pasta Integral': 26.0, 'Pasta al Huevo': 28.0, 'Pasta Sin Gluten': 30.0, 'Gnocchi': 33.0, 'Lasaña': 25.0,
    'Cuscús': 23.2, 'Bulgur': 18.6, 'Mijo': 23.7, 'Avena': 66.3, 'Cebada': 28.2, 'Centeno': 48.0,
    'Leche Entera': 4.8, 'Leche Desnatada': 5.0, 'Yogur Natural': 4.7, 'Yogur Griego': 3.6,
    'Yogur Desnatado': 7.0, 'Yogur de Fresa': 15.0, 'Yogur de Vainilla': 14.0, 'Yogur de Coco': 12.0,
    'Yogur de Soja': 2.0, 'Yogur Sin Lactosa': 4.7, 'Yogur de Sabores': 15.0, 'Queso Fresco': 3.0,
    'Queso Cheddar': 1.3, 'Queso Parmesano': 3.2, 'Queso Mozzarella': 2.2, 'Kefir': 4.8, 'Skyr': 4.0,
    'Ayran': 1.5, 'Petit Suisse': 12.0, 'Cuajada': 4.0, 'Yogur Líquido': 12.0,
    'Nueces': 13.7, 'Almendras': 21.6, 'Pistachos': 27.2, 'Anacardos': 30.2, 'Avellanas': 16.7,
    'Cacahuetes': 16.1, 'Nueces de Macadamia': 13.8, 'Nueces Pecanas': 13.9, 'Piñones': 13.1,
    'Pipas de Girasol': 20.0, 'Pipas de Calabaza': 15.0, 'Nueces de Brasil': 12.3,
    'Aceite de Oliva': 0.0, 'Mantequilla': 0.1, 'Mayonesa': 1.0, 'Tofu': 1.9, 'Seitán': 14.0, 'Tempeh': 9.4,
    'Chocolate Negro': 46.0, 'Chocolate con Leche': 59.0, 'Galletas': 68.0, 'Miel': 82.4, 'Mermelada': 69.0,
    'Azúcar': 100.0, 'Turrón': 50.0, 'Helado': 24.0, 'Gelatina': 14.0, 'Agua': 0.0, 'Infusión de Manzanilla': 0.0,
    'Té': 0.0, 'Vino Tinto': 2.6, 'Cerveza': 3.6, 'Coca Cola': 10.6, 'Café': 0.0, 'Zumo de Naranja': 10.4,
    'Zumo de Manzana': 11.3, 'Zumo de Piña': 13.0, 'Zumo de Uva': 14.8, 'Zumo de Tomate': 4.2,
    'Zumo de Pomelo': 9.2, 'Zumo de Zanahoria': 9.3, 'Zumo de Melocotón': 13.6, 'Zumo de Pera': 11.9,
    'Zumo de Arándanos': 12.2, 'Zumo de Mango': 13.0, 'Zumo de Granada': 13.1, 'Zumo de Limón': 2.5,
    'Zumo de Lima': 1.7, 'Zumo Multifruta': 11.0, 'Limonada': 10.0, 'Patatas Chips': 53.0, 'Nachos': 60.0,
    'Palomitas': 74.0, 'Ganchitos': 53.0, 'Barrita Energética': 65.0, 'Chocolatina': 60.0, 'Gominolas': 78.0,
    'Caramelos': 98.0, 'Regaliz': 70.0, 'Pretzels': 80.0, 'Galletas de Arroz': 82.0, 'Sal de Mesa': 0.0,
    'Vinagre': 0.0, 'Pimienta Negra': 64.0, 'Orégano': 68.8, 'Perejil': 6.3
}

def update_database():
    conn = sqlite3.connect('renal_diet.db')
    cursor = conn.cursor()
    
    # Aseguramos que el nutriente 'carbs' exista primero
    cursor.execute("SELECT id FROM nutrients WHERE key='carbs'")
    c_id_row = cursor.fetchone()
    
    if not c_id_row:
        print("Migrando DB: Añadiendo nutriente 'carbs' a la tabla nutrients...")
        cursor.execute("INSERT INTO nutrients (key, name_es, unit) VALUES ('carbs', 'Carbohidratos', 'g')")
        conn.commit()
        cursor.execute("SELECT id FROM nutrients WHERE key='carbs'")
        c_id_row = cursor.fetchone()

    c_id = c_id_row[0]
    cursor.execute("SELECT food_id, name FROM food_translations WHERE lang='es'")
    all_foods = cursor.fetchall()
    updated_count = 0
    for fid, fname in all_foods:
        exact_name = fname.split(' (')[0] if ' (' in fname else fname
        if exact_name in CARBS:
            val = CARBS[exact_name]
            # specific cooking method modifiers
            if '(Rebozado)' in fname: val += 15.0
            
            # Upsert logic to ensure we add the carb stat
            cursor.execute("SELECT * FROM food_nutrients WHERE food_id=? AND nutrient_id=?", (fid, c_id))
            exists = cursor.fetchone()
            if exists:
                cursor.execute("UPDATE food_nutrients SET value=? WHERE food_id=? AND nutrient_id=?", (val, fid, c_id))
            else:
                cursor.execute("INSERT INTO food_nutrients (food_id, nutrient_id, value) VALUES (?, ?, ?)", (fid, c_id, val))
            updated_count += 1
    
    conn.commit()
    print(f'DB Updated: {updated_count} foods received real carb data')
    conn.close()

if __name__ == "__main__":
    update_database()
