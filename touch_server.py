from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import sys
import socket

PORT = 5000

class TouchHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        client_ip = self.client_address[0]
        print(f"[REQUEST] from {client_ip}: {self.path}")
        
        if self.path == '/touch':
            print("[TOUCH DETECTED] Launching controller.py...")
            try:
                # Run controller.py
                subprocess.Popen([sys.executable, "main_controller.py"])
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Robot started!")
                print("[SUCCESS] Robot controller launched")
            except Exception as e:
                print(f"[ERROR] Failed to launch controller: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Error: {str(e)}".encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Not found")

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote server to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "localhost"

if __name__ == "__main__":
    # Bind to all interfaces (0.0.0.0) instead of just localhost
    server = HTTPServer(('0.0.0.0', PORT), TouchHandler)
    local_ip = get_local_ip()
    
    print(f"Touch Server Starting...")
    print(f"Local IP: {local_ip}")
    print(f"Listening on all interfaces, port {PORT}")
    print(f"ESP32 should connect to: http://{local_ip}:{PORT}/touch")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.server_close()