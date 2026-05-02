import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    
    def log_message(self, format, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"[HEALTH] Health check server running on port {port}")
    server.serve_forever()

def start_health_server():
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    print("[HEALTH] Health check server thread started")
