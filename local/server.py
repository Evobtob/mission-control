#!/usr/bin/env python3
"""
Mission Control Local Server with OpenClaw Bridge Proxy

Este servidor:
1. Serve o Mission Control em http://localhost:8080
2. Faz proxy dos pedidos /api/* para o OpenClaw Bridge (localhost:18790)

O OpenClaw Bridge é necessário porque o gateway OpenClaw (porta 18789) não expõe API REST.
O Bridge executa comandos CLI e expõe REST API na porta 18790.

Uso:
    cd ~/.openclaw/workspace/mission-control
    python3 local/server.py

Requisitos:
    1. OpenClaw Bridge deve estar a correr:
       python3 openclaw-bridge.py

    2. Depois abre: http://localhost:8080
"""

import http.server
import socketserver
import urllib.request
import json
import os
import subprocess

PORT = 8080
BRIDGE_PORT = 18790  # Porta do OpenClaw Bridge
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

    def check_bridge_running(self):
        """Verifica se o bridge está a correr"""
        try:
            # Tenta fazer um pedido simples ao bridge
            req = urllib.request.Request(f'http://localhost:{BRIDGE_PORT}/', method='HEAD')
            with urllib.request.urlopen(req, timeout=2) as response:
                return True
        except:
            return False

    def do_GET(self):
        # Proxy OpenClaw API requests to the Bridge
        if self.path.startswith('/api/'):
            self.proxy_to_bridge('GET')
            return
        super().do_GET()

    def do_POST(self):
        # Proxy OpenClaw API requests to the Bridge
        if self.path.startswith('/api/'):
            self.proxy_to_bridge('POST')
            return
        super().do_POST()

    def do_PATCH(self):
        if self.path.startswith('/api/'):
            self.proxy_to_bridge('PATCH')
            return
        self.send_error(405, "Method not allowed")

    def proxy_to_bridge(self, method):
        """Forward request to OpenClaw Bridge"""

        # Verifica se bridge está a correr
        if not self.check_bridge_running():
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({
                "ok": False,
                "error": "OpenClaw Bridge offline",
                "message": f"O Bridge não está a correr em localhost:{BRIDGE_PORT}.\n\nPara iniciar:\n1. Abre outro terminal\n2. cd ~/.openclaw/workspace/mission-control\n3. python3 openclaw-bridge.py"
            })
            self.wfile.write(error_response.encode())
            return

        try:
            target_url = f"http://localhost:{BRIDGE_PORT}{self.path}"

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

            # Send request to Bridge
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
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
            # Connection refused - bridge not running
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({
                "ok": False,
                "error": "Bridge connection failed",
                "message": f"Cannot connect to OpenClaw Bridge at localhost:{BRIDGE_PORT}. Is it running?"
            })
            self.wfile.write(error_response.encode())
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({
                "ok": False,
                "error": str(e),
                "message": f"Failed to proxy to Bridge on port {BRIDGE_PORT}"
            })
            self.wfile.write(error_response.encode())


if __name__ == '__main__':
    os.chdir(os.path.dirname(DIRECTORY))

    # Verifica se bridge está a correr
    bridge_running = False
    try:
        req = urllib.request.Request(f'http://localhost:{BRIDGE_PORT}/', method='HEAD')
        with urllib.request.urlopen(req, timeout=2) as response:
            bridge_running = True
    except:
        pass

    print(f"🚀 Mission Control Server running at http://localhost:{PORT}")
    print(f"📁 Serving files from: {os.path.dirname(DIRECTORY)}")

    if bridge_running:
        print(f"🔗 OpenClaw Bridge: ✅ Connected (port {BRIDGE_PORT})")
        print(f"   API Proxy active: /api/* → localhost:{BRIDGE_PORT}")
    else:
        print(f"⚠️  OpenClaw Bridge: ❌ NOT RUNNING")
        print(f"   Para iniciar o Bridge:")
        print(f"   python3 openclaw-bridge.py")
        print(f"")
        print(f"   O Mission Control vai funcionar em modo offline até o Bridge iniciar.")

    print(f"\n💡 Abre no browser: http://localhost:{PORT}")
    print(f"=" * 50)

    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped")
