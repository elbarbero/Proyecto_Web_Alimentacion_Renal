import http.server
import socketserver
import json
import sqlite3
import os
import urllib.parse
import urllib.request
import urllib.error


PORT = 8000
DB_NAME = "renal_diet.db"

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import binascii
import secrets
import time

def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                  provided_password.encode('utf-8'), 
                                  salt.encode('ascii'), 
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

# Configuración Email
# Intenta cargar variables desde .env
def load_env():
    env_vars = {}
    try:
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        # Limpiar comillas y espacios extra
                        val = value.strip().strip('"').strip("'")
                        # Si es el password, quitar espacios internos (formato Google)
                        if key == "EMAIL_PASS":
                            val = val.replace(" ", "")
                        env_vars[key] = val
            print("Cargada configuración desde .env")
    except Exception as e:
        print(f"Nota: No se pudo leer .env: {e}")
    return env_vars

env = load_env()

def run_migrations():
    """Ensure DB has necessary columns for password reset."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'reset_token' not in columns:
            print("Migrating DB: Adding reset_token...")
            cursor.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
            
        if 'reset_token_expiry' not in columns:
            print("Migrating DB: Adding reset_token_expiry...")
            cursor.execute("ALTER TABLE users ADD COLUMN reset_token_expiry REAL")
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Migration error: {e}")

run_migrations()

# Prioridad: Variables de entorno sistema > Fichero .env > Valores por defecto
SMTP_SERVER = os.environ.get("SMTP_SERVER", env.get("SMTP_SERVER", "smtp.gmail.com"))
SMTP_PORT = int(os.environ.get("SMTP_PORT", env.get("SMTP_PORT", 587)))
SENDER_EMAIL = os.environ.get("EMAIL_USER", env.get("EMAIL_USER", "nutrirenalweb@gmail.com"))
SENDER_PASSWORD = os.environ.get("EMAIL_PASS", env.get("EMAIL_PASS", ""))
RECIPIENT_EMAIL = os.environ.get("EMAIL_RECIPIENT", env.get("EMAIL_RECIPIENT", "nutrirenalweb@gmail.com"))

RECIPIENT_EMAIL = os.environ.get("EMAIL_RECIPIENT", env.get("EMAIL_RECIPIENT", "nutrirenalweb@gmail.com"))

class RenalDietHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/api/get_user':
            query_params = urllib.parse.parse_qs(parsed_path.query)
            # urllib.parse.parse_qs returns a list for each key, get the first one
            user_id = query_params.get('id', [None])[0]
            
            if not user_id:
                self.send_response(400)
                self.end_headers()
                return

            try:
                conn = sqlite3.connect(DB_NAME)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                user = cursor.fetchone()
                conn.close()

                if user:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "id": user['id'], 
                        "name": user['name'], 
                        "surnames": user['surnames'],
                        "birthdate": user['birthdate'],
                        "email": user['email'],
                        "has_insufficiency": user['has_insufficiency'],
                        "treatment_type": user['treatment_type'],
                        "kidney_stage": user['kidney_stage'],
                        "avatar_url": user['avatar_url']
                    }).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            except Exception as e:
                print(f"Error fetching user: {e}")
                self.send_response(500)
                self.end_headers()
            return

        elif self.path == '/api/foods':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            foods = self.get_foods()
            self.wfile.write(json.dumps(foods).encode())
            return
            
        # Fallback for other GET requests (static files)
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/feedback':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                message = data.get('message', '')
                
                # Intentar enviar email
                success, note = self.send_email_notification(message)
                
                if success:
                    # Éxito
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {"status": "success", "note": note}
                    self.wfile.write(json.dumps(response).encode())
                else:
                    # Fallo controlado (contraseña mal, etc)
                    print(f"Fallo envío email: {note}")
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {"status": "error", "note": note}
                    self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                print(f"Error procesando feedback: {e}")
                self.send_response(500)
                self.end_headers()

        elif self.path == '/api/register':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                email = data.get('email')
                password = data.get('password')
                name = data.get('name')
                surnames = data.get('surnames', '')
                birthdate = data.get('birthdate', '')

                if not email or not password:
                    self.send_response(400)
                    self.end_headers()
                    return

                # Check if user exists
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    self.send_response(409) # Conflict
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "Email already exists"}).encode())
                    conn.close()
                    return

                # Create user
                hashed_pw = hash_password(password)
                cursor.execute("INSERT INTO users (email, password_hash, name, surnames, birthdate) VALUES (?, ?, ?, ?, ?)", 
                               (email, hashed_pw, name, surnames, birthdate))
                conn.commit()
                user_id = cursor.lastrowid
                conn.close()

                self.send_response(201)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success", 
                    "userId": user_id, 
                    "name": name,
                    "surnames": surnames,
                    "birthdate": birthdate
                }).encode())

            except Exception as e:
                print(f"Error registering user: {e}")
                self.send_response(500)
                self.end_headers()

        elif self.path == '/api/update_profile':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                email = data.get('email')
                name = data.get('name')
                surnames = data.get('surnames')
                birthdate = data.get('birthdate')
                has_insufficiency = data.get('has_insufficiency')
                treatment_type = data.get('treatment_type')
                kidney_stage = data.get('kidney_stage')

                if not email:
                    self.send_response(400)
                    self.end_headers()
                    return

                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                
                # Update user
                cursor.execute("""
                    UPDATE users 
                    SET name = ?, surnames = ?, birthdate = ?, has_insufficiency = ?, treatment_type = ?, kidney_stage = ?
                    WHERE email = ?
                """, (name, surnames, birthdate, has_insufficiency, treatment_type, kidney_stage, email))
                
                if cursor.rowcount == 0:
                    conn.close()
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "User not found"}).encode())
                    return

                conn.commit()
                conn.close()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())

            except Exception as e:
                print(f"Error updating profile: {e}")
                self.send_response(500)
                self.end_headers()

        elif self.path == '/api/upload_avatar':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                email = data.get('email')
                image_data = data.get('image_data')

                if not email or not image_data:
                    self.send_response(400)
                    self.end_headers()
                    return

                # Decode Base64
                if "," in image_data:
                    header, encoded = image_data.split(",", 1)
                else:
                    encoded = image_data
                
                import base64
                file_content = base64.b64decode(encoded)
                
                # Ensure directory exists
                AVATAR_DIR = "images/avatars"
                if not os.path.exists(AVATAR_DIR):
                    os.makedirs(AVATAR_DIR)
                
                # Get User ID for filename
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                user = cursor.fetchone()
                
                if not user:
                    conn.close()
                    self.send_response(404)
                    self.end_headers()
                    return

                user_id = user[0]
                filename = f"{user_id}.png"
                filepath = os.path.join(AVATAR_DIR, filename)

                # Write file
                with open(filepath, "wb") as f:
                    f.write(file_content)
                
                # Update DB
                # Store relative path for frontend - using forward slashes for web consistency
                db_path = f"images/avatars/{filename}"
                cursor.execute("UPDATE users SET avatar_url = ? WHERE id = ?", (db_path, user_id))
                conn.commit()
                conn.close()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "avatar_url": db_path}).encode())

            except Exception as e:
                print(f"Error uploading avatar: {e}")
                self.send_response(500)
                self.end_headers()
        elif self.path == '/api/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                email = data.get('email')
                password = data.get('password')

                conn = sqlite3.connect(DB_NAME)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                user = cursor.fetchone()
                conn.close()

                if user and verify_password(user['password_hash'], password):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "success", 
                        "userId": user['id'], 
                        "name": user['name'],
                        "surnames": user['surnames'],
                        "birthdate": user['birthdate'],
                        "has_insufficiency": user['has_insufficiency'],
                        "treatment_type": user['treatment_type'],
                        "kidney_stage": user['kidney_stage'],
                        "avatar_url": user['avatar_url']
                    }).encode())
                else:
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "Invalid credentials"}).encode())

            except Exception as e:
                print(f"Error logging in: {e}")
                self.send_response(500)
                self.end_headers()

        elif self.path == '/api/request_password_reset':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                email = data.get('email')

                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                user = cursor.fetchone()

                if user:
                    # Generate token
                    token = secrets.token_urlsafe(32)
                    expiry = time.time() + 3600 # 1 hour
                    
                    cursor.execute("UPDATE users SET reset_token = ?, reset_token_expiry = ? WHERE email = ?", 
                                 (token, expiry, email))
                    conn.commit()
                    
                    # Send Email
                    reset_link = f"http://localhost:{PORT}/?reset_token={token}"
                    print(f"--- DEBUG RESET LINK: {reset_link} ---")
                    body = f"""
                    <h2>Recuperación de Contraseña</h2>
                    <p>Has solicitado restablecer tu contraseña. Haz clic en el siguiente enlace:</p>
                    <p><a href="{reset_link}">Restablecer Contraseña</a></p>
                    <p>Este enlace expira en 1 hora.</p>
                    <p>Si no has sido tú, ignora este mensaje.</p>
                    """
                    
                    # Send async or sync? Sync for simplicity now, but might block.
                    # Given the current architecture, simple sync is what we have.
                    self.send_email(email, "Restablecer Contraseña - Web Renal", body)

                conn.close()
                
                # Always return success to prevent email enumeration
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "Si el email existe, se ha enviado un correo."}).encode())

            except Exception as e:
                print(f"Error requesting reset: {e}")
                self.send_response(500)
                self.end_headers()

        elif self.path == '/api/reset_password':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                token = data.get('token')
                new_password = data.get('password')
                
                if not token or not new_password:
                    self.send_response(400)
                    self.end_headers()
                    return

                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                
                # Check token and expiry
                cursor.execute("SELECT id, reset_token_expiry FROM users WHERE reset_token = ?", (token,))
                user = cursor.fetchone()
                
                if not user:
                    conn.close()
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "Token inválido"}).encode())
                    return
                
                expiry = user[1]
                if time.time() > expiry:
                    conn.close()
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "El token ha expirado"}).encode())
                    return
                
                # Update password
                hashed_pw = hash_password(new_password)
                cursor.execute("UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL WHERE id = ?", 
                             (hashed_pw, user[0]))
                conn.commit()
                conn.close()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "Contraseña actualizada"}).encode())

            except Exception as e:
                print(f"Error resetting password: {e}")
                self.send_response(500)
                self.end_headers()

        elif self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            user_message = data.get('message', '')
            user_id = data.get('userId')
            
            # 1. Fetch User Context
            context_prompt = "Eres un nefrólogo experto y nutricionista renal. Ayudas a pacientes con enfermedad renal crónica (ERC)."
            
            if user_id:
                try:
                    conn = sqlite3.connect('renal_diet.db')
                    conn.row_factory = sqlite3.Row
                    c = conn.cursor()
                    
                    # A. User Medical Data
                    c.execute('SELECT has_insufficiency, kidney_stage, treatment_type FROM users WHERE id = ?', (user_id,))
                    row = c.fetchone()
                    
                    if row:
                        has_insufficiency, stage, treatment = row['has_insufficiency'], row['kidney_stage'], row['treatment_type']
                        context_prompt += f" Contexto del Paciente: "
                        if has_insufficiency == '1' or has_insufficiency == 1:
                            if treatment == 'dialysis':
                                context_prompt += " Está en DIÁLISIS. Recuerda: Alta proteína, bajo potasio/fósforo/sodio."
                            elif treatment == 'transplant':
                                context_prompt += f" Es paciente TRASPLANTADO RENAL en Estadio {stage}."
                                if str(stage) in ['1', '2', '3a']:
                                    context_prompt += " Buen funcionamiento del injerto. NO tiene restricciones estrictas de potasio salvo indicación. Dieta general saludable."
                                else:
                                    context_prompt += " Función del injerto reducida. Debe moderar potasio, fósforo y sal."
                            else:
                                context_prompt += f" Tiene ERC Estadio {stage} (Pre-diálisis). Ojo con potasio y proteínas."
                        else:
                            context_prompt += " SIN insuficiencia renal. Consejos generales de prevención."
                    
                    # B. Food Database Search (Simple Keyword Match)
                    try:
                        # 1. Get all food names in Spanish
                        c.execute("SELECT food_id, name FROM food_translations WHERE lang='es'")
                        all_foods = c.fetchall()
                        
                        # 2. Normalize function (remove accents/lower)
                        def normalize(text):
                            import unicodedata
                            return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')

                        user_msg_norm = normalize(user_message)
                        found_foods = []

                        for food in all_foods:
                            f_name = food['name']
                            f_id = food['food_id']
                            f_name_norm = normalize(f_name)
                            
                            # Check if food name appears in user message (e.g. "platano" in "puedo comer platano")
                            # Simple heuristic: if len > 3 and name in message
                            if len(f_name_norm) > 2 and f_name_norm in user_msg_norm:
                                found_foods.append((f_id, f_name))
                        
                        # 3. If foods found, fetch their nutrients
                        if found_foods:
                            context_prompt += "\n\nDATOS NUTRICIONALES REALES (de la base de datos):"
                            for f_id, f_name in found_foods[:3]: # Limit to top 3 matches to save tokens
                                c.execute("""
                                    SELECT n.key, fn.value, n.unit 
                                    FROM food_nutrients fn 
                                    JOIN nutrients n ON fn.nutrient_id = n.id 
                                    WHERE fn.food_id = ?
                                """, (f_id,))
                                nutrients = c.fetchall()
                                
                                nut_str = ", ".join([f"{n['key']}: {n['value']}{n['unit']}" for n in nutrients if n['key'] in ['potassium','phosphorus','protein','sodium','sugar']])
                                context_prompt += f"\n- {f_name}: {nut_str}"
                            
                            context_prompt += "\n(Usa estos valores exactos para tu recomendación)."

                    except Exception as e_db:
                        print(f"Error searching food DB: {e_db}")

                    conn.close()
                            
                except Exception as e:
                    print(f"Error reading DB: {e}")

            context_prompt += "\nResponde de forma breve, empática y clara."
            
            print(f"--- CHAT DEBUG ---")
            print(f"Context Generated: {context_prompt}")
            print(f"------------------", flush=True)

            # 2. Call Google Gemini API (REST)
            # No dependencies required, just urllib
            gemini_key = os.environ.get('GEMINI_API_KEY')
            if not gemini_key:
                # Try loading from .env if not in env vars
                try:
                    with open('.env', 'r') as f:
                        for line in f:
                            if line.startswith('GEMINI_API_KEY='):
                                gemini_key = line.strip().split('=')[1]
                                break
                except:
                    pass

            if not gemini_key:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Configuration error (missing API Key)"}).encode())
                return

            # Switch to gemini-flash-lite-latest
            # The ONLY model currently working for this key (others returned 429).
            # "Lite" models are cost-effective and have different quota pools.
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={gemini_key}"
            headers = {
                "Content-Type": "application/json"
            }
            
            # Construct Gemini Payload with History
            history = data.get('history', [])
            contents = []
            
            # Add History
            for note in history:
                role = note.get('role', 'user')
                text = note.get('text', '')
                if text:
                    contents.append({
                        "role": role,
                        "parts": [{"text": text}]
                    })
            
            # Add Current Message with System Context
            # We prepend the medical context to the *current* user prompt to ensure it's strictly followed
            full_prompt = f"{context_prompt}\n\nPregunta del usuario: {user_message}"
            
            contents.append({
                "role": "user",
                "parts": [{"text": full_prompt}]
            })
            
            payload = {
                "contents": contents
            }
            
            req = urllib.request.Request(api_url, data=json.dumps(payload).encode('utf-8'), headers=headers)
            
            try:
                print(f"Sending request to Gemini...", flush=True)
                with urllib.request.urlopen(req) as response:
                    response_data = response.read().decode('utf-8')
                    result = json.loads(response_data)
                    
                    # Parse Gemini Response
                    try:
                        ai_text = result['candidates'][0]['content']['parts'][0]['text']
                    except (KeyError, IndexError) as parse_err:
                        print(f"Error parsing Gemini response: {parse_err}. Raw: {result}")
                        ai_text = "Lo siento, no pude entender la respuesta del servidor."

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"response": ai_text}).encode())
                    
            except urllib.error.HTTPError as e:
                error_content = e.read().decode()
                print(f"Gemini API Error: {e.code} - {error_content}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"AI Service Error: {e.code}", "details": {"error": error_content}}).encode())

            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error in /api/chat: {e}")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Internal Server Error", "details": {"error": str(e)}}).encode())

        else:
            self.send_error(404, "Endpoint not found")

    def send_email(self, to_email, subject, body):
        """
        Helper genérico para enviar emails.
        """
        print(f"--- Intentando enviar email a {to_email} ---\nSubject: {subject}\n-------------------------------")
        msg = MIMEMultipart()
        msg['From'] = f"Web Renal (No-Reply) <{SENDER_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html')) # Changed to HTML for links

        try:
            if not SENDER_PASSWORD or SENDER_PASSWORD == "TU_CONTRASEÑA_AQUI":
                print(">> ERROR: Faltan credenciales en el archivo .env")
                return False, "Missing credentials in .env"

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            text = msg.as_string()
            server.sendmail(SENDER_EMAIL, to_email, text)
            server.quit()
            
            print(">> Email enviado CORRECTAMENTE.")
            return True, "Email sent successfully"
            
        except Exception as e:
            print(f">> ERROR CRÍTICO enviando email: {e}")
            return False, f"Failed to send email: {e}"

    def send_email_notification(self, feedback_text):
        """
        Envía un correo con la sugerencia (wrapper legacy).
        """
        subject = "Nueva Sugerencia - Web Alimentación Renal"
        return self.send_email(RECIPIENT_EMAIL, subject, feedback_text)



    def get_foods(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Fetch all foods
            cursor.execute("SELECT id, image_url FROM foods")
            foods_rows = cursor.fetchall()
            
            # Fetch all categories per food
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
            
            # Fetch all translations
            cursor.execute("SELECT food_id, lang, name FROM food_translations")
            trans_rows = cursor.fetchall()
            trans_dict = {}
            for row in trans_rows:
                if row['food_id'] not in trans_dict:
                    trans_dict[row['food_id']] = {}
                trans_dict[row['food_id']][row['lang']] = row['name']
                
            # Fetch all nutrients
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
                # Use Spanish name as default 'name' property for compatibility, or English if missing
                default_name = names.get('es', names.get('en', 'Unknown'))
                
                # Get categories as comma-separated string for frontend compatibility
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
            
            # Sort by name ES for consistency
            foods.sort(key=lambda x: x['name'])
            
            conn.close()
            return foods
        except Exception as e:
            print(f"Error DB: {e}")
            return []

# Configurar servidor
Handler = RenalDietHandler

print(f"Servidor iniciado en http://localhost:{PORT}")
print(f"API disponible en http://localhost:{PORT}/api/foods")

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServidor detenido.")
