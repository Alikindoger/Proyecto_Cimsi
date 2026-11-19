## ESTE CODIGO ES STATELESS, ES DECIR, NO TIENE POR QUE ESTAR EN UNA MAQUINA EN CONCRETO

import asyncio
import json
import os
import secrets
import asyncpg
import bcrypt
import redis.asyncio as redis
import websockets

TOKEN_INACTIVO = 60*15
TOKEN_ACTIVO = 60*60*24
TOKEN_JUGANDO = 60*60*24*30*3
CANAL_JUEGO = "canal_juego"

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "cimsi2627")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "cimsi_game")
POSTGRES_USER = os.getenv("POSTGRES_USER", "cimsi_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "cimsi2627")

cliente_redis = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD or None,
    decode_responses=True
)

db_pool = None
jugadores_conectados = set()


async def validate_user_token(user_name, token):
    if not isinstance(user_name, str) or not user_name:
        return False
    if not isinstance(token, str) or not token:
        return False
    token_guardado = await cliente_redis.get(f"usuario:{user_name}")
    return token_guardado is not None and token_guardado == token


def generate_new_token(user_name):
    return f"token_{user_name}_{secrets.token_urlsafe(32)}"


async def redis_listener():
    pubsub = cliente_redis.pubsub()
    await pubsub.subscribe(CANAL_JUEGO)
    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            payload = data.get("payload")
            if payload and jugadores_conectados:
                websockets.broadcast(jugadores_conectados, payload)


async def manage_connections(websocket):
    try:
        mensaje_inicial = await websocket.recv()
        data_in = json.loads(mensaje_inicial)
        if not isinstance(data_in, dict):
            await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Formato inválido"}))
            await websocket.close()
            return

        accion = data_in.get("ACTION")

        if accion == "registro":
            user_name = data_in.get("NAME")
            password = data_in.get("PASSWORD")
            email = data_in.get("EMAIL")

            if not user_name or not isinstance(user_name, str) or not password or not isinstance(password, str):
                await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Datos inválidos"}))
                await websocket.close()
                return

            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

            try:
                async with db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "INSERT INTO players (username, password_hash, email) VALUES ($1, $2, $3) RETURNING id",
                        user_name, hashed_password, email
                    )
                    player_id = row["id"]
            except asyncpg.UniqueViolationError:
                await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Usuario o email ya registrado"}))
                await websocket.close()
                return

            nuevo_token = generate_new_token(user_name)
            await cliente_redis.set(f"usuario:{user_name}", nuevo_token, ex=TOKEN_INACTIVO)

            await websocket.send(json.dumps({
                "TYPE": "registro",
                "ID": player_id,
                "TOKEN": nuevo_token
            }))
            await websocket.close()

        elif accion == "iniciar_sesion":
            user_name = data_in.get("NAME")
            token_recibido = data_in.get("TOKEN")
            password = data_in.get("PASSWORD")

            if not user_name or not isinstance(user_name, str):
                await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Nombre inválido"}))
                await websocket.close()
                return

            if token_recibido and await validate_user_token(user_name, token_recibido):
                await cliente_redis.expire(f"usuario:{user_name}", TOKEN_ACTIVO)
                await websocket.send(json.dumps({
                    "TYPE": "sesion_valida",
                    "TOKEN": token_recibido,
                    "MESSAGE": "Sesión activa verificada"
                }))
                await websocket.close()
                return

            if password and isinstance(password, str):
                async with db_pool.acquire() as conn:
                    player = await conn.fetchrow(
                        "SELECT id, password_hash FROM players WHERE username = $1",
                        user_name
                    )
                    if not player or not bcrypt.checkpw(password.encode("utf-8"), player["password_hash"].encode("utf-8")):
                        await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Credenciales incorrectas"}))
                        await websocket.close()
                        return

                    await conn.execute("UPDATE players SET last_login = CURRENT_TIMESTAMP WHERE id = $1", player["id"])

                token_existente = await cliente_redis.get(f"usuario:{user_name}")
                if token_existente:
                    await cliente_redis.expire(f"usuario:{user_name}", TOKEN_ACTIVO)
                    await websocket.send(json.dumps({
                        "TYPE": "sesion_valida",
                        "ID": player["id"],
                        "TOKEN": token_existente,
                        "MESSAGE": "Token vigente devuelto"
                    }))
                    await websocket.close()
                    return

                nuevo_token = generate_new_token(user_name)
                await cliente_redis.set(f"usuario:{user_name}", nuevo_token, ex=TOKEN_ACTIVO)
                await websocket.send(json.dumps({
                    "TYPE": "token_renovado",
                    "ID": player["id"],
                    "TOKEN": nuevo_token,
                    "MESSAGE": "Nuevo token generado"
                }))
                await websocket.close()
                return

            await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Token caducado"}))
            await websocket.close()

        elif accion == "validar_token":
            user_name = data_in.get("NAME")
            token_recibido = data_in.get("TOKEN")

            if await validate_user_token(user_name, token_recibido):
                await cliente_redis.expire(f"usuario:{user_name}", TOKEN_JUGANDO)
                await websocket.send(json.dumps({
                    "TYPE": "token_valido",
                    "VALYD": True
                }))
            else:
                await websocket.send(json.dumps({
                    "TYPE": "ERROR",
                    "VALYD": False,
                    "MESSAGE": "Token inválido o caducado"
                }))
            await websocket.close()

        elif accion == "jugar":
            user_name = data_in.get("NAME")
            token_recibido = data_in.get("TOKEN")

            if not await validate_user_token(user_name, token_recibido):
                await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Token inválido"}))
                await websocket.close()
                return

            await cliente_redis.expire(f"usuario:{user_name}", TOKEN_JUGANDO)
            jugadores_conectados.add(websocket)
            await websocket.send(json.dumps({"TYPE": "sistema", "MESSAGE": "Acceso concedido"}))

            async for message in websocket:
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    continue
                if isinstance(data, dict):
                    await cliente_redis.publish(CANAL_JUEGO, json.dumps({"payload": message}))

        elif accion == "cerrar_sesion":
            user_name = data_in.get("NAME")
            token_recibido = data_in.get("TOKEN")

            if await validate_user_token(user_name, token_recibido):
                await cliente_redis.expire(f"usuario:{user_name}", TOKEN_INACTIVO)
            await websocket.send(json.dumps({"TYPE": "sistema", "MESSAGE": "Fecha de caducidad actualizada"}))
            await websocket.close()

        else:
            await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Acción no reconocida"}))
            await websocket.close()

    except (websockets.exceptions.ConnectionClosed, json.JSONDecodeError):
        pass
    finally:
        jugadores_conectados.discard(websocket)


async def main():
    global db_pool
    db_pool = await asyncpg.create_pool(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        min_size=2,
        max_size=10
    )

    asyncio.create_task(redis_listener())
    try:
        async with websockets.serve(manage_connections, "0.0.0.0", 8765):
            print("tokenManager escuchando en puerto 8765")
            await asyncio.Future()
    finally:
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
