#!/usr/bin/env python3
"""
OpenClaw API Bridge for NIA OS Mission Control

Este servidor atua como ponte entre o NIA OS (Mission Control) e o OpenClaw.
Como o gateway OpenClaw não expõe API REST diretamente, este servidor:
1. Executa comandos CLI openclaw
2. Parseia o output JSON
3. Expõe REST API padronizada para o Mission Control

Uso:
    python3 openclaw-bridge.py

Endpoints:
    GET /api/v1/status          → Status completo do OpenClaw
    GET /api/v1/gateway/status  → Status do gateway
    GET /api/v1/cron/list       → Lista de cron jobs
    GET /api/v1/sessions/list   → Lista de sessões ativas
    GET /api/v1/agents/list     → Lista de agentes configurados
"""

import http.server
import socketserver
import json
import subprocess
import os
import sys
from urllib.parse import urlparse, parse_qs

PORT = 18791  # Porta diferente do gateway (18789)

class OpenClawBridgeHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Custom log com timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {self.address_string()} - {format % args}")

    def end_headers(self):
        # CORS headers para permitir acesso do Mission Control
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # API endpoints
        if path == '/api/v1/status':
            self.handle_status()
        elif path == '/api/v1/gateway/status':
            self.handle_gateway_status()
        elif path == '/api/v1/cron/list':
            self.handle_cron_list()
        elif path == '/api/v1/sessions/list':
            self.handle_sessions_list()
        elif path == '/api/v1/agents/list':
            self.handle_agents_list()
        elif path == '/':
            self.handle_index()
        else:
            self.send_error(404, "Endpoint not found")

    def run_openclaw_cli(self, args):
        """Executa comando openclaw CLI e retorna JSON"""
        try:
            cmd = ['openclaw'] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.expanduser('~')
            )

            if result.returncode != 0:
                return {
                    "ok": False,
                    "error": f"CLI error (code {result.returncode})",
                    "stderr": result.stderr[:500]
                }

            # Parse JSON output
            try:
                data = json.loads(result.stdout)
                return {"ok": True, "result": data}
            except json.JSONDecodeError as e:
                return {
                    "ok": False,
                    "error": f"Invalid JSON from CLI: {str(e)}",
                    "raw": result.stdout[:1000]
                }

        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "CLI command timed out"}
        except FileNotFoundError:
            return {"ok": False, "error": "openclaw CLI not found. Is OpenClaw installed?"}
        except Exception as e:
            return {"ok": False, "error": f"Unexpected error: {str(e)}"}

    def send_json_response(self, data, status_code=200):
        """Envia resposta JSON"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def handle_status(self):
        """Status completo do OpenClaw"""
        data = self.run_openclaw_cli(['status', '--json'])
        self.send_json_response(data)

    def handle_gateway_status(self):
        """Status específico do gateway"""
        full_status = self.run_openclaw_cli(['status', '--json'])

        if not full_status.get('ok'):
            self.send_json_response(full_status)
            return

        result = full_status.get('result', {})
        gateway = result.get('gateway', {})
        service = result.get('gatewayService', {})

        simplified = {
            "ok": True,
            "result": {
                "running": gateway.get('reachable', False) and 'running' in service.get('runtimeShort', ''),
                "url": gateway.get('url', 'ws://127.0.0.1:18789'),
                "reachable": gateway.get('reachable', False),
                "connectLatencyMs": gateway.get('connectLatencyMs', 0),
                "version": "v2026.2.13",  # Versão atual
                "model": result.get('sessions', {}).get('defaults', {}).get('model', 'kimi-k2.5:cloud'),
                "pid": service.get('runtimeShort', '').replace('running (pid ', '').replace(')', '') if 'running' in service.get('runtimeShort', '') else None,
                "mode": gateway.get('mode', 'local')
            }
        }
        self.send_json_response(simplified)

    def handle_cron_list(self):
        """Lista de cron jobs"""
        data = self.run_openclaw_cli(['cron', 'list', '--json'])

        if not data.get('ok'):
            self.send_json_response(data)
            return

        # Formata para o formato esperado pelo Mission Control
        jobs = data.get('result', {}).get('jobs', [])
        formatted = {
            "ok": True,
            "result": {
                "jobs": [
                    {
                        "id": job.get('id', f"job-{i}"),
                        "name": job.get('name', job.get('id', f"Job {i}")),
                        "description": job.get('description', ''),
                        "enabled": job.get('enabled', True),
                        "schedule": job.get('schedule', {}),
                        "payload": job.get('payload', {})
                    }
                    for i, job in enumerate(jobs)
                ],
                "total": len(jobs),
                "enabled": sum(1 for j in jobs if j.get('enabled', True))
            }
        }
        self.send_json_response(formatted)

    def handle_sessions_list(self):
        """Lista de sessões ativas"""
        data = self.run_openclaw_cli(['sessions', 'list', '--json'])

        if not data.get('ok'):
            self.send_json_response(data)
            return

        result = data.get('result', {})
        sessions = result.get('sessions', [])

        formatted = {
            "ok": True,
            "result": {
                "sessions": [
                    {
                        "key": s.get('key', ''),
                        "kind": s.get('kind', 'direct'),
                        "agentId": s.get('key', '').split(':')[1] if ':' in s.get('key', '') else 'main',
                        "channel": s.get('key', '').split(':')[2] if s.get('key', '').count(':') >= 2 else 'main',
                        "sessionId": s.get('sessionId', ''),
                        "updatedAt": s.get('updatedAt', 0),
                        "ageMs": s.get('ageMs', 0),
                        "model": s.get('model', 'unknown'),
                        "inputTokens": s.get('inputTokens', 0),
                        "outputTokens": s.get('outputTokens', 0),
                        "totalTokens": s.get('totalTokens', 0),
                        "contextTokens": s.get('contextTokens', 0),
                        "systemSent": s.get('systemSent', False)
                    }
                    for s in sessions
                ],
                "count": result.get('count', len(sessions)),
                "path": result.get('path', '')
            }
        }
        self.send_json_response(formatted)

    def handle_agents_list(self):
        """Lista de agentes configurados"""
        full_status = self.run_openclaw_cli(['status', '--json'])

        if not full_status.get('ok'):
            self.send_json_response(full_status)
            return

        agents_data = full_status.get('result', {}).get('agents', {})
        agents_list = agents_data.get('agents', [])

        # Ler SOUL.md e outros ficheiros de configuração para cada agente
        enriched_agents = []
        for agent in agents_list:
            agent_id = agent.get('id', 'main')
            workspace_dir = agent.get('workspaceDir', os.path.expanduser('~/.openclaw/workspace'))

            agent_info = {
                "id": agent_id,
                "workspaceDir": workspace_dir,
                "sessionsCount": agent.get('sessionsCount', 0),
                "lastActiveAgeMs": agent.get('lastActiveAgeMs', 0),
                "bootstrapPending": agent.get('bootstrapPending', False)
            }

            # Tentar ler IDENTITY.md se existir
            identity_path = os.path.join(workspace_dir, 'IDENTITY.md')
            if os.path.exists(identity_path):
                try:
                    with open(identity_path, 'r') as f:
                        content = f.read()
                        # Extrair nome, emoji, tipo
                        if 'Name:' in content:
                            agent_info['name'] = content.split('Name:')[1].split('\n')[0].strip()
                        if 'Emoji:' in content:
                            agent_info['emoji'] = content.split('Emoji:')[1].split('\n')[0].strip()
                        if 'Creature:' in content or 'Type:' in content:
                            agent_info['type'] = content.split('Creature:')[1].split('\n')[0].strip() if 'Creature:' in content else content.split('Type:')[1].split('\n')[0].strip()
                except:
                    pass

            enriched_agents.append(agent_info)

        formatted = {
            "ok": True,
            "result": {
                "agents": enriched_agents,
                "totalSessions": agents_data.get('totalSessions', 0),
                "defaultId": agents_data.get('defaultId', 'main')
            }
        }
        self.send_json_response(formatted)

    def handle_index(self):
        """Página inicial com documentação da API"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()

        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClaw API Bridge</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background: #0a0a0a; color: #e0e0e0; }
        h1 { color: #E82127; }
        h2 { color: #fff; border-bottom: 1px solid #333; padding-bottom: 10px; }
        .endpoint { background: #1a1a1a; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #E82127; }
        .method { color: #4ade80; font-weight: bold; }
        .url { color: #60a5fa; font-family: monospace; }
        code { background: #333; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
        .status { display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 0.875rem; font-weight: 600; }
        .status.ok { background: #4ade80; color: #000; }
    </style>
</head>
<body>
    <h1>🦞 OpenClaw API Bridge</h1>
    <p>Servidor ponte entre NIA OS Mission Control e OpenClaw CLI</p>

    <h2>Status</h2>
    <p><span class="status ok">RUNNING</span> Porta: <code>18790</code></p>

    <h2>Endpoints Disponíveis</h2>

    <div class="endpoint">
        <span class="method">GET</span> <span class="url">/api/v1/status</span>
        <p>Status completo do OpenClaw (equivalente a <code>openclaw status --json</code>)</p>
    </div>

    <div class="endpoint">
        <span class="method">GET</span> <span class="url">/api/v1/gateway/status</span>
        <p>Status simplificado do gateway (running, url, latency, etc.)</p>
    </div>

    <div class="endpoint">
        <span class="method">GET</span> <span class="url">/api/v1/cron/list</span>
        <p>Lista de cron jobs configurados</p>
    </div>

    <div class="endpoint">
        <span class="method">GET</span> <span class="url">/api/v1/sessions/list</span>
        <p>Sessões ativas com metadados (tokens, modelo, etc.)</p>
    </div>

    <div class="endpoint">
        <span class="method">GET</span> <span class="url">/api/v1/agents/list</span>
        <p>Agentes configurados com info de IDENTITY.md</p>
    </div>

    <h2>Integração NIA OS</h2>
    <p>Para usar com o Mission Control, atualiza a configuração da API:</p>
    <pre style="background: #1a1a1a; padding: 15px; border-radius: 8px; overflow-x: auto;">
const OPENCLAW_CONFIG = {
    host: 'localhost',
    port: 18790,  // ← Alterado de 18789 para 18790
    token: '',     // ← Não necessário para bridge local
    connected: false
};</pre>

    <p style="margin-top: 40px; color: #666; font-size: 0.875rem;">
        OpenClaw API Bridge v1.0 | NIA OS Integration
    </p>
</body>
</html>"""
        self.wfile.write(html.encode())


if __name__ == '__main__':
    print(f"🦞 OpenClaw API Bridge")
    print(f"🔗 API URL: http://localhost:{PORT}")
    print(f"📖 Docs: http://localhost:{PORT}/")
    print(f"\n💡 Para usar com NIA OS Mission Control:")
    print(f"   Atualiza a porta de 18789 para {PORT} no ficheiro index.html")
    print(f"\n⚠️  Certifica-te que o servidor local (local/server.py) está a correr em :8080")
    print(f"=" * 50)

    with socketserver.TCPServer(("", PORT), OpenClawBridgeHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Bridge stopped")
