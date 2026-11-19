#!/usr/bin/env bash
# ==============================================================================
# SCRIPT DE DIAGNÓSTICO Y VERIFICACIÓN DE POSTGRESQL
# Comprueba conexión y jugadores cargados
# ==============================================================================

CONTAINER_NAME=${1:-"cimsi_postgres"}
DB_NAME=${2:-"cimsi_game"}
DB_USER=${3:-"cimsi_user"}

echo "=== DIAGNÓSTICO POSTGRESQL (CIMSI) ==="
echo "Contenedor: ${CONTAINER_NAME}"
echo "Base de datos: ${DB_NAME}"
echo "Usuario: ${DB_USER}"
echo "--------------------------------------"

# 1. Comprobar pg_isready
echo -n "1. Estado del servicio: "
if docker exec "${CONTAINER_NAME}" pg_isready -U "${DB_USER}" -d "${DB_NAME}" > /dev/null 2>&1; then
    echo "ONLINE (Aceptando conexiones)"
else
    echo "OFFLINE o no responde"
    exit 1
fi

# 2. Listar tablas y recuento de filas
echo -e "\n2. Tablas creadas:"
docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "
SELECT 
    table_name,
    (xpath('/row/c/text()', query_to_xml(format('SELECT count(*) AS c FROM %I', table_name), false, true, '')))[1]::text::int AS row_count
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;
"

# 3. Mostrar jugadores registrados
echo -e "\n3. Jugadores registrados en 'players':"
docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "
SELECT id, username, email, created_at, last_login FROM players ORDER BY id;
"

echo "--------------------------------------"
echo "[OK] Verificación finalizada con éxito."
