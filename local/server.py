#!/usr/bin/env python3
"""
Mission Control Local Server

Este servidor simples serve o Mission Control com CORS habilitado
para permitir conexão ao gateway OpenClaw em localhost:18789

Uso:
    cd ~/.openclaw/workspace/mission-control
    python3 local/server.py

Depois abre: http://localhost:8080
"""

import http.server
import socketserver
import os

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()

    def translate_path(self, path):
        # Serve files from the parent directory (where index.html is)
        parent_dir = os.path.dirname(DIRECTORY)
        return os.path.join(parent_dir, path.lstrip('/'))

if __name__ == '__main__':
    os.chdir(os.path.dirname(DIRECTORY))  # Change to parent directory

    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"🚀 Mission Control Server running at http://localhost:{PORT}")
        print(f"📁 Serving files from: {os.path.dirname(DIRECTORY)}")
        print("\n💡 Press Ctrl+C to stop")
        print("=" * 50)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped")
