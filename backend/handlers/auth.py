import json
import time
import secrets
from ..database import get_db_connection
from ..utils import hash_password, verify_password, send_json
from ..email_service import send_email
from ..config import PORT



def handle_login(data, handler):
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and verify_password(user['password_hash'], password):
        send_json(handler, 200, {
            "status": "success", 
            "userId": user['id'], 
            "name": user['name'],
            "surnames": user['surnames'],
            "birthdate": user['birthdate'],
            "email": user['email'],
            "nationality": user['nationality'], # Added for profile
            "has_insufficiency": user['has_insufficiency'],
            "treatment_type": user['treatment_type'],
            "kidney_stage": user['kidney_stage'],
            "avatar_url": user['avatar_url']
        })
    else:
        send_json(handler, 401, {"status": "error", "message": "Invalid credentials"})

def handle_register(data, handler):
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    surnames = data.get('surnames', '')
    birthdate = data.get('birthdate', '')
    nationality = data.get('nationality', '') # Added

    if not email or not password:
        send_json(handler, 400, {"status": "error", "message": "Missing fields"})
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        send_json(handler, 409, {"status": "error", "message": "Email already exists"})
        return

    hashed_pw = hash_password(password)
    terms_accepted_at = time.time()
    
    try:
        cursor.execute("INSERT INTO users (email, password_hash, name, surnames, birthdate, nationality, terms_accepted_at) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (email, hashed_pw, name, surnames, birthdate, nationality, terms_accepted_at))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        send_json(handler, 201, {
            "status": "success", 
            "userId": user_id, 
            "name": name,
            "surnames": surnames,
            "birthdate": birthdate,
            "nationality": nationality,
            "email": email
        })
    except Exception as e:
        print(f"Register Error: {e}")
        conn.close()
        send_json(handler, 500, {"status": "error", "message": "Internal error"})

def handle_request_reset(data, handler):
    email = data.get('email')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if user:
        token = secrets.token_urlsafe(32)
        expiry = time.time() + 3600
        cursor.execute("UPDATE users SET reset_token = ?, reset_token_expiry = ? WHERE email = ?", (token, expiry, email))
        conn.commit()
        
        # Dynamic Host Logic for Ngrok/Localhost
        host = handler.headers.get("X-Forwarded-Host", handler.headers.get("Host", f"localhost:{PORT}"))
        scheme = handler.headers.get("X-Forwarded-Proto", "http")
        
        reset_link = f"{scheme}://{host}/?reset_token={token}"
        print(f"DEBUG LINK: {reset_link}")
        
        body = f"""
        <h2>Recuperación de Contraseña</h2>
        <p>Has solicitado restablecer tu contraseña. Haz clic en el siguiente enlace:</p>
        <p><a href="{reset_link}">Restablecer Contraseña</a></p>
        <p>Este enlace expira en 1 hora.</p>
        """
        send_email(email, "Restablecer Contraseña - Web Renal", body)

    conn.close()
    send_json(handler, 200, {"status": "success", "message": "Si el email existe, se ha enviado un correo."})

def handle_reset_password(data, handler):
    token = data.get('token')
    new_password = data.get('password')
    
    if not token or not new_password:
        send_json(handler, 400, {"status": "error", "message": "Missing data"})
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, reset_token_expiry FROM users WHERE reset_token = ?", (token,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        send_json(handler, 400, {"status": "error", "message": "Token inválido"})
        return
    
    if time.time() > user['reset_token_expiry']:
        conn.close()
        send_json(handler, 400, {"status": "error", "message": "Token expirado"})
        return
    
    hashed_pw = hash_password(new_password)
    cursor.execute("UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL WHERE id = ?", (hashed_pw, user['id']))
    conn.commit()
    conn.close()

    send_json(handler, 200, {"status": "success", "message": "Contraseña actualizada"})
