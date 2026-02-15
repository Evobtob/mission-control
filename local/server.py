#!/usr/bin/env python3
"""
Mission Control Local Server with OpenClaw Proxy

Este servidor:
1. Serve o Mission Control em http://localhost:8080
2. Faz proxy dos pedidos para o OpenClaw gateway (evita CORS)

Uso:
    cd ~/.openclaw/workspace/mission-control
    python3 local/server.py

Depois abre: http://localhost:8080
"""

import http.server
import socketserver
import urllib.request
import json
import os
import ssl

PORT = 8080
OPENCLAW_PORT = 18789
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for all responses
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PATCH')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def translate_path(self, path):
        # Serve files from the parent directory
        parent_dir = os.path.dirname(DIRECTORY)
        return os.path.join(parent_dir, path.lstrip('/'))

    def do_GET(self):
        # Proxy OpenClaw API requests
        if self.path.startswith('/api/'):
            self.proxy_to_openclaw('GET')
            return
        super().do_GET()

    def do_POST(self):
        # Proxy OpenClaw API requests
        if self.path.startswith('/api/'):
            self.proxy_to_openclaw('POST')
            return
        super().do_POST()

    def do_PATCH(self):
        # Proxy OpenClaw API requests
        if self.path.startswith('/api/'):
            self.proxy_to_openclaw('PATCH')
            return
        self.send_error(405, "Method not allowed")

    def proxy_to_openclaw(self, method):
        """Forward request to OpenClaw gateway"""
        try:
            target_url = f"http://localhost:{OPENCLAW_PORT}{self.path}"

            # Read request body if present
            body = None
            content_length = self.headers.get('Content-Length')
            if content_length:
                body = self.rfile.read(int(content_length))

            # Create request
            req_headers = {}
            if self.headers.get('Content-Type'):
                req_headers['Content-Type'] = self.headers.get('Content-Type')
            if self.headers.get('Authorization'):
                req_headers['Authorization'] = self.headers.get('Authorization')

            req = urllib.request.Request(
                target_url,
                data=body,
                method=method,
                headers=req_headers
            )

            # Send request to OpenClaw
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    response_body = response.read()
                    self.send_response(response.status)
                    # Copy response headers
                    for header, value in response.headers.items():
                        if header.lower() not in ['transfer-encoding', 'connection']:
                            try:
                                self.send_header(header, value)
                            except:
                                pass
                    self.end_headers()
                    self.wfile.write(response_body)
                    return
            except urllib.error.HTTPError as e:
                error_body = e.read()
                self.send_response(e.code)
                for header, value in e.headers.items():
                    if header.lower() not in ['transfer-encoding', 'connection']:
                        try:
                            self.send_header(header, value)
                        except:
                            pass
                self.end_headers()
                self.wfile.write(error_body)
                return

        except urllib.error.URLError as e:
            # Connection refused - gateway not running
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({
                "ok": False,
                "error": "Gateway offline",
                "message": f"Cannot connect to OpenClaw gateway at localhost:{OPENCLAW_PORT}. Is it running? Try: openclaw gateway start"
            })
            self.wfile.write(error_response.encode())
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({
                "ok": False,
                "error": str(e),
                "message": f"Failed to connect to OpenClaw gateway. Is it running on port {OPENCLAW_PORT}?"
            })
            self.wfile.write(error_response.encode())

if __name__ == '__main__':
    os.chdir(os.path.dirname(DIRECTORY))

    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"🚀 Mission Control Server running at http://localhost:{PORT}")
        print(f"📁 Serving files from: {os.path.dirname(DIRECTORY)}")
        print(f"🔗 OpenClaw Proxy: http://localhost:{PORT}/api/ → http://localhost:{OPENCLAW_PORT}/api/")
        print("\n💡 Press Ctrl+C to stop")
        print("=" * 50)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped")
