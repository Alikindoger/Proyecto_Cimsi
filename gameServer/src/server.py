import asyncio
import websockets
import json

ip = "127.0.0.1"
port = 8081

connected_players = []


async def init(webs):
    message = {}
    for ws in connected_players:
        message.clear()
        message["TYPE"]="INIT"
        message["ID"]= ws.id.int
        #pasar posicion, nombre...
        await unicast(message,webs)

async def player_reset(ws):
    message = {"TYPE":"PLAYER_RESET","ID": ws.id.int}
    await broadcast(message,ws)

async def unicast(message,ws):
    await ws.send(json.dumps(message))

async def broadcast(message, avoid_ws = -1):
    for ws in connected_players:

        if avoid_ws.id.int == ws.id.int:
            continue
        await ws.send(json.dumps(message))  # Envia el json al cliente

async def handler(websocket):
    print("¡Cliente conectado!")



    #comprobación token

    connected_players.append(websocket)
    #envia toda al informacion del resto de jugador conectados a todos los clientes
    await init(websocket)
    await player_reset(websocket)

    try:
        async for msg in websocket:
            print(msg)
    except websockets.ConnectionClosed:
        connected_players.remove(websocket)

async def main():
    print("Servidor escuchando")
    async with websockets.serve(handler, ip, port): # Abre la conexión con el cliente
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())