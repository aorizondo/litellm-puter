# Multi-stage build para reducir tamaño final
FROM python:3.12-slim as builder

# Variables de entorno para build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Copiar archivos de dependencias
COPY requirements.txt pyproject.toml ./
COPY litellm_puter/ ./litellm_puter/

# Instalar dependencias de build y Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && pip install --upgrade pip setuptools wheel \
    && pip install --prefix=/install -r requirements.txt \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Imagen final
FROM python:3.12-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    DISPLAY=:99 \
    CHROME_BIN=/usr/bin/google-chrome-stable

WORKDIR /app

# Copiar dependencias Python desde builder
COPY --from=builder /install /usr/local

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chrome dependencies
    wget \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libexpat1 \
    libgbm1 \
    libglib2.0-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxshmfence1 \
    # Xvfb y xvfbwrapper
    xvfb \
    python3-xvfbwrapper \
    # PostgreSQL client
    libpq5 \
    # Utilidades
    netcat-openbsd \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && playwright install chrome --with-deps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copiar archivos de la aplicación
COPY litellm_puter/ ./litellm_puter/
COPY config.yaml entrypoint.sh ./

# Hacer ejecutable el entrypoint
RUN chmod +x entrypoint.sh

# Crear usuario no-root
RUN useradd -m -u 1000 litellm && chown -R litellm:litellm /app
USER litellm

# Puerto para LiteLLM
EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:4000/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["litellm", "--config", "/app/config.yaml", "--port", "4000", "--host", "0.0.0.0"]