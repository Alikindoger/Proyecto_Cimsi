#!/usr/bin/env bash
# ==============================================================================
# SCRIPT DE RESTAURACIÓN (POSTGRESQL - PROYECTO CIMSI)
# Restaura un volcado .sql.gz en PostgreSQL
# Uso: ./restore.sh <ruta_al_archivo_backup.sql.gz>
# ==============================================================================

set -euo pipefail

BACKUP_FILE=${1:-""}
CONTAINER_NAME=${2:-"cimsi_postgres"}
DB_NAME=${3:-"cimsi_game"}
DB_USER=${4:-"cimsi_user"}

if [ -z "${BACKUP_FILE}" ] || [ ! -f "${BACKUP_FILE}" ]; then
    echo "[ERROR] Debes especificar un archivo de backup válido."
    echo "Uso: $0 <archivo_backup.sql.gz> [nombre_contenedor] [nombre_db] [usuario_db]"
    exit 1
fi

echo "[ADVERTENCIA] Esto sobrescribirá / aplicará los datos en '${DB_NAME}'."
read -p "¿Deseas continuar? (s/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[sS]$ ]]; then
    echo "[CANCELADO] Restauración abortada por el usuario."
    exit 0
fi

echo "[INFO] Restaurando backup desde '${BACKUP_FILE}'..."
gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}"

echo "[OK] Restauración completada exitosamente."
