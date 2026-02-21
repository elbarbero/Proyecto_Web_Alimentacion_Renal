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
        # Verification check
        # sqlite3.Row doesn't support .get(), check if columns exist by checking keys
        if 'email_verified' in user.keys() and user['email_verified'] == 0:
            sent_at = user['verification_sent_at'] if 'verification_sent_at' in user.keys() else None
            if sent_at and (time.time() - sent_at) > 7 * 24 * 3600:
                send_json(handler, 403, {"status": "error", "message": "unverified_email"})
                return

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
            "avatar_url": user['avatar_url'],
            "email_verified": user['email_verified'] if 'email_verified' in user.keys() else 1 # Default to 1 (verified) if column doesn't exist yet
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
    
    verification_token = secrets.token_urlsafe(32)
    verification_sent_at = time.time()
    
    try:
        cursor.execute("""
            INSERT INTO users (email, password_hash, name, surnames, birthdate, nationality, terms_accepted_at, avatar_url, email_verified, verification_token, verification_sent_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
        """, (email, hashed_pw, name, surnames, birthdate, nationality, terms_accepted_at, '/images/default_avatar.png', verification_token, verification_sent_at))
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
            "email_verified": 0,
            "email": email
        })
        
        # Send Verification Email
        host = handler.headers.get("X-Forwarded-Host", handler.headers.get("Host", f"localhost:{PORT}"))
        scheme = handler.headers.get("X-Forwarded-Proto", "http")
        verify_link = f"{scheme}://{host}/?verify_token={verification_token}"
        
        body = f"""
        <h2>Verifica tu correo electrónico</h2>
        <p>Gracias por registrarte en Alimentación Renal Inteligente. Haz clic en el siguiente enlace para verificar tu cuenta:</p>
        <p><a href="{verify_link}">Verificar mi cuenta</a></p>
        <p>Si no verificas tu cuenta en 7 días, será desactivada temporalmente.</p>
        """
        send_email(email, "Verifica tu cuenta - Alimentación Renal", body)
        
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

def handle_resend_verification(data, handler):
    email = data.get('email')
    
    if not email:
        send_json(handler, 400, {"status": "error", "message": "Email faltante"})
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email_verified FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        send_json(handler, 404, {"status": "error", "message": "Usuario no encontrado"})
        return
        
    # sqlite3.Row doesn't support .get(), check if columns exist by checking keys
    if 'email_verified' in user.keys() and user['email_verified'] == 1:
        conn.close()
        send_json(handler, 400, {"status": "error", "message": "El usuario ya está verificado"})
        return
        
    verification_token = secrets.token_urlsafe(32)
    verification_sent_at = time.time()
    
    cursor.execute("UPDATE users SET verification_token = ?, verification_sent_at = ? WHERE id = ?", (verification_token, verification_sent_at, user['id']))
    conn.commit()
    conn.close()
    
    # Send Verification Email
    host = handler.headers.get("X-Forwarded-Host", handler.headers.get("Host", f"localhost:{PORT}"))
    scheme = handler.headers.get("X-Forwarded-Proto", "http")
    verify_link = f"{scheme}://{host}/?verify_token={verification_token}"
    
    body = f"""
    <h2>Verifica tu correo electrónico</h2>
    <p>Has solicitado reenviar el correo de verificación. Haz clic en el siguiente enlace para verificar tu cuenta:</p>
    <p><a href="{verify_link}">Verificar mi cuenta</a></p>
    <p>Si no verificas tu cuenta en 7 días desde hoy, será desactivada temporalmente.</p>
    """
    send_email(email, "Reenvío - Verifica tu cuenta - Alimentación Renal", body)
    
    send_json(handler, 200, {"status": "success", "message": "Correo reenviado exitosamente"})

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

def handle_verify_email(data, handler):
    token = data.get('token')
    
    if not token:
        send_json(handler, 400, {"status": "error", "message": "Token faltante"})
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE verification_token = ?", (token,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        send_json(handler, 400, {"status": "error", "message": "Token inválido o cuenta ya verificada"})
        return
        
    cursor.execute("UPDATE users SET email_verified = 1, verification_token = NULL WHERE id = ?", (user['id'],))
    conn.commit()
    conn.close()
    
    send_json(handler, 200, {"status": "success", "message": "Cuenta verificada exitosamente"})
