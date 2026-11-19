#!/usr/bin/env bash
# ==============================================================================
# SCRIPT DE COPIA DE SEGURIDAD (POSTGRESQL - PROYECTO CIMSI)
# Guarda un volcado comprimido en el disco SSD externo del Worker 1
# ==============================================================================

set -euo pipefail

CONTAINER_NAME=${1:-"cimsi_postgres"}
DB_NAME=${2:-"cimsi_game"}
DB_USER=${3:-"cimsi_user"}
BACKUP_DIR=${4:-"/mnt/ssd/backups"}
DATE=$(date +"%Y%m%d_%H%M%S")
FILENAME="${BACKUP_DIR}/backup_${DB_NAME}_${DATE}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "[INFO] Iniciando backup de la base de datos '${DB_NAME}'..."
docker exec -t "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" | gzip > "${FILENAME}"

echo "[OK] Backup completado exitosamente en: ${FILENAME}"
ls -lh "${FILENAME}"
