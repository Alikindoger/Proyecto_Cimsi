"""
Script de prueba de integración con PostgreSQL (solo tabla players).
Ejecución: python example_usage.py
"""

import asyncio
from db_helper import db

async def test_workflow():
    print("--- INICIANDO PRUEBA DE INTEGRACIÓN POSTGRESQL (PLAYERS) ---")
    await db.connect()

    # 1. Consultar un jugador existente
    username = "player1"
    player = await db.get_player_by_username(username)
    if player:
        print(f"\n1. Jugador encontrado: ID={player['id']}, Username='{player['username']}', Email='{player['email']}'")
    else:
        print(f"\n1. Jugador '{username}' no encontrado.")

    # 2. Verificar credenciales con contraseña correcta ('cimsi2627')
    auth_ok = await db.verify_credentials("player1", "cimsi2627")
    print(f"2. Verificación de credenciales ('player1', 'cimsi2627'): {'EXITOSA' if auth_ok else 'FALLIDA'}")

    # 3. Probar verificación con contraseña incorrecta
    auth_fail = await db.verify_credentials("player1", "password_falsa")
    print(f"3. Verificación con contraseña errónea: {'FALLIDA (Correcto)' if not auth_fail else 'ERROR'}")

    # 4. Listar jugadores cargados en la base de datos
    players_list = await db.list_players()
    print(f"\n4. Total de jugadores registrados: {len(players_list)}")
    for p in players_list:
        print(f"   - [ID {p['id']}] {p['username']} ({p['email']})")

    await db.disconnect()
    print("\n--- PRUEBA COMPLETADA CON ÉXITO ---")

if __name__ == "__main__":
    import os
    if "POSTGRES_HOST" not in os.environ:
        os.environ["POSTGRES_HOST"] = "127.0.0.1"
    asyncio.run(test_workflow())
