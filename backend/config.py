import os

def load_env():
    """Load environment variables from .env file"""
    env_vars = {}
    try:
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        val = value.strip().strip('"').strip("'")
                        if key == "EMAIL_PASS":
                            val = val.replace(" ", "")
                        env_vars[key] = val
                        if key not in os.environ:
                            os.environ[key] = val
            print("Cargada configuración desde .env")
    except Exception as e:
        print(f"Nota: No se pudo leer .env: {e}")
    return env_vars

ENV = load_env()

SMTP_SERVER = os.environ.get("SMTP_SERVER", ENV.get("SMTP_SERVER", "smtp.gmail.com"))
SMTP_PORT = int(os.environ.get("SMTP_PORT", ENV.get("SMTP_PORT", 587)))
SENDER_EMAIL = os.environ.get("EMAIL_USER", ENV.get("EMAIL_USER", "nutrirenalweb@gmail.com"))
SENDER_PASSWORD = os.environ.get("EMAIL_PASS", ENV.get("EMAIL_PASS", ""))
RECIPIENT_EMAIL = os.environ.get("EMAIL_RECIPIENT", ENV.get("EMAIL_RECIPIENT", "nutrirenalweb@gmail.com"))
DB_NAME = "renal_diet.db"
PORT = 8000
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", ENV.get("GEMINI_API_KEY", ""))
