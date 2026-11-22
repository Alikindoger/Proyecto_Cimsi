## ESTE CODIGO ES STATELESS, ES DECIR, NO TIENE POR QUE ESTAR EN UNA MAQUINA EN CONCRETO Y 
## SU CAIDA NO ES TAN GRAVE COMO POR EJEMPLO LA DE LA BASE DE DATOS

import asyncio
import json
import os
import secrets
import asyncpg
import bcrypt
import redis.asyncio as redis
import websockets

TOKEN_INACTIVO = 900 # 15 MIN DE TOKEN SIN ACTIVAR JUGANDO
TOKEN_ACTIVO = 86400 # 1 DIA DE TOKEN AL DEJAR DE JUGAR
TOKEN_JUGANDO = 7776000 # 3 MESES DE TOKEN MIENTRAS ESTÉ EN PARTIDA

REDIS_HOST = os.getenv("REDIS_HOST", "redis") # VALOR DE LA V.E O "redis" SI NO LO ENCUENTRA (NOMBRE SERVICIO)
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379)) # VALOR DE LA V.E O EL PUERTO 6379 SI NO LO ENCUENTRA
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "cimsi2627") # VALOR DE LA V.E O "cimsi2627" SI NO LO ENCUENTRA

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres") # VALOR DE LA V.E O "postgres" SI NO LO ENCUENTRA (NOMBRE SERVICIO)
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432)) # VALOR DE LA V.E O EL PUERTO 5432 SI NO LO ENCUENTRA
POSTGRES_DB = os.getenv("POSTGRES_DB", "cimsi_game") # VALOR DE LA V.E O "cimsi_game" SI NO LO ENCUENTRA
POSTGRES_USER = os.getenv("POSTGRES_USER", "cimsi_user") # VALOR DE LA V.E O "cimsi_user" SI NO LO ENCUENTRA
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "cimsi2627") # VALOR DE LA V.E O "cimsi2627" SI NO LO ENCUENTRA

cliente_redis = redis.Redis( # VARIABLE QUE USAMOS PARA INTERACTUAR CON REDIS PARA LA GESTION DE SESIONES
    host=REDIS_HOST, 
    port=REDIS_PORT,
    password=REDIS_PASSWORD or None,
    decode_responses=True # TRADUCE LOS DATOS A FORMATO STRING
)
db_pool = None

# GUARDAMOS DOBLE CLAVE PARA PODER VERIFICAR SOLO CON EL TOKEN SIN NECESIDAD DEL NOMBRE DE USUARIO
async def guardar_token_redis(user_name, token, ttl):
    await cliente_redis.set(f"usuario:{user_name}", token, ex=ttl) # GUARDA TOKEN ASOCIADO A USUARIO (SI YA EXISTÍA, LO SOBREESCRIBE)
    await cliente_redis.set(f"token:{token}", user_name, ex=ttl) # PERMITE INICIAR SESION UNICAMENTE CON EL TOKEN SI EL CLIENTE LO TIENE

# FUNCION QUE SE ENCARGA DE CAMBIAR EL TTL DE CADA TOKEN
async def refresh_token_ttl(user_name, token, ttl):
    await cliente_redis.expire(f"usuario:{user_name}", ttl)
    await cliente_redis.expire(f"token:{token}", ttl)

# FUNCIÓN ENCARGADA DE VALIDAR LOS TOKENS
async def validate_user_token(token):  
    if not isinstance(token, str) or not token:
        return None
    user_name = await cliente_redis.get(f"token:{token}")
    if not user_name:
        return None
    token_guardado = await cliente_redis.get(f"usuario:{user_name}")
    return user_name if token_guardado == token else None # DEVUELVE EL NOMBRE PARA QUE GODOT SEPA QUIEN ES EL JUGADOR

# FUNCIÓN ENCARGADA DE GENERAR UN TOKEN A UN USUARIO CONCRETO
def generate_new_token(user_name):
    return f"token_{user_name}_{secrets.token_urlsafe(32)}"


