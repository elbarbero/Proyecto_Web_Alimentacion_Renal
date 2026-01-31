import http.server
import socketserver
import json
import urllib.parse
from backend.database import run_migrations
from backend.handlers import auth, users, foods, chat, countries
from backend.config import PORT

# Start migrations on boot
run_migrations()

class RenalDietHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # API Routes
        if path == '/api/get_user':
            query_params = urllib.parse.parse_qs(parsed_path.query)
            users.handle_get_user(query_params, self)
            return

        elif path == '/api/foods':
            foods.handle_get_foods(self)
            return
            
        elif path == '/api/countries':
            countries.handle_get_countries(self)
            return
            
        # Static Files Routing
        if path == '/':
             self.path = '/index.html'
        
        return super().do_GET()

    def do_POST(self):
        # Read body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            data = {}

        path = self.path

        if path == '/api/login':
            auth.handle_login(data, self)
        
        elif path == '/api/register':
            auth.handle_register(data, self)

        elif path == '/api/request_password_reset':
            auth.handle_request_reset(data, self)

        elif path == '/api/reset_password':
            auth.handle_reset_password(data, self)
            
        elif path == '/api/update_profile':
            users.handle_update_profile(data, self)
            
        elif path == '/api/upload_avatar':
            users.handle_upload_avatar(data, self)
            
        elif path == '/api/feedback':
            foods.handle_feedback(data, self)
            
        elif path == '/api/chat':
            chat.handle_chat(data, self)
            
        else:
            self.send_error(404, "Endpoint not found")

print(f"Servidor iniciado en http://localhost:{PORT}")
try:
    with socketserver.TCPServer(("", PORT), RenalDietHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServidor detenido.")
