import sqlite3
import json

DB_NAME = "renal_diet.db"

def get_foods():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, image_url FROM foods")
    foods_rows = cursor.fetchall()
    
    cursor.execute("""
        SELECT fc.food_id, c.key 
        FROM food_categories fc
        JOIN categories c ON fc.category_id = c.id
    """)
    cat_rows = cursor.fetchall()
    cat_dict = {}
    for row in cat_rows:
        if row['food_id'] not in cat_dict:
            cat_dict[row['food_id']] = []
        cat_dict[row['food_id']].append(row['key'])
    
    cursor.execute("SELECT food_id, lang, name FROM food_translations")
    trans_rows = cursor.fetchall()
    trans_dict = {}
    for row in trans_rows:
        if row['food_id'] not in trans_dict:
            trans_dict[row['food_id']] = {}
        trans_dict[row['food_id']][row['lang']] = row['name']
        
    cursor.execute("""
        SELECT fn.food_id, n.key as nutrient_key, fn.value 
        FROM food_nutrients fn
        JOIN nutrients n ON fn.nutrient_id = n.id
    """)
    nut_rows = cursor.fetchall()
    nut_dict = {}
    for row in nut_rows:
        if row['food_id'] not in nut_dict:
            nut_dict[row['food_id']] = {}
        nut_dict[row['food_id']][row['nutrient_key']] = row['value']

    foods = []
    for f in foods_rows:
        f_id = f['id']
        names = trans_dict.get(f_id, {})
        default_name = names.get('es', names.get('en', 'Unknown'))
        
        categories_list = cat_dict.get(f_id, [])
        category_string = ",".join(categories_list)
        
        foods.append({
            "id": f_id,
            "name": default_name,
            "category": category_string,
            "names": names,
            "image": f['image_url'],
            "nutrients": nut_dict.get(f_id, {})
        })
    
    conn.close()
    return foods

foods = get_foods()
print(f"Total foods: {len(foods)}")
if foods:
    print("Sample food:")
    print(json.dumps(foods[0], indent=2))
    print("\nSample food with multiple categories (if any):")
    multi = [f for f in foods if "," in f['category']]
    if multi:
        print(json.dumps(multi[0], indent=2))
    else:
        print("No multi-category foods found.")