# FUNCIÓN CORE QUE SE ENCARGA DE TODA LA LÓGICA DE TOKEN MANAGER
async def manage_connections(websocket):
    try:
        mensaje_inicial = await websocket.recv() # SE ESPERA AL MENSAJE A EVALUAR (ACTIVANDO SU RESPECTIVO PROTOCOLO)
        data_in = json.loads(mensaje_inicial) # SE CARGA DICHO MENSAJE
        if not isinstance(data_in, dict): # SE COMPRUEBA SI EL MENSAJE SIGUE EL FORMATO VÁLIDO DE DICCIONARIO JSON
            await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Formato inválido"}))
            await websocket.close()
            return

        # SI ES UN DICCIONARIO JSON CORRECTO, ENTONCES COMPROBAMOS QUE ACCION DEBEMOS EVALUAR
        accion = data_in.get("ACTION")  

        if accion == "registro": # SI LA ACCION ES REGISTRARSE, INICIAMOS DICHO PROTOCOLO
            user_name = data_in.get("NAME")
            password = data_in.get("PASSWORD")
            email = data_in.get("EMAIL") # (OPCIONAL)

            if not user_name or not isinstance(user_name, str) or not password or not isinstance(password, str):
                await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Datos inválidos"}))
                await websocket.close()
                return
            
            # ENCRIPTACIÓN DE CONTRASEÑA PARA QUE EL SERVICIO SEA SEGURO 
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

            try:
                # GUARDAMOS EN LA DB PERSISTENTE EL USERNAME, SU CONTRASEÑA Y SU CORREO (OPCIONAL)
                async with db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "INSERT INTO players (username, password_hash, email) VALUES ($1, $2, $3) RETURNING id",
                        user_name, hashed_password, email
                    )
                    player_id = row["id"]
            # SI EL EMAIL O EL USERNAME YA ESTÁN EN LA DB, LANZA ERROR
            except asyncpg.UniqueViolationError:
                await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Usuario o email ya registrado"}))
                await websocket.close()
                return

            # SI HA SALIDO BIEN, GENERA UN TOKEN Y SE LO MANDA A REDIS CON UN TTL DE 15 MIN
            nuevo_token = generate_new_token(user_name)
            await guardar_token_redis(user_name, nuevo_token, TOKEN_INACTIVO)

            # ENVIAMOS EL TOKEN, EL NOMBRE Y EL ID AL CLIENTE
            await websocket.send(json.dumps({
                "TYPE": "registro",
                "ID": player_id, # REALMENTE NO ES NECESARIO, PERO LO ENVÍO POR SI PUEDE FACILITAR ALGUNA TAREA TENER EL ID DE USUARIO
                "NAME": user_name,
                "TOKEN": nuevo_token
            }))
            await websocket.close()

        elif accion == "iniciar_sesion":
            user_name = data_in.get("NAME") 
            token_recibido = data_in.get("TOKEN") # EN GODOT SE DEBERÍA MANDAR EL TOKEN PARA EVITAR USAR CONTRASEÑA CONSTANTEMENTE
            password = data_in.get("PASSWORD") 

            if token_recibido: # INICIO DE SESION CON TOKEN
                usuario_del_token = await validate_user_token(token_recibido)
                if usuario_del_token: # SI NOS HA DEVUELTO UN NOMBRE, ENTONCES EL TOKEN ERA VALIDO
                    await refresh_token_ttl(usuario_del_token, token_recibido, TOKEN_ACTIVO) 
                    await websocket.send(json.dumps({
                        "TYPE": "sesion_valida",
                        "NAME": usuario_del_token,
                        "TOKEN": token_recibido,
                        "MESSAGE": "Sesión activa verificada"
                    }))
                    await websocket.close()
                    return
                else: #SI EL TOKEN ES INVÁLIDO (FALSO O CADUCADO), DEBEMOS HACER QUE EL CLIENTE INICIE SESION CON USUARIO Y CONTRASEÑA 
                    await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Token caducado"}))
                    await websocket.close()
                    return

            if not user_name or not isinstance(user_name, str) or not password or not isinstance(password, str):
                await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Datos de inicio de sesión inválidos"}))
                await websocket.close()
                return

            async with db_pool.acquire() as conn:
                player = await conn.fetchrow( # BUSCAMOS EN LA DB PERSISTENTE SI EXISTE TAL JUGADOR
                    "SELECT id, password_hash FROM players WHERE username = $1",
                    user_name
                )
                if not player or not bcrypt.checkpw(password.encode("utf-8"), player["password_hash"].encode("utf-8")): # SI EL USUARIO O LA CONTRASEÑA SON INCORRECTOS, ERROR
                    await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Credenciales incorrectas"}))
                    await websocket.close()
                    return

                await conn.execute("UPDATE players SET last_login = CURRENT_TIMESTAMP WHERE id = $1", player["id"]) # ACTUALIZAMOS EN LA DB PERSISTENTE LA COLUMNA DE ULTIMO LOGIN

            token_existente = await cliente_redis.get(f"usuario:{user_name}")
            if token_existente: # SI EFECITVAMENTE TENÍA TOKEN VÁLIDO, SE LO DAMOS
                await refresh_token_ttl(user_name, token_existente, TOKEN_ACTIVO)
                await websocket.send(json.dumps({
                    "TYPE": "sesion_valida",
                    "ID": player["id"],
                    "NAME": user_name,
                    "TOKEN": token_existente,
                    "MESSAGE": "Token vigente devuelto"
                }))
                await websocket.close()
                return

            nuevo_token = generate_new_token(user_name) # SI NO TENÍA TOKEN VÁLIDO LE DAMOS UNO NUEVO
            await guardar_token_redis(user_name, nuevo_token, TOKEN_ACTIVO)
            await websocket.send(json.dumps({
                "TYPE": "token_renovado",
                "ID": player["id"],
                "NAME": user_name,
                "TOKEN": nuevo_token,
                "MESSAGE": "Nuevo token generado"
            }))
            await websocket.close()

        elif accion == "validar_token": # PROTOCOLO ENCARGADO DE UNA VALIDACIÓN DE TOKEN PUNTUAL 
            token_recibido = data_in.get("TOKEN")
            usuario_del_token = await validate_user_token(token_recibido)

            if usuario_del_token:
                await websocket.send(json.dumps({
                    "TYPE": "token_valido",
                    "VALID": True,
                    "NAME": usuario_del_token
                }))
            else:
                await websocket.send(json.dumps({
                    "TYPE": "ERROR",
                    "VALID": False,
                    "MESSAGE": "Token inválido o caducado"
                }))
            await websocket.close()

        elif accion == "jugar": # SI LE DAMOS AL BOTÓN "JUGAR" INICIA ESTE PROTOCOLO
            token_recibido = data_in.get("TOKEN")
            usuario_del_token = await validate_user_token(token_recibido) # COMPROBAMOS SI EL TOKEN ES VÁLIDO Y USAMOS EL NOMRBE OBTENIDO MAS ADELANTE

            if usuario_del_token:
                await refresh_token_ttl(usuario_del_token, token_recibido, TOKEN_JUGANDO) # PONEMOS EL TTL A 3 MESES
                await websocket.send(json.dumps({
                    "TYPE": "sistema",
                    "MESSAGE": "TTL actualizado a jugando"
                }))
            else:
                await websocket.send(json.dumps({
                    "TYPE": "ERROR",
                    "MESSAGE": "Token inválido o caducado"
                }))
            await websocket.close()

        elif accion == "cerrar_sesion": # POR ÚLTIMO SI CERRAMOS SESIÓN, INICIAMOS ESTE PROTOCOLO
            token_recibido = data_in.get("TOKEN")
            usuario_del_token = await validate_user_token(token_recibido)

            if usuario_del_token: # SI HAY TOKEN VÁLIDO, LE CAMBIAMOS SU TTL A UN DÍA
                await refresh_token_ttl(usuario_del_token, token_recibido, TOKEN_ACTIVO)
                await websocket.send(json.dumps({"TYPE": "sistema", "MESSAGE": "Fecha de caducidad actualizada"}))
            await websocket.close() # SI NO HAY TOKEN VÁLIDO AL CERRAR LA SESIÓN (SI CADUCA EN MEDIO DE LA SESIÓN), NO PASA NADA

        else:
            await websocket.send(json.dumps({"TYPE": "ERROR", "MESSAGE": "Acción no reconocida"}))
            await websocket.close()

    except (websockets.exceptions.ConnectionClosed, json.JSONDecodeError):
        pass


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

    try:
        async with websockets.serve(manage_connections, "0.0.0.0", 8765):
            print("tokenManager escuchando en puerto 8765")
            await asyncio.Future()
    finally:
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(main())
