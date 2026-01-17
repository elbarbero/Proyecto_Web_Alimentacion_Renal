import http.server
import socketserver
import json
import sqlite3
import os

PORT = 8000
DB_NAME = "renal_diet.db"

class RenalDietHandler(http.server.SimpleHTTPRequestHandler):
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
