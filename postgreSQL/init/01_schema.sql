-- ==============================================================================
-- PROYECTO CIMSI - SISTEMA DE BASE DE DATOS RELACIONAL (POSTGRESQL)
-- Arquitectura de Microservicios / Clúster Docker Swarm (6 Raspberry Pi)
-- Responsable: José (PostgreSQL - Capa Relacional en Worker 1)
--
-- MODELO SIMPLIFICADO: Solo tabla 'players' (Fase Inicial del Juego)
-- ==============================================================================

-- 1. Función disparadora para actualizar automáticamente 'updated_at'
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- TABLA: PLAYERS (Cuentas y Credenciales de Jugadores)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS players (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login TIMESTAMPTZ
);

-- Índice para búsquedas rápidas por nombre de usuario al autenticar
CREATE INDEX IF NOT EXISTS idx_players_username ON players(username);

-- Trigger para mantener actualizado 'updated_at' en cada modificación
CREATE TRIGGER trg_players_updated_at
BEFORE UPDATE ON players
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
