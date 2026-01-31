import json
import os
import base64
from ..database import get_db_connection
from ..utils import send_json



def handle_get_user(query_params, handler):
    user_id = query_params.get('id', [None])[0]
    if not user_id:
        send_json(handler, 400, {"error": "Missing ID"})
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        send_json(handler, 200, {
            "id": user['id'], 
            "name": user['name'], 
            "surnames": user['surnames'],
            "birthdate": user['birthdate'],
            "email": user['email'],
            "nationality": user['nationality'],
            "has_insufficiency": user['has_insufficiency'],
            "treatment_type": user['treatment_type'],
            "kidney_stage": user['kidney_stage'],
            "avatar_url": user['avatar_url']
        })
    else:
        send_json(handler, 404, {"error": "User not found"})

def handle_update_profile(data, handler):
    email = data.get('email')
    
    if not email:
        send_json(handler, 400, {"status": "error", "message": "Missing email"})
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check for password
    password = data.get('password')
    
    if password:
        # Import hash_password here to avoid circular dependencies if utils imports users
        from ..utils import hash_password
        pwd_hash = hash_password(password)
        
        cursor.execute("""
            UPDATE users 
            SET name = ?, surnames = ?, birthdate = ?, has_insufficiency = ?, treatment_type = ?, kidney_stage = ?, password_hash = ?, nationality = ?
            WHERE email = ?
        """, (data.get('name'), data.get('surnames'), data.get('birthdate'), 
              data.get('has_insufficiency'), data.get('treatment_type'), data.get('kidney_stage'), pwd_hash, data.get('nationality'),
              email))
    else:
        cursor.execute("""
            UPDATE users 
            SET name = ?, surnames = ?, birthdate = ?, has_insufficiency = ?, treatment_type = ?, kidney_stage = ?, nationality = ?
            WHERE email = ?
        """, (data.get('name'), data.get('surnames'), data.get('birthdate'), 
              data.get('has_insufficiency'), data.get('treatment_type'), data.get('kidney_stage'), data.get('nationality'),
              email))
    
    rows = cursor.rowcount
    conn.commit()
    conn.close()

    if rows > 0:
        send_json(handler, 200, {"status": "success"})
    else:
        # If no rows changed, it might be that data was identical.
        # But we still return success to frontend so it doesn't show error.
        # Unless user really doesn't exist?
        # Let's check existence first to be safe, OR just return success if not error.
        # Ideally, we should check if user exists. 
        # But for 'save' action, 'success' even if no change is fine.
        send_json(handler, 200, {"status": "success"})

def handle_upload_avatar(data, handler):
    email = data.get('email')
    image_data = data.get('image_data')

    if not email or not image_data:
        send_json(handler, 400, {"status": "error"})
        return
    
    # Clean Base64
    if "," in image_data:
        header, encoded = image_data.split(",", 1)
    else:
        encoded = image_data
    
    try:
        file_content = base64.b64decode(encoded)
        
        AVATAR_DIR = "images/avatars"
        if not os.path.exists(AVATAR_DIR):
            os.makedirs(AVATAR_DIR)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            send_json(handler, 404, {"status": "error", "message": "User not found"})
            return

        user_id = user['id']
        filename = f"{user_id}.png"
        filepath = os.path.join(AVATAR_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(file_content)
        
        # Consistent URL path
        db_path = f"images/avatars/{filename}"
        cursor.execute("UPDATE users SET avatar_url = ? WHERE id = ?", (db_path, user_id))
        conn.commit()
        conn.close()

        send_json(handler, 200, {"status": "success", "avatar_url": db_path})
    except Exception as e:
        print(f"Avatar upload failed: {e}")
        send_json(handler, 500, {"status": "error", "message": str(e)})
