import http.server
import socketserver
import json
import sqlite3
import os

PORT = 8000
DB_NAME = "renal_diet.db"

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import binascii

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

# Prioridad: Variables de entorno sistema > Fichero .env > Valores por defecto
SMTP_SERVER = os.environ.get("SMTP_SERVER", env.get("SMTP_SERVER", "smtp.gmail.com"))
SMTP_PORT = int(os.environ.get("SMTP_PORT", env.get("SMTP_PORT", 587)))
SENDER_EMAIL = os.environ.get("EMAIL_USER", env.get("EMAIL_USER", "nutrirenalweb@gmail.com"))
SENDER_PASSWORD = os.environ.get("EMAIL_PASS", env.get("EMAIL_PASS", ""))
RECIPIENT_EMAIL = os.environ.get("EMAIL_RECIPIENT", env.get("EMAIL_RECIPIENT", "nutrirenalweb@gmail.com"))

class RenalDietHandler(http.server.SimpleHTTPRequestHandler):
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
                self.wfile.write(json.dumps({"status": "success", "userId": user_id, "name": name}).encode())

            except Exception as e:
                print(f"Error registering user: {e}")
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
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, password_hash FROM users WHERE email = ?", (email,))
                user = cursor.fetchone()
                conn.close()

                if user and verify_password(user[2], password):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success", "userId": user[0], "name": user[1]}).encode())
                else:
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "Invalid credentials"}).encode())

            except Exception as e:
                print(f"Error logging in: {e}")
                self.send_response(500)
                self.end_headers()

        else:
            self.send_error(404, "Endpoint not found")

    def send_email_notification(self, feedback_text):
        """
        Envía un correo con la sugerencia usando credenciales seguras.
        """
        print(f"--- Intentando enviar email ---\n{feedback_text}\n-------------------------------")
        # Configurar mensaje
        msg = MIMEMultipart()
        # "Web Renal (No-Reply)" será el nombre que veas, aunque el correo siga siendo el tuyo (Gmail obliga a esto)
        msg['From'] = f"Web Renal (No-Reply) <{SENDER_EMAIL}>"
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = "Nueva Sugerencia - Web Alimentación Renal"
        msg.attach(MIMEText(feedback_text, 'plain'))

        try:
            if not SENDER_PASSWORD or SENDER_PASSWORD == "TU_CONTRASEÑA_AQUI":
                print(">> ERROR: Faltan credenciales en el archivo .env")
                return False, "Missing credentials in .env"

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            text = msg.as_string()
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, text)
            server.quit()
            
            print(">> Email enviado CORRECTAMENTE.")
            return True, "Email sent successfully"
            
        except Exception as e:
            print(f">> ERROR CRÍTICO enviando email: {e}")
            return False, f"Failed to send email: {e}"

    def do_GET(self):
        # Rutas de API
        if self.path == '/api/foods':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            foods = self.get_foods()
            self.wfile.write(json.dumps(foods).encode())
        else:
            # Servir archivos estáticos (HTML, CSS, JS) normalmente
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def get_foods(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            conn.row_factory = sqlite3.Row # Para acceder por nombre de columna
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM foods")
            rows = cursor.fetchall()
            
            foods = []
            for row in rows:
                foods.append({
                    "id": row["id"],
                    "name": row["name"],
                    "names": {
                        "es": row["name"],
                        "en": row["name_en"],
                        "de": row["name_de"],
                        "fr": row["name_fr"],
                        "pt": row["name_pt"],
                        "ja": row["name_ja"]
                    },
                    "image": row["image_url"],
                    "nutrients": {
                        "protein": row["protein"],
                        "sugar": row["sugar"],
                        "fat": row["fat"],
                        "potassium": row["potassium"],
                        "phosphorus": row["phosphorus"],
                        "salt": row["salt"],
                        "calcium": row["calcium"]
                    }
                })
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
