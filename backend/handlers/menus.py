import json
from ..database import get_db_connection
from ..utils import send_json

def handle_get_menus(query_params, handler):
    try:
        user_id = query_params.get('user_id', [None])[0]
        if not user_id:
            return send_json(handler, 400, {"error": "user_id required"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get menus: User's private menus + All public menus
        cursor.execute("""
            SELECT * FROM menus 
            WHERE user_id = ? OR is_public = 1 
            ORDER BY is_public DESC, created_at DESC
        """, (user_id,))
        menus_rows = cursor.fetchall()
        
        menus = []
        for menu in menus_rows:
            menu_id = menu['id']
            # Get items for this menu
            cursor.execute("""
                SELECT mi.*, f.image_url 
                FROM menu_items mi 
                JOIN foods f ON mi.food_id = f.id 
                WHERE mi.menu_id = ?
            """, (menu_id,))
            items_rows = cursor.fetchall()
            
            # Get translations for food names
            items = []
            for item in items_rows:
                cursor.execute("SELECT lang, name FROM food_translations WHERE food_id = ?", (item['food_id'],))
                trans = {row['lang']: row['name'] for row in cursor.fetchall()}
                
                # Get nutrients for calculation
                cursor.execute("""
                    SELECT n.key, fn.value 
                    FROM food_nutrients fn 
                    JOIN nutrients n ON fn.nutrient_id = n.id 
                    WHERE fn.food_id = ?
                """, (item['food_id'],))
                nutrients = {row['key']: row['value'] for row in cursor.fetchall()}

                items.append({
                    "id": item['id'],
                    "food_id": item['food_id'],
                    "quantity": item['quantity'],
                    "meal_type": item['meal_type'],
                    "image": item['image_url'],
                    "names": trans,
                    "nutrients": nutrients
                })
            
            menus.append({
                "id": menu['id'],
                "name": menu['name'],
                "description": menu['description'],
                "is_public": menu['is_public'],
                "user_id": menu['user_id'],
                "created_at": menu['created_at'],
                "items": items
            })
            
        conn.close()
        send_json(handler, 200, menus)
    except Exception as e:
        print(f"Get Menus Error: {e}")
        send_json(handler, 500, {"error": str(e)})

def handle_create_menu(data, handler):
    try:
        user_id = data.get('user_id')
        name = data.get('name')
        description = data.get('description', '')
        is_public = 1 if data.get('is_public') else 0
        items = data.get('items', []) # Expected: [{food_id, quantity, meal_type}]
        
        if not user_id or not name:
            return send_json(handler, 400, {"error": "user_id and name required"})
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Create menu
        cursor.execute("INSERT INTO menus (user_id, name, description, is_public) VALUES (?, ?, ?, ?)", 
                       (user_id, name, description, is_public))
        menu_id = cursor.lastrowid
        
        # 2. Create menu items
        for item in items:
            cursor.execute("""
                INSERT INTO menu_items (menu_id, food_id, quantity, meal_type) 
                VALUES (?, ?, ?, ?)
            """, (menu_id, item['food_id'], item['quantity'], item['meal_type']))
            
        conn.commit()
        conn.close()
        send_json(handler, 200, {"status": "success", "menu_id": menu_id})
    except Exception as e:
        print(f"Create Menu Error: {e}")
        send_json(handler, 500, {"error": str(e)})

def handle_delete_menu(data, handler):
    try:
        user_id = data.get('user_id')
        menu_id = data.get('menu_id')
        if not user_id or not menu_id:
            return send_json(handler, 400, {"error": "user_id and menu_id required"})
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute("SELECT user_id FROM menus WHERE id = ?", (menu_id,))
        menu = cursor.fetchone()
        if not menu or menu['user_id'] != user_id:
            conn.close()
            return send_json(handler, 403, {"error": "Unauthorized: You do not own this menu"})
        
        # 1. Delete items
        cursor.execute("DELETE FROM menu_items WHERE menu_id = ?", (menu_id,))
        # 2. Delete menu
        cursor.execute("DELETE FROM menus WHERE id = ?", (menu_id,))
        
        conn.commit()
        conn.close()
        send_json(handler, 200, {"status": "success"})
    except Exception as e:
        print(f"Delete Menu Error: {e}")
        send_json(handler, 500, {"error": str(e)})

def handle_update_menu(data, handler):
    try:
        user_id = data.get('user_id')
        menu_id = data.get('menu_id')
        name = data.get('name')
        is_public = 1 if data.get('is_public') else 0
        items = data.get('items', [])
        
        if not user_id or not menu_id or not name:
            return send_json(handler, 400, {"error": "user_id, menu_id and name required"})
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute("SELECT user_id FROM menus WHERE id = ?", (menu_id,))
        menu = cursor.fetchone()
        if not menu or menu['user_id'] != user_id:
            conn.close()
            return send_json(handler, 403, {"error": "Unauthorized: You do not own this menu"})
        
        # 1. Update menu metadata
        cursor.execute("UPDATE menus SET name = ?, is_public = ? WHERE id = ?", 
                       (name, is_public, menu_id))
        
        # 2. Refresh items (Delete then Insert is safer for simple CRUD)
        cursor.execute("DELETE FROM menu_items WHERE menu_id = ?", (menu_id,))
        for item in items:
            cursor.execute("""
                INSERT INTO menu_items (menu_id, food_id, quantity, meal_type) 
                VALUES (?, ?, ?, ?)
            """, (menu_id, item['food_id'], item['quantity'], item['meal_type']))
            
        conn.commit()
        conn.close()
        send_json(handler, 200, {"status": "success"})
    except Exception as e:
        print(f"Update Menu Error: {e}")
        send_json(handler, 500, {"error": str(e)})
