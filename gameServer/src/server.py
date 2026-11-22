import asyncio
import websockets
import json

# Parametros provisionales que se cambiarán cuando se despligue en la máquina
ip = "127.0.0.1"
port = 8081

# Lista que guarda todas las conexiones (websockets) de los usuarios conectados
connected_players = []

# Protocolo de inicio para que los usuarios que se conectan reciban la información sobre el servidor
async def init(webs):
    message = {}
    message["TYPE"] = "INIT"
    message["ID"] = webs.id.int
    await unicast(message, webs)

    for ws in connected_players:
        if ws != webs:
            message.clear()
            message["TYPE"] = "PLAYER_RESET"
            message["ID"] = ws.id.int
            await unicast(message, webs)

# Protocolo para que el resto de usuarios (ya conectados) sepan cuando otro se conecta al servidor
async def player_reset(ws):
    message = {"TYPE":"PLAYER_RESET","ID": ws.id.int}
    await broadcast(message,ws)

# Protocolo para cuando se desconecta un usuario
async def disconnect(ws):
    connected_players.remove(ws)
    message = {}
    message["TYPE"] = "DISCONNECT"
    message["ID"] = ws.id.int
    await broadcast(message, ws)

# Manda un mensaje a un solo usuario
async def unicast(message,ws):
    await ws.send(json.dumps(message))

# Manda mensaje a todos los usuarios (pudiendose exceptuar uno de forma opcional)
async def broadcast(message, avoid_ws = -1):
    for ws in connected_players:

        if avoid_ws.id.int == ws.id.int:
            continue
        await ws.send(json.dumps(message))  # Envia el json al cliente

# Función que realiza todos los protocolos necesarios al conectarse un usuario
async def handler(websocket):
    # Debug
    print("¡Cliente conectado!")
    
    #comprobación token (por implementar)

    # Se guarda la conexión entrante si el token es correcto
    connected_players.append(websocket)
    
    #envia toda al información a los 
    await init(websocket)
    await player_reset(websocket)

    try:
        async for msg in websocket:
            print(msg)
    except websockets.ConnectionClosed:
        await disconnect(websocket)
        
async def main():
    print("Servidor escuchando")
    async with websockets.serve(handler, ip, port): # Abre la conexión con el cliente
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
