import asyncio
import websockets
import json
import secrets
import time

## UNA VEZ LEVANTADO EL SERVER DECIRLE A ALFONSO LA IP INTERNA Y ABRIR EL PUERTO 9100 PARA PROMETHEUS
## MI APLICACION CORRE POR DEFECTO EN EL PUERTO 8765

TOKEN_INACTIVO = 900  #Si un token no está activo (recién generado) se dispone de 15 minutos para usarlo
TOKEN_ACTIVO = 60*60*24 #Si un token está activo, es válido por un día

connected_players, tokens = set(), dict() # Diccionarios temporales para probar el código hasta que esté listo Redis

async def validate_token(token):
    if not isinstance(token, str) or not token: # Si el token no sigue el formato o no hay token devuelve falso para no continuar
        return False

    # TODO: Conectar con DB en el futuro
    await asyncio.sleep(0.2)  # Simulacion de consulta
    clean_expired_tokens() # Función a implementar en Redis para eliminar los token expirados
    return token in tokens # Devolvemos el token que hemos validado

async def generate_new_token(player_name):
    # Elegimos esta generación de 32 bytes ya que es más seguro y es el estándar para tokens
    random_code = secrets.token_urlsafe(32) 
    final_token = f"token_{player_name}_{random_code}" # Agregamos el nombre a el token para extender este y que sea más fácil de encontrar en la DB

    # TODO: Cuando José (PostgreSQL) o Pablo (Redis) tengan lista su parte, 
    # aquí añado la línea para insertar 'final_token' en sus bases de datos.

    print(f"[N] Nuevo token fabricado para {player_name}: {final_token}")
    return final_token

async def manage_connections(websocket):
    try:
        initial_message = await websocket.recv() #Se queda esperando hasta el primer mensaje del cliente
        data_in = json.loads(initial_message) #Carga este primer mensaje
        if not isinstance(data_in, dict): #Si los datos no siguen el formato JSON (Diccionario), falla
            await websocket.send(json.dumps({"tipo": "error", "mensaje": "Formato inválido."}))
            await websocket.close()
            return
        
        if data_in.get("accion") == "solicitar_token": # Si la accion es solicitar el token, entra en este bloque
            player_name = data_in.get("nombre") #Coge el nombre de este cliente
            clean_expired_tokens() # Se debe eliminar los token expirados
            used_names = {d["nombre"] for d in tokens.values()} # Creamos una memoria de nombres seleccionados para que no se repitan
            if player_name in used_names: #Si ya existe el nombre, fuera
                await websocket.send(json.dumps({"tipo":"error", "mensaje":"Nombre no disponible, prueba con otro"}))
                await websocket.close()
                return
            elif not player_name: # Si no hay nombre, fuera
                await websocket.send(json.dumps({"tipo":"error", "mensaje":"Nombre vacío"}))
                await websocket.close()
                return
            elif not isinstance(player_name, str): # Si el texto no sigue el formato texto, fuera
                await websocket.send(json.dumps({"tipo":"error", "mensaje":"Formato de texto inválido"}))
                await websocket.close()
                return
            
            new_token = await generate_new_token(player_name) # Si todo ha salido bien, creamos el token para este usuario
            tokens[new_token] = {"nombre":player_name, "expira":time.time() + TOKEN_INACTIVO} # Guardamos el nombre de usuario como valor y su token como clave
            
            await websocket.send(json.dumps({"tipo": "registro", "token": new_token}))
            await websocket.close()
            return
            
        elif data_in.get("accion") == "jugar": # Si la accion es jugar (Jugador ya validado previamente)
            recieved_token = data_in.get("token") # Cogemos el token
            is_valid = await validate_token(recieved_token) # Validamos el token por si ha expirado

            if not is_valid: # Si se decide que el token no es válido (ha caducado), fuera
                await websocket.send(json.dumps({"tipo": "error", "mensaje": "Token inválido o expirado."}))
                await websocket.close()
                return
            tokens[recieved_token]["expira"] = time.time() + TOKEN_ACTIVO # Cuando juegue, se reinicia el contador del token (1 día)
            connected_players.add(websocket) # Se añade el jugador a la memoria de jugadores conectados
            print(f"[V] Nuevo jugador validado. Online: {len(connected_players)}")
            await websocket.send(json.dumps({"tipo": "sistema", "mensaje": "Acceso concedido"})) #Enviamos al cliente que puede jugar

            async for message in websocket: # Una vez validado y se esté jugando, esperamos nuevos mensajes mediante espera activa
                try:
                    data = json.loads(message) # Cargammos el nuevo mensaje
                except json.JSONDecodeError: # Si el códigp es basura (No sigue el formato JSON) lo ignora
                    continue
                if not isinstance(data, dict): # Si sí es formato JSON y no sigue el formato de diccionario, también lo ignora
                    continue
                print(f"Recibido de un jugador: {data}")
                websockets.broadcast(connected_players - {websocket}, message) #Se envía a todos los jugadores la información
                                                                               #(Por ejemplo que un jugador se ha movió)
                        
        else: # Si no es ninguna acción reconocida, manda el error correspondiente
            await websocket.send(json.dumps({"tipo": "error", "mensaje": "Acción no reconocida."}))
            await websocket.close()
            return

    except websockets.exceptions.ConnectionClosed: # Si el jugador se ha desconectado, no se corta la conexión (aún)
        pass
    except json.JSONDecodeError: # Si se envía basura y el jugador no estaba conectado, se manda un mensaje de error
        print("Alerta: Se recibió un mensaje que no es formato JSON válido.")
    finally: #Bloque que cierra la conexión una vez el jugador se desconecta
        if websocket in connected_players:
            connected_players.remove(websocket)
            print(f"[D] Jugador desconectado. Online: {len(connected_players)}")

async def main():
    async with websockets.serve(manage_connections, "0.0.0.0", 8765): # Cada vez que alguien se quiera conectar, se pasa a la funcion manejadora.
                                                                      # Además que se escucha por todas las interfaces de red
        print("Servidor de Tokens arrancado y escuchando en el puerto 8765")
        await asyncio.Future() # Esto evita que el programa se cierre al llegar aquí (final del código)

def clean_expired_tokens(): # Función a implementar en Redis para la limpieza de tokens expirados
    now = time.time()
    for t in [t for t, d in tokens.items() if d["expira"] < now]:
        del tokens[t]

if __name__ == "__main__":
    asyncio.run(main())