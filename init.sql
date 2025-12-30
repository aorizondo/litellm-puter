-- ============================================================================
-- LiteLLM PostgreSQL Initialization Script
-- ============================================================================
-- 
-- Este script inicializa la base de datos para LiteLLM con soporte para
-- pgvector (embeddings) y las tablas necesarias para logging y cache.
--
-- ============================================================================

-- Habilitar extensión pgvector para embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Crear schema para LiteLLM
CREATE SCHEMA IF NOT EXISTS litellm;

-- Configurar search path
SET search_path TO litellm, public;

-- ============================================================================
-- Tabla de logs de requests
-- ============================================================================
CREATE TABLE IF NOT EXISTS litellm.request_logs (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) UNIQUE NOT NULL,
    model VARCHAR(255) NOT NULL,
    messages JSONB,
    response JSONB,
    status_code INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255),
    api_key_hash VARCHAR(255),
    cost DECIMAL(10, 6),
    tokens_used INTEGER,
    latency_ms INTEGER
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_request_logs_created_at ON litellm.request_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_request_logs_model ON litellm.request_logs(model);
CREATE INDEX IF NOT EXISTS idx_request_logs_user_id ON litellm.request_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_request_logs_api_key_hash ON litellm.request_logs(api_key_hash);

-- ============================================================================
-- Tabla de cache de respuestas
-- ============================================================================
CREATE TABLE IF NOT EXISTS litellm.response_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(512) UNIQUE NOT NULL,
    model VARCHAR(255) NOT NULL,
    messages JSONB NOT NULL,
    response JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    hit_count INTEGER DEFAULT 0
);

-- Índices para cache
CREATE INDEX IF NOT EXISTS idx_response_cache_key ON litellm.response_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_response_cache_expires ON litellm.response_cache(expires_at);

-- ============================================================================
-- Tabla de embeddings (opcional, para búsqueda semántica)
-- ============================================================================
CREATE TABLE IF NOT EXISTS litellm.embeddings (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI ada-002 dimension
    model VARCHAR(255) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para búsqueda de similitud
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON litellm.embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================================================
-- Tabla de API keys
-- ============================================================================
CREATE TABLE IF NOT EXISTS litellm.api_keys (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_name VARCHAR(255),
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    rate_limit INTEGER,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON litellm.api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON litellm.api_keys(user_id);

-- ============================================================================
-- Tabla de usuarios
-- ============================================================================
CREATE TABLE IF NOT EXISTS litellm.users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_users_user_id ON litellm.users(user_id);

-- ============================================================================
-- Función para limpiar cache expirado
-- ============================================================================
CREATE OR REPLACE FUNCTION litellm.cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM litellm.response_cache
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Función para actualizar updated_at automáticamente
-- ============================================================================
CREATE OR REPLACE FUNCTION litellm.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para request_logs
CREATE TRIGGER update_request_logs_updated_at
    BEFORE UPDATE ON litellm.request_logs
    FOR EACH ROW
    EXECUTE FUNCTION litellm.update_updated_at_column();

-- ============================================================================
-- Permisos
-- ============================================================================
-- Otorgar permisos al usuario de LiteLLM
GRANT ALL PRIVILEGES ON SCHEMA litellm TO CURRENT_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA litellm TO CURRENT_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA litellm TO CURRENT_USER;

-- ============================================================================
-- Datos iniciales (opcional)
-- ============================================================================
-- Insertar usuario admin de ejemplo
INSERT INTO litellm.users (user_id, email, metadata)
VALUES ('admin', 'admin@example.com', '{"role": "admin"}')
ON CONFLICT (user_id) DO NOTHING;

-- ============================================================================
-- Información de inicialización
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'LiteLLM Database Initialized Successfully';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Schema: litellm';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  - request_logs';
    RAISE NOTICE '  - response_cache';
    RAISE NOTICE '  - embeddings';
    RAISE NOTICE '  - api_keys';
    RAISE NOTICE '  - users';
    RAISE NOTICE 'Extensions enabled:';
    RAISE NOTICE '  - pgvector';
    RAISE NOTICE '============================================';
END $$;
