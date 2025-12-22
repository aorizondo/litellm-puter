#!/bin/bash
set -e

# Iniciar Xvfb en background si está habilitado
if [ "${USE_XVFB:-1}" = "1" ] || [ "${USE_XVFB:-1}" = "true" ]; then
    echo "🖥️  Iniciando Xvfb en display :99"
    rm -f /tmp/.X99-lock 2>/dev/null || true
    Xvfb :99 -screen 0 1280x1024x24 -ac +extension GLX +render -noreset &
    XVFB_PID=$!
    export DISPLAY=:99
    sleep 2
    echo "✅ Xvfb iniciado (PID: $XVFB_PID)"
fi

# Esperar a PostgreSQL si está configurado
if [ -n "${DATABASE_URL}" ] || [ -n "${POSTGRES_HOST}" ]; then
    POSTGRES_HOST="${POSTGRES_HOST:-db}"
    POSTGRES_PORT="${POSTGRES_PORT:-5432}"

    echo "⏳ Esperando a PostgreSQL en ${POSTGRES_HOST}:${POSTGRES_PORT}..."

    timeout=30
    while ! nc -z "${POSTGRES_HOST}" "${POSTGRES_PORT}"; do
        timeout=$((timeout-1))
        if [ $timeout -le 0 ]; then
            echo "❌ Timeout esperando PostgreSQL"
            exit 1
        fi
        echo "⚠️  PostgreSQL no disponible, reintentando..."
        sleep 1
    done
    echo "✅ PostgreSQL listo!"
fi

# Verificar Chrome
if [ -x "$(command -v google-chrome)" ]; then
    echo "🌐 Chrome disponible: $(google-chrome --version)"
else
    echo "❌ Chrome no encontrado"
    exit 1
fi

echo "🚀 Iniciando aplicación..."
exec "$@"