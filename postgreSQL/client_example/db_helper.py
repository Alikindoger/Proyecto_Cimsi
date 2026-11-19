"""
Módulo de Integración con PostgreSQL para el Proyecto CIMSI.
Diseñado para la gestión y autenticación de cuentas (tabla 'players').

Uso principal:
  - TokenManager: Verificar que el usuario existe y la contraseña es correcta antes de emitir tokens en Redis.
  - GameServer: Consultar información básica del jugador si se requiere.

Utiliza asyncpg para consultas asíncronas compatibles con asyncio y websockets.
"""

import os
import asyncio
import asyncpg
import bcrypt
from typing import Optional, List, Dict, Any

# Variables de entorno
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "cimsi_game")
DB_USER = os.getenv("POSTGRES_USER", "cimsi_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "cimsi2627")


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Inicializa el pool de conexiones a PostgreSQL."""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                min_size=2,
                max_size=10,
            )
            print(f"[DB] Conexión establecida con PostgreSQL ({DB_HOST}:{DB_PORT}/{DB_NAME})")

    async def disconnect(self):
        """Cierra el pool de conexiones."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            print("[DB] Pool de conexiones cerrado.")

    # --------------------------------------------------------------------------
    # MÉTODOS DE JUGADORES / CUENTAS
    # --------------------------------------------------------------------------
    async def get_player_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Busca un jugador por su nombre de usuario."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, username, password_hash, email, created_at, updated_at, last_login FROM players WHERE username = $1",
                username
            )
            return dict(row) if row else None

    async def get_player_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Busca un jugador por su ID numérico."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, username, password_hash, email, created_at, updated_at, last_login FROM players WHERE id = $1",
                player_id
            )
            return dict(row) if row else None

    async def create_player(self, username: str, password_raw: str, email: Optional[str] = None) -> Optional[int]:
        """Registra un nuevo jugador con contraseña cifrada (bcrypt). Devuelve el ID generado."""
        salt = bcrypt.gensalt(rounds=12)
        pwd_hash = bcrypt.hashpw(password_raw.encode('utf-8'), salt).decode('utf-8')

        query = """
            INSERT INTO players (username, password_hash, email) 
            VALUES ($1, $2, $3) 
            RETURNING id;
        """
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, username, pwd_hash, email)
                return row["id"] if row else None
            except asyncpg.UniqueViolationError:
                print(f"[DB] Error: El usuario o email '{username}' ya existe.")
                return None

    async def verify_credentials(self, username: str, password_raw: str) -> Optional[Dict[str, Any]]:
        """
        Verifica usuario y contraseña.
        Si son correctos, actualiza 'last_login' y devuelve los datos del jugador.
        """
        player = await self.get_player_by_username(username)
        if not player:
            return None

        stored_hash = player["password_hash"].encode('utf-8')
        if bcrypt.checkpw(password_raw.encode('utf-8'), stored_hash):
            async with self.pool.acquire() as conn:
                await conn.execute("UPDATE players SET last_login = CURRENT_TIMESTAMP WHERE id = $1", player["id"])
            return player
        return None

    async def list_players(self) -> List[Dict[str, Any]]:
        """Devuelve un listado de todos los jugadores registrados (sin exponer hashes)."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, username, email, created_at, last_login FROM players ORDER BY id ASC;")
            return [dict(r) for r in rows]


# Instancia singleton para importación directa
db = Database()
