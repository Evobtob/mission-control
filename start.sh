#!/bin/bash
#
# Start NIA OS Mission Control with OpenClaw Bridge
# Este script inicia ambos os servidores necessários para sincronização completa
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 NIA OS Mission Control - Startup Script"
echo "=========================================="
echo ""

# Verifica se python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Erro: python3 não encontrado"
    exit 1
fi

# Verifica se openclaw CLI está disponível
if ! command -v openclaw &> /dev/null; then
    echo "⚠️  Aviso: openclaw CLI não encontrado no PATH"
    echo "   O Bridge pode não funcionar corretamente."
    echo ""
fi

# Função para limpar processos ao sair
cleanup() {
    echo ""
    echo "🛑 A parar servidores..."
    if [ -n "$BRIDGE_PID" ]; then
        kill $BRIDGE_PID 2>/dev/null
        echo "   Bridge parado"
    fi
    if [ -n "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null
        echo "   Server parado"
    fi
    echo "👋 Adeus!"
    exit 0
}

# Captura Ctrl+C
trap cleanup INT TERM

echo "📋 Arquitetura:"
echo "   1. OpenClaw Bridge (porta 18790) ← CLI → OpenClaw"
echo "   2. Mission Control Server (porta 8080) ← Proxy → Bridge"
echo ""

# Inicia o Bridge em background
echo "🦞 A iniciar OpenClaw Bridge na porta 18790..."
python3 openclaw-bridge.py > /tmp/openclaw-bridge.log 2>&1 &
BRIDGE_PID=$!

# Espera um pouco e verifica se iniciou
sleep 2
if ! kill -0 $BRIDGE_PID 2>/dev/null; then
    echo "❌ Erro: Bridge não conseguiu iniciar"
    echo "   Verifica: cat /tmp/openclaw-bridge.log"
    exit 1
fi

echo "   ✅ Bridge iniciado (PID: $BRIDGE_PID)"
echo ""

# Inicia o Mission Control Server em background
echo "🌐 A iniciar Mission Control Server na porta 8080..."
python3 local/server.py > /tmp/mission-control-server.log 2>&1 &
SERVER_PID=$!

# Espera e verifica
sleep 2
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "❌ Erro: Server não conseguiu iniciar"
    echo "   Verifica: cat /tmp/mission-control-server.log"
    kill $BRIDGE_PID 2>/dev/null
    exit 1
fi

echo "   ✅ Server iniciado (PID: $SERVER_PID)"
echo ""

echo "=========================================="
echo "🎉 NIA OS está pronto!"
echo ""
echo "🔗 Acede em: http://localhost:8080"
echo "📖 Documentação API: http://localhost:18790/"
echo ""
echo "⚠️  Para parar, prime Ctrl+C"
echo "=========================================="
echo ""

# Mantém o script a correr
wait
