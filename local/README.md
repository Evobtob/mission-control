# Mission Control - Modo Local (CORS Fix)

## O Problema

O Mission Control hospedado no GitHub Pages não consegue conectar-se diretamente ao gateway OpenClaw em `localhost:18789` devido a restrições de segurança do browser (CORS).

## Solução: Modo Local

### Opção 1: Servidor Python (Recomendado)

1. Abre o terminal no Mac
2. Vai para a pasta do Mission Control:
```bash
cd ~/.openclaw/workspace/mission-control
```

3. Inicia o servidor local:
```bash
python3 local/server.py
```

4. Abre no browser:
```
http://localhost:8080
```

5. Agora o Mission Control consegue falar com o OpenClaw gateway! 🎉

### Opção 2: Abrir diretamente (modo demo)

1. Abre o ficheiro local:
```
~/.openclaw/workspace/mission-control/local/index.html
```

2. Funciona em modo demo (sem dados reais do OpenClaw)

### Opção 3: Tailscale Funnel (Acesso remoto)

Para aceder de qualquer lugar (incluindo GitHub Pages):

```bash
# Configura o OpenClaw gateway para usar Tailscale Funnel
openclaw gateway --tailscale funnel --auth password
```

Depois atualiza o Mission Control para usar o URL Tailscale em vez de localhost.

---

## Comandos úteis

```bash
# Ver estado do gateway
openclaw gateway status

# Obter token para o Mission Control
openclaw gateway token
# ou
cat ~/.openclaw/openclaw.json | grep token

# Testar se o gateway está a responder
curl http://localhost:18789/api/v1/status
```

## Ligação automática

O Mission Control guarda o token em `localStorage` do browser. Depois de introduzir uma vez, lembra-se para as próximas vezes.
