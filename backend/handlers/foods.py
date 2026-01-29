import json
from ..database import get_db_connection
from ..email_service import send_email_notification

def send_json(handler, status, data):
    handler.send_response(status)
    handler.send_header('Content-type', 'application/json')
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode())

def handle_get_foods(handler):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Foods
        cursor.execute("SELECT id, image_url FROM foods")
        foods_rows = cursor.fetchall()
        
        # Categories
        cursor.execute("SELECT fc.food_id, c.key FROM food_categories fc JOIN categories c ON fc.category_id = c.id")
        cat_rows = cursor.fetchall()
        cat_dict = {}
        for row in cat_rows:
            if row['food_id'] not in cat_dict: cat_dict[row['food_id']] = []
            cat_dict[row['food_id']].append(row['key'])
        
        # Translations
        cursor.execute("SELECT food_id, lang, name FROM food_translations")
        trans_rows = cursor.fetchall()
        trans_dict = {}
        for row in trans_rows:
            if row['food_id'] not in trans_dict: trans_dict[row['food_id']] = {}
            trans_dict[row['food_id']][row['lang']] = row['name']
            
        # Nutrients
        cursor.execute("SELECT fn.food_id, n.key as nutrient_key, fn.value FROM food_nutrients fn JOIN nutrients n ON fn.nutrient_id = n.id")
        nut_rows = cursor.fetchall()
        nut_dict = {}
        for row in nut_rows:
            if row['food_id'] not in nut_dict: nut_dict[row['food_id']] = {}
            nut_dict[row['food_id']][row['nutrient_key']] = row['value']

        foods = []
        for f in foods_rows:
            f_id = f['id']
            names = trans_dict.get(f_id, {})
            default_name = names.get('es', names.get('en', 'Unknown'))
            category_string = ",".join(cat_dict.get(f_id, []))
            
            foods.append({
                "id": f_id,
                "name": default_name,
                "category": category_string,
                "names": names,
                "image": f['image_url'],
                "nutrients": nut_dict.get(f_id, {})
            })
        
        foods.sort(key=lambda x: x['name'])
        conn.close()
        send_json(handler, 200, foods)
    except Exception as e:
        print(f"Get Foods Error: {e}")
        send_json(handler, 500, [])

def handle_feedback(data, handler):
    message = data.get('message', '')
    success, note = send_email_notification(message)
    
    if success:
        send_json(handler, 200, {"status": "success", "note": note})
    else:
        send_json(handler, 500, {"status": "error", "note": note})
